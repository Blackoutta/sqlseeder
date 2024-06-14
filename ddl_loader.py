import re


def load_ddl(sql_ddl):
    tables = {}
    current_table = None
    lines = sql_ddl.splitlines()

    create_table_pattern = re.compile(r'create table (\w+)')
    comment_table_pattern = re.compile(r"comment on table (\w+) is '(.*?)';")
    comment_column_pattern = re.compile(r"comment on column (\w+)\.(\w+) is '(.*?)';")

    for line in lines:
        create_table_match = create_table_pattern.search(line)
        if create_table_match:
            current_table = create_table_match.group(1)
            tables[current_table] = {
                'create_statement': '',
                'comments': {}
            }

        comment_table_match = comment_table_pattern.search(line)
        if comment_table_match:
            table_name = comment_table_match.group(1)
            comment = comment_table_match.group(2)
            if table_name in tables:
                tables[table_name]['table_comment'] = comment

        comment_column_match = comment_column_pattern.search(line)
        if comment_column_match:
            table_name = comment_column_match.group(1)
            column_name = comment_column_match.group(2)
            comment = comment_column_match.group(3)
            if table_name in tables:
                tables[table_name]['comments'][column_name] = comment

        if current_table and 'create_statement' in tables[current_table]:
            tables[current_table]['create_statement'] += line + '\n'

        if line.strip() == ');':
            current_table = None

    return tables


if __name__ == '__main__':
    with open('./ddl.txt') as f:
        m = load_ddl(f.read())
    print(m['account'])
