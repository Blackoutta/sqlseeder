import re

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_relation_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that helps correct sql insert statements.
            Your SQL dialect is Postgres 13.
            You only respond with the follow format in triple quote:
            '''
            foreign_key_to_foreign_table:
            - foreign_key_name: foreign_table_name
            - foreign_key_name: foreign_table_name

            foreign_key_value_to_replace:
            - from: origin_value_1 (which field?)
              to: new_value_1 (which foreign table?)

            modified_statements:
            - modified sql insert statement           

            thoughts:
            - step 1
            - step 2
            - step 3
            '''
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            '''{ddl}'''

            The following target statement has arbitrary values for its foreign key fields:
            '''{stmt}'''  

            change its foreign key values based on the foreign key context provided below:
            '''{fk_ctx}'''
            
            Requirements:
            - don't add or remove values, just modify
            - replace all the foreign key values with existing values in the context only
            - ignore any field that is named like 'parent_id'
            """
        )
    ])


def parse_text_to_dict(text):
    result = {
        "foreign_key_to_foreign_table": {},
        "modified_statements": [],
        "thoughts": []
    }

    # 正则表达式匹配各个部分
    foreign_key_section = re.search(r'foreign_key_to_foreign_table:\n((?:\s*-\s*\S+:\s*\S+\n)+)', text)
    modified_statements_section = re.search(r'modified_statements:\n((?:\s*-\s*.*\n)+)', text)
    thoughts_section = re.search(r'thoughts:\n((?:\s*-\s*.*\n)+)', text)

    # 解析 foreign_key_to_foreign_table 部分
    if foreign_key_section:
        foreign_key_lines = foreign_key_section.group(1).strip().split('\n')
        for line in foreign_key_lines:
            field, foreign_table = re.findall(r'(\S+):\s*(\S+)', line)[0]
            result["foreign_key_to_foreign_table"][field] = foreign_table

    # 解析 modified_statements 部分
    if modified_statements_section:
        modified_statements_lines = modified_statements_section.group(1).strip().split('\n')
        for line in modified_statements_lines:
            statement = re.findall(r'-\s*(.*)', line)[0]
            result["modified_statements"].append(statement)

    # 解析 thoughts 部分
    if thoughts_section:
        thoughts_lines = thoughts_section.group(1).strip().split('\n')
        for line in thoughts_lines:
            thought = re.findall(r'-\s*(.*)', line)[0]
            result["thoughts"].append(thought)

    return result


class RelationPromptOutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        print(text)
        try:
            return parse_text_to_dict(text)
        except Exception as e:
            print(f'Failed to parse text result:\n{text}\n')


if __name__ == '__main__':
    # 示例文本
    text = """
                foreign_key_to_foreign_table:
                - foreign_key_name_1: foreign_table_name_1
                - foreign_key_name_2: foreign_table_name_2

                modified_statements:
                - modified sql insert statement 1

                thoughts:
                - step 1
                - step 2
                - step 3
    """

    # 调用函数并打印结果
    parsed_dict = parse_text_to_dict(text)
    print(parsed_dict)
