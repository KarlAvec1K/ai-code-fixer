import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

CONFIG = {
    "project_path": os.path.join(BASE_DIR, "test_projects", "exemple_repo"),
    "llm_model": "deepseek-coder",
    "max_iterations": 10,
    "auto_commit": False,
    "branch_prefix": "ai-fix/",
    "log_file": os.path.join(BASE_DIR, "logs", "ai_fixer.log"),
    "memory_file": os.path.join(BASE_DIR, "memory.json"),
    "language": "python",
    "test_command": "pytest",
    "use_gpu": True,
    "max_concurrent_requests": 2,
    "parallel_execution": True,
    "model_selection": {
        "cache_dir": os.path.join(BASE_DIR, "cache", "model_selection"),
        "performance_file": os.path.join(BASE_DIR, "data", "model_performance.json")
    }
}
