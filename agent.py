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
        self.model = 'glm-4'
        self.llm = ChatOpenAI(model=self.model,
                              temperature=0.3,
                              verbose=True,
                              )
        self.threshold = 3

    def generate(self, target_table: str) -> List[str]:
        self.queue.put(target_table)

        while not self.queue.empty():
            print(f'current queue size: {self.queue.qsize()}')
            target = self.queue.get()
            ddl = self.ddl_dict.get(target)
            print(f'ddl: {ddl}')
            chain = (get_prompt() | self.llm | OutputParser())
            result = chain.invoke({"ddl": ddl})
            stmt = result['statement']
            print(f'generated: {stmt}')
            self.generated.append(stmt)
            print(f'current generated count: {len(self.generated)}')
            fts = result['foreign_tables']
            for ft in fts:
                if ft not in self.counter:
                    self.counter[ft] = 1
                else:
                    self.counter[ft] = self.counter[ft] + 1
                if self.counter[ft] <= self.threshold:
                    self.queue.put(ft)
        return self.generated


if __name__ == '__main__':
    with open('./ddl.txt', 'r') as f:
        d = load_ddl(f.read())

    agent = Agent(d)
    generated = agent.generate('trading_task')
    for s in generated:
        print(s)
