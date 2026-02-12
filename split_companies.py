"""
Split company_list.json into smaller batches of 5 jobs each.
"""

import json
from pathlib import Path

def split_companies(batch_size=5):
    """Split company list into batches."""
    
    # Load full company list
    company_list_path = Path("company_list.json")
    
    with open(company_list_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)
    
    total = len(companies)
    print(f"Total jobs: {total}")
    print(f"Batch size: {batch_size}")
    print(f"Number of batches: {(total + batch_size - 1) // batch_size}")
    print()
    
    # Create batches
    batches_dir = Path("batches")
    batches_dir.mkdir(exist_ok=True)
    
    for i in range(0, total, batch_size):
        batch_num = (i // batch_size) + 1
        batch_companies = companies[i:i + batch_size]
        
        # Save batch file
        batch_filename = batches_dir / f"batch_{batch_num:02d}.json"
        
        with open(batch_filename, 'w', encoding='utf-8') as f:
            json.dump(batch_companies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created {batch_filename}")
        print(f"   Jobs {i+1}-{min(i+batch_size, total)} ({len(batch_companies)} jobs):")
        for company in batch_companies:
            print(f"   - {company['name']}")
        print()
    
    print("=" * 80)
    print("✅ BATCHES CREATED")
    print("=" * 80)
    print()
    print("To run batch 1:")
    print("   python batch_apply.py --company-list batches/batch_01.json --skip-generation")
    print()
    print("To run batch 2:")
    print("   python batch_apply.py --company-list batches/batch_02.json --skip-generation")
    print()
    print("And so on...")

if __name__ == "__main__":
    split_companies(batch_size=5)
