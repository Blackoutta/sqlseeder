import queue
from typing import List

from langchain_openai import ChatOpenAI

from ddl_loader import load_ddl
from gen_prompt import get_gen_prompt, GenPromptOutputParser
from relation_prompt import get_relation_prompt, RelationPromptOutputParser


class Agent:
    def __init__(self, ddl_dict: dict):
        self.ddl_dict = ddl_dict  # ddl
        self.queue = queue.Queue()
        self.counter = {}  # 表计数
        self.generated = []  # 已生成的SQL
        self.optimized = []  # 已优化的SQL
        self.gen_history = {}  # 已生成SQL的记录，注入到prompt中让大语言模型尽量避开重复的数据
        self.model = 'glm-4-9b-chat'
        self.llm = ChatOpenAI(model=self.model,
                              temperature=0,
                              verbose=True,
                              max_tokens=8000,
                              api_key="EMPTY",
                              base_url="http://localhost:8000/v1",
                              )
        self.threshold = 3

    def generate(self, target_table: str) -> (List[str], List[str]):
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
            print(f'generated: {stmt}')
            self.generated.append(stmt)
            print(f'current generated count: {len(self.generated)}')

            # 记录生成语句历史
            if self.gen_history.get(target) is not None:
                self.gen_history[target].append(stmt)
            else:
                self.gen_history[target] = [stmt]

            fts = result['foreign_tables']
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

            # 优化SQL语句之间的外键关系
            rel_chain = (get_relation_prompt() | self.llm | RelationPromptOutputParser())
            result = rel_chain.invoke({"stmts": '\n'.join(self.generated)})
            self.optimized = result['modified_statements']

        return self.generated, self.optimized

    def history_as_prompt(self, target) -> str:
        his = self.gen_history.get(target)
        if his is None:
            return ""
        return '\n'.join(his)


if __name__ == '__main__':
    with open('./ddl.txt', 'r') as f:
        d = load_ddl(f.read())

    agent = Agent(d)
    generated, optimized = agent.generate('trading_task')
    print('final result:')
    with open('./generated.txt', 'w') as g:
        for s in generated:
            g.write(s + '\n')
    with open('./optimized.txt', 'w') as g:
        for s in optimized:
            g.write(s + '\n')
    print()
    print("ALL DONE!!!")
