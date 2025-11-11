# ============================================================================
# Zendesk Pipeline with AUTO-RESUME (Crash-Proof!)
# ============================================================================
# This script saves progress after EVERY domain.
# If it crashes, just re-run this cell and it continues where it left off!

import os

os.chdir('/content/lead-generator')

# IMPORTANT: Use the SAME filenames every time you run
INPUT_FILE = "top_25k_us_focused_domains.csv"
OUTPUT_CSV = "zendesk_leads_FULL.csv"
OUTPUT_DB = "zendesk_leads_FULL.db"

print("🚀 Starting/Resuming Pipeline with Auto-Save")
print("="*80)
print(f"📁 Input: {INPUT_FILE}")
print(f"💾 Output: {OUTPUT_CSV}")
print(f"🗄️  Database: {OUTPUT_DB}")
print("="*80)

# Run with --resume flag (automatically skips completed domains)
!python run_pipeline.py \
  --input {INPUT_FILE} \
  --output {OUTPUT_CSV} \
  --db-path {OUTPUT_DB} \
  --threads 10 \
  --us-only \
  --resume

print("\n" + "="*80)
print("📊 Checking Results...")
print("="*80)

# Show current progress
import pandas as pd
if os.path.exists(OUTPUT_CSV):
    df = pd.read_csv(OUTPUT_CSV)
    total = len(df)
    detected = df['detected_zendesk'].sum()

    print(f"\n✅ Progress saved!")
    print(f"   Processed so far: {total:,} domains")
    print(f"   Zendesk detected: {detected:,}")
    print(f"   Detection rate: {(detected/total*100):.1f}%")

    if total >= 25000:
        print("\n🎉 COMPLETE! All 25K domains processed!")
        print("\n💾 Downloading results...")
        from google.colab import files
        files.download(OUTPUT_CSV)
    else:
        remaining = 25000 - total
        print(f"\n⏳ Still processing... {remaining:,} domains remaining")
        print(f"   If disconnected, just re-run this cell to continue!")
else:
    print("\n⚠️ No results yet. Pipeline starting fresh.")

print("\n" + "="*80)
