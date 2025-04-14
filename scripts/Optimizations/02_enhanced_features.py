#!/usr/bin/env python3
"""
Script 2: Enhanced Features for AI Code Fixer
- Implements parallel processing
- Adds smarter test selection
- Enhances telemetry and metrics
- Improves model selection
- Implements context optimization
"""

import os
import sys
import json
import shutil
import logging
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_fixer_enhancement.log')
    ]
)
logger = logging.getLogger("ai-fixer-enhancer")

# Paths
BASE_DIR = Path(__file__).parent.parent.absolute()
AI_FIXER_DIR = BASE_DIR / "ai_fixer"
BACKUP_DIR = BASE_DIR / "backups" / "script2_backup"

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

        # Create new backup directory
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Copy all Python files from AI_FIXER_DIR
        for file in AI_FIXER_DIR.glob("**/*.py"):
            relative_path = file.relative_to(AI_FIXER_DIR)
            target_path = BACKUP_DIR / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(file, target_path)
            except Exception as e:
                logger.error(f"Error copying {file}: {e}")
                continue

        logger.info(f"Backup created at {BACKUP_DIR}")
        return True

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False

def implement_parallel_processing():
    """Implement parallel processing for test runs and LLM calls"""
    logger.info("Implementing parallel processing...")
    
    # Create new parallel_utils.py module
    parallel_utils = """# ai_fixer/parallel_utils.py

import time
import logging
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Callable, Tuple, Coroutine
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial

from ai_fixer.config import CONFIG

logger = logging.getLogger("ai-fixer-parallel")

# Global executor for thread pooling
thread_executor = ThreadPoolExecutor(max_workers=CONFIG.get("max_concurrent_requests", 3))
process_executor = ProcessPoolExecutor(max_workers=2)

async def run_async(func, *args, **kwargs):
    """Run a synchronous function asynchronously in a thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_executor, partial(func, *args, **kwargs))

async def run_models_in_parallel(prompt: str, models: List[str], use_gpu=True) -> Dict[str, str]:
    """Run multiple LLM models in parallel and return their outputs"""
    from ai_fixer.llm_interface import run_ollama
    
    async def _run_model(model: str) -> Tuple[str, str]:
        try:
            # Add timeout handling
            async with asyncio.timeout(120):  # 2 minute timeout
                output, success = await run_async(run_ollama, model, prompt, use_gpu)
                if not success and use_gpu:
                    # Fallback to CPU if GPU fails
                    output, success = await run_async(run_ollama, model, prompt, False)
                return model, output if success else ""
        except asyncio.TimeoutError:
            print(f"⚠️ Timeout running model {model}")
            return model, ""
        except Exception as e:
            print(f"❌ Error running model {model}: {e}")
            return model, ""
    
    # Run models in parallel with concurrency limit
    semaphore = asyncio.Semaphore(3)  # Limit concurrent executions
    
    async def _run_with_semaphore(model: str) -> Tuple[str, str]:
        async with semaphore:
            return await _run_model(model)
    
    tasks = [_run_with_semaphore(model) for model in models]
    results = await asyncio.gather(*tasks)
    
    # Filter out empty results and return as dict
    return {model: output for model, output in results if output}

def run_multiple_models(prompt: str, models: List[str], use_gpu=True) -> Dict[str, str]:
    """Synchronous wrapper for running multiple models in parallel"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run_models_in_parallel(prompt, models, use_gpu))
    except Exception as e:
        logger.error(f"Error in parallel model execution: {e}")
        # Fallback to sequential execution
        results = {}
        for model in models:
            from ai_fixer.llm_interface import run_ollama
            output, _ = run_ollama(model, prompt, use_gpu)
            results[model] = output
        return results

async def run_test_variants_async(test_variants: List[Dict]) -> List[Dict]:
    """Run multiple test variants asynchronously and return results"""
    from ai_fixer.utils import run_specific_test
    
    async def _run_test_variant(variant: Dict) -> Dict:
        result = await run_async(run_specific_test, 
                                variant.get("test_path"), 
                                variant.get("test_name"))
        return {**variant, "result": result}
    
    tasks = [_run_test_variant(variant) for variant in test_variants]
    return await asyncio.gather(*tasks)

def run_test_variants(test_variants: List[Dict]) -> List[Dict]:
    """Synchronous wrapper for running test variants in parallel"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run_test_variants_async(test_variants))
    except Exception as e:
        logger.error(f"Error in parallel test execution: {e}")
        # Fallback to sequential execution
        results = []
        from ai_fixer.utils import run_specific_test
        for variant in test_variants:
            result = run_specific_test(variant.get("test_path"), variant.get("test_name"))
            results.append({**variant, "result": result})
        return results
