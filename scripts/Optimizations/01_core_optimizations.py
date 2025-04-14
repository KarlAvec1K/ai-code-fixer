#!/usr/bin/env python3
"""
Script 1: Core Optimizations for AI Code Fixer
- Improves error handling
- Enhances file path handling
- Implements response validation and caching
- Adds better logging system
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
import tempfile
import hashlib
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_fixer_optimization.log')
    ]
)
logger = logging.getLogger("ai-fixer-optimizer")

# Paths
BASE_DIR = Path(__file__).parent.parent.absolute()
AI_FIXER_DIR = BASE_DIR / "ai_fixer"
CACHE_DIR = BASE_DIR / "cache"
BACKUP_DIR = BASE_DIR / "backups" / "script1_backup"


def backup_current_code():
    """Create a backup of the current code state"""
    logger.info("Creating backup of current code...")
    try:
        if BACKUP_DIR.exists():
            # Create temporary backup before removal
            temp_backup = Path(tempfile.mkdtemp()) / "temp_backup"
            shutil.copytree(BACKUP_DIR, temp_backup)
            try:
                shutil.rmtree(BACKUP_DIR)
            except Exception as e:
                # Restore from temp if removal fails
                if temp_backup.exists():
                    shutil.copytree(temp_backup, BACKUP_DIR)
                logger.error(f"Error removing old backup: {e}")
                return False

        # Create new backup
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(AI_FIXER_DIR, BACKUP_DIR, dirs_exist_ok=True)
        logger.info(f"Created backup at {BACKUP_DIR}")
        return True

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False
def setup_cache_system():
    """Set up LLM response caching system"""
    logger.info("Setting up LLM response caching system...")

    try:
        cache_dir = CACHE_DIR / "llm_responses"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Add cache statistics tracking
        stats_file = cache_dir / "cache_stats.json"
        if not stats_file.exists():
            stats = {
                "hits": 0,
                "misses": 0,
                "size": 0,
                "last_cleanup": None
            }
            stats_file.write_text(json.dumps(stats))

        # Create cache helper module with enhanced features
        cache_module = """# ai_fixer/cache_manager.py
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock
CACHE_DIR = Path(__file__).parent.parent / "cache" / "llm_responses"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
# Thread-safe cache access
cache_lock = Lock()
stats_lock = Lock()
def generate_cache_key(prompt: str, model: str) -> str:
    """Generate a unique cache key for a prompt and model"""
    combined = f"{model}:{prompt}"
    return hashlib.md5(combined.encode()).hexdigest()
def get_cached_response(prompt: str, model: str) -> Optional[str]:
    """Retrieve a cached LLM response if available"""
    cache_key = generate_cache_key(prompt, model)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    with cache_lock:
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # Check cache expiry
                if time.time() - cache_data.get("timestamp", 0) > 86400:  # 24h expiry
                    return None

                # Update cache stats
                update_cache_stats("hits")
def cache_response(prompt: str, model: str, response: str) -> None:
    """Cache an LLM response with metadata"""
    if not response or not prompt:
        return
    cache_key = generate_cache_key(prompt, model)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    cache_data = {
        "response": response,
        "timestamp": time.time(),
        "model": model,
        "prompt_hash": hashlib.md5(prompt.encode()).hexdigest()
    }

    with cache_lock:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        update_cache_stats("size", len(response))
def cache_response(prompt: str, model: str, response: str) -> None:
    """Cache an LLM response with metadata"""
    if not response or not prompt:
        return

    cache_key = generate_cache_key(prompt, model)
    cache_file = CACHE_DIR / f"{cache_key}.json"

