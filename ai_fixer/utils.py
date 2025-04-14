# ai_fixer/utils.py

import os
import re
import json
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ai_fixer.config import CONFIG


def run_tests(test_command: List[str] = None, project_path: str = None) -> Dict[str, Any]:
    """
    Run tests in the specified project and capture the results.

    Args:
        test_command: Command to run tests (e.g., ["pytest"])
        project_path: Path to the project to test

    Returns:
        Dict containing:
            - success (bool): Whether tests passed
            - traceback (str): Error traceback if tests failed
            - command (str): Command that was run
    """
    if project_path is None:
        project_path = CONFIG.get("project_path", os.getcwd())

    if test_command is None:
        test_command = CONFIG.get("test_command", ["pytest"])

    try:
        # Change to the project directory
        original_dir = os.getcwd()
        os.chdir(project_path)

        # Run the test command
        result = subprocess.run(
            test_command,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit code
        )

        # Change back to original directory
        os.chdir(original_dir)

        # Check if tests passed
        if result.returncode == 0:
            return {
                "success": True,
                "command": " ".join(test_command),
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "command": " ".join(test_command),
                "traceback": result.stderr,
                "output": result.stdout
            }
    except Exception as e:
        # Change back to original directory in case of exception
        if 'original_dir' in locals():
            os.chdir(original_dir)

        return {
            "success": False,
            "command": " ".join(test_command) if test_command else "Unknown",
            "traceback": f"Failed to run tests: {str(e)}"
        }


def find_failing_file(traceback: str, project_path: str, fallback: bool = False) -> Optional[str]:
    """
    Parse the traceback to find the file that caused the error.

    Args:
        traceback: The error traceback string
        project_path: The root path of the project
        fallback: Whether to use function name fallback method

    Returns:
        Path to the failing file or None if not found
    """
    if not traceback:
        return None

    # Look for file paths in the traceback using regex
    file_paths = re.findall(r'File "([^"]+)"', traceback)

    # Extract line numbers for context
    line_numbers = re.findall(r'line (\d+)', traceback)

    # Process each file path
    for idx, path in enumerate(file_paths):
        # Skip virtual environment paths, libraries, and internal framework files
        if not os.path.exists(path):
            continue

        # Focus on project files
        if project_path in path and not any(
                skip_pattern in path for skip_pattern in
                ['__pycache__', 'site-packages', 'venv', '.git']
        ):
            # Avoid core project files that shouldn't be modified
            if path.endswith(('__init__.py', 'conftest.py')):
                continue

            # Return absolute path to the file
            return os.path.abspath(path)

    # Fallback: use assertion error or function names in the traceback
    if fallback:
        # Look for test files
        test_files = [p for p in file_paths if 'test_' in p or 'tests/' in p]
        if test_files:
            for test_file in test_files:
                if os.path.exists(test_file):
                    # Read the test file
                    with open(test_file, 'r') as f:
                        content = f.read()

                    # Look for import statements to find the file being tested
                    imports = re.findall(r'from\s+(\S+)\s+import', content)
                    imports.extend(re.findall(r'import\s+(\S+)', content))

                    for imp in imports:
                        # Convert import to potential file path
                        module_path = imp.replace('.', '/')
                        potential_files = [
                            f"{project_path}/{module_path}.py",
                            f"{project_path}/{module_path}/__init__.py"
                        ]

                        for pot_file in potential_files:
                            if os.path.exists(pot_file):
                                return os.path.abspath(pot_file)

        # If no file found, try to extract error message and grep for it
        error_messages = re.findall(r'(AssertionError:.+?)$', traceback, re.MULTILINE)
        if error_messages:
            error_msg = error_messages[0].strip()
            # Use grep to find files containing this error message
            try:
                grep_result = subprocess.run(
                    ["grep", "-r", error_msg, project_path],
                    capture_output=True,
                    text=True
                )
                if grep_result.stdout:
                    file_matches = re.findall(r'^([^:]+):', grep_result.stdout, re.MULTILINE)
                    for file_match in file_matches:
                        if os.path.exists(file_match) and os.path.isfile(file_match):
                            return os.path.abspath(file_match)
            except Exception:
                pass

    return None


def read_file(file_path: str) -> str:
    """
    Read a file and return its contents as a string.

    Args:
        file_path: Path to the file

    Returns:
        str: Contents of the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1 if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def write_file(file_path: str, content: str) -> bool:
    """
    Write content to a file.

    Args:
        file_path: Path to the file
        content: String content to write

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Write the content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing to file {file_path}: {str(e)}")
        return False


