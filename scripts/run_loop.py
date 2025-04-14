# scripts/run_loop.py

import argparse
from ai_fixer.agent import run_correction_loop

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI code fixer")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them")
    args = parser.parse_args()

    run_correction_loop(dry_run=args.dry_run)
