class TreeNode:
    def __init__(self, name, depth):
        self.name = name
        self.depth = depth
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.name) + " (Depth: " + str(self.depth) + ")\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret


def build_tree(data, depth=0):
    def build_node(key, value, depth, visited):
        if key in visited:
            return None
        visited.add(key)
        node = TreeNode(key, depth)
        for table in value.get('foreign_tables', []):
            child_node = build_node(table, data[table], depth + 1, visited)
            if child_node:
                node.add_child(child_node)
        visited.remove(key)
        return node

    root = TreeNode('root', depth)
    visited = set()
    for key, value in data.items():
        root.add_child(build_node(key, value, depth + 1, visited))

    return root


def traverse_and_collect_names(node):
    name_depth_map = {}

    def traverse(node):
        if node.name in name_depth_map:
            name_depth_map[node.name] = max(name_depth_map[node.name], node.depth)
        else:
            name_depth_map[node.name] = node.depth
        for child in node.children:
            traverse(child)

    traverse(node)
    sorted_names = sorted(name_depth_map.items(), key=lambda x: x[1], reverse=True)
    return [name for name, depth in sorted_names]


if __name__ == '__main__':
    # Example usage
    data = {
        'trading_task': {
            'stmts': [
                "insert into trading_task (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_time, buy_remainingm, buy_volume, execute_status, expire_date, last_trading_time, sell_remainingm, sell_volume, task_no, traded_volumem, transferred_volumem, ym, assigner_id, buy_currency_id, instruction_id, parent_id, sell_currency_id, trader_id) VALUES (1, '2023-04-01 12:00:00.000000', 'user123', NULL, NULL, NULL, '2023-04-02 12:00:00.000000', 100.00, 200.00, 'PENDING', '2023-05-01 12:00:00.000000', NULL, 150.00, 250.00, 'T123456', 50.00, 30.00, 2023, 1, 1, 1, 1, 1, 1); "
            ],
            'foreign_tables': [
                'general_user',
                'currency',
                'instruction',
                'trading_task'
            ]
        },
        'general_user': {
            'stmts': [
                "insert into general_user (id, employee_number, extension, organization_name, user_id) VALUES (1, '123456', '{}', 'Example Organization', 'user123'); "
            ],
            'foreign_tables': []
        },
        'currency': {
            'stmts': [
                "insert into currency (id, code, name) VALUES (1, 'USD', 'United States Dollar'); "
            ],
            'foreign_tables': []
        },
        'instruction': {
            'stmts': [
                'insert into instruction (id, created_at, created_by, deleted_at, updated_at, updated_by, assign_status, assigned_volumem, confirmed_volumem, execute_status, "from", generated_time, instruction_no, trade_direction, traded_volumem, trading_volumem, hedge_plan_entry_id, master_id) VALUES (1, \'2023-04-01 12:00:00.000000+00\', \'user123\', NULL, NULL, NULL, \'PENDING\', 100.00, 200.00, \'PENDING\', \'HEDGE_PLAN\', \'2023-04-01 12:05:00.000000+00\', \'INSTR12345\', \'BUY\', 50.00, 150.00, 1, 2); '
            ],
            'foreign_tables': [
                'hedge_plan_entry',
                'company'
            ]
        },
        'hedge_plan_entry': {
            'stmts': [
                "insert into hedge_plan_entry (id, created_at, created_by, deleted_at, updated_at, updated_by, month_term, remark, company_currency_id, exposure_currency_id, hedge_currency_id, hedge_group_id, plan_id) VALUES (1, '2023-04-01 12:00:00.000000', 'user123', NULL, NULL, NULL, 6, 'Monthly hedge plan', 1, 2, 3, 4, 5); "
            ],
            'foreign_tables': [
                'company_currency',
                'currency',
                'hedge_group',
                'hedge_plan'
            ]
        },
        'company': {
            'stmts': [
                "insert into company (id, created_at, created_by, deleted_at, updated_at, updated_by, delivery_prep_days, delivery_type, supervised, company_base_id) VALUES (1, '2023-04-01 12:00:00.000000+00', 'user123', NULL, NULL, NULL, 5, 'FULL', true, 1); "
            ],
            'foreign_tables': [
                'company_base'
            ]
        },
        'company_currency': {
            'stmts': [
                "insert into company_currency (id, created_at, created_by, deleted_at, updated_at, updated_by, fut_mon_avg_bias_limit, mom_bias_limit, mon_avg_bias_limit, payment_period, comp_currency_id, company_id) VALUES (1, '2023-04-01 12:00:00+00', 'user123', NULL, NULL, NULL, 100.00, 200.00, 300.00, 12, 1, 1); "
            ],
            'foreign_tables': [
                'currency',
                'company'
            ]
        },
        'hedge_group': {
            'stmts': [
                "insert into hedge_group (id, created_at, created_by, deleted_at, updated_at, updated_by, key, reject_reason, status, code, comment, name, delegate_id, group_currency_id, master_id) VALUES (1, '2023-04-01 12:00:00.000000', 'user123', NULL, NULL, NULL, 'hedgeKey123', NULL, 'PENDING', 'HG20230401', 'Initial hedge group setup', 'HedgeGroup1', 1, 1, 1); "
            ],
            'foreign_tables': [
                'company',
                'currency',
                'company_currency'
            ]
        },
        'hedge_plan': {
            'stmts': [
                "insert into hedge_plan (id, created_at, created_by, deleted_at, updated_at, updated_by, approval_status, plan_no, year_month) VALUES (1, '2023-04-01 12:00:00.000000', 'user123', NULL, NULL, NULL, 'PENDING', 'HP202304', 202304); "
            ],
            'foreign_tables': []
        },
        'company_base': {
            'stmts': [
                "insert into company_base (id, alias, attribute, business_group, code, consolidated, domestic, name) VALUES (1, 'field value 1 generated', 'field value 2 generated', 'field value 3 generated', 'field value 4 generated', true, false, 'field value 5 generated'); "
            ],
            'foreign_tables': []
        }
    }

    tree = build_tree(data)
    print(tree)

    unique_names = traverse_and_collect_names(tree)
    print(unique_names)
