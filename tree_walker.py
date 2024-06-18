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
    def build_node(k, v, dp, already_visited):
        if k in already_visited:
            return None
        already_visited.add(k)
        node = TreeNode(k, dp)
        for table in v.get('foreign_tables', []):
            child_node = build_node(table, data[table], dp + 1, already_visited)
            if child_node:
                node.add_child(child_node)
        already_visited.remove(k)
        return node

    root = TreeNode('root', depth)
    visited = set()
    for key, value in data.items():
        root.add_child(build_node(key, value, depth + 1, visited))

    return root


def traverse_and_collect_names(node):
    name_depth_map = {}

    def traverse(n):
        if n.name in name_depth_map:
            name_depth_map[n.name] = max(name_depth_map[n.name], n.depth)
        else:
            name_depth_map[n.name] = n.depth
        for child in n.children:
            traverse(child)

    traverse(node)
    sorted_names = sorted(name_depth_map.items(), key=lambda x: x[1], reverse=True)
    return [name for name, depth in sorted_names]