"""
    
    with open(AI_FIXER_DIR / "parallel_utils.py", "w") as f:
        f.write(parallel_utils)
    
    logger.info("Created parallel_utils.py")
    
    # Update utils.py to add run_specific_test function
    utils_path = AI_FIXER_DIR / "utils.py"
    with open(utils_path, "r") as f:
        utils_content = f.read()
    
    run_specific_test = """def run_specific_test(test_path=None, test_name=None):
    """Run a specific test file or test case"""
    from ai_fixer.config import CONFIG
    
    cmd = [CONFIG["test_command"]]
    
    if test_path:
        cmd.append(str(test_path))
        
    if test_name:
        cmd.append(f"-k {test_name}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=CONFIG["project_path"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "traceback": result.stdout if result.returncode != 0 else result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "traceback": "Test execution timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "traceback": f"Error running tests: {str(e)}"
        }
"""
    
    # Add run_specific_test to utils.py
    if "def run_specific_test" not in utils_content:
        # Add after run_tests function
        if "def run_tests" in utils_content:
            run_tests_pos = utils_content.find("def run_tests")
            next_def_pos = utils_content.find("def ", run_tests_pos + 1)
            if next_def_pos != -1:
                utils_content = utils_content[:next_def_pos] + run_specific_test + "\n\n" + utils_content[next_def_pos:]
            else:
                utils_content += "\n\n" + run_specific_test
                
        with open(utils_path, "w") as f:
            f.write(utils_content)
    
    logger.info("Updated utils.py with run_specific_test function")

def add_telemetry_metrics():
    """Add telemetry and metrics module"""
    logger.info("Adding telemetry and metrics module...")
    
    telemetry_module = """# ai_fixer/telemetry.py

import os
import json
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ai_fixer.config import CONFIG

logger = logging.getLogger("ai-fixer-telemetry")

