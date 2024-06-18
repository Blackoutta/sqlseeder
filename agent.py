import queue
import re
import uuid

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from loguru import logger

from db_tool import DbTool
from ddl_loader import load_ddl_postgres_13
from prompt_gen import get_gen_prompt, GenPromptOutputParser
from prompt_revise import get_revise_prompt, RevisePromptOutputParser, get_revise_request_prompt
from tree_walker import build_tree, traverse_and_collect_names


class Agent:
    def __init__(self,
                 ddl_dict: dict,
                 db_conn_param: dict,
                 model: str,
                 loop_cnt=30,
                 api_key=None,
                 api_base_url=None,
                 temperature: float = 0,
                 max_tokens: int = 18000,
                 ):
        self.ddl_dict = ddl_dict  # ddl
        self.queue = queue.Queue()
        self.counter = {}  # 表计数
        self.generated = {}  # 已生成的SQL
        self.optimized = []  # 已优化的SQL
        self.llm = ChatOpenAI(model=model,
                              temperature=temperature,
                              verbose=True,
                              max_tokens=max_tokens,
                              api_key=api_key,
                              base_url=api_base_url,
                              )
        self.threshold = 1
        self.db_tool = DbTool(db_conn_param)
        self.store = {}
        self.loop_cnt = loop_cnt

    def revise_loop(self, stmt, err):
        """
        将问题语句和错误输入给大模型, 让它以reAct的自循环形式来尝试修复问题, 并最终将数据成功插入到数据库

        :param stmt: 有问题的插入语句
        :param err:  具体问题
        :return: 错误信息, 为None表示没有错误
        """
        logger.warning(f"revising stmt: {stmt}")
        session_id = str(uuid.uuid4())
        chain: Runnable = (get_revise_prompt() | self.llm | RevisePromptOutputParser())
        with_message_history = RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history",
            output_messages_key='output'
        )
        result = with_message_history.invoke(
            input={"input": get_revise_request_prompt().format(stmt=stmt, err=err)},
            config={"configurable": {"session_id": session_id}},
        )

        next_step = result['parsed']
        next_tool = next_step['tool_name']

        tools = {
            'get_next_valid_id': self.db_tool.execute_sql_query,
            'get_data_example_by_table': self.db_tool.get_data_example_by_table,
            'insert_to_db': self.db_tool.execute_sql_insert,
            'check_table_ddl': self.ddl_dict.get,
        }

        for i in range(self.loop_cnt):
            logger.info(f"revision attempt {i + 1}")
            if next_tool == 'finish':
                logger.success('revise finished!')
                return None
            func = tools.get(next_tool)
            if func is None:
                raise ValueError(f"invalid next tool: {next_tool}")
            tool_param = next_step['tool_input']
            exec_result = func(tool_param)
            logger.debug(f'tool call result: {exec_result}')
            result = with_message_history.invoke(
                input={"input": f"tool call: {next_tool} returned: {exec_result}"},
                config={"configurable": {"session_id": session_id}},
            )
            next_step = result['parsed']
            next_tool = next_step['tool_name']
        return f"problem not solved after {self.loop_cnt} loops, cancel operation"

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def save(self):
        for data in self.optimized:
            if data is None:
                continue
            stmts = data['stmts']
            for stmt in stmts:
                if stmt is None:
                    continue
                insert_err = self.db_tool.execute_sql_insert(stmt)
                if insert_err is None:
                    continue
                # 进入修正循环
                print(insert_err)
                revise_err = self.revise_loop(stmt, insert_err)
                if revise_err is not None:
                    logger.error(revise_err)
                    return
        logger.success("All statements inserted!")

    def generate(self, target_table: str):
        self.queue.put(target_table)

        while not self.queue.empty():
            logger.debug(f'current queue size: {self.queue.qsize()}')
            target = self.queue.get()
            logger.info(f'generating for target: {target}')
            # 获取目标表DLL
            ddl = self.ddl_dict.get(target)
            if ddl is None:
                continue

            # 获取目标表已生成的语句
            history = self.history_as_prompt(target)

            # 大语言模型生成语句
            gen_chain: Runnable = (get_gen_prompt() | self.llm | GenPromptOutputParser())
            result = gen_chain.invoke({"ddl": ddl, "history": history})

            # 记录生成的语句
            stmt = result['statement']
            fts = result['foreign_tables']
            logger.success(f'generated: {stmt}')
            if self.generated.get(target) is not None:
                self.generated[target]['stmts'].append(stmt)
            else:
                self.generated[target] = {'stmts': [stmt], 'foreign_tables': fts}

            logger.debug(f'foreign tables: {fts}')
            for ft in fts:
                # 跳过自依赖
                if ft.lower() == target.lower():
                    continue
                if ft not in self.counter:
                    self.counter[ft] = 1
                else:
                    self.counter[ft] = self.counter[ft] + 1

                if self.counter[ft] <= self.threshold:
                    logger.debug(f'enqueue: {ft}')
                    self.queue.put(ft)
        root = build_tree(self.generated)
        tables_in_order = traverse_and_collect_names(root)
        for table in tables_in_order:
            self.optimized.append(self.generated.get(table))
        logger.success('All statements generated!')

    def history_as_prompt(self, target) -> str:
        his = self.db_tool.get_data_example_by_table(target)
        if his is None or len(his) == 0:
            return ""
        logger.debug(f'existing data: {his}')
        return str(his)

    def extract_table_name(self, s):
        # 使用正则表达式匹配表名
        match = re.search(r'insert\s+into\s+(\w+)', s, re.IGNORECASE)
        if match:
            return match.group(1)
        return None


if __name__ == '__main__':
    with open('test_data/ddl.txt', 'r') as f:
        d = load_ddl_postgres_13(f.read())

    db_conn_param = {
        'dbname': 'forex_hdge',
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'port': '5432'
    }
    agent = Agent(ddl_dict=d,
                  db_conn_param=db_conn_param,
                  loop_cnt=30,
                  model='glm-4-9b-chat',
                  api_key='EMPTY',
                  api_base_url='"http://localhost:6006/v1"',
                  temperature=0.0,
                  max_tokens=18000,
                  )
    agent.generate('trading_task')
    agent.save()

    print("ALL DONE!!!")
