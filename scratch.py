def build_dependency_tree(data, start_table):
    # 定义一个内部函数来递归构建依赖树
    def recurse(table):
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

        # 递归处理当前表的外键表
        for foreign_table in table_data['foreign_tables']:
            child_node = recurse(foreign_table)
            if child_node:
                node['dependencies'].append(child_node)

        return node

    # 从起始表名开始递归构建依赖树
    return recurse(start_table)


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
        'foreign_tables': ['company_base']
    },
    'company_base': {
        'stmts': [
        ],
        'foreign_tables': []
    }
}

# 构建依赖树
dependency_tree = build_dependency_tree(data, 'company_currency')
print(dependency_tree)

from collections import deque


def bfs_dependency_tree(dependency_tree):
    # 如果树为空，直接返回空列表
    if not dependency_tree:
        return []

    # 初始化队列，将根节点加入队列
    queue = deque([dependency_tree])
    # 存储遍历顺序的表名列表
    table_list = []

    # 当队列不为空时，进行广度优先遍历
    while queue:
        # 从队列中取出一个节点
        current_node = queue.popleft()
        # 将当前节点的表名添加到列表中
        table_list.append(current_node)
        # 将当前节点的所有子节点加入队列
        for child in current_node['dependencies']:
            queue.append(child)

    table_list.reverse()
    return table_list


# 进行广度优先遍历
table_list = bfs_dependency_tree(dependency_tree)
print(table_list)
