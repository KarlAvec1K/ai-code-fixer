# ai_fixer/agent.py

import os
import json
import time
from typing import List, Dict, Optional

from ai_fixer.llm_interface import generate_fix, generate_multi_file_fix
from ai_fixer.utils import (
    find_failing_file, run_tests, read_file, write_file,
    find_relevant_files, log_correction
)
from ai_fixer.config import CONFIG


def run_correction_loop(dry_run=False):
    print("🚀 Starting AI agent\n")
    iteration = 1

    while iteration <= CONFIG["max_iterations"]:
        print(f"🔁 Iteration {iteration}...")

        test_result = run_tests()
        if test_result["success"]:
            print("✅ All tests passed.")
            return True

        # First try to find multiple relevant files
        relevant_files = find_relevant_files(test_result["traceback"], CONFIG["project_path"])

        if relevant_files:
            success = handle_multi_file_fix(relevant_files, test_result, iteration, dry_run)
        else:
            # Fallback to single file approach
            file_path = find_failing_file(test_result["traceback"], CONFIG["project_path"])
            if not file_path:
                print("⚠️ No file found in traceback. Trying fallback using function names...")
                file_path = find_failing_file(test_result["traceback"], CONFIG["project_path"], fallback=True)

            if not file_path:
                print("🚫 No valid target file identified.")
                iteration += 1
                continue

            success = handle_single_file_fix(file_path, test_result, iteration, dry_run)

        # If no changes were made in this iteration, we should still increment
        iteration += 1

    print(f"⚠️ Reached maximum iterations ({CONFIG['max_iterations']})")
    return False


def handle_single_file_fix(file_path: str, test_result: Dict, iteration: int, dry_run: bool) -> bool:
    """
    Handle fixing a single file.

    Args:
        file_path: Path to the file to fix
        test_result: Test result dictionary with traceback
        iteration: Current iteration number
        dry_run: Whether to actually apply changes

    Returns:
        bool: True if changes were made, False otherwise
    """
    current_code = read_file(file_path)
    suggestion = generate_fix(test_result["traceback"], current_code, file_path, attempt=iteration)

    if suggestion.strip() == current_code.strip() or not suggestion.strip():
        print("⚠️ Suggestion identical to current code or empty.")
        return False

    if dry_run:
        print("💡 Suggested change (dry-run, not applied):")
        print(suggestion)
        return True

    # Write new code
    write_file(file_path, suggestion)
    print(f"✅ File updated: {file_path}")

    # Log the correction
    log_correction(
        file_path=file_path,
        original_code=current_code,
        modified_code=suggestion,
        error_trace=test_result["traceback"],
        iteration=iteration,
        success=True
    )

    return True


def handle_multi_file_fix(
        relevant_files: List[Dict],
        test_result: Dict,
        iteration: int,
        dry_run: bool
) -> bool:
    """
    Handle fixing multiple files that might be related to the error.

    Args:
        relevant_files: List of relevant files with paths and relevance scores
        test_result: Test result dictionary with traceback
        iteration: Current iteration number
        dry_run: Whether to actually apply changes

    Returns:
        bool: True if changes were made, False otherwise
    """
    print(f"🔍 Found {len(relevant_files)} relevant files for this error")

    # Prepare context from all relevant files
    file_contents = {}
    for file_info in relevant_files:
        file_path = file_info["path"]
        file_contents[file_path] = read_file(file_path)
        print(f"  - {file_path} (relevance: {file_info['relevance']})")

    # For complex fixes, we'll try the multi-file approach first
    if len(relevant_files) > 1:
        file_fixes = generate_multi_file_fix(
            test_result["traceback"],
            file_contents,
            relevant_files,
            attempt=iteration
        )

        if file_fixes and any(file_fixes.values()):
            changes_made = False
            for file_path, new_content in file_fixes.items():
                if not new_content or new_content.strip() == file_contents[file_path].strip():
                    continue

                if dry_run:
                    print(f"💡 Suggested change for {file_path} (dry-run, not applied):")
                    print(new_content)
                else:
                    # Apply the fix
                    write_file(file_path, new_content)
                    print(f"✅ File updated: {file_path}")

                    # Log the correction
                    log_correction(
                        file_path=file_path,
                        original_code=file_contents[file_path],
                        modified_code=new_content,
                        error_trace=test_result["traceback"],
                        iteration=iteration,
                        success=True
                    )

                changes_made = True

            return changes_made

    # Fallback to trying to fix just the most relevant file
    most_relevant_file = relevant_files[0]["path"]
    return handle_single_file_fix(most_relevant_file, test_result, iteration, dry_run)


def run_single_pass(project_path: Optional[str] = None):
    """
    Run a single pass of the AI fixer without looping.
    Useful for debugging or one-off fixes.

    Args:
        project_path: Optional path to project. Uses CONFIG if not provided.
    """
    if project_path:
        original_path = CONFIG["project_path"]
        CONFIG["project_path"] = project_path

    test_result = run_tests()

    if test_result["success"]:
        print("✅ All tests already pass.")
        return

    relevant_files = find_relevant_files(test_result["traceback"], CONFIG["project_path"])

    if not relevant_files:
        print("⚠️ No relevant files found for this error.")
        return

    print(f"🔍 Found {len(relevant_files)} relevant files:")
    for file_info in relevant_files:
        print(f"  - {file_info['path']} (relevance: {file_info['relevance']})")

    # Reset CONFIG if we changed it
    if project_path:
        CONFIG["project_path"] = original_path
