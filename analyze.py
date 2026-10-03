"""Steps 2-4: World Cup matches since 2002, then the question from every angle.

    ./venv/bin/python analyze.py
        -> results/matches.csv  by_sex.csv  by_tournament.csv  goal_distribution.csv  tests.csv  headline.json  perm_null.csv  leave_one_out.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).parent
R = HERE / "results"
SEED, PERMS = 0, 10_000


def load(sex):
    """Step 2. FIFA World Cup finals matches only (not qualifiers), 'goals' = both teams' goals in the match."""
    d = pd.read_csv(HERE / "data" / f"{sex}.csv")
    d = d[d["tournament"] == "FIFA World Cup"].copy()
    d["sex"], d["year"] = sex, d["date"].str[:4].astype(int)
    d["goals"] = d["home_score"] + d["away_score"]
    d["margin"] = (d["home_score"] - d["away_score"]).abs()
    return d[["sex", "date", "year", "home_team", "away_team", "home_score", "away_score", "goals", "margin"]]


def tests(women, men, rng):
    """One-sided: do women's matches have MORE goals? Mann-Whitney U (the brief's test), Welch t, permutation of the mean difference."""
    diff = women.mean() - men.mean()
    allg, nw = np.concatenate([women, men]), len(women)
    null = np.empty(PERMS)
    for i in range(PERMS):
        p = rng.permutation(allg)
        null[i] = p[:nw].mean() - p[nw:].mean()
    return {"n_women": len(women), "n_men": len(men), "mean_women": women.mean(), "mean_men": men.mean(), "diff": diff,
            "p_mannwhitney": stats.mannwhitneyu(women, men, alternative="greater").pvalue,
            "p_welch": stats.ttest_ind(women, men, equal_var=False, alternative="greater").pvalue,
            "p_permutation": (1 + (null >= diff).sum()) / (1 + PERMS)}, null


def main():
    R.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    m = pd.concat([load("men"), load("women")])
    m = m[m["year"] >= 1991]                                          # first women's World Cup; windows below cut it further
    m.to_csv(R / "matches.csv", index=False)
    since = m[m["year"] >= 2002]

    # Step 2: what the matches look like
    bt = since.groupby(["sex", "year"]).agg(matches=("goals", "size"), mean_goals=("goals", "mean"), mean_margin=("margin", "mean"),
                                           pct_5plus=("goals", lambda x: 100 * (x >= 5).mean())).round(2).reset_index()
    bt.to_csv(R / "by_tournament.csv", index=False)
    bs = since.groupby("sex").agg(matches=("goals", "size"), mean_goals=("goals", "mean"), median_goals=("goals", "median"), mean_margin=("margin", "mean"),
                                  pct_margin_3plus=("margin", lambda x: 100 * (x >= 3).mean()), pct_5plus_goals=("goals", lambda x: 100 * (x >= 5).mean())).round(2).reset_index()
    bs.to_csv(R / "by_sex.csv", index=False)
    dist = since.assign(g=since["goals"].clip(upper=6)).groupby(["sex", "g"]).size().rename("matches").reset_index()
    dist["pct"] = (100 * dist["matches"] / dist.groupby("sex")["matches"].transform("sum")).round(1)
    dist.to_csv(R / "goal_distribution.csv", index=False)

    # Step 3: the same question over six windows (start year x last tournament included)
    rows = []
    for start in (2002, 1991):
        for end in (2019, 2023, 2026):
            w = m[(m["sex"] == "women") & m["year"].between(start, end)]["goals"].to_numpy()
            x = m[(m["sex"] == "men") & m["year"].between(start, end)]["goals"].to_numpy()
            t, null = tests(w, x, rng)
            rows.append({"since": start, "through": end, **t})
            if (start, end) == (2002, 2026):
                headline, headline_null = t, null
    pd.DataFrame(rows).to_csv(R / "tests.csv", index=False)
    pd.DataFrame({"diff": headline_null}).round(4).to_csv(R / "perm_null.csv", index=False)
    w = since[since["sex"] == "women"]["goals"].to_numpy(); x = since[since["sex"] == "men"]["goals"].to_numpy()
    boot = np.array([rng.choice(w, len(w)).mean() - rng.choice(x, len(x)).mean() for _ in range(PERMS)])
    headline.update(ci_low=np.percentile(boot, 2.5), ci_high=np.percentile(boot, 97.5))
    json.dump({k: float(v) for k, v in headline.items()}, open(R / "headline.json", "w"), indent=2)

    # Step 4: leave one tournament out (all matches since 2002)
    loo = []
    for (sex, year), _ in since.groupby(["sex", "year"]):
        k = since[~((since["sex"] == sex) & (since["year"] == year))]
        a, b = k[k["sex"] == "women"]["goals"], k[k["sex"] == "men"]["goals"]
        loo.append({"left_out_sex": sex, "left_out_year": year, "diff": a.mean() - b.mean(),
                    "p_mannwhitney": stats.mannwhitneyu(a, b, alternative="greater").pvalue})
    pd.DataFrame(loo).round(4).to_csv(R / "leave_one_out.csv", index=False)

    print(bs.to_string(index=False)); print(bt.to_string(index=False)); print(pd.DataFrame(rows).round(4).to_string(index=False))
    print({k: round(float(v), 4) for k, v in headline.items()}); print(pd.DataFrame(loo).round(4).to_string(index=False))
    print(dist.to_string(index=False))


if __name__ == "__main__":
    main()
