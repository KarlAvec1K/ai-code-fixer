import logging
from pathlib import Path
AI_FIXER_DIR = Path(__file__).parent.parent.parent / "ai_fixer"
    # Create model_selection.py
    model_selection = """import os
import json
import re
from typing import Dict, List, Tuple, Set, Optional, Any
import logging
import random
from pathlib import Path
from collections import defaultdict, Counter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model_selection")

class ModelSelector:
    """
    Smart
    model
    selection
    system
    for AI code fixing"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize model selector with config"""
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "model_selection.json"
        )
        self.models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "model_performance"
        )

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

        # Load or create configuration
        self.config = self._load_or_create_config()

        # Load performance data
        self.performance_data = self._load_performance_data()

        # Cache for file characteristics
        self.file_characteristics_cache = {}

    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load config or create default if not exists"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")

        # Default configuration
        default_config = {
            "models": {
                "gpt-3.5-turbo": {
                    "cost_per_token": 0.000002,
                    "max_tokens": 4096,
                    "suitable_for": ["syntax_errors", "simple_logic_errors", "type_errors"],
                    "strengths": ["fast", "cost_effective"],
                    "weaknesses": ["complex_algorithms", "deep_context_understanding"]
                },
                "gpt-4": {
                    "cost_per_token": 0.00006,
                    "max_tokens": 8192,
                    "suitable_for": ["complex_logic_errors", "architectural_issues", "performance_problems"],
                    "strengths": ["deep_reasoning", "context_understanding"],
                    "weaknesses": ["cost", "speed"]
                },
                "claude-2": {
                    "cost_per_token": 0.00003,
                    "max_tokens": 100000,
                    "suitable_for": ["large_files", "complex_context", "architectural_issues"],
                    "strengths": ["long_context", "code_understanding"],
                    "weaknesses": ["availability", "cost"]
                }
            },
            "error_types": {
                "syntax_error": {
                    "preferred_models": ["gpt-3.5-turbo", "gpt-4"],
                    "pattern": "SyntaxError|IndentationError"
                },
                "type_error": {
                    "preferred_models": ["gpt-4", "gpt-3.5-turbo"],
                    "pattern": "TypeError|AttributeError"
                },
                "name_error": {
                    "preferred_models": ["gpt-3.5-turbo"],
                    "pattern": "NameError|UnboundLocalError"
                },
                "import_error": {
                    "preferred_models": ["gpt-3.5-turbo"],
                    "pattern": "ImportError|ModuleNotFoundError"
                },
                "value_error": {
                    "preferred_models": ["gpt-4", "gpt-3.5-turbo"],
                    "pattern": "ValueError|AssertionError"
                },
                "runtime_error": {
                    "preferred_models": ["gpt-4"],
                    "pattern": "RuntimeError|RecursionError"
                },
                "index_error": {
                    "preferred_models": ["gpt-3.5-turbo", "gpt-4"],
                    "pattern": "IndexError|KeyError"
                },
                "memory_error": {
                    "preferred_models": ["gpt-4"],
                    "pattern": "MemoryError|OverflowError"
                },
                "logic_error": {
                    "preferred_models": ["gpt-4", "claude-2"],
                    "pattern": "LogicError|AlgorithmError"
                }
            },
            "file_characteristics": {
                "small": {
                    "max_size": 2000,  # characters
                    "preferred_models": ["gpt-3.5-turbo"]
                },
                "medium": {
                    "max_size": 10000,  # characters
                    "preferred_models": ["gpt-4"]
                },
                "large": {
                    "max_size": 50000,  # characters
                    "preferred_models": ["claude-2", "gpt-4"]
                },
                "complex": {
                    "complex_patterns": [
                        "class\\s+\\w+\\(.*\\):",
                        "def\\s+\\w+\\(.*\\):\\s*\\n\\s*\"\"\"[\\s\\S]*?\"\"\"",
                        "with\\s+.*?:\\s*\\n\\s*(?:with|if|for|while|try)",
                        "(?:if|for|while)\\s+.*?:\\s*\\n\\s*(?:if|for|while|try)"
                    ],
                    "threshold": 5,  # Number of patterns to consider complex
                    "preferred_models": ["gpt-4", "claude-2"]
                }
            },
            "weights": {
                "error_type_match": 3.0,
                "historical_performance": 2.5,
                "file_characteristics": 1.5,
                "cost_efficiency": 1.0,
                "random_exploration": 0.2
            },
            "parallel_execution": {
                "enabled": True,
                "max_parallel_models": 2,
                "timeout_seconds": 120
            }
        }

        # Save default config
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error creating config: {e}")

        return default_config

    def _load_performance_data(self) -> Dict[str, Dict]:
        """Load historical performance data for models"""
        performance_data = {}

        # Check if directory exists
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir, exist_ok=True)
            return performance_data

        # Load data for each model
        for model_name in self.config["models"].keys():
            model_file = os.path.join(self.models_dir, f"{model_name}.json")
            if os.path.exists(model_file):
                try:
                    with open(model_file, 'r') as f:
                        performance_data[model_name] = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading performance data for {model_name}: {e}")
                    performance_data[model_name] = self._create_default_performance_data()
            else:
                performance_data[model_name] = self._create_default_performance_data()

        return performance_data

    def _create_default_performance_data(self) -> Dict:
        """Create default performance data structure"""
        return {
            "overall": {
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "average_fix_time": 0.0,
                "total_tokens_used": 0,
                "total_cost": 0.0
            },
            "by_error_type": {},
            "by_file_type": {},
            "by_complexity": {
                "simple": {"success_rate": 0.0, "count": 0},
                "medium": {"success_rate": 0.0, "count": 0},
                "complex": {"success_rate": 0.0, "count": 0}
            },
            "recent_performance": []  # Last 20 attempts
        }

    def analyze_file_characteristics(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Analyze file characteristics for model selection"""
        # Use cached result if available
        if file_path in self.file_characteristics_cache:
            return self.file_characteristics_cache[file_path]

        file_size = len(file_content)
        file_ext = os.path.splitext(file_path)[1].lower()

        # Count complex patterns
        complexity_score = 0
        complex_patterns = self.config["file_characteristics"]["complex"]["complex_patterns"]
        for pattern in complex_patterns:
            complexity_score += len(re.findall(pattern, file_content))

        # Determine size category
        size_category = "large"
        for category in ["small", "medium", "large"]:
            if file_size <= self.config["file_characteristics"][category]["max_size"]:
                size_category = category
                break

        # Determine complexity category
        complexity_category = "simple"
        if complexity_score >= self.config["file_characteristics"]["complex"]["threshold"]:
            complexity_category = "complex"
        elif complexity_score >= self.config["file_characteristics"]["complex"]["threshold"] // 2:
            complexity_category = "medium"

        # Calculate function and class counts
        function_count = len(re.findall(r"def\s+\w+\s*\(", file_content))
        class_count = len(re.findall(r"class\s+\w+\s*[:\(]", file_content))

        # Calculate cyclomatic complexity estimation
        # Count decision points as a rough approximation
        decision_points = len(re.findall(r"\s(if|else|elif|for|while|try|except)\s", file_content))

        characteristics = {
            "file_size": file_size,
            "file_extension": file_ext,
            "size_category": size_category,
            "complexity_category": complexity_category,
            "complexity_score": complexity_score,
            "function_count": function_count,
            "class_count": class_count,
            "decision_points": decision_points
        }

        # Cache the result
        self.file_characteristics_cache[file_path] = characteristics

        return characteristics

    def identify_error_type(self, error_message: str) -> str:
        """Identify the type of error from error message"""
        for error_type, error_info in self.config["error_types"].items():
            if re.search(error_info["pattern"], error_message, re.IGNORECASE):
                return error_type

        # Default to generic error if no specific type is identified
        return "generic_error"

    def _calculate_model_scores(self,
                               error_type: str,
                               file_characteristics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scores for each model based on various factors"""
        scores = {}
        weights = self.config["weights"]

        for model_name in self.config["models"].keys():
            score = 0.0

            # 1. Error type match
            if error_type in self.config["error_types"]:
                preferred_models = self.config["error_types"][error_type]["preferred_models"]
                if model_name in preferred_models:
                    # Higher score for models that are primary choices for this error
                    score += weights["error_type_match"] * (1.0 / (preferred_models.index(model_name) + 1))

            # 2. Historical performance
            if model_name in self.performance_data:
                model_perf = self.performance_data[model_name]

                # Overall success rate
                if model_perf["overall"]["success_count"] + model_perf["overall"]["failure_count"] > 0:
                    success_rate = model_perf["overall"]["success_count"] / (
                        model_perf["overall"]["success_count"] + model_perf["overall"]["failure_count"]
                    )
                    score += weights["historical_performance"] * success_rate

                # Error type specific success rate
                if error_type in model_perf.get("by_error_type", {}) and model_perf["by_error_type"][error_type]["count"] > 0:
                    error_success_rate = model_perf["by_error_type"][error_type]["success_rate"]
                    score += weights["historical_performance"] * 1.5 * error_success_rate  # Extra weight for specific error type

                # File complexity success rate
                complexity = file_characteristics["complexity_category"]
                if complexity in model_perf["by_complexity"] and model_perf["by_complexity"][complexity]["count"] > 0:
                    complexity_success_rate = model_perf["by_complexity"][complexity]["success_rate"]
                    score += weights["historical_performance"] * 0.8 * complexity_success_rate

            # 3. File characteristics match
            size_category = file_characteristics["size_category"]
            if size_category in self.config["file_characteristics"]:
                preferred_models = self.config["file_characteristics"][size_category]["preferred_models"]
                if model_name in preferred_models:
                    score += weights["file_characteristics"] * (1.0 / (preferred_models.index(model_name) + 1))

            complexity_category = file_characteristics["complexity_category"]
            if complexity_category == "complex" and "complex" in self.config["file_characteristics"]:
                preferred_models = self.config["file_characteristics"]["complex"]["preferred_models"]
                if model_name in preferred_models:
                    score += weights["file_characteristics"] * 1.2 * (1.0 / (preferred_models.index(model_name) + 1))

            # 4. Cost efficiency for the file size
            model_config = self.config["models"][model_name]
            file_size = file_characteristics["file_size"]
            # Lower score for expensive models on small files
            if file_size < 2000 and model_config["cost_per_token"] > 0.00001:
                score -= weights["cost_efficiency"] * 0.5
            # Higher score for cost-effective models on small files
            elif file_size < 2000 and model_config["cost_per_token"] <= 0.00001:
                score += weights["cost_efficiency"] * 0.5

            # 5. Random exploration factor
            score += weights["random_exploration"] * random.random()

            scores[model_name] = max(0.1, score)  # Ensure non-negative score

        return scores

    def select_model(self, file_path: str, file_content: str, error_message: str) -> str:
        """Select the best model for fixing the error"""
        error_type = self.identify_error_type(error_message)
        file_characteristics = self.analyze_file_characteristics(file_path, file_content)

        # Calculate scores for each model
        scores = self._calculate_model_scores(error_type, file_characteristics)

        # Select the model with highest score
        if not scores:
            return "gpt-3.5-turbo"  # Default model if no scores

        best_model = max(scores.items(), key=lambda x: x[1])[0]

        logger.info(f"Selected model {best_model} (score: {scores[best_model]:.2f}) for error type {error_type}")
        return best_model

    def select_models_for_parallel(self, file_path: str, file_content: str, error_message: str) -> List[str]:
        """Select multiple models for parallel execution"""
        if not self.config["parallel_execution"]["enabled"]:
            return [self.select_model(file_path, file_content, error_message)]

        error_type = self.identify_error_type(error_message)
        file_characteristics = self.analyze_file_characteristics(file_path, file_content)

        # Calculate scores for each model
        scores = self._calculate_model_scores(error_type, file_characteristics)

        # Sort models by score
        sorted_models = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Select top N models
        max_models = min(self.config["parallel_execution"]["max_parallel_models"], len(sorted_models))
        selected_models = [model[0] for model in sorted_models[:max_models]]

        logger.info(f"Selected models for parallel execution: {selected_models}")
        return selected_models

    def record_success(self, model_name: str, error_type: str, file_characteristics: Dict,
                       success: bool, tokens_used: int, fix_time: float) -> None:
        """Record model performance for future selection"""
        if model_name not in self.performance_data:
            self.performance_data[model_name] = self._create_default_performance_data()

        model_perf = self.performance_data[model_name]

        # Update overall stats
        if success:
            model_perf["overall"]["success_count"] += 1
        else:
            model_perf["overall"]["failure_count"] += 1

        total_attempts = model_perf["overall"]["success_count"] + model_perf["overall"]["failure_count"]
        model_perf["overall"]["success_rate"] = model_perf["overall"]["success_count"] / total_attempts

        # Update fix time average
        current_avg = model_perf["overall"]["average_fix_time"]
        model_perf["overall"]["average_fix_time"] = (
            (current_avg * (total_attempts - 1) + fix_time) / total_attempts
        )

        # Update token usage and cost
        model_perf["overall"]["total_tokens_used"] += tokens_used
        cost_per_token = self.config["models"][model_name]["cost_per_token"]
        model_perf["overall"]["total_cost"] += tokens_used * cost_per_token

        # Update error type stats
        if error_type not in model_perf["by_error_type"]:
            model_perf["by_error_type"][error_type] = {
                "success_count": 0,
                "failure_count": 0,
                "success_rate": 0.0,
                "count": 0
            }

        error_stats = model_perf["by_error_type"][error_type]
        if success:
            error_stats["success_count"] += 1
        else:
            error_stats["failure_count"] += 1

        error_stats["count"] = error_stats["success_count"] + error_stats["failure_count"]
        error_stats["success_rate"] = error_stats["success_count"] / error_stats["count"]

        # Update complexity stats
        complexity = file_characteristics["complexity_category"]
        complexity_stats = model_perf["by_complexity"][complexity]
        complexity_stats["count"] += 1

        # Calculate success rate for this complexity level
        if success:
            old_success_count = complexity_stats["success_rate"] * complexity_stats["count"] - 1
            complexity_stats["success_rate"] = (old_success_count + 1) / complexity_stats["count"]
        else:
            old_success_count = complexity_stats["success_rate"] * complexity_stats["count"]
            complexity_stats["success_rate"] = old_success_count / complexity_stats["count"]

        # Update recent performance
        model_perf["recent_performance"].append({
            "timestamp": str(Path(__file__).stat().st_mtime),
            "success": success,
            "error_type": error_type,
            "file_size": file_characteristics["file_size"],
            "complexity": complexity,
            "tokens_used": tokens_used,
            "fix_time": fix_time
        })

        # Keep only the most recent 20 attempts
        if len(model_perf["recent_performance"]) > 20:
            model_perf["recent_performance"] = model_perf["recent_performance"][-20:]

        # Save updated performance data
        self._save_performance_data(model_name)

    def _save_performance_data(self, model_name: str) -> None:
        """Save performance data for a specific model"""
        if model_name not in self.performance_data:
            return

        model_file = os.path.join(self.models_dir, f"{model_name}.json")
        try:
            with open(model_file, 'w') as f:
                json.dump(self.performance_data[model_name], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving performance data for {model_name}: {e}")

    def get_model_stats(self) -> Dict[str, Dict]:
        """Get statistics about model performance"""
        stats = {}
        for model_name, perf_data in self.performance_data.items():
            stats[model_name] = {
                "success_rate": perf_data["overall"]["success_rate"],
                "average_fix_time": perf_data["overall"]["average_fix_time"],
                "total_cost": perf_data["overall"]["total_cost"],
                "total_fixes": perf_data["overall"]["success_count"]
            }
        return stats

# Global model selector instance
model_selector = ModelSelector()

def select_model(file_path: str, file_content: str, error_message: str) -> str:
    """Convenience function to select best model"""
    return model_selector.select_model(file_path, file_content, error_message)

def select_models_for_parallel(file_path: str, file_content: str, error_message: str) -> List[str]:
    """Convenience function to select models for parallel execution"""
    return model_selector.select_models_for_parallel(file_path, file_content, error_message)

def record_success(model_name: str, error_type: str, file_characteristics: Dict,
                  success: bool, tokens_used: int, fix_time: float) -> None:
    """Convenience function to record model success / failure"""
    return model_selector.record_success(
        model_name, error_type, file_characteristics, success, tokens_used, fix_time
    )

def get_best_models() -> Dict[str, Dict]:
    """Get statistics about model performance"""
    return model_selector.get_model_stats()
"""

    with open(AI_FIXER_DIR / "model_selection.py", "w") as f:
        f.write(model_selection)

    logger.info("Created model_selection.py")

    # Update agent.py to use model selection
    agent_path = AI_FIXER_DIR / "agent.py"

    with open(agent_path, "r") as f:
        agent_content = f.read()

    # Add model selection import
    if "from ai_fixer.model_selection import" not in agent_content:
        imports_end = agent_content.find("from ai_fixer")
        imports_end = agent_content.find("\n", imports_end)
        agent_content = agent_content[
                        :imports_end + 1] + "from ai_fixer.model_selection import select_model, record_success\n" + agent_content[
                                                                                                                    imports_end + 1:]

    # Modify the fix_code function to use model selection
    if "def fix_code(" in agent_content:
        fix_code_start = agent_content.find("def fix_code(")
        call_llm_pattern = r"response = call_llm\(.*?\)"

        # Find all call_llm invocations
        matches = re.finditer(call_llm_pattern, agent_content[fix_code_start:], re.DOTALL)
        for match in matches:
            start_pos = fix_code_start + match.start()
            end_pos = fix_code_start + match.end()

            # Get the original call
            original_call = agent_content[start_pos:end_pos]

            # Create new call with model selection
            if "model=" not in original_call:
                new_call = original_call.replace(
                    "call_llm(",
                    "start_time = time.time()\n"
                    "    selected_model = select_model(file_path, content, str(error))\n"
                    "    response = call_llm(model=selected_model, "
                )
            else:
                new_call = re.sub(
                    r"model=[\"\'].*?[\"\']",
                    "model=selected_model",
                    original_call
                )
                new_call = "start_time = time.time()\n    selected_model = select_model(file_path, content, str(error))\n    " + new_call

            # Replace the call
            agent_content = agent_content[:start_pos] + new_call + agent_content[end_pos:]

    # Add recording of model performance after fix attempt
    if "def fix_code(" in agent_content and "return fixed_content" in agent_content:
        return_pos = agent_content.find("return fixed_content", agent_content.find("def fix_code("))

        # Add code to record performance
        performance_code = """
    # Record model performance
    fix_time = time.time() - start_time
    tokens_used = len(content) // 4  # Approximate token count
    file_characteristics = {
        "file_size": len(content),
        "complexity_category": "medium" if len(content) > 1000 else "simple"
    }
    error_type = str(error).split(':')[0] if ':' in str(error) else "generic_error"
    record_success(
        model_name=selected_model,
        error_type=error_type,
        file_characteristics=file_characteristics,
        success=fixed_content != content,  # True if changes were made
        tokens_used=tokens_used,
        fix_time=fix_time
    )
    
    """
        agent_content = agent_content[:return_pos] + performance_code + agent_content[return_pos:]

    # Add time import if not present
    if "import time" not in agent_content:
        import_pos = agent_content.find("import")
        agent_content = agent_content[:import_pos] + "import time\n" + agent_content[import_pos:]

    # Save updated agent.py
    with open(agent_path, "w") as f:
        f.write(agent_content)

    logger.info("Updated agent.py to use model selection")