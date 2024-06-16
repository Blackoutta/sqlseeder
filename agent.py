import queue
import re
from collections import deque

from langchain_openai import ChatOpenAI

from db_tool import DbTool
from ddl_loader import load_ddl
from prompt_gen import get_gen_prompt, GenPromptOutputParser


class Agent:
    def __init__(self, ddl_dict: dict, db_conn_param: dict):
        self.ddl_dict = ddl_dict  # ddl
        self.queue = queue.Queue()
        self.counter = {}  # 表计数
        self.generated = {}  # 已生成的SQL
        self.optimized = {}  # 已优化的SQL
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

    def revise_loop(self, stmt):
        pass

    def save(self):
        for data in self.optimized:
            stmts = data['stmts']
            for stmt in stmts:
                insert_err = self.db_tool.execute_sql_insert(stmt)
                if insert_err is None:
                    continue
                # 进入修正循环
                print(insert_err)
                revise_err = self.revise_loop(stmt)
                if revise_err is not None:
                    raise ValueError(revise_err)

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
        tree = self.build_dependency_tree(self.generated, target_table)
        self.optimized = self.bfs_dependency_tree(tree)

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

    def build_dependency_tree(self, data, start_table):
        # 定义一个内部函数来递归构建依赖树
        def recurse(table):
            # 获取当前表的数据
            table_data = data.get(table)
            if not table_data:
                return None

            # 构建当前表的依赖节点
            node = {
                'table': table,
                'stmts': table_data['stmts'],  # SQL插入语句
                'dependencies': []  # 子依赖
            }

            # 递归处理当前表的外键表
            for foreign_table in table_data['foreign_tables']:
                child_node = recurse(foreign_table)
                if child_node:
                    node['dependencies'].append(child_node)

            return node

        # 从起始表名开始递归构建依赖树
        return recurse(start_table)

    def bfs_dependency_tree(self, dependency_tree):
        # 如果树为空，直接返回空列表
        if not dependency_tree:
            return []

        # 初始化队列，将根节点加入队列
        queue = deque([dependency_tree])
        # 存储遍历顺序的表名列表
        table_list = []

        # 当队列不为空时，进行广度优先遍历
        while queue:
            # 从队列中取出一个节点
            current_node = queue.popleft()
            # 将当前节点的表名添加到列表中
            table_list.append(current_node)
            # 将当前节点的所有子节点加入队列
            for child in current_node['dependencies']:
                queue.append(child)

        table_list.reverse()
        return table_list



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

    agent = Agent(d, db_conn_param)
    agent.generate('company_currency')
    agent.save()

    print("ALL DONE!!!")
