"""
Quick script to verify generated files and show their paths.
Run this to check if your resume and cover letter were generated correctly.
"""

import os
from pathlib import Path
import glob

print("=" * 80)
print("CHECKING GENERATED FILES")
print("=" * 80)
print()

# Check generated_documents directory
docs_dir = Path("generated_documents")

if not docs_dir.exists():
    print("❌ generated_documents/ directory not found")
    print("   Run the automation first to generate files")
    exit(1)

print(f"✅ Directory: {docs_dir.resolve()}")
print()

# Find all files
resumes = list(docs_dir.glob("*resume*.docx"))
cover_letters = list(docs_dir.glob("*cover_letter*.docx"))

print(f"📄 RESUMES FOUND: {len(resumes)}")
print("-" * 80)
for resume in sorted(resumes, reverse=True):
    size = resume.stat().st_size
    print(f"  ✅ {resume.name}")
    print(f"     Size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"     Path: {resume.resolve()}")
    print(f"     Exists: {resume.exists()}")
    print()

print(f"✉️  COVER LETTERS FOUND: {len(cover_letters)}")
print("-" * 80)
for letter in sorted(cover_letters, reverse=True):
    size = letter.stat().st_size
    print(f"  ✅ {letter.name}")
    print(f"     Size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"     Path: {letter.resolve()}")
    print(f"     Exists: {letter.exists()}")
    print()

if resumes:
    latest_resume = sorted(resumes, reverse=True)[0]
    print("=" * 80)
    print("LATEST RESUME")
    print("=" * 80)
    print(f"Name: {latest_resume.name}")
    print(f"Full Path: {latest_resume.resolve()}")
    print(f"Windows Path: {str(latest_resume.resolve())}")
    print(f"Forward Slash: {str(latest_resume.resolve()).replace(chr(92), '/')}")
    print()

if cover_letters:
    latest_letter = sorted(cover_letters, reverse=True)[0]
    print("=" * 80)
    print("LATEST COVER LETTER")
    print("=" * 80)
    print(f"Name: {latest_letter.name}")
    print(f"Full Path: {latest_letter.resolve()}")
    print(f"Windows Path: {str(latest_letter.resolve())}")
    print(f"Forward Slash: {str(latest_letter.resolve()).replace(chr(92), '/')}")
    print()

print("=" * 80)
print("💡 TIP: If file uploads fail in browser automation:")
print("   1. Copy the file path above")
print("   2. Try uploading manually during the automation pause")
print("   3. Or update the script to use a different path format")
print("=" * 80)
