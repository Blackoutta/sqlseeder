from typing import TypedDict

import psycopg2
from loguru import logger
from psycopg2 import Error


class DbTool:
    def __init__(self, connection_params):
        self.connection_params = connection_params

    def execute_sql_insert(self, sql_string):
        logger.debug(f'executing insert stmt:{sql_string}')
        connection = None
        cursor = None
        try:
            # 连接到PostgreSQL数据库
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()

            # 执行SQL插入语句
            cursor.execute(sql_string)

            # 提交事务
            connection.commit()

            # 返回None表示没有错误
            logger.debug('insert success')
            return None

        except Error as e:
            # 如果有错误，返回错误信息
            return str(e)

        finally:
            # 关闭游标和连接
            if connection:
                cursor.close()
                connection.close()

    def execute_sql_query(self, sql_query):
        connection = None
        cursor = None
        try:
            # 连接到PostgreSQL数据库
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()

            # 执行SQL查询语句
            cursor.execute(sql_query)

            # 获取查询结果
            results = cursor.fetchall()

            # 返回查询结果
            return results

        except Error as e:
            # 如果有错误，返回错误信息
            return str(e)

        finally:
            # 关闭游标和连接
            if connection:
                cursor.close()
                connection.close()

    def get_data_example_by_table(self, table_name):
        return self.execute_sql_query("""
        SELECT * FROM {}
        """.format(table_name))

    def tool_reminder(self):
        return """
        You have the following tools to use:
            - tool_name: get_next_valid_id
              tool_input: only a SQL query targeting a specific table to find the next valid id to use, example: SELECT nextval('table_name_id_seq')
            - tool_name: get_data_example_by_table
              tool_input: only a string representing table name
            - tool_name: insert_to_db 
              tool_input: only a SQL insert statement
            - tool_name: check_table_ddl
              tool_input: only a table name
            - tool_name: finish
              tool_input: None
        """


class BaseTool(TypedDict, total=False):
    query_db: str
    insert_to_db: str
    check_ddl: str


def get_tool_keys():
    return ['query_db', 'insert_to_db', 'check_ddl']


DBAgentTool = TypedDict('DBAgentTool', {key: str for key in get_tool_keys()})

if __name__ == '__main__':
    db_tool = DbTool(connection_params={
        'dbname': 'forex_hdge',
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'port': '5432'
    })

    res = db_tool.execute_sql_query("""
    select * FROM currency;
    """)
