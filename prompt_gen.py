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
            - field_name_1: field value 1 generated
            - field_name_2: field value 2 generated

            statement:
            insert into (field_name_1, field_name_2, ...) VALUES (value1, value2,...);

            foreign_tables:
            - foreign_table_1
            - foreign_table_2
            '''
            don't make up foreign tables, look for them in ddl where the 'references' key word appear.
            always end your statement with semi-column ';'
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            please give me a SQL insert based on this schema:'''{ddl}'''
            Here are some examples of statements of this table:
            {history}
            Requirements:
            - all fields in ddl must appear
            - all fields appeared must have a valid value
            - values should be different from the examples given, especially for fields that are highly distinguishable, for instance: id
            - use integer values on 'id' field, starting from 10000
            """
        )
    ])


def parse_text_to_dict(text):
    lines = text.strip().split('\n')
    result = {}
    current_key = None

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.endswith(':'):
            current_key = stripped_line[:-1]
            if current_key == 'context':
                result[current_key] = {}
            elif current_key == 'foreign_tables':
                result[current_key] = []
            else:
                result[current_key] = ''
        elif current_key == 'context' and stripped_line.startswith('-'):
            key_value = stripped_line[2:].split(':', 1)
            if len(key_value) == 2:
                key, value = key_value[0].strip(), key_value[1].strip()
                try:
                    result[current_key][key] = json.loads(value)
                except json.JSONDecodeError:
                    result[current_key][key] = value
        elif current_key == 'foreign_tables' and stripped_line.startswith('-'):
            ft = stripped_line[2:].strip()
            if ft != '':
                result[current_key].append(ft)
        elif current_key == 'statement':
            if result[current_key] == '':
                result[current_key] = stripped_line
            else:
                result[current_key] += ' ' + stripped_line

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
