import re


def load_ddl(ddl_text: str) -> dict:
    table_pattern = re.compile(r'create table (\w+)\s*\((.*?)\);', re.DOTALL | re.IGNORECASE)
    matches = table_pattern.findall(ddl_text)

    ddl_dict = {}
    for match in matches:
        table_name, table_definition = match
        ddl_dict[table_name] = f"create table {table_name} (\n{table_definition.strip()}\n);"

    return ddl_dict
