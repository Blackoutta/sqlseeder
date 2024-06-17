import re

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_revise_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a professional and hardworking DBA.
            Your SQL dialect is Postgres 13.
            You act on yourself and you don't wait for user input.
            
            # Tooling
            You have the following tools to use:
            - tool_name: query_db
              tool_input: str(a SQL query statement)
            - tool_name: insert_to_db 
              tool_input: str(a SQL insert statement)
            - tool_name: check_ddl
              tool_input: str(a table name) 
            - tool_name: finish
              tool_input: None
              
            tool tips:
            - if no tools can be used, be sure to use the 'finish' tool.
            - if a tool returns None, that means it executed successfully.
            
            # Response Format#
            You only respond with the follow YAML format: 
            ```
            goals:
            - goal 1
            - goal 2
            - goal 3
            
            previous_tool_call_returned: describe the previous tool call response
            
            thoughts:
            - your thought 1
            - your thought 2
            - your thought 3
            
            reasoning: describe the reasoning
            
            criticism: criticise your thoughts
            
            next_thing_to_do: what to do next
            
            tool_call:
              tool_name: tool name
              tool_input: tool input
            ```
            """
        ),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])


def get_revise_request_prompt():
    return ChatPromptTemplate.from_template("""
            inserting the following statement: '''{stmt}''' has met an error '''{err}'''
            your goal is to utilize your tools only to solve the error and eventually insert the statement with success.
            if the problem is solved, make sure to use the 'finish' tool.
            tips:
            - if the error is foreign key constraint related, you can try insert a new data into that foreign table, be sure to look up the ddl of the foreign table before inserting, this way your data will look more realistic
            """)


def extract_tool_call(text):
    # 使用正则表达式匹配 tool_call 部分
    pattern = r'tool_call:\s*\n\s*tool_name:\s*(\w+)\s*\n\s*tool_input:\s*(.+?)\s*(?=\n\S|$)'
    match = re.search(pattern, text, re.DOTALL)

    # 如果找到匹配的内容，返回字典
    if match:
        return {
            "tool_name": match.group(1),
            "tool_input": match.group(2).strip().strip('"')
        }
    else:
        return None


class RevisePromptOutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        print(f'### parsing context###:\n{text}')
        print("--------------------------------------")
        return {'parsed': extract_tool_call(text), 'output': text}
