# benchmark_models.py

import time
from ai_fixer.llm_interface import run_ollama

TEST_PROMPT = "Write a function in Python to subtract two numbers: a and b."

MODELS = [
    "codellama:7b-instruct",
    "codellama:13b-instruct",
    "deepseek-coder:6.7b",
    "mistral:7b-instruct",
]

def benchmark(model: str):
    print(f"\n🧪 [{model}] | Mode: GPU")
    start = time.time()
    output_gpu = run_ollama(model, TEST_PROMPT, use_gpu=True)
    duration_gpu = round(time.time() - start, 2)
    print(f"🕒 Duration: {duration_gpu}s")
    print(f"📤 Output: {output_gpu[:100].strip()}\n")

    print(f"🧪 [{model}] | Mode: CPU")
    start = time.time()
    output_cpu = run_ollama(model, TEST_PROMPT, use_gpu=False)
    duration_cpu = round(time.time() - start, 2)
    print(f"🕒 Duration: {duration_cpu}s")
    print(f"📤 Output: {output_cpu[:100].strip()}")

if __name__ == "__main__":
    for model in MODELS:
        benchmark(model)
