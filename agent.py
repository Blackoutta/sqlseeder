import queue
import re
import uuid

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from db_tool import DbTool
from ddl_loader import load_ddl
from prompt_gen import get_gen_prompt, GenPromptOutputParser
from prompt_revise import get_revise_prompt, RevisePromptOutputParser, get_revise_request_prompt
from tree_walker import build_tree, traverse_and_collect_names


class Agent:
    def __init__(self, ddl_dict: dict, db_conn_param: dict, loop_cnt: int):
        self.ddl_dict = ddl_dict  # ddl
        self.queue = queue.Queue()
        self.counter = {}  # 表计数
        self.generated = {}  # 已生成的SQL
        self.optimized = []  # 已优化的SQL
        self.gen_history = {}  # 已生成SQL的记录，注入到prompt中让大语言模型尽量避开重复的数据
        self.model = 'glm-4-9b-chat'
        self.llm = ChatOpenAI(model=self.model,
                              temperature=0,
                              verbose=True,
                              max_tokens=18000,
                              api_key="EMPTY",
                              base_url="http://localhost:6006/v1",
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
        session_id = str(uuid.uuid4())
        chain = (get_revise_prompt() | self.llm | RevisePromptOutputParser())
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
            if next_tool == 'finish':
                print('revise finished!')
                return None
            func = tools.get(next_tool)
            if func is None:
                raise ValueError(f"invalid next tool: {next_tool}")
            tool_param = next_step['tool_input']
            exec_result = func(tool_param)
            print(f'tool call result: {exec_result}')
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
            if data is not None:
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
                    raise ValueError(revise_err)
        print("All statements inserted!")

    def generate(self, target_table: str):
        self.queue.put(target_table)

        while not self.queue.empty():
            print(f'current queue size: {self.queue.qsize()}')
            target = self.queue.get()
            print(f'generating for target: {target}')
            # 获取目标表DLL
            ddl = self.ddl_dict.get(target)
            if ddl is None:
                continue

            # 获取目标表已生成的语句
            history = self.history_as_prompt(target)
            # print(f'history: {history}')

            # 大语言模型生成语句
            # print(f'ddl: {ddl}')
            gen_chain = (get_gen_prompt() | self.llm | GenPromptOutputParser())
            result = gen_chain.invoke({"ddl": ddl, "history": history})
            # ctx = result['context']
            # print(f'context: {ctx}')

            # 记录生成的语句
            stmt = result['statement']
            fts = result['foreign_tables']
            print(f'generated: {stmt}')
            if self.generated.get(target) is not None:
                self.generated[target]['stmts'].append(stmt)
            else:
                self.generated[target] = {'stmts': [stmt], 'foreign_tables': fts}

            # 记录生成语句历史
            if self.gen_history.get(target) is not None:
                self.gen_history[target].append(stmt)
            else:
                self.gen_history[target] = [stmt]

            print(f'foreign tables: {fts}')
            for ft in fts:
                # 跳过自依赖
                if ft.lower() == target.lower():
                    continue
                if ft not in self.counter:
                    self.counter[ft] = 1
                else:
                    self.counter[ft] = self.counter[ft] + 1

                if self.counter[ft] <= self.threshold:
                    print(f'enqueue: {ft}')
                    self.queue.put(ft)
        root = build_tree(self.generated)
        tables_in_order = traverse_and_collect_names(root)
        for table in tables_in_order:
            self.optimized.append(self.generated.get(table))
        print('All statements generated!')

    def history_as_prompt(self, target) -> str:
        his = self.gen_history.get(target)
        if his is None:
            return ""
        return '\n'.join(his)

    def extract_table_name(self, s):
        # 使用正则表达式匹配表名
        match = re.search(r'insert\s+into\s+(\w+)', s, re.IGNORECASE)
        if match:
            return match.group(1)
        return None


if __name__ == '__main__':
    with open('./ddl.txt', 'r') as f:
        d = load_ddl(f.read())

    db_conn_param = {
        'dbname': 'forex_hdge',
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'port': '5432'
    }

    agent = Agent(ddl_dict=d, db_conn_param=db_conn_param, loop_cnt=25)
    agent.generate('trading_task')

    # agent.save()

    print("ALL DONE!!!")
