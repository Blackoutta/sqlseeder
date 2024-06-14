import json
import re

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that creates SQL insert statements based on given table schema.
            Your SQL dialet is Postgres 13.
            You only respond with the follow JSON format in triple quote:
            '''
            {{
            "context": {{
            "field_name_1": "value you've generated for a field",
            "field_name_2": "value you've generated for a field",
            ...
            }},
            "statement": "the complete SQL statement generated based on context object above",
            "foreign_tables": ["foreign table_1, foreign table_2"]
            }}
            '''
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            please give me a SQL insert based on this schema:'''{ddl}'''
            Requirements:
            - all fields must have a value
            - do not include 'id' field in your statement
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

