from langchain_openai import ChatOpenAI

from relation_prompt import get_relation_prompt, RelationPromptOutputParser

generated_text = """
insert into trading_task (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_time, buy_remainingm, buy_volume, execute_status, expire_date, last_trading_time, sell_remainingm, sell_volume, task_no, traded_volumem, transferred_volumem, ym, assigner_id, buy_currency_id, instruction_id, parent_id, sell_currency_id, trader_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, '2023-04-02 10:00:00+00', 100.00, 200.00, 'PENDING', '2023-05-01 12:00:00+00', NULL, 150.00, 250.00, 'T123456', 50.00, 30.00, 2023, 101, 201, 301, NULL, 401, 501);
insert into general_user (id, extension, employee_number, organization_name, user_id) VALUES (1234567890, '{"name": "John Doe", "age": 30}', 'E123456', 'Global Corp', 'user123');
insert into currency (id, code, name) VALUES (1, 'USD', 'United States Dollar');
insert into instruction (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_status, assigned_volumem, confirmed_volumem, execute_status, "from", generated_time, instruction_no, trade_direction, traded_volumem, trading_volumem, hedge_plan_entry_id, master_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 'ASSIGNED', 100.00, 150.00, 'EXECUTING', 'HEDGE_PLAN', '2023-04-01 12:01:00+00', 'INST12345', 'BUY', 50.00, 75.00, 101, 202);
insert into currency (id, code, name) VALUES (2, 'EUR', 'Euro');
insert into general_user (id, extension, employee_number, organization_name, user_id) VALUES (1234567891, '{"name": "Jane Smith", "age": 25}', 'E123457', 'Tech Innovations', 'user456');
insert into hedge_plan_entry (id, created_at, created_by, deleted_at, updated_at, updated_by, month_term, remark, company_currency_id, exposure_currency_id, hedge_currency_id, hedge_group_id, plan_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 6, 'Monthly hedge plan for Q2', 101, 102, 103, 201, 301);
insert into company (id, created_at, created_by, deleted_at, updated_at, updated_by, delivery_prep_days, delivery_type, notify_email_list, passed_email_list, supervised, company_base_id) VALUES (1, '2023-04-01 12:00:00+00', 'admin', NULL, NULL, NULL, 5, 'FULL', '[{"email": "example1@example.com"}, {"email": "example2@example.com"}]', '[{"email": "example3@example.com"}, {"email": "example4@example.com"}]', true, 101);
insert into company_currency (id, created_at, created_by, deleted_at, updated_at, updated_by, fut_mon_avg_bias_limit, mom_bias_limit, mon_avg_bias_limit, payment_period, comp_currency_id, company_id) VALUES (1001, '2023-04-01 12:00:00+00', 'admin', NULL, NULL, NULL, 5.50, 4.25, 3.75, 30, 2001, 3001);
insert into currency (id, code, name) VALUES (1, 'JPY', 'Japanese Yen');
insert into hedge_group (id, created_at, created_by, deleted_at, updated_at, updated_by, key, reject_reason, status, code, comment, name, delegate_id, group_currency_id, master_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 'HG001', NULL, 'PENDING', 'HG20230401', 'Initial hedge group setup', 'Spring Hedge Group', 101, 201, 301);
insert into hedge_plan (id, created_at, created_by, deleted_at, updated_at, updated_by, approval_status, plan_no, year_month) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 'PENDING', 'HP202304', 202304);
insert into company_base (id, extension, alias, attribute, business_group, code, consolidated, domestic, name) VALUES (1, '{"key1": "value1", "key2": "value2"}', 'CompanyAlias', 'CompanyAttribute', 'BusinessGroup1', 'C12345', true, false, 'Company Name');
insert into company (id, created_at, created_by, deleted_at, updated_at, updated_by, delivery_prep_days, delivery_type, notify_email_list, passed_email_list, supervised, company_base_id) VALUES (2, '2023-04-02 12:00:00+00', 'user123', NULL, NULL, NULL, 3, 'DIF', '[{"email": "notify1@example.com"}, {"email": "notify2@example.com"}]', '[{"email": "passed1@example.com"}, {"email": "passed2@example.com"}]', false, 102);
insert into company (id, created_at, created_by, deleted_at, updated_at, updated_by, delivery_prep_days, delivery_type, notify_email_list, passed_email_list, supervised, company_base_id) VALUES (1, '2023-04-03 12:00:00+00', 'admin_user', NULL, NULL, NULL, 7, 'FULL', '[{"email": "notify3@example.com"}, {"email": "notify4@example.com"}]', '[{"email": "passed3@example.com"}, {"email": "passed4@example.com"}]', true, 103);
insert into company_currency (id, created_at, created_by, deleted_at, updated_at, updated_by, fut_mon_avg_bias_limit, mom_bias_limit, mon_avg_bias_limit, payment_period, comp_currency_id, company_id) VALUES (1002, '2023-04-02 12:00:00+00', 'user123', NULL, NULL, NULL, 6.25, 5.00, 4.50, 45, 2002, 3002);
insert into company_base (id, extension, alias, attribute, business_group, code, consolidated, domestic, name) VALUES (2, '{"key3": "value3", "key4": "value4"}', 'CompanyAliasX', 'CompanyAttributeX', 'BusinessGroup2', 'C67890', true, false, 'Company Name X');
insert into company_base (id, extension, alias, attribute, business_group, code, consolidated, domestic, name) VALUES (3, '{"key5": "value5", "key6": "value6"}', 'CompanyAliasY', 'CompanyAttributeY', 'BusinessGroup3', 'C23456', true, true, 'Company Name Y');
"""

llm = ChatOpenAI(model='glm-4-9b-chat',
                 temperature=0,
                 verbose=True,
                 max_tokens=8000,
                 api_key="EMPTY",
                 base_url="http://localhost:8000/v1",
                 )

rel_chain = (get_relation_prompt() | llm | RelationPromptOutputParser())
result = rel_chain.invoke({"stmts": generated_text})
optimized = result['modified_statements']
with open('optimized.txt', 'w') as f:
    for i in optimized:
        f.write(i + "\n")
