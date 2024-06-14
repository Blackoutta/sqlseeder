import queue
from typing import List

from langchain_openai import ChatOpenAI

from ddl_loader import load_ddl
from prompt import get_prompt, OutputParser


class Agent:
    def __init__(self, ddl_dict: dict):
        self.ddl_dict = ddl_dict  # ddl
        self.queue = queue.Queue()
        self.counter = {}  # 表计数
        self.generated = []  # 已生成的SQL
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

    def generate(self, target_table: str) -> List[str]:
        self.queue.put(target_table)

        while not self.queue.empty():
            print(f'current queue size: {self.queue.qsize()}')
            target = self.queue.get()
            # 获取目标表DLL
            ddl = self.ddl_dict.get(target)

            # 获取目标表已生成的语句
            history = self.history_as_prompt(target)
            print(f'history: {history}')

            # 大语言模型生成语句
            # print(f'ddl: {ddl}')
            chain = (get_prompt() | self.llm | OutputParser())
            result = chain.invoke({"ddl": ddl, "history": history})
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
            for ft in fts:
                if ft not in self.counter:
                    self.counter[ft] = 1
                else:
                    self.counter[ft] = self.counter[ft] + 1
                if self.counter[ft] <= self.threshold and ft != target:
                    self.queue.put(ft)
        return self.generated

    def history_as_prompt(self, target) -> str:
        his = self.gen_history.get(target)
        if his is None:
            return ""
        return '\n'.join(his)


if __name__ == '__main__':
    with open('./ddl.txt', 'r') as f:
        d = load_ddl(f.read())

    agent = Agent(d)
    generated = agent.generate('trading_task')
    print('final result:')
    for s in generated:
        print(s)
    with open('./generated.txt', 'w') as g:
        for s in generated:
            g.write(s + '\n')