def enhance_error_handling():
    """Enhance error handling in llm_interface.py"""
    logger.info("Enhancing error handling in llm_interface.py...")

    try:
        llm_interface_path = AI_FIXER_DIR / "llm_interface.py"
        if not llm_interface_path.exists():
            logger.error(f"File not found: {llm_interface_path}")
            return False

        with open(llm_interface_path, "r") as f:
            content = f.read()

        # Add enhanced imports
        imports_to_add = """import time
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Union
from functools import wraps
from ai_fixer.cache_manager import get_cached_response, cache_response
"""
        # Add retry decorator
        retry_decorator = """
def retry_with_exponential_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        delay = base_delay * (2 ** (attempt - 1))
                        print(f"🔄 Retry {attempt}/{max_retries} after {delay}s delay")
                        await asyncio.sleep(delay)

                    return await func(*args, **kwargs)

                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            return None
        return wrapper
    return decorator
"""
        # Enhanced run_ollama function
        enhanced_run_ollama = """async def run_ollama(model: str, prompt: str, use_gpu=True, max_retries=3, retry_delay=2) -> Tuple[str, bool]:
    """Run the Ollama model with retries and error handling"""
    env = {**os.environ, "OLLAMA_CUBLAS": "1" if use_gpu else "0"}
    
    # Check cache first
    cached_response = get_cached_response(prompt, model)
    if cached_response:
        print(f"📄 Using cached response for model [{model}]")
        return cached_response, True

    @retry_with_exponential_backoff(max_retries=max_retries, base_delay=retry_delay)
    async def _run_model():
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: subprocess.run(
                    ["ollama", "run", model, prompt],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env=env
                )
            )
            
            if result.stderr and "error" in result.stderr.lower():
                print(f"⚠️ Warning from model [{model}]: {result.stderr}")
                
            if not result.stdout.strip():
                print(f"❗ Empty response from model [{model}]")
                raise ValueError("Empty model response")
                
            return result.stdout

    try:
        response = await _run_model()

        # Cache successful response
        if response:
            cache_response(prompt, model, response)

        return response, True

    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout from model [{model}] (GPU={'ON' if use_gpu else 'OFF'})")
    except subprocess.SubprocessError as e:
        print(f"❌ Subprocess error with model [{model}]: {e}")
    except Exception as e:
        print(f"❌ Unexpected error using model [{model}]: {e}")

    return "", False
"""
        # Add validation function
        validation_function = """def is_valid_python(code: str) -> bool:
    """Check if the provided code is valid Python syntax"""
    if not code.strip():
        return False

    try:
        import ast
        ast.parse(code)
        return True
    except SyntaxError:
        return False
    except Exception:
        return False
"""
        # Combine all changes
        updated_content = content
        
        # Add imports if not present
        if "from typing import Dict, List" not in content:
            updated_content = imports_to_add + updated_content
            
        # Add retry decorator
        if "def retry_with_exponential_backoff" not in updated_content:
            function_position = updated_content.find("def run_ollama")
            if function_position != -1:
                updated_content = (
                    updated_content[:function_position] +
                    retry_decorator +
                    "\n" +
                    updated_content[function_position:]
                )
                
        # Add validation function
        if "def is_valid_python" not in updated_content:
            function_position = updated_content.find("def clean_llm_output")
            if function_position != -1:
                updated_content = (
                    updated_content[:function_position] +
                    validation_function +
                    "\n" +
                    updated_content[function_position:]
                )
                
