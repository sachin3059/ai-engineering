#safe file system and terminal functions


import os
import subprocess

# Define a safe workspace directory to restrict file operations (Sandboxing)
WORKSPACE_DIR = os.path.abspath("./workspace")

# Ensure workspace directory exists
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def _get_safe_path(filepath: str) -> str:
    """Ensure file paths remain within the designated workspace directory."""
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filepath))
    if not target_path.startswith(WORKSPACE_DIR):
        raise ValueError(f"Access denied: Path '{filepath}' is outside workspace.")
    return target_path

def read_file(filepath: str) -> str:
    """Read contents of a file."""
    try:
        path = _get_safe_path(filepath)
        if not os.path.exists(path):
            return f"Error: File '{filepath}' does not exist."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Create or overwrite a file with new content."""
    try:
        path = _get_safe_path(filepath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filepath}' written successfully."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_directory(path: str = ".") -> str:
    """List files and directories within a given workspace folder."""
    try:
        target_path = _get_safe_path(path)
        if not os.path.exists(target_path):
            return f"Error: Directory '{path}' does not exist."
        items = os.listdir(target_path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def delete_file(filepath: str) -> str:
    """Delete a file."""
    try:
        path = _get_safe_path(filepath)
        if not os.path.exists(path):
            return f"Error: File '{filepath}' does not exist."
        os.remove(path)
        return f"File '{filepath}' deleted successfully."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def run_command(command: str) -> str:
    """Execute a terminal command in the workspace directory."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
        return output if output.strip() else "Command executed with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"