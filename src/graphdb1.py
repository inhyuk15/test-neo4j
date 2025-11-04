from langchain_core.tools import tool

from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "1234aaaa" 
driver = GraphDatabase.driver(uri, auth=(user, password))

def create_sample_data(tx):
    tx.run("""
// 함수 노드 생성
CREATE (f1:Function {name: 'check_password'})
CREATE (f2:Function {name: 'login_user'})

// check_password 로직 표현
CREATE (cond1:Condition {expression: 'strcmp(password, "admin123") == 0'})
CREATE (ret_true1:Return {value: true})
CREATE (f1)-[:HAS_CONDITION]->(cond1)
CREATE (cond1)-[:RETURNS]->(ret_true1)

// login_user 로직 표현
CREATE (cond2:Condition {expression: 'check_password(username, password)'})
CREATE (printf_call:Call {function: 'printf'})
CREATE (log_call:Call {function: 'log_auth_failure'})
CREATE (ret_true2:Return {value: true})
CREATE (ret_false2:Return {value: false})

CREATE (f2)-[:HAS_CONDITION]->(cond2)
CREATE (cond2)-[:IF_TRUE]->(printf_call)
CREATE (printf_call)-[:RETURNS]->(ret_true2)
CREATE (cond2)-[:IF_FALSE]->(log_call)
CREATE (log_call)-[:RETURNS]->(ret_false2)

CREATE (f2)-[:CALLS]->(f1)
CREATE (f2)-[:CALLS]->(printf_call)
CREATE (f2)-[:CALLS]->(log_call)

    """)
    

def print_functions(tx):
    # result = tx.run('MATCH (f:Function) RETURN f.name AS name')
    result = tx.run("""
    MATCH path = (f:Function {name: 'login_user'})-[*1..3]->(n)
    RETURN path;
    """)

    for record in result:
        print(f"Function: {record['path']}")

def delete_all(tx):
    tx.run('match (n) detach delete n')


def test():
    print(f'driver: {driver}')

    with driver.session(database="neo4j") as session:
        session.execute_write(create_sample_data)
        # session.execute_write(delete_all)
        session.execute_read(print_functions)


@tool
def call_graph_tool(function_name: str) -> str:
    """
    Returns a list of all functions directly called by the given function.
    
    Args:
        function_name: Name of the function to analyze (e.g., "login_user", "check_password")
    
    Returns:
        Comma-separated string of called function names.
        Returns appropriate message if function not found or has no calls.
    
    Examples:
        call_graph_tool("login_user") 
        → "check_password, printf, log_auth_failure"
    """
    query = """
    MATCH (f:Function {name: $fname})-[:CALLS]->(callee)
    RETURN callee.name AS called
    """
    print(f'[call_graph_tool] function_name: {function_name}')
    
    with driver.session(database="neo4j") as session:
        result = session.run(query, fname=function_name)
        called_funcs = [record["called"] for record in result]
        
        if not called_funcs:
            return f"Function '{function_name}' not found or has no function calls."
        
        return ", ".join(called_funcs)


@tool
def cfg_tool(function_name: str, branch: str = "IF_FALSE") -> str:
    """
    Returns functions called in a specific branch of the control flow graph (CFG).
    
    Args:
        function_name: Name of the function to analyze (e.g., "login_user")
        branch: Branch type to analyze. "IF_TRUE" or "IF_FALSE" (default: "IF_FALSE")
                IF_TRUE: path executed when condition is true
                IF_FALSE: path executed when condition is false (authentication failure, etc.)
    
    Returns:
        Comma-separated string of function names called in the branch.
        Returns appropriate message if no results found.
    
    Examples:
        cfg_tool("login_user", "IF_FALSE")
        → "log_auth_failure"
        
        cfg_tool("login_user", "IF_TRUE")
        → "printf"
    """
    if branch not in ["IF_TRUE", "IF_FALSE"]:
        return f"Invalid branch value. Use 'IF_TRUE' or 'IF_FALSE'. (input: {branch})"
    
    query = f"""
    MATCH (f:Function {{name: $fname}})-[:HAS_CONDITION]->(c:Condition)
    MATCH (c)-[:{branch}]->(callee)
    RETURN callee.function AS called
    """
    print(f'[cfg_tool] function_name: {function_name}, branch: {branch}')

    with driver.session(database="neo4j") as session:
        result = session.run(query, fname=function_name)
        called_funcs = [record["called"] for record in result]
        
        if not called_funcs:
            return f"No functions found in {branch} branch of function '{function_name}'."
        
        return ", ".join(called_funcs)