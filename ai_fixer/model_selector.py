# ai_fixer/model_selector.py
import os
import random
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("model_selector")
# Model configurations
LANGUAGE_MODELS = {
    ".py": ["deepseek-coder", "codellama:13b-instruct"],
    ".js": ["deepseek-coder", "codellama:13b-instruct"],
    ".ts": ["deepseek-coder", "codellama:13b-instruct"],
    ".java": ["deepseek-coder"],
    ".cpp": ["deepseek-coder"],
    ".c": ["deepseek-coder"],
    ".go": ["deepseek-coder"],
    ".rs": ["deepseek-coder"],
    ".rb": ["deepseek-coder"],
    "default": ["deepseek-coder"]
}
ERROR_TYPE_MODELS = {
    "SyntaxError": ["deepseek-coder"],
    "IndentationError": ["deepseek-coder"],
    "TypeError": ["deepseek-coder", "codellama:13b-instruct"],
    "AssertionError": ["deepseek-coder", "codellama:13b-instruct"],
    "ImportError": ["deepseek-coder"],
    "AttributeError": ["deepseek-coder", "codellama:13b-instruct"],
    "IndexError": ["deepseek-coder"],
    "ValueError": ["deepseek-coder", "codellama:13b-instruct"],
    "RuntimeError": ["codellama:13b-instruct", "deepseek-coder"],
    "MemoryError": ["codellama:13b-instruct"],
    "LogicError": ["codellama:13b-instruct", "deepseek-coder"]
}
FALLBACK_MODELS = ["deepseek-coder", "codellama:13b-instruct"]
class ModelSelector:
    def __init__(self):
        self.performance_data = {}
        self.load_performance_data()
    def load_performance_data(self):
        """Load historical performance data"""
        data_file = Path(__file__).parent.parent / "data" / "model_performance.json"
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    self.performance_data = json.load(f)
            except json.JSONDecodeError:
                logger.error("Error loading performance data")
    def select_model(self, filename: str, file_content: str, error_log: str, attempt: int = 0) -> str:
        """Select the most appropriate model based on various factors"""
        # For complex multi-file fixes, use the most capable model
        if filename == "multiple_files":
            return "deepseek-coder"
        # Get file extension
        _, ext = os.path.splitext(filename)
        language_models = LANGUAGE_MODELS.get(ext, LANGUAGE_MODELS["default"])
        # On later attempts, try different models
        if attempt > 0 and attempt % 3 == 0:
            return random.choice(FALLBACK_MODELS)
        # Try to match error type
        for error_type, models in ERROR_TYPE_MODELS.items():
            if error_type in error_log:
                return models[0]
        # Default to the first model for this language
        return language_models[0]
# Global instance
model_selector = ModelSelector()
def select_model(filename: str, file_content: str, error_log: str, attempt: int = 0) -> str:
    """Convenience function to select a model"""
    return model_selector.select_model(filename, file_content, error_log, attempt)

        # Select based on complexity and performance
        category = self._select_category(complexity, attempt)
        return self._select_from_category(category)

    def _get_error_type(self, error_log: str) -> str:
        """Extract error type from error log"""
        error_patterns = [
            "SyntaxError", "TypeError", "AttributeError",
            "ImportError", "IndentationError", "AssertionError"
        ]
        for pattern in error_patterns:
            if pattern in error_log:
                return pattern
        return "unknown"

    def _assess_complexity(self, content: str) -> str:
        """Assess code complexity"""
        lines = content.split("\n")
        if len(lines) < 50 and content.count("def ") < 3:
            return "simple"
        if len(lines) > 200 or content.count("class ") > 2:
            return "complex"
        return "medium"

    def _select_category(self, complexity: str, attempt: int) -> str:
        """Select model category based on complexity and attempt number"""
        if complexity == "simple" and attempt < 3:
            return "small"
        if complexity == "complex" or attempt > 5:
            return "large"
        return "medium"

    def _select_from_category(self, category: str) -> str:
        """Select specific model from category based on performance"""
        models = self.models[category]["models"]

        # Use performance history if available
        model_scores = []
        for model in models:
            perf = self.performance_history.get(model, {"success": 0, "total": 1})
            score = perf["success"] / perf["total"]
            model_scores.append((model, score))

        # Sort by score and add some randomization
        model_scores.sort(key=lambda x: x[1] + random.random() * 0.2)
        return model_scores[-1][0]
