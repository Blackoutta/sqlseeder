from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import *
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from db_tool import DbTool
from ddl_loader import load_ddl
from prompt_revise import get_revise_prompt, RevisePromptOutputParser

with open('./ddl.txt', 'r') as f:
    d = load_ddl(f.read())

stmt = """
insert into company_currency (id, created_at, created_by, deleted_at, updated_at, updated_by, fut_mon_avg_bias_limit, mom_bias_limit, mon_avg_bias_limit, payment_period, comp_currency_id, company_id) VALUES (10000, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 5.00, 3.00, 4.00, 30, 200, 300); 
"""

db_tool = DbTool(connection_params={
    'dbname': 'forex_hdge',
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
})

tools = {
    'query_db': db_tool.execute_sql_query,
    'insert_to_db': db_tool.execute_sql_insert,
    'check_ddl': d.get,
}

store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


llm = ChatOpenAI(model='glm-4-9b-chat',
                 temperature=0,
                 verbose=True,
                 max_tokens=8000,
                 api_key="EMPTY",
                 base_url="http://localhost:6006/v1",
                 )

problem = {"stmt": stmt,
           "err": """insert or update on table "company_currency" violates foreign key constraint "FKt6ajykrwbetyof7i00e1ev793"
DETAIL:  Key (comp_currency_id)=(200) is not present in table "currency"."""}

chain = (get_revise_prompt() | llm | RevisePromptOutputParser())
with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
    output_messages_key='output'
)

msg = ChatPromptTemplate.from_template("""
        inserting the following statement: '''{stmt}''' has met an error '''{err}'''
        your goal is to utilize your tools only to solve the error and eventually insert the statement with success.
        if the problem is solved, make sure to use the 'finish' tool.
        tips:
        - if the error is foreign key constraint related, you can try insert a new data into that foreign table, be sure to look up the ddl of the foreign table before inserting, this way your data will look more realistic

        """).format(**problem)

result = with_message_history.invoke(
    input={"input": msg},
    config={"configurable": {"session_id": "abc123"}},
)

print(result)
parsed = result['parsed']
tool_name = parsed['tool_name']
for i in range(25):
    if tool_name == 'finish':
        print('finish!')
        break
    func = tools[tool_name]
    tool_param = parsed['tool_input']
    exec_result = func(tool_param)
    print(f'tool call result: {exec_result}')
    result = with_message_history.invoke(
        input={"input": f"tool call: {tool_name} returned: {exec_result}"},
        config={"configurable": {"session_id": "abc123"}},
    )
    parsed = result['parsed']
    tool_name = parsed['tool_name']
