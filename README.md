# Do women's World Cup matches have more goals than men's?

A classic teaching question, answered with every World Cup match since 2002 and then pushed on: how much does the answer depend on
which tournaments you include, which test you use and which significance level you pick?

The question follows DataCamp's "Hypothesis Testing with Men's and Women's Soccer Matches" project. The data is the open
international-results dataset on GitHub, not a course copy, and it includes the 2026 men's tournament.

Build log: https://mrrishit909.github.io/projects/soccer-goals-test/

## Data

The `martj42` "international results" datasets on GitHub, men's (49,547 matches, 1872 to 2026) and women's (11,650 matches,
1956 to 2026), both CC0, pulled 2026-10-03. Kept: rows whose tournament is "FIFA World Cup" (the finals, not qualifiers).
Goals are both teams' goals in the match. Scores include extra time, not shootouts. `download.py` fetches the files; they are
not committed. `results/pull.json` records the pull.

```
./venv/bin/pip install pandas scipy matplotlib certifi      # in a venv
./venv/bin/python download.py    # data/men.csv, data/women.csv
./venv/bin/python analyze.py     # results/*.csv, headline.json
./venv/bin/python check.py
./venv/bin/python charts.py
```

## Steps

1. **Download** both files.
2. **Matches.** World Cup finals matches from 1991 (the first women's World Cup); the main window is 2002 on: 488 men's matches
   (2002 to 2026) and 264 women's (2003 to 2023). Goals per match, and the margin (winner's goals minus loser's).
3. **Tests.** One-sided, women's more than men's: Mann-Whitney U (goal counts aren't normal), Welch t and a permutation test of the
   mean difference (10,000 shuffles of the pooled goals). Run over six windows: first year (2002 or 1991) times last tournament
   (2019, 2023, 2026). A bootstrap interval for the mean difference in the main window.
4. **Leave one tournament out** (13 reruns of the Mann-Whitney).
5. **Check.** `check.py` recomputes 110 numbers with plain Python: Mann-Whitney rebuilt by counting every pair, the permutation
   test and bootstrap re-simulated with another random generator and more draws, means and shares from csv rows.
6. **Charts.**

## Results

| Matches through | Women | Men | Difference | Mann-Whitney p | Welch p | Permutation p |
|---|---|---|---|---|---|---|
| 2019 (men 2002-18) | 2.98 | 2.48 | +0.50 | 0.004 | 0.002 | 0.001 |
| 2023 (men 2002-22) | 2.88 | 2.51 | +0.37 | 0.023 | 0.008 | 0.007 |
| 2026 (all) | 2.88 | 2.61 | +0.27 | 0.083 | 0.034 | 0.029 |

- Goals per match, women 2.88 and men 2.61 over all matches since 2002. The bootstrap 95% interval for the difference is
  -0.01 to +0.57 goals.
- **The verdict depends on the choices.** At 0.01, only the 2019 window says yes (and two of three tests for 2023). At 0.05 the
  tests disagree for the full window (Welch and permutation yes, Mann-Whitney no). At 0.10 all agree. Starting in 1991 instead
  of 2002 adds the very lopsided early women's tournaments, and then every test gives p of 0.001 or less.
- **The gap is mostly two tournaments.** Women's 2003 and 2007 averaged 3.34 and 3.47 goals (mean margin 2.4 and 2.3 goals); the
  next four averaged 2.56 to 2.81. Leave out either and the Mann-Whitney p is about 0.20. Leave out the men's 2026 tournament
  (2.96 goals, 48 teams) and it falls to 0.023.
- **Where the extra goals come from:** 25.8% of women's matches were decided by three or more goals, against 15.4% of men's; the
  mean margin is 1.87 against 1.39. Women's matches have fewer 2-goal games (17.8% vs 23.8%).

## Not done, and caveats

- Matches in one tournament share teams and conditions, so they aren't independent; the tests treat them as if they were, and
  the p-values are probably too small.
- The windows are not independent tests of the same thing, and trying six of them is exactly the kind of choice a single
  p-value hides. That is the point, not a recommendation to pick one.
- Scores include extra time, and the data has no stage, so group games and knockouts can't be separated.
- Nothing here models why: quality gaps between teams, format changes (32 to 48 teams) and tactics are not in the data.
