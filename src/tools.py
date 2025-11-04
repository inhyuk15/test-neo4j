from langchain.tools import tool
import subprocess

@tool("terminal_tool")
def terminal_tool(command: str) -> str:
    """
    Executes terminal commands within safe boundaries.
    Example: 'grep -rn TODO src/'
    """
    print(f'tool: {command}')
    # Security filter
    blocked = ["rm", "sudo", "reboot", "shutdown", "mv", "kill"]
    if any(b in command for b in blocked):
        return "⚠️ This command is not allowed for security reasons."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout:
            return result.stdout.strip()
        elif result.stderr:
            return f"(stderr)\n{result.stderr.strip()}"
        else:
            return "(no output)"
    except subprocess.TimeoutExpired:
        return "⏰ Command execution timed out."
    except Exception as e:
        return f"❌ Error occurred: {e}"