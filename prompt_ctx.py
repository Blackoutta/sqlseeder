from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers.base import T
from langchain_core.prompts import *


def get_ctx_prompt():
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            """
            You are a helpful assistant that understands the foreign key relations between sql insert statements.
            Your SQL dialect is Postgres 13.
            You only respond with the follow format:
            available_ids_by_table:
            - table_name_1: 1,2,3,4,5
            - table_name_2: 1,2,3,4,5
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
    # 初始化一个空字典
    result = {}

    # 分割文本为行
    lines = text.strip().split('\n')

    for line in lines:
        # 去掉行首的短横线和空格，分割表名和ID
        line = line.strip('- ').strip()
        if line:
            # 处理表名和ID部分
            if ': ' in line:
                table_name, ids = line.split(': ', 1)  # 仅分割一次，避免额外的冒号导致问题
                ids_list = [int(id.strip()) for id in ids.split(',')]

                # 如果表名已经存在，合并ID列表
                if table_name in result:
                    result[table_name].extend(ids_list)
                else:
                    result[table_name] = ids_list
            else:
                print(f"Skipping malformed line: {line}")

    # 删除ID列表中的重复项
    for key in result:
        result[key] = list(set(result[key]))

    return result


class CtxPromptOutputParser(BaseOutputParser):
    def parse(self, text: str) -> T:
        print(text)
        try:
            return parse_text_to_dict(text)
        except Exception as e:
            print(f'Failed to parse text result:\n{text}\n')


if __name__ == '__main__':
    # 示例文本
    text = """
    available_ids_by_table:
    - trading_task: 1
    - general_user: 1234567890, 1234567891
    - currency: 1, 2
    - instruction: 1
    - hedge_plan_entry: 1
    - company: 1, 2, 1
    - company_currency: 1001, 1002
    - currency: 1
    - hedge_group: 1
    - hedge_plan: 1
    - company_base: 1, 2, 3
    - company: 1, 2, 1
    - company_currency: 1002
    - company_base: 2, 3
    """

    # 调用函数并打印结果
    parsed_dict = parse_text_to_dict(text)
    print(parsed_dict)
