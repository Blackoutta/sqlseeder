import json

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_gen_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that creates SQL insert statements based on given table schema.
            Your SQL dialect is Postgres 13.
            You only respond with the follow format in triple quote:
            '''
            context:
            - field_name_1: field value generated
            - field_name_2: field value generated
            ...

            statement:
            insert into (field_name_1, field_name_2, ...) VALUES (value1, value2,...);

            foreign_tables:
            - foreign_table_1
            - foreign_table_2
            ...
            '''
            don't make up foreign tables, look for them in ddl where the 'references' key word appear.
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            Here are some examples of statements you should be generating:
            {history}
            
            please give me a SQL insert based on this schema:'''{ddl}'''
            Requirements:
            - all fields in ddl must appear
            - all fields appeared must have a valid value
            - values should be different from the examples given, especially for fields that are highly distinguishable
            """
        )
    ])


def parse_text_to_dict(text):
    result = {
        "available_ids_by_table": {},
        "foreign_table_mapping": {},
        "modified_statements": []
    }
    
    available_ids_section = re.search(r'available_ids_by_table:\n((?:\s*-\s*\S+:\s*[\d,]+\n)+)', text)
    foreign_table_mapping_section = re.search(r'foreign_table_mapping:\n((?:\s*-\s*\S+:\s*\S+\n)+)', text)
    modified_statements_section = re.search(r'modified_statements:\n((?:\s*-\s*.*\n)+)', text)
    
    if available_ids_section:
        available_ids_lines = available_ids_section.group(1).strip().split('\n')
        for line in available_ids_lines:
            table, ids = re.findall(r'(\S+):\s*([\d,]+)', line)[0]
            result["available_ids_by_table"][table] = list(map(int, ids.split(',')))

    if foreign_table_mapping_section:
        foreign_table_mapping_lines = foreign_table_mapping_section.group(1).strip().split('\n')
        for line in foreign_table_mapping_lines:
            field, foreign_table = re.findall(r'(\S+):\s*(\S+)', line)[0]
            result["foreign_table_mapping"][field] = foreign_table

    if modified_statements_section:
        modified_statements_lines = modified_statements_section.group(1).strip().split('\n')
        for line in modified_statements_lines:
            statement = re.findall(r'-\s*(.*)', line)[0]
            result["modified_statements"].append(statement)

    return result


class GenPromptOutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        try:
            return parse_text_to_dict(text)
        except Exception as e:
            print(f'Failed to parse text result:\n{text}\n')


if __name__ == '__main__':
    # 示例文本
    text = """
    context:
     - field_name_1: field value generated
     - field_name_2: field value generated
     - field_name_3: {"json_field": "json value"}

    statement:
    insert into (field_name_1, field_name_2) VALUES (value1, value2);

    foreign_tables:
     - foreign_table_1
     - foreign_table_2
    """

    # 调用函数并打印结果
    parsed_dict = parse_text_to_dict(text)
    print(parsed_dict)
