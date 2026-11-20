# What a creative is worth, on real ad data

Three questions an AI creative strategist has to answer before it automates anything:
1. How much of an ad's click-through rate (CTR) is the creative, and how much is the product or audience behind it?
2. How early can you call a winning creative?
3. What is shifting budget toward the leader actually worth?

All three are checked on 3.18 million real rows of display ad data. A weekly summary with noise-aware alerts sits on top.

**Data.** The CreativeRanking test split (Hugging Face `Evan12/CreativeRanking`, Apache-2.0). It is Alibaba display ads from *Hybrid Bandit Model with Visual Priors for Creative Ranking in Display Advertising* (WWW 2021). Each row is one product, one creative image, one day (0 to 14), with impressions and clicks:
- 100,345 products, each with 3 or more creatives running in parallel;
- 340,906 product-creative pairs;
- overall CTR 2.97%.

## Findings (run 21 Nov 2026, `out/results.json`)

**1. Most of the CTR spread is the product, not the creative.** This covers creatives with at least 500 impressions (12,568 creatives across 3,301 products). Expected binomial noise is subtracted first, so random noise is not counted as a creative effect.
- About **64% of the CTR variance is between products**.
- About **36% is between creatives of the same product**.

So a model that learns "visual feature X → high CTR" across products mostly learns which products sell, unless it compares creatives *within* the same product or campaign. Within a product the creative still matters a lot. In the busiest product, the best creative ran at about 5% CTR and the worst at about 1.1%, on roughly 7,000 impressions each (`out/weekly_summary_example.md`).

**2. Early winners are unreliable.** The test covers 1,760 products with at least 3,000 impressions. The leader after the first days is judged only against later, unseen days. Chance level is 24% because most products have 3 to 4 creatives.

| Days observed | Leader also wins the later days | Products where the leader is ≥95% "sure" | …and it actually wins later |
|---|---|---|---|
| 1 | 42% | 2% | 93% |
| 3 | 48% | 9% | 85% |
| 7 | 51% | 17% | 82% |

- Even after a week, the leader wins the following week only about half the time.
- When a standard Bayesian test says it is 95% sure, it is right only 82 to 93% of the time.
- The model assumes each creative has a fixed CTR, but here CTRs drift from week to week (fatigue, audience mix). A production system should use a time-decayed or windowed comparison and re-test winners, not lock them in.

**3. Gradually moving budget beats picking a winner early.** This is a simulation:
- Each product's creatives get "true" CTRs taken from their 15-day CTR, shrunk toward the product mean by the measured signal share (0.71). Without the shrink, noise would make the creatives look more different than they are.
- Each policy spends 200 impressions a day for 15 days.

| Policy | Clicks vs always showing the true best | Lift vs an even split |
|---|---|---|
| Even split | 75% | 0 |
| Pick the day-1 leader, then all budget to it | 83% | +10% |
| Thompson sampling (shift budget daily by posterior win probability) | 87% | +16% |

**4. Weekly summary with alerts** (`weekly_summary()`):
- Compares week 1 vs week 2 per creative.
- Raises an alert only when the change is bigger than noise (two-proportion z ≥ 2.5).
- Says when a creative had too little traffic to judge.

This is the shape of a guided weekly summary that does not cry wolf.

## Honest limits

- **Spend confounding.** In this dataset, impressions were not steered by performance: the rank correlation between impressions and CTR is about −0.05, both pooled and within product. So the main confounder here is the product, handled above. In real Meta, Google or TikTok accounts the platform's delivery algorithm **does** push spend toward ads it predicts will do well, and away from the rest. A naive "visual feature → performance" model on that data is confounded by spend: long-running, high-spend ads look like winners partly because they were given the budget. The fixes are the same idea as finding 1: compare creatives inside the same ad set and time window, weight by impressions, and confirm with a holdout or split test before trusting a feature.
- **The simulation is a model, not an online test.** It assumes CTRs are fixed over the 15 days, which finding 2 shows is not true. Real gains from budget shifting would likely be smaller than the simulated +16%.
- **No visual features yet.** The images are a 115 GB archive, so this run uses only the performance logs. The next step: read a sample of images from the zip with HTTP range requests. Then extract simple features (text area, faces, colour, product size), and test them with the within-product design above.
- **Domain:** Alibaba e-commerce display ads, not video ads for US fintech apps. The methods carry over; the exact numbers will not.

## Run

```
# data/test_data_list.txt from https://huggingface.co/datasets/Evan12/CreativeRanking (243 MB)
python analysis.py        # about 30 s on a laptop; writes out/results.json and out/weekly_summary_example.md
python -m pytest -q       # 6 tests on synthetic data where the right answer is known
```
pandas, numpy, pyarrow, pytest.
