# main loop, model calls, tool execution, final answer

from openai import OpenAI
import os
import tools
import json

client = OpenAI(
    api_key=os.environ.get("SNOWFLAKE_TOKEN"),
    base_url=os.environ.get("SNOWFLAKE_BASE_URL")
)


# tools schema
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text content of a file within the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to the file"}
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with specific content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to the file"},
                    "content": {"type": "string", "description": "Content to write into the file"},
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List all files and folders in a specified path inside workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path (defaults to '.')"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file inside the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to the file"}
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command inside the workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"}
                },
                "required": ["command"],
            },
        },
    },
]



# 1. Map tool names (from schema) to actual Python functions in tools.py
TOOL_MAP = {
    "read_file": tools.read_file,
    "write_file": tools.write_file,
    "list_directory": tools.list_directory,
    "delete_file": tools.delete_file,
    "run_command": tools.run_command,
}


# Define commands that require manual human approval for safety
DANGEROUS_COMMANDS = ["rm -rf", "git reset --hard", "git push", "del /f", "rd /s"]


def requires_approval(command: str) -> bool:
    """Check if a shell command is potentially dangerous."""
    return any(danger in command.lower() for danger in DANGEROUS_COMMANDS)


def run_agent(prompt: str, max_steps: int = 15) :
    """ Main ReAct loop for the coding agent."""

    #Initialize message history with a system prompt guiding its behavior

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AI coding agent. You have access to tools to read, write, "
                "and edit files, list directories, and run terminal commands. "
                "Work step-by-step to fulfill user requests. Always test your created code by running it."
            )
        },
        {
            "role": "user",
            "content": prompt   
        }
    ]

    print(f"\n🚀 [Agent Started]: {prompt}\n" + "="*50)


    # ReAct loop
    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step}/{max_steps} ---")

        # Call OpenAI with tools enabled
        response = client.chat.completions.create(
            model="openai-gpt-5-mini",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )


        response_message = response.choices[0].message
        messages.append(response_message)


        # If the LLM didn't request a tool call, it means it gave its Final Answer

        if not response_message.tool_calls:
            print("\n🏁 [Final Answer]:")
            print(response_message.content)
            break
        
        # Process each tool call requested by the model
        for tool_call in response_message.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"🛠️ [Tool Call]: {func_name}({args})")

            # Human-in-the-Loop check for dangerous terminal actions
            if func_name == "run_command" and requires_approval(args.get("command", "")):
                user_approval = input(f"⚠️ Action '{args['command']}' requires approval. Allow? (y/n): ")
                if user_approval.lower() != 'y':
                    observation = "Execution aborted by user."
                    print("🛑 Execution blocked by user.")
                else:
                    observation = TOOL_MAP[func_name](**args)
            else:
                # Execute the tool function dynamically
                if func_name in TOOL_MAP:
                    observation = TOOL_MAP[func_name](**args)
                else:
                    observation = f"Error: Tool {func_name} not found."

            print(f"👁️ [Observation]:\n{observation}\n")

            # Feed the tool's output back into the conversation history as a 'tool' role
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(observation)
            })



if __name__ == "__main__":
    # Test prompt from your assignment requirements
    test_prompt = (
        "Crate a python script that explains me about re rooting tree dp concets of dynamic programming"
        "Explain with some suitable examples and mention these examples in the script"
    )
    run_agent(test_prompt)


