from agent import Agent
from ddl_loader import load_ddl_postgres_13

with open('test_data/ddl.txt', 'r') as f:
    d = load_ddl_postgres_13(f.read())

db_conn_param = {
    'dbname': 'forex_hdge',
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'port': '5432'
}

agent = Agent(d, db_conn_param)
# agent.generate('company_currency')
# agent.save()
err = agent.db_tool.execute_sql_insert(
    """
insert into company_currency (id, created_at, created_by, deleted_at, updated_at, updated_by, fut_mon_avg_bias_limit, mom_bias_limit, mon_avg_bias_limit, payment_period, comp_currency_id, company_id) VALUES (10000, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 5.00, 3.00, 4.00, 30, 200, 300); 
    """
)
print(err)

print("ALL DONE!!!")
