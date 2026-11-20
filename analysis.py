"""Creative performance on real ad data: what the creative explains, when a winner can be called, what shifting budget is worth.

Data: CreativeRanking test split (Hugging Face Evan12/CreativeRanking, Apache-2.0; Alibaba display ads, from
"Hybrid Bandit Model with Visual Priors for Creative Ranking in Display Advertising", WWW 2021).
Each row = (product, creative image, day 0-14, impressions, clicks). Every product has 3+ creatives shown in parallel.

Run: python analysis.py   (writes out/results.json and out/report.md)
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
SEED = 0


# ---------- loading ----------
def load(path=ROOT / "data" / "cr_test.parquet"):
    if path.exists():
        return pd.read_parquet(path)
    d = pd.read_csv(ROOT / "data" / "test_data_list.txt", sep="\t", header=None,
                    names=["product", "creative", "day", "imp", "clk"])
    d.to_parquet(path)
    return d


def creative_table(d):
    """One row per (product, creative): total impressions and clicks over all days."""
    return d.groupby(["product", "creative"], as_index=False)[["imp", "clk"]].sum()


# ---------- 1. how much of CTR is the creative vs the product ----------
def variance_split(ct, min_imp=500):
    """Split creative-level CTR variance into between-product and within-product parts.
    Only creatives with >= min_imp impressions, and products with 2+ such creatives, so noise is small.
    Binomial noise is subtracted from the within-product part so it is not counted as creative effect."""
    c = ct[ct.imp >= min_imp].copy()
    c = c[c.groupby("product").creative.transform("count") >= 2]
    c["ctr"] = c.clk / c.imp
    pm = c.groupby("product").ctr.transform("mean")
    total = c.ctr.var()
    within_raw = ((c.ctr - pm) ** 2).mean()
    noise = (c.ctr * (1 - c.ctr) / c.imp).mean()          # expected sampling variance per creative
    within_true = max(within_raw - noise, 0.0)
    between = ((pm - c.ctr.mean()) ** 2).mean()
    return {"creatives": int(len(c)), "products": int(c["product"].nunique()), "min_imp": min_imp,
            "total_var": total, "between_product_var": between, "within_product_var_raw": within_raw,
            "sampling_noise_var": noise, "within_product_var_after_noise": within_true,
            "share_between_product": between / (between + within_true),
            "share_within_product_creative": within_true / (between + within_true)}


def pooled_vs_within(ct, min_imp=500):
    """The confounding check: do creatives that got MORE impressions look better pooled, and does that hold within a product?
    Spearman correlation of impressions vs CTR, pooled and averaged within product."""
    c = ct[ct.imp >= min_imp].copy()
    c["ctr"] = c.clk / c.imp
    pooled = c[["imp", "ctr"]].rank().corr().iloc[0, 1]
    c = c[c.groupby("product").creative.transform("count") >= 3]
    within = c.groupby("product").apply(lambda g: g[["imp", "ctr"]].rank().corr().iloc[0, 1], include_groups=False).dropna()
    # within-product: share of products where the most-shown creative also has the best CTR
    top_imp_is_best = c.loc[c.groupby("product").imp.idxmax()].set_index("product").creative.eq(
        c.loc[c.groupby("product").ctr.idxmax()].set_index("product").creative).mean()
    return {"pooled_spearman_imp_ctr": float(pooled), "mean_within_product_spearman": float(within.mean()),
            "products": int(within.size), "most_shown_is_best_ctr_share": float(top_imp_is_best),
            "chance_level_for_3plus_creatives": float((1 / c.groupby("product").creative.count()).mean())}


# ---------- 2. when can a winner be called ----------
def early_call(d, min_total_imp=3000, days=(0, 1, 2, 3, 6), prior=(1.0, 30.0)):
    """For products with enough traffic, the 'final winner' = best smoothed CTR over all 15 days.
    After the first k+1 days, how often is the current leader the final winner? Also: precision when
    we only call it once the leader is ahead with posterior probability >= 0.95 (else 'keep testing')."""
    a0, b0 = prior
    tot = creative_table(d)
    big = tot.groupby("product").imp.sum()
    prods = big[big >= min_total_imp].index
    dd = d[d["product"].isin(prods)]
    tot = tot[tot["product"].isin(prods)]
    rng = np.random.default_rng(SEED)
    rows = []
    for k in days:
        e = dd[dd.day <= k].groupby(["product", "creative"], as_index=False)[["imp", "clk"]].sum()
        e["post"] = (e.clk + a0) / (e.imp + a0 + b0)
        lead = e.loc[e.groupby("product").post.idxmax(), ["product", "creative"]].set_index("product").creative
        # the winner is judged ONLY on later, unseen days (k+1..14), so early and final data never overlap
        later = dd[dd.day > k].groupby(["product", "creative"], as_index=False)[["imp", "clk"]].sum()
        later["post"] = (later.clk + a0) / (later.imp + a0 + b0)
        final = later.loc[later.groupby("product").post.idxmax(), ["product", "creative"]].set_index("product").creative
        hit = (lead == final.reindex(lead.index))
        # posterior prob that the leader beats every other creative (Monte Carlo, 400 draws)
        conf = {}
        for p, g in e.groupby("product"):
            s = rng.beta(g.clk.values[:, None] + a0, (g.imp - g.clk).values[:, None] + b0, size=(len(g), 400))
            conf[p] = (s.argmax(0) == g.post.values.argmax()).mean()
        conf = pd.Series(conf)
        called = conf[conf >= 0.95].index
        rows.append({"days_observed": k + 1, "products": int(len(lead)),
                     "leader_wins_later_days": float(hit.mean()),
                     "share_callable_at_95": float(len(called) / len(lead)),
                     "precision_when_called": float(hit.reindex(called).mean()) if len(called) else None,
                     "median_imp_per_creative": float(e.imp.median())})
    chance = float((1 / tot.groupby("product").creative.count()).mean())
    return {"min_total_imp": min_total_imp, "products": int(len(prods)), "chance_level": chance, "by_day": rows}


# ---------- 3. what is shifting budget worth (replay simulation) ----------
def budget_sim(d, shrink, min_total_imp=3000, daily=200, n_days=15, prior=(1.0, 30.0), reps=3):
    """Simulate a product's creatives with 'true' CTR = their 15-day smoothed CTR, and spend `daily` impressions per day.
    Compare: uniform split, greedy (all to the day-1 leader), Thompson sampling. Report clicks relative to always
    showing the true best (oracle). This is a model of the data, not an online A/B result: see README limits."""
    a0, b0 = prior
    tot = creative_table(d)
    big = tot.groupby("product").imp.sum()
    tot = tot[tot["product"].isin(big[big >= min_total_imp].index)]
    raw = tot.clk / tot.imp
    pm = tot.assign(r=raw).groupby("product").r.transform("mean")
    # observed spread between creatives includes sampling noise; keep only the signal share (from variance_split)
    tot["p"] = (pm + shrink * (raw - pm)).clip(1e-4, 0.99)
    groups = [g.p.values for _, g in tot.groupby("product")]
    res = {"uniform": [], "greedy_after_day1": [], "thompson": [], "oracle": []}
    rng = np.random.default_rng(SEED)
    for _ in range(reps):
        for p in groups:
            K = len(p)
            res["oracle"].append(p.max() * daily * n_days)
            res["uniform"].append(p.mean() * daily * n_days)
            # greedy: day 1 uniform, then everything to the observed leader
            c1 = rng.binomial(daily // K, p)
            res["greedy_after_day1"].append(c1.sum() + p[c1.argmax()] * daily * (n_days - 1))
            # Thompson: each day split impressions by posterior win probability
            S, F, clicks = np.zeros(K), np.zeros(K), 0.0
            for _day in range(n_days):
                w = (rng.beta(S[:, None] + a0, F[:, None] + b0, size=(K, 200)).argmax(0)[None, :] == np.arange(K)[:, None]).mean(1)
                n = rng.multinomial(daily, w)
                c = rng.binomial(n, p)
                S += c; F += n - c; clicks += c.sum()
            res["thompson"].append(clicks)
    o = np.sum(res["oracle"])
    return {"products": len(groups), "daily_impressions": daily, "days": n_days, "reps": reps,
            "clicks_vs_oracle": {k: float(np.sum(v) / o) for k, v in res.items()},
            "lift_vs_uniform": {k: float(np.sum(v) / np.sum(res["uniform"]) - 1) for k, v in res.items()}}


# ---------- 4. weekly summary with alerts ----------
def weekly_summary(d, product, min_imp=200):
    """Week 1 (days 0-6) vs week 2 (days 7-13) for one product: per-creative CTR, change, and an alert only when the
    change is bigger than noise (two-proportion z >= 2.5). This is the shape of a 'guided weekly summary'."""
    g = d[d["product"] == product]
    w = {}
    for name, lo, hi in [("w1", 0, 6), ("w2", 7, 13)]:
        w[name] = g[(g.day >= lo) & (g.day <= hi)].groupby("creative")[["imp", "clk"]].sum()
    t = w["w1"].join(w["w2"], lsuffix="_w1", rsuffix="_w2", how="outer").fillna(0)
    lines, alerts = [], []
    for cr, r in t.iterrows():
        if r.imp_w1 < min_imp or r.imp_w2 < min_imp:
            lines.append(f"- `{cr[:8]}`: not enough traffic to compare ({int(r.imp_w1)} / {int(r.imp_w2)} impressions)")
            continue
        p1, p2 = r.clk_w1 / r.imp_w1, r.clk_w2 / r.imp_w2
        pp = (r.clk_w1 + r.clk_w2) / (r.imp_w1 + r.imp_w2)
        se = np.sqrt(pp * (1 - pp) * (1 / r.imp_w1 + 1 / r.imp_w2)) or 1e-9
        z = (p2 - p1) / se
        lines.append(f"- `{cr[:8]}`: CTR {p1:.2%} -> {p2:.2%} ({int(r.imp_w2)} impressions this week)")
        if abs(z) >= 2.5:
            alerts.append(f"- ALERT `{cr[:8]}` CTR {'fell' if z < 0 else 'rose'} {p1:.2%} -> {p2:.2%} (z = {z:.1f})")
    return "\n".join([f"### Weekly summary, product `{product[:8]}`", *lines, "", "**Alerts**", *(alerts or ["- none (all changes within noise)"])])


def main():
    OUT.mkdir(exist_ok=True)
    d = load()
    ct = creative_table(d)
    res = {"rows": int(len(d)), "products": int(d["product"].nunique()), "creatives": int(len(ct)),
           "overall_ctr": float(d.clk.sum() / d.imp.sum()),
           "variance_split": variance_split(ct), "confounding": pooled_vs_within(ct),
           "early_call": early_call(d)}
    vs = res["variance_split"]
    shrink = vs["within_product_var_after_noise"] / vs["within_product_var_raw"]
    res["budget_sim"] = budget_sim(d, shrink)
    res["budget_sim"]["shrink_factor"] = shrink
    (OUT / "results.json").write_text(json.dumps(res, indent=2))
    # a sample weekly summary for the busiest product
    busiest = ct.groupby("product").imp.sum().idxmax()
    (OUT / "weekly_summary_example.md").write_text(weekly_summary(d, busiest), encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
