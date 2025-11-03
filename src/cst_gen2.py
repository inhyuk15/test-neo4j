from pathlib import Path
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_c as tsc


C_LANGUAGE = Language(tsc.language())
parser = Parser(C_LANGUAGE)

class TSRunner:
    def __init__(self, language, source_bytes):
        self.language = language
        self.src = source_bytes

    def run(self, query_src: str, node):
        q = Query(self.language, query_src)
        cursor = QueryCursor(q)
        for _, captures in cursor.matches(node):
            yield captures

    def text(self, node):
        return self.src[node.start_byte:node.end_byte].decode('utf8')


FUNC_QUERY = r"""
(function_definition
  declarator: (function_declarator (identifier) @func_name)
  body: (compound_statement) @body
)
"""

CALL_QUERY = r"""(call_expression function: (identifier) @func_name)"""
RETURN_QUERY = r"""(return_statement (_) @return_value)"""


def first_named_statement(node):
    """compound/statement_list 래퍼를 벗겨 첫 번째 statement 노드 반환"""
    if node is None:
        return None
    for ch in node.named_children:
        if ch.type.endswith("statement"):
            return ch
        if ch.type == "statement_list":
            for st in ch.named_children:
                if st.type.endswith("statement"):
                    return st
    return None

def alt_as_if(node):
    """alternative가 if_statement인지(혹은 래퍼 안에 if_statement인지) 판별"""
    if node is None:
        return None
    if node.type == "if_statement":
        return node
    fst = first_named_statement(node)
    return fst if fst and fst.type == "if_statement" else None

def print_block(runner: TSRunner, block_node, indent="  "):
    for cap in runner.run(CALL_QUERY, block_node):
        for n in cap.get("func_name", []):
            print(f"{indent}  CALL {runner.text(n)}()")
    for cap in runner.run(RETURN_QUERY, block_node):
        for n in cap.get("return_value", []):
            print(f"{indent}  RETURN {runner.text(n)}")

def print_if_chain(runner: TSRunner, if_node, indent="  "):
    node, first = if_node, True
    while True:
        cond = node.child_by_field_name("condition")
        then = node.child_by_field_name("consequence")
        alt  = node.child_by_field_name("alternative")

        head = "IF" if first else "ELSE IF"
        first = False
        cond_text = runner.text(cond) if cond else ""
        print(f"{indent}{head} {cond_text}")
        if then:
            print_block(runner, then, indent)

        if not alt:
            break
        nxt = alt_as_if(alt)
        if nxt:
            node = nxt
            continue
        print(f"{indent}ELSE")
        print_block(runner, alt, indent)
        break

def analyze_file(path: str):
    code = Path(path).read_text(encoding="utf-8")
    src = code.encode("utf-8")
    tree = parser.parse(src)
    runner = TSRunner(C_LANGUAGE, src)

    for cap in runner.run(FUNC_QUERY, tree.root_node):
        func_name = runner.text(cap["func_name"][0])
        body = cap["body"][0]
        print(f"\nFunction: {func_name}")

        top_ifs = [ch for ch in body.children if ch.type == "if_statement"]

        for if_node in top_ifs:
            print_if_chain(runner, if_node, indent="  ")

def get_call_graph_with_cfg():
    analyze_file("/Users/ihkang/workspace/paper/mavul/test-neo4j/auth.c")
