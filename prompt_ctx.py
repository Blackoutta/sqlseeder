import re

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_ctx_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that understands the foreign key relations between sql insert statements.
            Your SQL dialect is Postgres 13.
            You only respond with the follow format in triple quote:
            '''
            available_ids_by_table:
            - table_name_1: 1,2,3,4,5
            - table_name_2: 1,2,3,4,5
            '''
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            In the following statements, summarize each table's id list:
            {stmts}
            """
        )
    ])


def parse_text_to_dict(text):
    result = {
        "available_ids_by_table": {}
    }

    # 正则表达式匹配 available_ids_by_table 部分
    available_ids_section = re.search(r'available_ids_by_table:\n((?:\s*-\s*\S+:\s*[\d,]+\n)+)', text)

    # 解析 available_ids_by_table 部分
    if available_ids_section:
        available_ids_lines = available_ids_section.group(1).strip().split('\n')
        for line in available_ids_lines:
            table, ids = re.findall(r'(\S+):\s*([\d,]+)', line)[0]
            result["available_ids_by_table"][table] = list(map(int, ids.split(',')))

    return result


class CtxPromptOutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        try:
            return parse_text_to_dict(text)
        except Exception as e:
            print(f'Failed to parse text result:\n{text}\n')


if __name__ == '__main__':
    text = """
            available_ids_by_table:
            - table_name_1: 1,2,3,4,5
            - table_name_2: 1,2,3,4,5
"""

    # 调用函数并打印结果
    parsed_dict = parse_text_to_dict(text)
    print(parsed_dict)
