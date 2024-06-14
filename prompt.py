import json
import re

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that generates sql insert statements based on given ddl.
            You only respond with the follow JSON format in triple quote:
            '''
            {{
            "statement": "sql you have generated",
            "field_and_value": {{
            "field_1": 1.2,
            "field_2": "hello world",
            "field_3": true,
            "field_4": {},
            ...
            }},
            "foreign_tables": ["foreign table_1, foreign table_2"]
            }}
            '''
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            Generate a sql insert statement based on this ddl:
            '''
            {ddl}
            '''
            """
        )
    ])


def extract_json_from_text(text):
    # 使用正则表达式匹配JSON部分
    json_pattern = re.compile(r'\{.*}', re.DOTALL)
    match = json_pattern.search(text)
    if match:
        return match.group()
    else:
        return None


class OutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        stripped = extract_json_from_text(text).strip("```json").strip("```")
        try:
            return json.loads(stripped)
        except Exception as e:
            print(f'Failed to parse {stripped}: {e}')
            raise e

