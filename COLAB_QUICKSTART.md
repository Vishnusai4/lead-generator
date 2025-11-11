# Google Colab Quick Start

**Run the Zendesk Lead Generator on Google Colab in 3 clicks!**

Google Colab has unrestricted internet access and bypasses all proxy blocking.

## Option 1: Direct Link (Easiest)

**Click this link to open in Colab:**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Vishnusai4/lead-generator/blob/main/run_on_colab.ipynb)

Then just click "Runtime" → "Run all"

## Option 2: Manual Upload

1. Go to https://colab.research.google.com/
2. Click "File" → "Upload notebook"
3. Upload `run_on_colab.ipynb` from this repo
4. Click "Runtime" → "Run all"

## What It Does

1. ✅ Clones this repository
2. ✅ Installs dependencies
3. ✅ Configures ScraperAPI (your key is already set)
4. ✅ Tests internet connectivity
5. ✅ Runs detection on 100 domains (test)
6. ✅ Runs full 25K pipeline (~45 minutes)
7. ✅ Shows results and lets you download CSV

## Expected Results

For 25,000 domains:
- **Runtime:** ~45 minutes
- **Zendesk found:** 1,250 - 3,750 companies (5-15%)
- **Success rate:** 90%+ (with ScraperAPI)
- **Output:** `zendesk_leads_full.csv` (downloadable)

## Advantages of Colab

✅ **No proxy blocking** - Full internet access
✅ **Free tier** - 12-hour runtime (enough for 25K)
✅ **No setup** - Everything pre-configured
✅ **Easy download** - Results download to your computer
✅ **GPU available** - (though we don't need it)

## Need Help?

If the Colab link doesn't work:
1. Go to https://colab.research.google.com/
2. Click "GitHub" tab
3. Paste: `https://github.com/Vishnusai4/lead-generator`
4. Select `run_on_colab.ipynb`

## Cost

**Google Colab:** FREE (12-hour sessions)
**ScraperAPI:** FREE tier (1,000 requests/month)

For 25K domains, you'll use ~25K ScraperAPI credits. If you need more:
- ScraperAPI paid: $49/month for 100K requests
- Or run in batches using free tier over multiple months

## Alternative: Colab Pro

If you need longer sessions or faster processing:
- **Colab Pro:** $10/month
- 24-hour sessions
- Faster GPUs (not needed for this)
- Background execution

---

**Ready to run?** Click the Colab badge above and hit "Run all"! 🚀
