#!/bin/bash

echo "🔧 Initialisation du projet AI Code Fixer avec DeepSeek-Coder"

# 1. Vérification & installation de ollama
if ! command -v ollama &> /dev/null; then
    echo "📦 Ollama non détecté. Installation..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama déjà installé."
fi

# 2. Démarrage de ollama
echo "🚀 Démarrage du service Ollama..."
ollama serve > /dev/null 2>&1 &
sleep 3

# 3. Téléchargement du modèle DeepSeek-Coder
echo "📥 Téléchargement de deepseek-coder..."
ollama pull deepseek-coder:latest

# 4. Création de l'arborescence
echo "📁 Création de l’arborescence..."
mkdir -p ai-code-fixer/{ai_fixer,scripts,test_projects/exemple_repo/tests,logs,examples}
cd ai-code-fixer
touch memory.json README.md requirements.txt

# 5. Création des fichiers Python

echo "📄 Génération des fichiers..."
# ai_fixer/__init__.py
touch ai_fixer/__init__.py

# ai_fixer/config.py
cat <<EOF > ai_fixer/config.py
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

CONFIG = {
    "project_path": os.path.join(BASE_DIR, "test_projects", "exemple_repo"),
    "llm_model": "deepseek-coder:latest",
    "max_iterations": 10,
    "auto_commit": False,
    "branch_prefix": "ai-fix/",
    "log_file": os.path.join(BASE_DIR, "logs", "ai_fixer.log"),
    "memory_file": os.path.join(BASE_DIR, "memory.json"),
    "language": "python",
    "test_command": "pytest",
}
EOF

# ai_fixer/llm_interface.py
cat <<EOF > ai_fixer/llm_interface.py
import subprocess
import json

def generate_fix(error_log, file_content, filename):
    prompt = f"""
You are a senior software engineer. Analyze the following test failure and propose a fix for the file {filename}.
### Test Error:
{error_log}
### File Content:
{file_content}
### Return only the fixed file content. No explanations.
"""
    result = subprocess.run(
        ["ollama", "run", "deepseek-coder", prompt],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()
EOF

# ai_fixer/code_editor.py
cat <<EOF > ai_fixer/code_editor.py
def overwrite_file(filepath, new_content):
    with open(filepath, "w") as f:
        f.write(new_content)
    print(f"✅ Fichier modifié : {filepath}")
EOF

# ai_fixer/agent.py
cat <<EOF > ai_fixer/agent.py
import subprocess
import os
from ai_fixer.config import CONFIG
from ai_fixer.llm_interface import generate_fix
from ai_fixer.code_editor import overwrite_file

def run_tests():
    print("🧪 Lancement des tests...")
    try:
        result = subprocess.run(
            CONFIG["test_command"],
            cwd=CONFIG["project_path"],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.returncode, result.stdout
    except Exception as e:
        return 1, str(e)

def extract_target_file():
    return os.path.join(CONFIG["project_path"], "main.py")

def run_correction_loop():
    for i in range(CONFIG["max_iterations"]):
        print(f"🔁 Itération {i+1}...")
        code, output = run_tests()
        if code == 0:
            print("✅ Tous les tests sont passés.")
            break

        target_file = extract_target_file()
        with open(target_file, "r") as f:
            file_content = f.read()

        fix = generate_fix(output, file_content, target_file)
        overwrite_file(target_file, fix)
    else:
        print("🚫 Échec après nombre maximal d’itérations.")
EOF

# scripts/run_loop.py
cat <<EOF > scripts/run_loop.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai_fixer.agent import run_correction_loop

if __name__ == "__main__":
    print("🚀 Lancement de l'agent IA")
    run_correction_loop()
EOF

# test_projects/exemple_repo/main.py
cat <<EOF > test_projects/exemple_repo/main.py
def add(a, b):
    return a + b
EOF

# test_projects/exemple_repo/tests/test_main.py
cat <<EOF > test_projects/exemple_repo/tests/test_main.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import add

def test_add():
    assert add(2, 2) == 5  # Erreur volontaire
EOF

# test_projects/exemple_repo/requirements.txt
echo "pytest" > test_projects/exemple_repo/requirements.txt

# 6. Création de l'environnement virtuel
echo "🐍 Création d'un environnement Python virtuel..."
python3 -m venv ai-code-fixer.venv
source ai-code-fixer.venv/bin/activate

# 7. Installation des dépendances
echo "📦 Installation des dépendances Python..."
pip install --upgrade pip
pip install ollama-python --break-system-packages
pip install pytest --break-system-packages

echo "✅ Setup terminé. Lancez maintenant l'agent avec :"
echo "cd ai-code-fixer"
echo "source ai-code-fixer.venv/bin/activate"
echo "python3 scripts/run_loop.py"
