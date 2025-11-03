from pathlib import Path
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_c as tsc
from dataclasses import dataclass, field
from typing import List, Dict


C_LANGUAGE = Language(tsc.language())
parser = Parser(C_LANGUAGE)


@dataclass
class CFGNode:
    id: int
    type: str
    code: str
    line: int
    successors: List[int] = field(default_factory=list)


@dataclass
class Function:
    name: str
    start_line: int
    end_line: int
    calls: List[str]
    cfg: List[CFGNode]


class CFGBuilder:
    def __init__(self, source_bytes: bytes):
        self.src = source_bytes
        self.node_id = 0
        self.cfg_nodes = []
        
    def text(self, node) -> str:
        if not node:
            return ""
        return self.src[node.start_byte:node.end_byte].decode('utf8')
    
    def new_node(self, node_type: str, code: str, line: int) -> CFGNode:
        node = CFGNode(self.node_id, node_type, code, line)
        self.node_id += 1
        self.cfg_nodes.append(node)
        return node
    
    def build_cfg(self, body_node) -> List[CFGNode]:
        self.cfg_nodes = []
        self.node_id = 0
        
        entry = self.new_node('entry', 'ENTRY', body_node.start_point[0])
        exit_node = self.new_node('exit', 'EXIT', body_node.end_point[0])
        
        last_nodes = [entry]
        for stmt in body_node.named_children:
            last_nodes = self._process_statement(stmt, last_nodes, exit_node)
        
        for node in last_nodes:
            if 'return' not in node.type:
                node.successors.append(exit_node.id)
        
        return self.cfg_nodes
    
    def _process_statement(self, stmt, predecessors: List[CFGNode], 
                          exit_node: CFGNode) -> List[CFGNode]:
        
        if stmt.type == 'if_statement':
            return self._process_if(stmt, predecessors, exit_node)
        
        if stmt.type in ('while_statement', 'for_statement'):
            return self._process_loop(stmt, predecessors, exit_node)
        
        if stmt.type == 'return_statement':
            return self._process_return(stmt, predecessors, exit_node)
        
        if stmt.type == 'expression_statement':
            return self._process_expression(stmt, predecessors)
        
        if stmt.type == 'compound_statement':
            last = predecessors
            for child in stmt.named_children:
                last = self._process_statement(child, last, exit_node)
            return last
        
        node = self.new_node('statement', self.text(stmt), stmt.start_point[0])
        for pred in predecessors:
            pred.successors.append(node.id)
        return [node]
    
    def _process_if(self, if_stmt, predecessors, exit_node) -> List[CFGNode]:
        cond = if_stmt.child_by_field_name('condition')
        consequence = if_stmt.child_by_field_name('consequence')
        alternative = if_stmt.child_by_field_name('alternative')
        
        cond_node = self.new_node(
            'condition',
            self.text(cond),
            cond.start_point[0] if cond else if_stmt.start_point[0]
        )
        for pred in predecessors:
            pred.successors.append(cond_node.id)
        
        then_last = self._process_statement(consequence, [cond_node], exit_node)
        
        if alternative:
            else_last = self._process_statement(alternative, [cond_node], exit_node)
            return then_last + else_last
        
        return then_last + [cond_node]
    
    def _process_loop(self, loop_stmt, predecessors, exit_node) -> List[CFGNode]:
        cond = loop_stmt.child_by_field_name('condition')
        body = loop_stmt.child_by_field_name('body')
        
        cond_node = self.new_node(
            'condition',
            self.text(cond) if cond else 'loop',
            loop_stmt.start_point[0]
        )
        for pred in predecessors:
            pred.successors.append(cond_node.id)
        
        body_last = self._process_statement(body, [cond_node], exit_node)
        
        for node in body_last:
            node.successors.append(cond_node.id)
        
        return [cond_node]
    
    def _process_return(self, ret_stmt, predecessors, exit_node) -> List[CFGNode]:
        node = self.new_node('return', self.text(ret_stmt), ret_stmt.start_point[0])
        for pred in predecessors:
            pred.successors.append(node.id)
        node.successors.append(exit_node.id)
        return []
    
    def _process_expression(self, expr_stmt, predecessors) -> List[CFGNode]:
        is_call = self._has_call_expression(expr_stmt)
        node_type = 'call' if is_call else 'statement'
        
        node = self.new_node(node_type, self.text(expr_stmt), expr_stmt.start_point[0])
        for pred in predecessors:
            pred.successors.append(node.id)
        return [node]
    
    def _has_call_expression(self, node) -> bool:
        if node.type == 'call_expression':
            return True
        return any(self._has_call_expression(child) for child in node.children)


class CodeAnalyzer:
    def __init__(self, source_code: str):
        self.code = source_code
        self.src = source_code.encode('utf-8')
        self.tree = parser.parse(self.src)
        self.functions: Dict[str, Function] = {}
        
    def text(self, node) -> str:
        if not node:
            return ""
        return self.src[node.start_byte:node.end_byte].decode('utf8')
    
    def analyze(self):
        self._extract_functions()
        return self.functions
    
    def _extract_functions(self):
        query = Query(C_LANGUAGE, """
            (function_definition
              declarator: (function_declarator 
                declarator: (identifier) @func_name)
              body: (compound_statement) @body
            )
        """)
        
        cursor = QueryCursor(query)
        for _, captures in cursor.matches(self.tree.root_node):
            func_name_node = captures['func_name'][0]
            body_node = captures['body'][0]
            
            func_name = self.text(func_name_node)
            
            builder = CFGBuilder(self.src)
            cfg = builder.build_cfg(body_node)
            calls = self._extract_calls(body_node)
            
            self.functions[func_name] = Function(
                name=func_name,
                start_line=func_name_node.start_point[0],
                end_line=body_node.end_point[0],
                calls=calls,
                cfg=cfg
            )
    
    def _extract_calls(self, node) -> List[str]:
        calls = []
        
        def visit(n):
            if n.type == 'call_expression':
                func = n.child_by_field_name('function')
                if func and func.type == 'identifier':
                    calls.append(self.text(func))
            for child in n.children:
                visit(child)
        
        visit(node)
        return calls
    
    def print_analysis(self):
        print("=" * 60)
        print("CODE ANALYSIS REPORT")
        print("=" * 60)
        
        for func_name, func in self.functions.items():
            print(f"\n{'=' * 60}")
            print(f"Function: {func_name}")
            print(f"Lines: {func.start_line + 1} - {func.end_line + 1}")
            print(f"Calls: {', '.join(func.calls) if func.calls else 'None'}")
            print(f"{'=' * 60}")
            print("\nControl Flow Graph:")
            self._print_cfg(func.cfg)
    
    def _print_cfg(self, cfg: List[CFGNode]):
        for node in cfg:
            code = node.code.replace('\n', ' ').strip()
            if len(code) > 50:
                code = code[:47] + "..."
            
            print(f"  [{node.id:2d}] {node.type:12s} | {code:50s}", end="")
            if node.successors:
                print(f" -> {node.successors}")
            else:
                print()
    
    def print_call_graph(self):
        print("\n" + "=" * 60)
        print("Call Graph:")
        print("=" * 60)
        for func_name, func in self.functions.items():
            if func.calls:
                for callee in func.calls:
                    print(f"  {func_name} -> {callee}")


def get_call_graph_with_cfg():
    code = Path("/Users/ihkang/workspace/paper/mavul/test-neo4j/auth.c").read_text()
    
    analyzer = CodeAnalyzer(code)
    analyzer.analyze()
    analyzer.print_analysis()
    analyzer.print_call_graph()


if __name__ == "__main__":
    get_call_graph_with_cfg()