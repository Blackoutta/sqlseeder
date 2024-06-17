def correct_sql(sql_string):
    return sql_string.replace('"from"', '`from`')


# Example usage with the 'instruction' table insert statement
statement = """
insert into instruction (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_status, assigned_volumem, confirmed_volumem, execute_status, "from", generated_time, instruction_no, trade_direction, traded_volumem, trading_volumem, hedge_plan_entry_id, master_id) 
VALUES (1, '2023-04-01 12:00:00.000000+00', 'user123', NULL, NULL, NULL, 'PENDING', 100.00, 200.00, 'PENDING', 'HEDGE_PLAN', '2023-04-01 12:05:00.000000+00', 'INSTR12345', 'BUY', 50.00, 150.00, 1, 2); 
"""

corrected = correct_sql(statement)
print(corrected)
