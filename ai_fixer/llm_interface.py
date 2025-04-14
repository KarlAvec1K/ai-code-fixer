# ai_fixer/llm_interface.py

import subprocess
import re
import os
import json
from typing import Dict, List
from ai_fixer.config import CONFIG
from ai_fixer.model_selector import select_model
from ai_fixer.parallel_utils import run_models_in_parallel

def clean_llm_output(raw_output: str) -> str:
    if "```" in raw_output:
        matches = re.findall(r"```(?:python)?\\s*(.*?)```", raw_output, re.DOTALL)
        return matches[0].strip() if matches else raw_output.strip()
    return raw_output.strip()


def extract_file_content(raw_output: str, file_marker: str) -> str:
    """
    Extract content for a specific file from a multi-file LLM response.

    Args:
        raw_output: Raw LLM output
        file_marker: File marker to look for (typically the filename)

    Returns:
        The extracted content for the specific file
    """
    pattern = rf"```(?:python)?\s*(?:#\s*{re.escape(file_marker)}.*?\n)(.*?)```"
    matches = re.findall(pattern, raw_output, re.DOTALL)

    if matches:
        return matches[0].strip()

    # Try a more generic extraction pattern
    sections = re.split(r'#{1,3}\s+(?:File:)?\s*([^\n]+)', raw_output)
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            if file_marker in sections[i]:
                content = sections[i + 1].strip()
                # Remove any markdown code blocks
                content = re.sub(r'```(?:python)?(.*?)```', r'\1', content, flags=re.DOTALL)
                return content.strip()

    return ""


def load_test_code() -> str:
    test_path = os.path.join(CONFIG["project_path"], "tests", "test_main.py")
    if not os.path.exists(test_path):
        return ""
    with open(test_path, "r", encoding="utf-8") as f:
        return f.read()


def run_ollama(model: str, prompt: str, use_gpu=True) -> str:
    env = {**os.environ, "OLLAMA_CUBLAS": "1" if use_gpu else "0"}
    try:
        print(f"⚙️ Running model [{model}] with GPU={'ON' if use_gpu else 'OFF'}")
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout from model [{model}] (GPU={'ON' if use_gpu else 'OFF'})")
        return ""
    except Exception as e:
        print(f"❌ Error using model [{model}] (GPU={'ON' if use_gpu else 'OFF'}): {e}")
        return ""


def generate_fix(error_log: str, file_content: str, filename: str, attempt: int = 0) -> str:
    test_code = load_test_code()
    model = select_model(filename, file_content, error_log, attempt)

    prompt = f"""You are an expert code assistant.

Fix the following file so that the tests pass.

Filename: {filename}
Current content:
{file_content}

Test file:
{test_code}

Test errors:
{error_log}

Please return ONLY the corrected code, without explanation, comments or markdown.
"""

    raw_output = run_ollama(model, prompt, use_gpu=True)

    if not raw_output.strip():
        print("🔁 Retrying with CPU fallback...")
        raw_output = run_ollama(model, prompt, use_gpu=False)

    output = clean_llm_output(raw_output)
    print(f"🧾 Cleaned LLM output from [{model}] (length: {len(output)})")
    return output


def generate_multi_file_fix(
        error_log: str,
        file_contents: Dict[str, str],
        relevant_files: List[Dict],
        attempt: int = 0
) -> Dict[str, str]:
    """
    Generate fixes for multiple related files.

    Args:
        error_log: Error log from test execution
        file_contents: Dict mapping file paths to their contents
        relevant_files: List of relevant file info dicts with path and relevance
        attempt: Current attempt number

    Returns:
        Dict mapping file paths to their fixed contents
    """
    test_code = load_test_code()
    model = select_model("multiple_files", "", error_log, attempt)

    # Build file content section
    files_section = ""
    for file_info in relevant_files:
        file_path = file_info["path"]
        files_section += f"=== File: {file_path} ===\n"
        files_section += file_contents[file_path] + "\n\n"

    # Build prompt
    prompt = f"""You are an expert code assistant that fixes bugs across multiple files.

The following files are involved in a bug:

{files_section}

Test errors:
{error_log}

Test file:
{test_code}

Analyze the bug and fix it by modifying one or more of the files above.
For each file that needs to be changed, output its FULL corrected content.
Use the format:

### File: <filepath>
```python
# Fixed content here
```

Only include files that need to be modified.
"""

    raw_output = run_ollama(model, prompt, use_gpu=True)

    if not raw_output.strip():
        print("🔁 Retrying multi-file fix with CPU fallback...")
        raw_output = run_ollama(model, prompt, use_gpu=False)

    # Extract fixes for each file
    result = {}
    for file_path in file_contents.keys():
        file_basename = os.path.basename(file_path)
        extracted_content = extract_file_content(raw_output, file_path)

        if not extracted_content:
            # Try with just the filename
            extracted_content = extract_file_content(raw_output, file_basename)

        if extracted_content:
            result[file_path] = extracted_content

    print(f"🧾 Multi-file fix generated from [{model}] for {len(result)} files")
    return result
