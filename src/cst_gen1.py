from pathlib import Path
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_c as tsc


# parser setting
C_LANGUAGE = Language(tsc.language())
parser = Parser(C_LANGUAGE)


def test3():
    # get_call_graph()
    get_cfg()

    


def get_call_graph():
    auth_c_path = Path("/Users/ihkang/workspace/paper/mavul/test-neo4j/auth.c")
    # logger_c_path = Path("/Users/ihkang/workspace/paper/mavul/test-neo4j/logger.c")

    auth_c_code = auth_c_path.read_text(encoding='utf8')
    tree = parser.parse(bytes(auth_c_code, 'utf8'))
    code_bytes = bytes(auth_c_code, 'utf8')

    query = Query(C_LANGUAGE, """
(
    function_definition
        declarator: (
            function_declarator(identifier) @func_name
        )
        body: (compound_statement) @body
)
""")
    cursor = QueryCursor(query)
    for _, captures in cursor.matches(tree.root_node):
        if "func_name" in captures:
            for node in captures['func_name']:
                print(f'... {node}')
                func_name = code_bytes[node.start_byte:node.end_byte].decode('utf8')
                print(f'func name: {func_name}') #2
    
    
def get_function_name(node, code_bytes):
    current = node
    while current:
        if current.type == 'function_definition':
            declarator = current.child_by_field_name('declarator')
            if declarator:
                for child in declarator.children:
                    if child.type == 'identifier':
                        return code_bytes[child.start_byte:child.end_byte].decode('utf8')
        current = current.parent
    return None

def get_cfg():
    auth_c_path = Path("/Users/ihkang/workspace/paper/mavul/test-neo4j/auth.c")
    # logger_c_path = Path("/Users/ihkang/workspace/paper/mavul/test-neo4j/logger.c")

    auth_c_code = auth_c_path.read_text(encoding='utf8')
    tree = parser.parse(bytes(auth_c_code, 'utf8'))
    code_bytes = bytes(auth_c_code, 'utf8')
    query = Query(C_LANGUAGE, """
(
    if_statement
        condition: (_) @condition
        consequence: (_) @then
        alternative: (_)? @else
)
""")

    
    cursor = QueryCursor(query)

    for _, captures in cursor.matches(tree.root_node):
        # func_name = get_function_name(captures, code_bytes)
        # print(f'name: {func_name}, len: {len(captures)}')
        if 'condition' in captures:
            condition_node = captures['condition'][0]
            func_name = get_function_name(condition_node, code_bytes)
            print(f'name: {func_name}, len: {len(captures)}')
            print(len(captures['condition']))
            cond_text = code_bytes[condition_node.start_byte:condition_node.end_byte].decode('utf8')
            print(f'cond: {cond_text}')

        if 'then' in captures:
            then_node = captures['then'][0]
            func_name = get_function_name(then_node, code_bytes)
            print(f'name: {func_name}, len: {len(captures)}')
            then_text = code_bytes[then_node.start_byte:then_node.end_byte].decode('utf8')
            print(f'then: {then_text}')
        
        if 'else' in captures:
            else_node = captures['else'][0]
            func_name = get_function_name(else_node, code_bytes)
            print(f'name: {func_name}, len: {len(captures)}')
            else_text = code_bytes[else_node.start_byte:else_node.end_byte].decode('utf8')
            print(f'else: {else_text}')