class Telemetry:
    """Telemetry system for collecting metrics and statistics"""
    
    def __init__(self):
        self.metrics_file = CONFIG.get("metrics_file", Path(CONFIG["log_file"]).parent / "metrics.json")
        self.session_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.metrics = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "iterations": [],
            "models": {},
            "files": {},
            "errors": [],
            "test_runs": 0,
            "success": False
        }
    
    def load_metrics(self):
        """Load existing metrics if available"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r") as f:
                    data = json.load(f)
                    
                # Keep historical sessions but start a new one
                if "sessions" in data:
                    self.metrics["sessions"] = data["sessions"]
                else:
                    self.metrics["sessions"] = []
                    
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading metrics: {e}")
    
    def save_metrics(self):
        """Save current metrics"""
        # Calculate duration
        self.metrics["duration"] = time.time() - self.start_time
        
        # Create directory if needed
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        
        try:
            # Load existing data if any
            existing_data = {}
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, "r") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        pass
            
            # Add current session to historical sessions
            if "sessions" not in existing_data:
                existing_data["sessions"] = []
                
            # Add current session
            session_copy = dict(self.metrics)
            if "sessions" in session_copy:
                del session_copy["sessions"]
                
            existing_data["sessions"].append(session_copy)
            
            # Update the latest metrics
            existing_data["latest"] = session_copy
            
            # Calculate aggregate statistics
            existing_data["stats"] = self._calculate_aggregates(existing_data["sessions"])
            
            # Save everything
            with open(self.metrics_file, "w") as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _calculate_aggregates(self, sessions: List[Dict]) -> Dict:
        """Calculate aggregate statistics from all sessions"""
        if not sessions:
            return {}
            
        total_sessions = len(sessions)
        successful_sessions = sum(1 for s in sessions if s.get("success", False))
        total_iterations = sum(len(s.get("iterations", [])) for s in sessions)
        total_test_runs = sum(s.get("test_runs", 0) for s in sessions)
        
        # Model usage stats
        models = {}
        for session in sessions:
            for model, count in session.get("models", {}).items():
                if model not in models:
                    models[model] = 0
                models[model] += count
        
        # Calculate average iterations per fix
        avg_iterations = total_iterations / total_sessions if total_sessions > 0 else 0
        
        return {
            "success_rate": successful_sessions / total_sessions if total_sessions > 0 else 0,
            "total_sessions": total_sessions,
            "avg_iterations": avg_iterations,
            "total_test_runs": total_test_runs,
            "model_usage": models,
            "last_updated": datetime.now().isoformat()
        }
    
    def record_iteration(self, iteration: int, files: List[str], success: bool, error: Optional[str] = None):
        """Record data for a single iteration"""
        iteration_data = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "files": files,
            "success": success
        }
        
        if error:
            iteration_data["error"] = error
            self.metrics["errors"].append(error)
            
        self.metrics["iterations"].append(iteration_data)
        
        # Update file stats
        for file in files:
            if file not in self.metrics["files"]:
                self.metrics["files"][file] = 0
            self.metrics["files"][file] += 1
    
    def record_model_usage(self, model: str):
        """Record usage of a specific model"""
        if model not in self.metrics["models"]:
            self.metrics["models"][model] = 0
        self.metrics["models"][model] += 1
    
    def record_test_run(self):
        """Record a test run"""
        self.metrics["test_runs"] += 1
    
    def record_completion(self, success: bool):
        """Record completion of the fixing process"""
        self.metrics["success"] = success
        self.metrics["end_time"] = datetime.now().isoformat()
        self.save_metrics()
    
    def get_model_performance(self) -> Dict[str, float]:
        """Get performance metrics for each model"""
        # This would require additional tracking of which model fixed which file
        # For now, return just the usage counts
        return self.metrics["models"]
    
    def get_summary(self) -> Dict:
        """Get a summary of the current session"""
        duration = time.time() - self.start_time
        return {
            "session_id": self.session_id,
            "duration": duration,
            "iterations": len(self.metrics["iterations"]),
            "test_runs": self.metrics["test_runs"],
            "success": self.metrics["success"],
            "files_modified": len(self.metrics["files"]),
            "models_used": list(self.metrics["models"].keys())
        }

# Global telemetry instance
telemetry = Telemetry()
"""
    
    with open(AI_FIXER_DIR / "telemetry.py", "w") as f:
        f.write(telemetry_module)
    
    logger.info("Created telemetry.py module")
    
    # Update agent.py to use telemetry
    agent_path = AI_FIXER_DIR / "agent.py"
    with open(agent_path, "r") as f:
        agent_content = f.read()
    
    # Add telemetry import
    if "from ai_fixer.telemetry import telemetry" not in agent_content:
        imports_end = agent_content.find("from ai_fixer")
        imports_end = agent_content.find("\n", imports_end)
        agent_content = agent_content[:imports_end+1] + "from ai_fixer.telemetry import telemetry\n" + agent_content[imports_end+1:]
    
    # Add telemetry to run_correction_loop
    modified_agent = agent_content.replace(
        "def run_correction_loop(dry_run=False):",
        """def run_correction_loop(dry_run=False):
    """Run the main AI fixer loop with enhanced telemetry"""
    print("🚀 Starting AI agent\\n")
    telemetry.load_metrics()
    """
    ).replace(
        "print(f\"🔁 Iteration {iteration}/{CONFIG['max_iterations']}...\")",
        """print(f"🔁 Iteration {iteration}/{CONFIG['max_iterations']}...")
        telemetry.record_test_run()"""
    ).replace(
        "print(\"✅ All tests passed.\")",
        """print("✅ All tests passed.")
                telemetry.record_completion(True)"""
    ).replace(
        "print(f\"⚠️ Reached maximum iterations ({CONFIG['max_iterations']})\")",
        """print(f"⚠️ Reached maximum iterations ({CONFIG['max_iterations']})")
    telemetry.record_completion(False)"""
    )
    
    with open(agent_path, "w") as f:
        f.write(modified_agent)
    
    logger.info("Updated agent.py to use telemetry")

