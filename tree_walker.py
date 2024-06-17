from collections import deque


def build_dependency_tree(data, start_table):
    # 定义一个内部函数来递归构建依赖树
    def recurse(table, visited):
        # 获取当前表的数据
        table_data = data.get(table)
        if not table_data:
            return None

        # 构建当前表的依赖节点
        node = {
            'table': table,
            'stmts': table_data['stmts'],  # SQL插入语句
            'dependencies': []  # 子依赖
        }

        # 添加当前表到已访问集合，防止自依赖和循环依赖
        visited.add(table)

        # 递归处理当前表的外键表
        for foreign_table in table_data['foreign_tables']:
            if foreign_table == table or foreign_table in visited:
                continue
            child_node = recurse(foreign_table, visited)
            if child_node:
                node['dependencies'].append(child_node)

        # 递归完成后移除当前表，以便其他路径可以访问该表
        visited.remove(table)

        return node

    # 从起始表名开始递归构建依赖树
    return recurse(start_table, set())


def bfs_dependency_tree(dependency_tree):
    # 如果树为空，直接返回空列表
    if not dependency_tree:
        return []

    # 初始化队列，将根节点加入队列
    queue = deque([dependency_tree])
    # 存储遍历顺序的表名列表
    table_list = []
    # 用于跟踪已访问的节点
    visited = set()

    # 当队列不为空时，进行广度优先遍历
    while queue:
        # 从队列中取出一个节点
        current_node = queue.popleft()

        # 如果当前节点的表名已经访问过，跳过该节点
        if current_node['table'] in visited:
            continue

        # 将当前节点的表名添加到已访问集合中
        visited.add(current_node['table'])
        # 将当前节点添加到列表中
        table_list.append(current_node)

        # 将当前节点的所有子节点加入队列
        for child in current_node['dependencies']:
            queue.append(child)

    table_list.reverse()
    return table_list


if __name__ == '__main__':
    # 测试数据
    data = {
        'company_currency': {
            'stmts': [

            ],
            'foreign_tables': ['currency', 'company']
        },
        'currency': {
            'stmts': [],
            'foreign_tables': []
        },
        'company': {
            'stmts': [
            ],
            'foreign_tables': ['company_base', 'company']
        },
        'company_base': {
            'stmts': [
            ],
            'foreign_tables': []
        }
    }

    # 构建依赖树
    dependency_tree = build_dependency_tree(data, 'company_currency')
    print(len(dependency_tree))
    print(dependency_tree)

    # 进行广度优先遍历
    table_list = bfs_dependency_tree(dependency_tree)
    print(len(table_list))
    print(table_list)
    for i in table_list:
        print(i['table'])
