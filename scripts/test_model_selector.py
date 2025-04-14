from ai_fixer.model_selector import select_model

def test_case(filename, content="def foo(): pass", error_log="", attempt=0):
    model = select_model(filename, content, error_log, attempt)
    print(f"🧪 File: {filename:<30} ➜ Model selected: {model}")

if __name__ == "__main__":
    test_case("main.py", "def add(a,b): return a+b")
    test_case("long_script.py", "\n".join(["line"] * 300))
    test_case("test_math.py", "def test_add(): assert add(1,2) == 3")
    test_case("data.yaml", "")
    test_case("config.json", "")
    test_case("weird.txt", "def custom(): pass")
    test_case("main.py", "def bad():\n fail", attempt=1)