enhanced_generate_fix = """async def generate_fix(prompt: str, model: str = None) -> str:
    """Generate a fix using the specified LLM model"""
    if not model:
        model = CONFIG.get("llm_model", "codellama:13b-instruct")

    raw_output, success = await run_ollama(model, prompt, use_gpu=True)

    if not success or not raw_output.strip():
        print("⚠️ All attempts failed, trying fallback model...")
        fallback_model = "codellama:13b-instruct" if model != "codellama:13b-instruct" else "deepseek-coder"
        raw_output, _ = await run_ollama(fallback_model, prompt, use_gpu=True)
    output = clean_llm_output(raw_output)

    # Validate output
    if is_valid_python(output):
        print(f"✅ Generated valid Python code from [{model}] (length: {len(output)})")
    else:
        print(f"⚠️ Generated potentially invalid Python code from [{model}]")
        
    return output
"""
    except Exception as e:
        logger.error(f"Failed to enhance error handling: {e}")
        return False
        if not success or not raw_output.strip():
            print("⚠️ All attempts failed, trying fallback model...")
            fallback_model = "codellama:13b-instruct" if model != "codellama:13b-instruct" else "deepseek-coder"
            raw_output, _ = run_ollama(fallback_model, prompt, use_gpu=True)

    output = clean_llm_output(raw_output)
    
    # Validate output
    if is_valid_python(output):
        print(f"✅ Generated valid Python code from [{model}] (length: {len(output)})")
    else:
        print(f"⚠️ Generated potentially invalid Python code from [{model}]")
        
    return output
"""

    # Add validation function
    validation_function = """def is_valid_python(code: str) -> bool:
    """
    Check if the
    provided
    code is valid
    Python
    syntax
    """
    if not code.strip():
        return False
        
    try:
        # Try to parse the code using ast
        import ast
        ast.parse(code)
        return True
    except SyntaxError:
        return False
    except Exception:
        return False
"""

    # Update multi_file_fix to use enhanced error handling
    updated_multi_file = content.replace(
        "    raw_output = run_ollama(model, prompt, use_gpu=True)",
        "    raw_output, success = run_ollama(model, prompt, use_gpu=True)"
    ).replace(
        "    if not raw_output.strip():",
        "    if not success or not raw_output.strip():"
    ).replace(
        "        output = run_ollama(model, prompt, use_gpu=False)",
        "        raw_output, _ = run_ollama(model, prompt, use_gpu=False)"
    )

    # Combine changes
    updated_content = content

    # Add imports
    if "from typing import Dict, List" not in content:
        updated_content = imports_to_add + updated_content

    # Add validation function
    if "def is_valid_python" not in updated_content:
        function_position = updated_content.find("def clean_llm_output")
        if function_position != -1:
            updated_content = (
                    updated_content[:function_position] +
                    validation_function +
                    "\n" +
                    updated_content[function_position:]
            )

    # Replace run_ollama function
    if "def run_ollama" in updated_content:
        start_idx = updated_content.find("def run_ollama")
        end_idx = updated_content.find("def ", start_idx + 1)
        if end_idx == -1:
            end_idx = len(updated_content)
        updated_content = updated_content[:start_idx] + enhanced_run_ollama + updated_content[end_idx:]

    # Replace generate_fix function
    if "def generate_fix" in updated_content:
        start_idx = updated_content.find("def generate_fix")
        end_idx = updated_content.find("def ", start_idx + 1)
        if end_idx == -1:
            end_idx = len(updated_content)
        updated_content = updated_content[:start_idx] + enhanced_generate_fix + updated_content[end_idx:]

    # Write updated content
    with open(llm_interface_path, "w") as f:
        f.write(updated_content)

    logger.info("Enhanced error handling in llm_interface.py")


def improve_path_handling():
    """Improve path handling in utils.py using pathlib"""
    logger.info("Improving path handling in utils.py...")

    utils_path = AI_FIXER_DIR / "utils.py"
    if not utils_path.exists():
        logger.error(f"File not found: {utils_path}")
        return

    with open(utils_path, "r") as f:
        content = f.read()

    # Add pathlib import
    if "from pathlib import Path" not in content:
        content = content.replace(
            "import os",
            "import os\nfrom pathlib import Path"
        )

    # Update read_file and write_file to use pathlib
    updated_read_file = """def read_file(file_path: str) -> str:
    """
    Read
    the
    content
    of
    a
    file
    with proper error handling"""
    path = Path(file_path)
    try:
        with path.open("r", encoding="utf-8") as f:
            return f.read()
    except (IOError, UnicodeDecodeError) as e:
        print(f"⚠️ Error reading file {file_path}: {e}")
        try:
            # Fallback to latin-1 encoding
            with path.open("r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read file {file_path}: {e}")
            return ""
