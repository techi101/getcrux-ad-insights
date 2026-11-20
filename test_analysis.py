"""Checks the methods on synthetic data where the right answer is known. Run: python -m pytest -q"""
import numpy as np
import pandas as pd
import analysis as A


def synth(n_prod=300, k=3, days=15, imp=400, creative_gap=0.0, seed=1):
    """Products with different base CTRs; creative 0 is better by `creative_gap` (absolute CTR)."""
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_prod):
        base = rng.uniform(0.01, 0.06)
        for c in range(k):
            ctr = base + (creative_gap if c == 0 else 0.0)
            for d in range(days):
                rows.append((f"p{p}", f"p{p}_c{c}", d, imp, rng.binomial(imp, ctr)))
    return pd.DataFrame(rows, columns=["product", "creative", "day", "imp", "clk"])


def test_variance_split_ignores_pure_noise():
    # creatives identical within each product -> creative share should be ~0 once noise is removed
    vs = A.variance_split(A.creative_table(synth(creative_gap=0.0)), min_imp=500)
    assert vs["share_within_product_creative"] < 0.05


def test_variance_split_finds_real_creative_effect():
    vs = A.variance_split(A.creative_table(synth(creative_gap=0.02)), min_imp=500)
    assert vs["share_within_product_creative"] > 0.2


def test_early_call_finds_clear_winner():
    r = A.early_call(synth(creative_gap=0.03), min_total_imp=1000, days=(2,))
    assert r["by_day"][0]["leader_wins_later_days"] > 0.9


def test_early_call_is_chance_without_winner():
    r = A.early_call(synth(creative_gap=0.0), min_total_imp=1000, days=(2,))
    assert abs(r["by_day"][0]["leader_wins_later_days"] - 1 / 3) < 0.1


def test_budget_sim_ordering():
    r = A.budget_sim(synth(n_prod=80, creative_gap=0.02), shrink=1.0, reps=1)
    v = r["clicks_vs_oracle"]
    assert v["uniform"] < v["thompson"] <= 1.0 + 1e-9


def test_weekly_summary_alerts_only_on_real_change():
    rows = []
    for d in range(14):
        rows.append(("p", "stable_creative", d, 1000, 30))
        rows.append(("p", "dropping_creative", d, 1000, 40 if d < 7 else 15))
    s = A.weekly_summary(pd.DataFrame(rows, columns=["product", "creative", "day", "imp", "clk"]), "p")
    assert "ALERT `dropping`" in s and "ALERT `stable_c`" not in s