def log_correction(file_path: str, original_code: str, modified_code: str,
                   error_trace: str, iteration: int, success: bool) -> None:
    """
    Log a correction attempt to the memory file.

    Args:
        file_path: Path to the file that was modified
        original_code: Original code before modification
        modified_code: Modified code after correction
        error_trace: Error traceback that triggered the correction
        iteration: Iteration number in the correction loop
        success: Whether the correction was successful
    """
    memory_file = CONFIG.get("memory_file", "memory.json")

    # Create an entry for this correction
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file": file_path,
        "iteration": iteration,
        "success": success,
        "error_trace": error_trace,
        "original_code": original_code,
        "modified_code": modified_code,
        "diff": generate_diff(original_code, modified_code)
    }

    # Load existing memory if it exists
    try:
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory = json.load(f)
        else:
            memory = []
    except json.JSONDecodeError:
        # If the file is corrupted, start fresh
        memory = []

    # Append the new entry
    memory.append(entry)

    # Write back to the memory file
    with open(memory_file, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=2)


def generate_diff(original: str, modified: str) -> List[Dict[str, Union[str, int]]]:
    """
    Generate a structured diff between original and modified code.

    Args:
        original: Original code string
        modified: Modified code string

    Returns:
        List of dict with changes, each with:
            - type: 'added', 'removed', or 'unchanged'
            - line: the line content
            - line_num: original line number
    """
    import difflib

    diff = difflib.unified_diff(
        original.splitlines(),
        modified.splitlines(),
        lineterm='',
        n=3  # Context lines
    )

    # Skip the first two lines (diff headers)
    next(diff, None)
    next(diff, None)

    result = []
    line_num = 0

    for line in diff:
        if line.startswith('@@'):
            # Extract line number information
            line_info = re.search(r'\-(\d+),(\d+) \+(\d+),(\d+)', line)
            if line_info:
                line_num = int(line_info.group(1)) - 1
            continue

        if line.startswith('+'):
            result.append({
                "type": "added",
                "line": line[1:],
                "line_num": None  # Added lines don't have original line numbers
            })
        elif line.startswith('-'):
            line_num += 1
            result.append({
                "type": "removed",
                "line": line[1:],
                "line_num": line_num
            })
        else:
            line_num += 1
            result.append({
                "type": "unchanged",
                "line": line[1:] if line.startswith(' ') else line,
                "line_num": line_num
            })

    return result


def find_relevant_files(error_trace: str, project_path: str) -> List[Dict[str, Union[str, int]]]:
    """
    Find all files relevant to an error for multi-file fixes.

    Args:
        error_trace: Error traceback string
        project_path: Root path of the project

    Returns:
        List of dict with file information, each with:
            - path: absolute path to the file
            - relevance: relevance score (higher = more likely to be the source)
            - line_num: line number mentioned in the error trace (if any)
    """
    if not error_trace:
        return []

    # Find all files mentioned in the traceback
    file_mentions = re.findall(r'File "([^"]+)", line (\d+)', error_trace)

    # Build a list of relevant files with relevance scores
    relevant_files = []
    mentioned_files = set()

    for file_path, line_num in file_mentions:
        # Skip if not in project path or if it's in a typical exclusion area
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            continue

        if any(skip_pattern in file_path for skip_pattern in
               ['__pycache__', 'site-packages', 'venv', '.git']):
            continue

        # Calculate relevance score - files mentioned later in the traceback
        # are usually more relevant
        relevance = len(file_mentions) - len(mentioned_files)

        # If file contains test_ or is under tests/ directory, reduce relevance
        if 'test_' in file_path or '/tests/' in file_path:
            relevance -= 5

        # Check if the file is mentioned in an assertion error line
        assertion_lines = re.findall(r'AssertionError.*?File "([^"]+)"', error_trace, re.DOTALL)
        if file_path in ''.join(assertion_lines):
            relevance += 10

        # Only consider each file once
        if file_path in mentioned_files:
            continue

        mentioned_files.add(file_path)

        relevant_files.append({
            "path": os.path.abspath(file_path),
            "relevance": relevance,
            "line_num": int(line_num)
        })

    # Sort by relevance (highest first)
    relevant_files.sort(key=lambda x: x['relevance'], reverse=True)

    return relevant_files
