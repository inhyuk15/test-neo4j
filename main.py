import os
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from src.graphdb1 import call_graph_tool, cfg_tool, test
from src.tools import terminal_tool
from dotenv import load_dotenv

load_dotenv()

prompt = """
You are a code analysis agent.

### Rules
- Maximum 3 tool calls
- No duplicate searches
- Answer immediately with sufficient info

### Tools
1. **terminal_tool**: Find function names via grep
2. **call_graph_tool**: Get functions called by a function
3. **cfg_tool**: Get functions called in IF_TRUE/IF_FALSE branch

### Strategy
1. Use terminal_tool to find relevant function name
2. Use call_graph_tool to see what that function calls
3. If question asks about "failure" or "error", use cfg_tool with IF_FALSE

### Output
One sentence: "Function X is called in Y situation."
"""



def get_agent():
    gpt_model = ChatOpenAI(
        model="gpt-4o-mini",
        # model="gpt-3.5-turbo-0125",
        openai_api_base="https://api.openai.com/v1",
        openai_api_key=os.getenv('OPENAI_API_KEY'),
    )

    return create_agent(
        tools=[terminal_tool, call_graph_tool, cfg_tool],
        # tools=[terminal_tool],
        system_prompt=prompt,
        model=gpt_model,
    )


def main():
    # test()
    agent = get_agent()
    msg = HumanMessage('What function is called when authentication fails in /Users/ihkang/workspace/paper/mavul/test-neo4j/MAVUL?')
    result = agent.invoke({
        "messages": msg
    })
    print(result.get("messages")[-1].content) 


if __name__ == "__main__":
    main()