def improve_model_selection():
    """Improve model selection logic"""
    logger.info("Improving model selection logic...")
    
    # Create model_selector.py
    model_selector = """# ai_fixer/model_selector.py

import os
import json
import random
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

from ai_fixer.config import CONFIG
from ai_fixer.telemetry import telemetry

class ModelSelector:
    """Intelligent model selection based on file type, error patterns, and history"""
    
    def __init__(self):
        self.models = {
            "small": ["codellama:7b-instruct"],
            "medium": ["codellama:13b-instruct", "deepseek-coder:6.7b-instruct"],
            "large": ["codellama:34b-instruct", "deepseek-coder:33b-instruct"],
            "fallback": ["codellama:7b-instruct", "deepseek-coder:6.7b-instruct"]
        }
        
        # Track model performance for this session
        self.performance = {}
        
        # Track which models have been tried for specific errors
        self.error_model_mapping = {}
        
        # Load past performance data if available
        self.history_file = CONFIG.get("metrics_file", Path(CONFIG["log_file"]).parent / "metrics.json")
        self.load_performance_history()
    
    def load_performance_history(self):
        """Load historical performance data"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    if "stats" in data and "model_usage" in data["stats"]:
                        # Initialize performance with historical data
                        self.performance = {model: {"used": count, "success": 0} 
                                          for model, count in data["stats"]["model_usage"].items()}
            except (json.JSONDecodeError, IOError):
                pass
    
    def select_model(self, file_path: str, error_log: str, iteration: int) -> str:
        """Select the best model for the given file and error"""
        file_ext = Path(file_path).suffix.lower()
        
        # Force model change if environment variable is set
        force_change = os.environ.get("AI_FIXER_FORCE_MODEL_CHANGE", "0") == "1"
        if force_change:
            os.environ["AI_FIXER_FORCE_MODEL_CHANGE"] = "0"
            return self._select_alternative_model(file_path, error_log)
        
        # Early iterations: use smaller models
        if iteration < 2:
            model = random.choice(self.models["small"])
        # Middle iterations: use medium models 
        elif iteration < 5:
            model = random.choice(self.models["medium"])
        # Later iterations: use larger models
        else:
            model = random.choice(self.models["large"])
        
        # Record model usage
        telemetry.record_model_usage(model)
        
        # Generate an error signature
        error_sig = self._generate_error_signature(error_log)
        
        # Check if we've tried this model for this error before
        if error_sig in self.error_model_mapping and model in self.error_model_mapping[error_sig]:
            # Try a different model
            return self._select_alternative_model(file_path, error_log)
        
        # Record this model for this error
        if error_sig not in self.error_model_mapping:
            self.error_model_mapping[error_sig] = set()
        self.error_model_mapping[error_sig].add(model)
        
        return model
    
    def _select_alternative_model(self, file_path: str, error_log: str) -> str:
        """Select an alternative model that hasn't been tried"""
        # Get error signature
        error_sig = self._generate_error_signature(error_log)
        
        # Get all models
        all_models = []
        for model_list in self.models.values():
            all_models.extend(model_list)
        
        # Filter out models already tried for this error
        models_to_try = [m for m in all_models if error_sig not in self.error_model_mapping or 
                         m not in self.error_model_mapping[error_sig]]
        
        if not models_to_try:
            # If all models tried, use a random one
            model = random.choice(all_models)
        else:
            # Use one we haven't tried yet
            model = random.choice(models_to_try)
        
        # Record usage
        telemetry.record_model_usage(model)
        
        # Record this model for this error
        if error_sig not in self.error_model_mapping:
            self.error_model_mapping[error_sig] = set()
        self.error_model_mapping[error_sig].add(model)
        
        return model
    
    def _generate_error_signature(self, error_log: str) -> str:
        """Generate a signature for an error to identify similar errors"""
        import hashlib
        
        # Extract the most relevant parts of the error
        lines = error_log.strip().split('\\n')
        error_lines = []
        
        for line in lines:
            if "Error" in line or "Exception" in line or "AssertionError" in line:
                error_lines.append(line)
        
        # Join error lines or use the whole error if no specific errors found
        signature_text = "\\n".join(error_lines) if error_lines else error_log
        
        # Generate hash for the error signature
        return hashlib.md5(signature_text.encode()).hexdigest()
    
    def record_success(self, model: str, fixed: bool):
        """Record success/failure for a model"""
        if model not in self.performance:
            self.performance[model] = {"used": 0, "success": 0}
        
        self.performance[model]["used"] += 1
        if fixed:
            self.performance[model]["success"] += 1
    
    def get_best_models(self, limit: int = 3) -> List[str]:
        """Get the best performing models based on success rate"""
        # Calculate success rates
        models_with_rates = []
        for model, stats in self.performance.items():
            if stats["used"] > 0:
                success_rate = stats["success"] / stats["used"]
                models_with_rates.append((model, success_rate))
        
        # Sort by success rate descending
        models_with_rates.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N models
        return [model for model, _ in models_with_rates[:limit]]
    
    def select_models_for_parallel(self, file_path: str, error_log: str, iteration: int) -> List[str]:
        """Select multiple models for parallel execution"""
        # Get best models based on history
        best_models = self.get_best_models(2)
        
        # Ensure we have enough models
        if len(best_models) < 2:
            if iteration < 3:
                model_set = self.models["small"] + self.models["medium"]
            else:
                model_set = self.models["medium"] + self.models["large"]
                
            # Add some models that aren't in best_models
            additional = [m for m in model_set if m not in best_models]
            best_models.extend(additional[:2])
        
        # Ensure we use at most 3 models
        models_to_use = best_models[:3]
        
        # Record usage for telemetry
        for model in models_to_use:
            telemetry.record_model_usage(model)
        
        return models_to_use

