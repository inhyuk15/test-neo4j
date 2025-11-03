from pathlib import Path
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_c as tsc


# parser setting
C_LANGUAGE = Language(tsc.language())
parser = Parser(C_LANGUAGE)


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