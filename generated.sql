insert into trading_task (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_time, buy_remainingm, buy_volume, execute_status, expire_date, last_trading_time, sell_remainingm, sell_volume, task_no, traded_volumem, transferred_volumem, ym, assigner_id, buy_currency_id, instruction_id, parent_id, sell_currency_id, trader_id) VALUES (1, '2023-04-01 12:00:00.000000', 'user123', NULL, NULL, NULL, '2023-04-02 10:00:00.000000', 100.00, 200.00, 'PENDING', '2023-05-01 12:00:00.000000', NULL, 150.00, 300.00, 'T123456', 50.00, 25.00, 2023, 101, 201, 301, NULL, 401, 501); 
insert into general_user (id, extension, employee_number, organization_name, user_id) VALUES (1234567890, '{"name": "John Doe", "age": 30}', 'EMP12345', 'Global Corp', 'USER123456'); 
insert into currency (id, code, name) VALUES (123456, 'USD', 'United States Dollar'); 
insert into instruction (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_status, assigned_volumem, confirmed_volumem, execute_status, "from", generated_time, instruction_no, trade_direction, traded_volumem, trading_volumem, hedge_plan_entry_id, master_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 'PENDING', 100.00, 200.00, 'PENDING', 'HEDGE_PLAN', '2023-04-01 12:01:00+00', 'INST12345', 'BUY', 50.00, 150.00, 101, 501); 
insert into hedge_plan_entry (id, created_at, created_by, deleted_at, updated_at, updated_by, month_term, remark, company_currency_id, exposure_currency_id, hedge_currency_id, hedge_group_id, plan_id) VALUES (1, '2023-04-01 12:00:00.000000+00', 'user123', NULL, NULL, NULL, 6, 'Monthly hedge plan for Q2', 101, 102, 103, 201, 301); 
insert into company (id, created_at, created_by, deleted_at, updated_at, updated_by, delivery_prep_days, delivery_type, notify_email_list, passed_email_list, supervised, company_base_id) VALUES (1, '2023-04-01 12:00:00.000000+00', 'user123', NULL, NULL, NULL, 5, 'FULL', '{"email": "example1@example.com}", "email": "example2@example.com"}', '{"email": "example3@example.com}", "email": "example4@example.com"}', true, 101); 
insert into company_currency (id, created_at, created_by, deleted_at, updated_at, updated_by, fut_mon_avg_bias_limit, mom_bias_limit, mon_avg_bias_limit, payment_period, comp_currency_id, company_id) VALUES (1, '2023-04-01 12:00:00.000000', 'user123', NULL, NULL, NULL, 100.00, 50.00, 75.00, 30, 101, 201); 
insert into hedge_group (id, created_at, created_by, deleted_at, updated_at, updated_by, key, reject_reason, status, code, comment, name, delegate_id, group_currency_id, master_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 'HG001', NULL, 'PENDING', 'HG2023001', 'Initial hedge group setup', 'Hedge Group A', 101, 201, 301); 
insert into hedge_plan (id, created_at, created_by, deleted_at, updated_at, updated_by, approval_status, plan_no, year_month) VALUES (1, '2023-04-01 12:00:00.000000', 'user123', NULL, NULL, NULL, 'SUBMITTED', 'HP202304', 202304); 
insert into company_base (id, extension, alias, attribute, business_group, code, consolidated, domestic, name) VALUES (1, '{"key1": "value1", "key2": "value2"}', 'CompanyAlias123', 'AttributeX', 'BusinessGroupY', 'Code123', true, false, 'CompanyNameExample'); 
