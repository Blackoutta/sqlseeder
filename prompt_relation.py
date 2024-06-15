import re

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_relation_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that helps correct the foreign key values between sql insert statements.
            Your SQL dialect is Postgres 13.

            foreign keys have the following feature:
            1. they are of type: bigint
            2. they have a constraint that references another table, for example: 
            '''head_id bigint constraint "FKkcvd91xpwoq75mmn5a91307hk" references bank_head'''
            3. 'id' is not a foreign key


            You only respond with the follow format within triple quotes:
            '''
            # you may output up to 10 steps
            thoughts:
            - step 1
            - step 2
            - step 3

            what are the available ids from tables:
            - table: table name
              ids: 1,2,3,4,5

            # which foreign key field points to which table
            foreign_key_to_foreign_table:
            - foreign_key: foo
              foreign_table: bar

            foreign_key_value_to_replace:
            - source_value: original_value (#which field does the original value belong to:)
              target_value: new_value (#which foreign table you found the new value from:)

            modified_statements:
            - insert into (f1,f2,f3) values (v1,v2,v3);    

            '''
            """
        ),
        HumanMessagePromptTemplate.from_template(
            """
            The following target statement has arbitrary integer values generated at all the foreign key fields:
            '''{stmt}'''  

            your task is to replace the integer values of its foreign keys with the integer values found in this table-and-id context, the context tells you which table has what available ids to chooose from:
            '''{fk_ctx}'''

            this ddl will help you identifying which fields are foreign keys:
            '''{ddl}'''

            tips for the task:
            - you should only use integer values to replace foreign key values.
            - skip this task if no foreign keys are found.
            - don't add or remove values, just modify
            - output only 1 statement
            - ignore any field that is named like 'parent_id'
            """
        )
    ])


def parse_text_to_dict(text):
    result = {"modified_statements": []}

    # 使用正则表达式匹配 `modified_statements` 部分
    modified_statements_pattern = re.compile(r"modified_statements:\s*(- .*)", re.DOTALL)
    modified_statements_match = modified_statements_pattern.search(text)

    if modified_statements_match:
        # 获取 `modified_statements` 部分的内容
        modified_statements_content = modified_statements_match.group(1).strip()

        # 使用正则表达式提取每个SQL语句
        sql_pattern = re.compile(r"-\s*(insert.*?;)", re.DOTALL)
        sql_matches = sql_pattern.findall(modified_statements_content)

        # 将每个SQL语句添加到结果字典中
        for sql in sql_matches:
            result["modified_statements"].append(sql.strip())

    return result


class RelationPromptOutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        print(f'parsing relation:\n{text}\n')
        try:
            return parse_text_to_dict(text)
        except Exception as e:
            print(f'Failed to parse text result:\n{text}\n')


if __name__ == '__main__':
    # 示例文本
    text = """
    thoughts:
    - step 1: Identify the foreign key fields in the target statement
    - step 2: Match the foreign key fields with the corresponding tables from the context
    - step 3: Replace the integer values with the appropriate values from the context

    # which foreign key field points to which table
    foreign_key_to_foreign_table:
    - foreign_key: business_group
      foreign_table: company

    # foreign_key_value_to_replace
    foreign_key_value_to_replace:
    - from: BusinessGroupW (#business_group field does the original value belong to:)
      to: 1001 (#company table you found the new value from:)

    modified_statements:
    - insert into company_base (id, extension, alias, attribute, business_group, code, consolidated, domestic, name) VALUES (1500, '{"key1": "value1", "key3": "value3"}', 'CompanyAlias789', 'AttributeZ', 1001, 'Code2345', true, false, 'Company Name 789'); 
    
    """

    # 调用函数并打印结果
    result = parse_text_to_dict(text)
    print(result)
