import argparse
import sys

from loguru import logger

from agent import Agent
from ddl_loader import load_ddl_postgres_13


def get_user_input():
    parser = argparse.ArgumentParser(description="Configure the Agent parameters.")
    parser.add_argument('--ddl-file', type=str, required=True, help='Path to the DDL file')
    parser.add_argument('--dbname', type=str, required=True, help='Database name')
    parser.add_argument('--user', type=str, required=True, help='Database user')
    parser.add_argument('--password', type=str, required=True, help='Database password')
    parser.add_argument('--host', type=str, required=True, help='Database host')
    parser.add_argument('--port', type=int, required=True, help='Database port')
    parser.add_argument('--loop-cnt', type=int, default=30, help='Loop count for the agent')
    parser.add_argument('--model', type=str, default='glm-4-9b-chat', help='Model for the agent')
    parser.add_argument('--api-key', type=str, required=True, help='API key for the agent')
    parser.add_argument('--api-base-url', type=str, required=True, help='API base URL for the agent')
    parser.add_argument('--temperature', type=float, default=0.0, help='Temperature for the agent')
    parser.add_argument('--max-tokens', type=int, default=18000, help='Maximum tokens for the agent')
    parser.add_argument('--debug-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Debug level for logging')

    args = parser.parse_args()
    return args


def print_and_select_table(d):
    # 打印所有的键
    print()
    print("Available tables:")
    for key in d.keys():
        print(key)
    print()

    # 获取用户输入并校验
    while True:
        selected_key = input("Please select a table from the above list: ")
        if selected_key in d:
            return selected_key
        else:
            print("Invalid table name. Please try again.")


if __name__ == '__main__':
    args = get_user_input()

    # logger setting
    logger.remove()
    logger.add(sys.stderr, format="<green>{time}</green> <level>{message}</level>", level=args.debug_level)

    with open(args.ddl_file, 'r') as f:
        d = load_ddl_postgres_13(f.read())

    db_conn_param = {
        'dbname': args.dbname,
        'user': args.user,
        'password': args.password,
        'host': args.host,
        'port': str(args.port)  # port should be a string
    }

    agent = Agent(ddl_dict=d,
                  db_conn_param=db_conn_param,
                  loop_cnt=args.loop_cnt,
                  model=args.model,
                  api_key=args.api_key,
                  api_base_url=args.api_base_url,
                  temperature=args.temperature,
                  max_tokens=args.max_tokens,
                  )

    while True:
        selected = print_and_select_table(d)
        print(f"You selected: {selected}")
        agent.generate(selected)
        agent.save()
        input("Press Enter to continue...")
