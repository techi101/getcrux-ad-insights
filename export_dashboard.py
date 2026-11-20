"""Export the numbers the demo dashboard shows (demo/data.js). Every number comes from the same data and code as analysis.py.
Run after analysis.py: python export_dashboard.py"""
import json
from pathlib import Path
import numpy as np
import analysis as A

ROOT = Path(__file__).resolve().parent


def creative_rows(d, product):
    g = d[d["product"] == product].groupby("creative")[["imp", "clk"]].sum().reset_index()
    g["ctr"] = g.clk / g.imp
    # 95% Wilson interval so the chart shows how sure each CTR is
    z = 1.96
    n, p = g.imp, g.ctr
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    g["lo"], g["hi"] = centre - half, centre + half
    g = g.sort_values("ctr", ascending=False)
    return [{"id": r.creative[:8], "imp": int(r.imp), "clk": int(r.clk), "ctr": float(r.ctr), "lo": float(r.lo), "hi": float(r.hi)}
            for r in g.itertuples()]


def find_alert_product(d, ct, min_imp=1500):
    """A busy product where at least one creative moved more than noise between week 1 and week 2 (z >= 2.5)."""
    busy = ct.groupby("product").imp.sum().sort_values(ascending=False).index[:400]
    for p in busy:
        s = A.weekly_summary(d, p, min_imp=min_imp)
        if "ALERT" in s:
            return p
    return None


def weekly_rows(d, product, min_imp=200):
    g = d[d["product"] == product]
    out = []
    for cr, x in g.groupby("creative"):
        w1 = x[x.day <= 6][["imp", "clk"]].sum()
        w2 = x[(x.day >= 7) & (x.day <= 13)][["imp", "clk"]].sum()
        if w1.imp < min_imp or w2.imp < min_imp:
            continue
        p1, p2 = w1.clk / w1.imp, w2.clk / w2.imp
        pp = (w1.clk + w2.clk) / (w1.imp + w2.imp)
        zz = (p2 - p1) / np.sqrt(pp * (1 - pp) * (1 / w1.imp + 1 / w2.imp))
        out.append({"id": cr[:8], "imp_w1": int(w1.imp), "imp_w2": int(w2.imp), "ctr_w1": float(p1), "ctr_w2": float(p2),
                    "z": float(zz), "alert": bool(abs(zz) >= 2.5)})
    return sorted(out, key=lambda r: -abs(r["z"]))


def main():
    res = json.loads((ROOT / "out" / "results.json").read_text())
    d = A.load()
    ct = A.creative_table(d)
    busiest = ct.groupby("product").imp.sum().idxmax()
    alert_p = find_alert_product(d, ct)
    data = {"summary": {k: res[k] for k in ["rows", "products", "creatives", "overall_ctr"]},
            "variance_split": res["variance_split"], "early_call": res["early_call"], "budget_sim": res["budget_sim"],
            "confounding": res["confounding"],
            "adset": {"product": busiest[:8], "creatives": creative_rows(d, busiest)},
            "weekly": {"product": alert_p[:8] if alert_p else None, "rows": weekly_rows(d, alert_p) if alert_p else []}}
    (ROOT / "demo").mkdir(exist_ok=True)
    (ROOT / "demo" / "data.js").write_text("window.DATA = " + json.dumps(data, indent=1) + ";\n")
    print("adset", busiest[:8], len(data["adset"]["creatives"]), "| weekly", data["weekly"]["product"],
          [(r["id"], round(r["ctr_w1"], 4), round(r["ctr_w2"], 4), round(r["z"], 1)) for r in data["weekly"]["rows"]])


if __name__ == "__main__":
    main()
