"""Step 5: the project's check. Recompute everything from the raw CSVs with plain Python (csv, math, random) and require it to agree
with results/. Mann-Whitney is rebuilt by counting every pair (no scipy.mannwhitneyu), the permutation test and the bootstrap use a
different random generator and more draws than analyze.py, and the means come from csv rows, not pandas.

    ./venv/bin/python check.py
"""
import csv
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).parent
R = HERE / "results"
random.seed(1)


def goals(sex, lo, hi, skip=None):
    out = []
    for r in csv.DictReader(open(HERE / "data" / f"{sex}.csv")):
        y = int(r["date"][:4])
        if r["tournament"] == "FIFA World Cup" and lo <= y <= hi and (skip is None or skip != (sex, y)):
            out.append(int(r["home_score"]) + int(r["away_score"]))
    return out


def mannwhitney_greater(a, b):
    """U by counting pairs; one-sided normal p with tie and continuity corrections (what 'greater' means for a)."""
    u = sum((x > y) + 0.5 * (x == y) for x in a for y in b)
    n1, n2 = len(a), len(b)
    n = n1 + n2
    ties = {}
    for v in a + b:
        ties[v] = ties.get(v, 0) + 1
    sigma = math.sqrt(n1 * n2 / 12 * ((n + 1) - sum(t ** 3 - t for t in ties.values()) / (n * (n - 1))))
    z = (u - n1 * n2 / 2 - 0.5) / sigma
    return u, 0.5 * math.erfc(z / math.sqrt(2))


def welch_t(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    return (ma - mb) / math.sqrt(va / len(a) + vb / len(b)), (va / len(a) + vb / len(b)) ** 2 / ((va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))


def main():
    n = 0

    def close(label, got, want, tol):
        nonlocal n
        n += 1
        assert abs(got - want) <= tol, f"{label}: recount {got} != results {want}"

    for r in csv.DictReader(open(R / "by_tournament.csv")):       # per-tournament means, counts, share of 5+ goal matches
        g = goals(r["sex"], int(r["year"]), int(r["year"]))
        close(f"{r['sex']} {r['year']} matches", len(g), int(r["matches"]), 0)
        close(f"{r['sex']} {r['year']} mean", sum(g) / len(g), float(r["mean_goals"]), 0.0051)
        close(f"{r['sex']} {r['year']} 5+", 100 * sum(x >= 5 for x in g) / len(g), float(r["pct_5plus"]), 0.0051)

    for r in csv.DictReader(open(R / "by_sex.csv")):               # whole-sample descriptives (margin = winner's goals minus loser's)
        g = goals(r["sex"], 2002, 2026)
        mg = [abs(int(x["home_score"]) - int(x["away_score"])) for x in csv.DictReader(open(HERE / "data" / f"{r['sex']}.csv"))
              if x["tournament"] == "FIFA World Cup" and int(x["date"][:4]) >= 2002]
        s = sorted(g)
        close(f"{r['sex']} matches", len(g), int(r["matches"]), 0)
        close(f"{r['sex']} mean goals", sum(g) / len(g), float(r["mean_goals"]), 0.0051)
        close(f"{r['sex']} median goals", (s[(len(s) - 1) // 2] + s[len(s) // 2]) / 2, float(r["median_goals"]), 0)
        close(f"{r['sex']} mean margin", sum(mg) / len(mg), float(r["mean_margin"]), 0.0051)
        close(f"{r['sex']} margin 3+", 100 * sum(x >= 3 for x in mg) / len(mg), float(r["pct_margin_3plus"]), 0.0051)
        close(f"{r['sex']} 5+ goals", 100 * sum(x >= 5 for x in g) / len(g), float(r["pct_5plus_goals"]), 0.0051)

    from scipy import stats                                       # only for the t distribution's tail
    for r in csv.DictReader(open(R / "tests.csv")):
        lo, hi = int(r["since"]), int(r["through"])
        w, m = goals("women", lo, hi), goals("men", lo, hi)
        tag = f"{lo}-{hi}"
        close(tag + " n women", len(w), int(r["n_women"]), 0)
        close(tag + " n men", len(m), int(r["n_men"]), 0)
        close(tag + " diff", sum(w) / len(w) - sum(m) / len(m), float(r["diff"]), 1e-9)
        close(tag + " mannwhitney p", mannwhitney_greater(w, m)[1], float(r["p_mannwhitney"]), 1e-9)
        t, df = welch_t(w, m)
        close(tag + " welch p", stats.t.sf(t, df), float(r["p_welch"]), 1e-9)

    head = json.load(open(R / "headline.json"))                  # headline window: re-simulate with another generator, 20,000 draws
    w, m = goals("women", 2002, 2026), goals("men", 2002, 2026)
    pooled, hit = w + m, 0
    for _ in range(20_000):
        random.shuffle(pooled)
        hit += sum(pooled[:len(w)]) / len(w) - sum(pooled[len(w):]) / len(m) >= head["diff"]
    close("permutation p (Monte Carlo)", (1 + hit) / 20_001, head["p_permutation"], 0.01)
    boot = sorted(sum(random.choices(w, k=len(w))) / len(w) - sum(random.choices(m, k=len(m))) / len(m) for _ in range(20_000))
    close("bootstrap low", boot[int(0.025 * len(boot))], head["ci_low"], 0.04)
    close("bootstrap high", boot[int(0.975 * len(boot))], head["ci_high"], 0.04)

    for r in csv.DictReader(open(R / "leave_one_out.csv")):
        skip = (r["left_out_sex"], int(r["left_out_year"]))
        a, b = goals("women", 2002, 2026, skip), goals("men", 2002, 2026, skip)
        close(f"without {skip} diff", sum(a) / len(a) - sum(b) / len(b), float(r["diff"]), 0.00006)
        close(f"without {skip} p", mannwhitney_greater(a, b)[1], float(r["p_mannwhitney"]), 0.00006)
    print(f"check.py: {n} recomputed numbers agree with results/")


if __name__ == "__main__":
    main()