# Global model selector instance
model_selector = ModelSelector()

def select_model(file_path: str, error_log: str, iteration: int) -> str:
    """Convenience function to select a model"""
    return model_selector.select_model(file_path, error_log, iteration)

def select_models_for_parallel(file_path: str, error_log: str, iteration: int) -> List[str]:
    """Convenience function to select models for parallel execution"""
    return model_selector.select_models_for_parallel(file_path, error_log, iteration)
"""
    
    with open(AI_FIXER_DIR / "model_selector.py", "w") as f:
        f.write(model_selector)
    
    logger.info("Created model_selector.py")
    
    # Update llm_interface.py to use model_selector
    llm_interface_path = AI_FIXER_DIR / "llm_interface.py"
    with open(llm_interface_path, "r") as f:
        llm_content = f.read()
    
    # Replace select_model function
    if "def select_model" in llm_content:
        start_idx = llm_content.find("def select_model")
        next_def = llm_content.find("def ", start_idx + 1)
        if next_def != -1:
            # Replace the function with an import
            select_model_import = """# Use the enhanced model selector
from ai_fixer.model_selector import select_model, select_models_for_parallel
"""
            llm_content = llm_content[:start_idx] + select_model_import + llm_content[next_def:]
            
            with open(llm_interface_path, "w") as f:
                f.write(llm_content)
    
    logger.info("Updated llm_interface.py to use model_selector")

def implement_context_optimization():
    """Implement source code context optimization for better prompts"""
    logger.info("Implementing context optimization...")
    
    # Create context_optimizer.py
    context_optimizer = """# ai_fixer/context_optimizer.py

import os
import re
import ast
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path

class ContextOptimizer:
    """Optimize code context for better LLM understanding"""
    
    def __init__(self):
        self.imports_cache = {}
        self.class_defs_cache = {}
    
    def optimize_context(self, file_content: str, error_log: str) -> str:
        """Optimize the code context for better LLM performance"""
        # If file is empty or too small, return as is
        if not file_content or len(file_content) < 500:
            return file_content
            
        try:
            # Parse the AST to get structure information
            tree = ast.parse(file_content)
            
            # Get essential elements like imports and class definitions
            imports = self._extract_imports(tree)
            classes = self._extract_classes(tree)
            functions = self._extract_functions(tree)
            
            # Find relevant parts based on error
            relevant_elements = self._find_relevant_elements(error_log, functions, classes)
            
            # Reconstruct optimized file content
            optimized = self._reconstruct_optimized_content(
                file_content, imports, classes, functions, relevant_elements
            )
            
            return optimized
        except SyntaxError:
            # File has syntax errors, can't parse - return original
            return file_content
        except Exception as e:
            print(f"Error optimizing context: {e}")
            return file_content
    
    def _extract_imports(self, tree: ast.Module) -> List[Tuple[int, int, str]]:
        """Extract import statements with line positions"""
        imports = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append((node.lineno, node.end_lineno, ast.unparse(node)))
        return imports
    
    def _extract_classes(self, tree: ast.Module) -> Dict[str, Tuple[int, int, str]]:
        """Extract class definitions with line positions"""
        classes = {}
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = (node.lineno, node.end_lineno, ast.unparse(node))
        return classes
    
    def _extract_functions(self, tree: ast.Module) -> Dict[str, Tuple[int, int, str]]:
        """Extract function definitions with line positions"""
        functions = {}
        
        # Get top-level functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = (node.lineno, node.end_lineno, ast.unparse(node))
        
        # Also get class methods
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                for subnode in ast.iter_child_nodes(node):
                    if isinstance(subnode, ast.FunctionDef):
                        functions[f"{node.name}.{subnode.name}"] = (
                            subnode.lineno, subnode.end_lineno, ast.unparse(subnode)
                        )
        
        return functions
    
    def _find_relevant_elements(
        self, error_log: str, functions: Dict[str, Tuple[int, int, str]], 
        classes: Dict[str, Tuple[int, int, str]]
    ) -> Set[str]:
        """Find relevant elements based on error message"""
        relevant = set()
        
        # Extract function and class names from error log
        for func_name in functions:
            # Handle both regular functions and class methods
            simple_name = func_name.split('.')[-1]
            if simple_name in error_log or func_name in error_log:
                relevant.add(func_name)
                # If it's a method, add its class too
                if '.' in func_name:
                    class_name = func_name.split('.')[0]
                    if class_name in classes:
                        relevant.add(class_name)
        
        # Extract class names from error log
        for class_name in classes:
            if class_name in error_log:
                relevant.add(class_name)
        
        return relevant
    
    def _reconstruct_optimized_content(
        self, original: str, imports: List[Tuple[int, int, str]], 
        classes: Dict[str, Tuple[int, int, str]], 
        functions: Dict[str, Tuple[int, int, str]], 
        relevant: Set[str]
    ) -> str:
        """Reconstruct optimized file content"""
        # If we didn't find anything relevant, return original
        if not relevant and len(original) < 2000:
            return original
            
        # Start with imports
        result = ""
        for _, _, import_str in imports:
            result += import_str + "\\n"
        
        result += "\\n"

