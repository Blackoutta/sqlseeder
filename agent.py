import queue
import re
from typing import List

from langchain_openai import ChatOpenAI

from ddl_loader import load_ddl
from prompt_ctx import get_ctx_prompt, CtxPromptOutputParser
from prompt_gen import get_gen_prompt, GenPromptOutputParser
from prompt_relation import get_relation_prompt, RelationPromptOutputParser


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
                              max_tokens=18000,
                              api_key="EMPTY",
                              base_url="http://localhost:8000/v1",
                              )
        self.threshold = 1

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

        # 从已生成的数据中获取各个表的外键id
        ctx_chain = (get_ctx_prompt() | self.llm | CtxPromptOutputParser())
        fk_ctx = ctx_chain.invoke({"stmts": '\n'.join(self.generated)})

        for stmt in self.generated:
            # 优化SQL语句之间的外键关系
            rel_chain = (get_relation_prompt() | self.llm | RelationPromptOutputParser())
            result = rel_chain.invoke(
                {
                    "ddl": self.ddl_dict.get(self.extract_table_name(stmt)),
                    "stmt": stmt,
                    "fk_ctx": fk_ctx
                }
            )
            self.optimized.append(result['modified_statements'][0])
        return self.generated, self.optimized

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

    agent = Agent(d)
    generated, optimized = agent.generate('trading_task')
    with open('./generated.sql', 'w') as g:
        for s in generated:
            g.write(s + '\n')
    with open('./optimized.sql', 'w') as g:
        for s in optimized:
            g.write(s + '\n')
    print()
    print("ALL DONE!!!")
