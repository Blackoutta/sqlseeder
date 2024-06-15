from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_relation_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that understands foreign key relations between SQL insert statements.
            Your SQL dialect is Postgres 13.
            You only respond with the follow format in triple quote:
            '''
            available_ids_by_table:
            - table_name_1: 1,2,3,4,5...
            - table_name_2: 1,2,3,4,5...
            ...

            modified_statements:
            - modified sql insert statement 1
            - modified sql insert statement 2
            ...
            '''
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            analyze the foreign key relations between the following statements, 
            modifying their 'id' field or fields that ends with '_id' suffix(aka foreign keys) 
            so that when inserting them, they will not 
            violate foreign key constraints:
            '''{stmts}'''
            """
        )
    ])


def parse_text_to_dict(text):
    # 初始化结果字典
    result = {
        "available_ids_by_table": {},
        "modified_statements": []
    }

    lines = text.strip().split('\n')

    current_section = None

    for line in lines:
        line = line.strip()

        if line.startswith('available_ids_by_table:'):
            current_section = 'available_ids_by_table'
        elif line.startswith('modified_statements:'):
            current_section = 'modified_statements'
        elif current_section == 'available_ids_by_table':
            if line.startswith('-'):
                table_name, ids = line[1:].split(':')
                table_name = table_name.strip()
                ids = [int(id.strip()) for id in ids.split(',')]
                result['available_ids_by_table'][table_name] = ids
        elif current_section == 'modified_statements':
            if line.startswith('-'):
                statement = line[1:].strip()
                result['modified_statements'].append(statement)

    return result


class RelationPromptOutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        try:
            return parse_text_to_dict(text)
        except Exception as e:
            print(f'Failed to parse text result:\n{text}\n')


if __name__ == '__main__':
    text = """
    available_ids_by_table:
    - table_name_1: 1,2,3,4,5
    - table_name_2: 6,7,8,9,10

    modified_statements:
    - modified sql insert statement 1
    - modified sql insert statement 2
    """

    # 解析文本
    parsed_dict = parse_text_to_dict(text)
    print(parsed_dict)
