"""
Quick script to view the latest batch summary.
"""

import os
from pathlib import Path

LOGS_DIR = Path(__file__).parent / "logs"
BATCH_SUMMARY_FILE = LOGS_DIR / "batch_summary.txt"

def view_summary():
    """Display the batch summary."""
    
    if not BATCH_SUMMARY_FILE.exists():
        print("❌ No batch summary found yet.")
        print(f"   Expected at: {BATCH_SUMMARY_FILE}")
        print("\nRun batch_apply.py first to generate a summary.")
        return
    
    # Read and display
    with open(BATCH_SUMMARY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(content)
    print("\n" + "="*80)
    print(f"Summary file: {BATCH_SUMMARY_FILE}")
    print("="*80)

if __name__ == "__main__":
    view_summary()