# Add relevant classes
for class_name, (_, _, class_str) in classes.items():
    if class_name in relevant:
        result += class_str + "\n\n"
    else:
        # Include class definition without methods
        class_lines = class_str.split("\n")
        class_def_line = class_lines[0]
        result += class_def_line + ":\n    # Class implementation not shown (not relevant to error)\n    pass\n\n"

# Add relevant functions
for func_name, (_, _, func_str) in functions.items():
    if func_name in relevant or not relevant:
        # Add either relevant functions or all if no relevant ones found
        if "." not in func_name:  # Skip methods as they're included with classes
            result += func_str + "\n\n"

# Include a note about optimization
result += "\n# Note: This file has been optimized for error fixing.\n"
result += "# Some code may be omitted for clarity and relevance.\n"

return result

# Global context optimizer instance
context_optimizer = ContextOptimizer()


def optimize_file_context(file_content: str, error_log: str) -> str:
    """Convenience function to optimize file context"""
    return context_optimizer.optimize_context(file_content, error_log)


"""
    
    with open(AI_FIXER_DIR / "context_optimizer.py", "w") as f:
        f.write(context_optimizer)
    
    logger.info("Created context_optimizer.py")
    
    # Update agent.py to use context optimizer
    agent_path = AI_FIXER_DIR / "agent.py"
    with open(agent_path, "r") as f:
        agent_content = f.read()
    
    # Add context optimizer import
    if "from ai_fixer.context_optimizer import optimize_file_context" not in agent_content:
        imports_end = agent_content.find("from ai_fixer")
        imports_end = agent_content.find("\n", imports_end)
        agent_content = agent_content[:imports_end+1] + "from ai_fixer.context_optimizer import optimize_file_context\n" + agent_content[imports_end+1:]
    
    # Modify get_file_content function to use context optimizer
    if "def get_file_content(" in agent_content:
        file_content_start = agent_content.find("def get_file_content(")
        file_content_end = agent_content.find("def ", file_content_start + 1)
        
        # Get the function content
        file_content_func = agent_content[file_content_start:file_content_end]
        
        # Create optimized version
        optimized_func = file_content_func.replace(
            "    return content",
            "    # Optimize context based on error log if available\n"
            "    error_log = ''\n"
            "    if os.path.exists(CONFIG['log_file']):\n"
            "        try:\n"
            "            with open(CONFIG['log_file'], 'r') as f:\n"
            "                error_log = f.read()\n"
            "        except Exception:\n"
            "            pass\n"
            "    \n"
            "    # Apply context optimization\n"
            "    optimized = optimize_file_context(content, error_log)\n"
            "    return optimized"
        )
        
        # Replace the function
        agent_content = agent_content[:file_content_start] + optimized_func + agent_content[file_content_end:]
    
    with open(agent_path, "w") as f:
        f.write(agent_content)
    
    logger.info("Updated agent.py to use context optimizer")

def main():
    """
Main
function
to
enhance
AI
code
fixer
"""
    # Backup current code
    backup_current_code()
    
    # Implement enhancements
    implement_parallel_processing()
    add_telemetry_metrics()
    improve_model_selection()
    implement_context_optimization()
    
    logger.info("All enhancements have been implemented!")
    logger.info(f"Backup of original code is available at: {BACKUP_DIR}")

if __name__ == "__main__":
    main()