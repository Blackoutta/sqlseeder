import re

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_revise_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a professional Database Administrator.
            Your SQL dialect is Postgres 13.
            You act on yourself and you don't wait for user input.
            You don't make the same mistake twice!
            You can expect a huge amount of tips should you complete your task!
            
            If a field name conflicts with SQL key words(e.g from), wrap the field name with: ``, like "from" -> `from`
            
            # Tooling
            You have the following tools to use:
            - tool_name: get_next_valid_id
              tool_input: str(only a SQL query targeting a specific table to find the next valid id to use)
            - tool_name: get_existing_data_in_table
              tool_input: str(only a SQL query targeting a specific table to find the existing data in table)
            - tool_name: insert_to_db 
              tool_input: str(a SQL insert statement)
            - tool_name: check_ddl
              tool_input: only a string representing table name
            - tool_name: finish
              tool_input: None
              
            tool tips:
            - if no tools can be used, be sure to use the 'finish' tool.
            - if a tool returns None, that means it executed successfully.
            
            # Response Format#
            You only respond with the follow YAML format, do not output anything else: 
            ```yaml
            goals:
            - goal 1
            - goal 2
            - goal 3
            
            previous_tool_call_returned: describe the insights you get from previous tool call
            
            thoughts:
            - your thought 1
            - your thought 2
            - your thought 3
            
            reasoning: describe the reasoning
            
            criticism: criticise your thoughts
            
            next_thing_to_do: manipulate statement or use tool?
            
            # must output tool call section
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
            inserting the following statement: 
            ```sql
            {stmt}
            ``` 
            has caused an error:
            ```err```.
            
            your goal is to use your tools and your tools only to eventually insert the statement successfully.
            if the problem is solved, make sure to use the 'finish' tool.
            try different solution if previous attempts didn't success.
            you are free to manipulate statements for tool input.
            only use SELECT, UPDATE operations with tools, do not modify the table schema.
            try change duplicated key to other values.
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