"""

    updated_write_file = """def write_file(file_path: str, content: str) -> bool:
    """
    Write
    content
    to
    a
    file
    with proper error handling"""
    path = Path(file_path)
    try:
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup before writing
        backup_path = path.with_suffix(f"{path.suffix}.bak")
        if path.exists():
            shutil.copy2(path, backup_path)
        
        with path.open("w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"❌ Error writing to file {file_path}: {e}")
        # Restore from backup if available
        if backup_path.exists():
            shutil.copy2(backup_path, path)
            print(f"✅ Restored {file_path} from backup")
        return False
"""

    # Replace functions
    if "def read_file" in content:
        start_idx = content.find("def read_file")
        end_idx = content.find("def ", start_idx + 1)
        content = content[:start_idx] + updated_read_file + content[end_idx:]

    if "def write_file" in content:
        start_idx = content.find("def write_file")
        end_idx = content.find("def ", start_idx + 1)
        content = content[:start_idx] + updated_write_file + content[end_idx:]

    # Update find_failing_file to use pathlib
    content = content.replace(
        "os.path.join(",
        "Path("
    ).replace(
        "os.path.exists(",
        "Path("
    ).replace(
        "os.path.abspath(",
        "Path("
    ).replace(
        "os.path.dirname(",
        "Path("
    ).replace(
        ").exists()",
        ").exists()"
    )

    with open(utils_path, "w") as f:
        f.write(content)

    logger.info("Improved path handling in utils.py")


def enhance_agent_robustness():
    """Enhance agent.py to be more robust"""
    logger.info("Enhancing agent.py robustness...")

    agent_path = AI_FIXER_DIR / "agent.py"
    if not agent_path.exists():
        logger.error(f"File not found: {agent_path}")
        return

    with open(agent_path, "r") as f:
        content = f.read()

    # Add timeout and circuit breaker
    enhanced_imports = """import os
import json
import time
import logging
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path

from ai_fixer.llm_interface import generate_fix, generate_multi_file_fix
from ai_fixer.utils import find_failing_file, run_tests, read_file, write_file, find_relevant_files, log_correction
from ai_fixer.config import CONFIG

# Setup logging
logger = logging.getLogger("ai-fixer-agent")
"""

    # Add helper functions for timeout and circuit breaker
    helper_functions = """def detect_loop(history: List[str], max_similar=3) -> bool:
    """
    Detect if we
    're in a loop of similar fixes"""
    if len(history) < max_similar * 2:
        return False

    # Check last few fixes
    latest_fixes = history[-max_similar:]

    # Check if we're seeing similar errors repeatedly
    similarity_count = 0
    for i in range(len(latest_fixes)):
        for j in range(i + 1, len(latest_fixes)):
            if are_similar_fixes(latest_fixes[i], latest_fixes[j]):
                similarity_count += 1

    return similarity_count >= (max_similar // 2)


def are_similar_fixes(fix1: str, fix2: str) -> bool:
    """Check if two fixes are very similar"""
    import difflib

    # Calculate similarity ratio
    similarity = difflib.SequenceMatcher(None, fix1, fix2).ratio()
    return similarity > 0.9  # 90% similarity threshold


"""
    
    # Update run_correction_loop
    enhanced_run_loop = """


def run_correction_loop(dry_run=False):
    """Run the main AI fixer loop with enhanced robustness"""
    print("🚀 Starting AI agent\\n")
    iteration = 1

    # Keep track of file modifications to detect loops
    fix_history = []

    # Set of errors we've seen to detect recurring issues
    seen_errors = set()

    while iteration <= CONFIG["max_iterations"]:
        print(f"🔁 Iteration {iteration}/{CONFIG['max_iterations']}...")

        try:
            test_result = run_tests()

            if test_result["success"]:
                print("✅ All tests passed.")
                return True

            # Check if we've seen this exact error before
            error_hash = hash(test_result["traceback"])
            if error_hash in seen_errors and iteration > 2:
                print("⚠️ Detected recurring error pattern. Trying different approach...")
                # Force use of a different model in the next attempt
                os.environ["AI_FIXER_FORCE_MODEL_CHANGE"] = "1"
            else:
                seen_errors.add(error_hash)

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

            # Check for loop detection
            if len(fix_history) > 3:
                if detect_loop(fix_history):
                    print("🔄 Detected potential fix loop. Trying different approach...")
                    # Force model change
                    os.environ["AI_FIXER_FORCE_MODEL_CHANGE"] = "1"

            # If no changes were made in this iteration, we should still increment
            iteration += 1

        except KeyboardInterrupt:
            print("\\n👋 Process interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Unexpected error in correction loop: {e}")
            # Continue to next iteration
            iteration += 1
            time.sleep(1)  # Brief pause after error

    print(f"⚠️ Reached maximum iterations ({CONFIG['max_iterations']})")
    return False


"""
    
    # Replace imports
    if "import os" in content:
        end_imports = content.find("from ai_fixer")
        if end_imports == -1:
            end_imports = content.find("def ")
        content = enhanced_imports + content[end_imports:]
    
    # Add helper functions
    if "def detect_loop" not in content:
        function_pos = content.find("def run_correction_loop")
        content = content[:function_pos] + helper_functions + "\n" + content[function_pos:]
    
    # Replace run_correction_loop
    if "def run_correction_loop" in content:
        start_idx = content.find("def run_correction_loop")
        next_def = content.find("def ", start_idx + 1)
        content = content[:start_idx] + enhanced_run_loop + content[next_def:]
    
    with open(agent_path, "w") as f:
        f.write(content)
    
    logger.info("Enhanced agent.py robustness")

def update_config():
    """
Update
config.py
with additional options"""
    logger.info("Updating config.py with additional options...")
    
    config_path = AI_FIXER_DIR / "config.py"
    if not config_path.exists():
        logger.error(f"File not found: {config_path}")
        return
    
    with open(config_path, "r") as f:
        content = f.read()
    
    # Enhanced config
    enhanced_config = """ import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()

CONFIG = {
    # Core settings
    "project_path": BASE_DIR / "test_projects" / "exemple_repo",
    "llm_model": "codellama:13b-instruct",
    "max_iterations": 10,

    # Version control settings
    "auto_commit": False,
    "branch_prefix": "ai-fix/",

    # Logging and memory
    "log_file": BASE_DIR / "logs" / "ai_fixer.log",
    "memory_file": BASE_DIR / "memory.json",

    # Language and testing
    "language": "python",
    "test_command": "pytest",

    # Performance settings
    "use_gpu": True,
    "max_concurrent_requests": 1,

    # Advanced settings
    "cache_responses": True,
    "cache_dir": BASE_DIR / "cache",
    "timeout": 120,
    "retry_attempts": 3,
}

# Create necessary directories
for path in [CONFIG["log_file"].parent, CONFIG["cache_dir"]]:
    path.mkdir(parents=True, exist_ok=True)
"""
    
    with open(config_path, "w") as f:
        f.write(enhanced_config)
    
    logger.info("Updated config.py with additional options")

def main():
    """
Main
function
to
run
all
optimizations
"""
    logger.info("Starting core optimizations for AI Code Fixer...")
    
    # Create backup
    backup_current_code()
    
    # Setup cache system
    setup_cache_system()
    
    # Enhance error handling
    enhance_error_handling()
    
    # Improve path handling
    improve_path_handling()
    
    # Enhance agent robustness
    enhance_agent_robustness()
    
    # Update config
    update_config()
    
    logger.info("Core optimizations completed successfully!")
    logger.info("You can now proceed to script 2 for enhanced features and performance improvements.")

if __name__ == "__main__":
    main()