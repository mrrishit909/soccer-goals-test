"""Step 6: charts.   ./venv/bin/python charts.py -> charts/00_cover.png, 01_distribution.png, 02_by_tournament.png, 03_windows.png, 04_leave_one_out.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
R = HERE / "results"
INK, DIM, GRID, BG, BLUE, ORANGE, GRAY = "#f2f2f0", "#8a8a87", "#1d1d1d", "#0b0b0b", "#3987e5", "#d95926", "#9a9a96"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
                     "axes.edgecolor": "#3a3a3a", "axes.labelcolor": DIM, "xtick.color": DIM, "ytick.color": DIM,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 13,
                     "axes.titlelocation": "left", "axes.titlepad": 12})


def save(fig, name):
    fig.tight_layout(); fig.savefig(HERE / "charts" / name, dpi=150); plt.close(fig)


def by_tournament(ax):
    b = pd.read_csv(R / "by_tournament.csv")
    for sex, color, label in [("men", BLUE, "men's World Cups"), ("women", ORANGE, "women's World Cups")]:
        d = b[b["sex"] == sex]
        ax.plot(d["year"], d["mean_goals"], color=color, marker="o", linewidth=2.5, label=label)
    ax.annotate("women 2003, 2007:\n3.3 and 3.5, many lopsided games", (2005, 3.41), (2008.5, 3.3), color=INK, fontsize=9, arrowprops={"arrowstyle": "-", "color": DIM})
    ax.annotate("men 2026: 2.96\n(48 teams, 104 matches)", (2026, 2.96), (2014.2, 3.12), color=INK, fontsize=9, arrowprops={"arrowstyle": "-", "color": DIM})
    ax.set_ylim(2.0, 3.7); ax.set_ylabel("goals per match"); ax.set_xticks(range(2002, 2027, 4)); ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="lower left")
    ax.set_title("Average goals per match, by tournament")


def windows(ax):
    t = pd.read_csv(R / "tests.csv"); y = np.arange(len(t))[::-1]
    for col, marker, name in [("p_mannwhitney", "o", "Mann-Whitney"), ("p_welch", "s", "Welch t"), ("p_permutation", "D", "permutation")]:
        ax.scatter(np.maximum(t[col], 1e-4), y, marker=marker, s=46, color={"o": ORANGE, "s": BLUE, "D": GRAY}[marker], label=name, zorder=3)
    ax.set_xscale("log"); ax.set_xlim(8e-5, 1); ax.set_ylim(-0.6, len(t) - 0.4); ax.set_yticks(y); ax.set_yticklabels([f"{a}-{b}" for a, b in zip(t["since"], t["through"])])
    for v in (0.01, 0.05, 0.10):
        ax.axvline(v, color=ORANGE if v == 0.01 else DIM, linestyle="--", linewidth=1)
        ax.text(v * 1.08, len(t) - 0.62, f"{v:.2f}", color=DIM, fontsize=9, ha="left")
    ax.set_xlabel("p-value that women's matches have more goals (log scale; below 0.0001 drawn at the edge)")
    ax.grid(axis="y", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="lower right")
    ax.set_title("The verdict by window: first year to last tournament")


def main():
    (HERE / "charts").mkdir(exist_ok=True)
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={"width_ratios": [1, 1]})
    by_tournament(a); windows(b)
    for ax in (a, b):
        ax.title.set_fontsize(15)
    fig.suptitle("Do women's World Cup matches have more goals? It depends on the window", x=0.01, ha="left", fontsize=20, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "charts" / "00_cover.png", dpi=100); plt.close(fig)

    d = pd.read_csv(R / "goal_distribution.csv"); fig, ax = plt.subplots(figsize=(10, 3.8)); x = np.arange(7)
    for off, sex, color, label in [(-0.2, "men", BLUE, "men (488 matches)"), (0.2, "women", ORANGE, "women (264 matches)")]:
        v = d[d["sex"] == sex].sort_values("g")
        ax.bar(x + off, v["pct"], width=0.38, color=color, label=label)
    ax.set_xticks(x); ax.set_xticklabels(["0", "1", "2", "3", "4", "5", "6 or more"]); ax.set_xlabel("goals in the match"); ax.set_ylabel("% of matches")
    ax.grid(axis="x", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=9)
    ax.set_title("Women's matches: fewer 0-0 and 2-goal games, more 3-goal and 6+ games")
    save(fig, "01_distribution.png")

    fig, ax = plt.subplots(figsize=(10, 3.8)); by_tournament(ax); save(fig, "02_by_tournament.png")
    fig, ax = plt.subplots(figsize=(10, 3.8)); windows(ax); save(fig, "03_windows.png")

    l = pd.read_csv(R / "leave_one_out.csv").sort_values(["left_out_sex", "left_out_year"], ascending=[False, True])
    fig, ax = plt.subplots(figsize=(10, 3.8)); x = np.arange(len(l))
    ax.bar(x, l["p_mannwhitney"], color=[ORANGE if s == "women" else BLUE for s in l["left_out_sex"]], width=0.7)
    for v, c in [(0.10, DIM), (0.05, DIM), (0.01, ORANGE)]:
        ax.axhline(v, color=c, linestyle="--", linewidth=1)
        ax.text(1.008, v, f"{v:.2f}", color=c, fontsize=9, va="center", transform=ax.get_yaxis_transform())
    for i, p in enumerate(l["p_mannwhitney"]):
        ax.text(i, p + 0.004, f"{p:.2f}", ha="center", color=INK, fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([f"{'W' if s == 'women' else 'M'} {y}" for s, y in zip(l["left_out_sex"], l["left_out_year"])], fontsize=9)
    ax.set_ylabel("Mann-Whitney p"); ax.grid(axis="x", visible=False)
    ax.set_xlabel("tournament left out (W = women's, M = men's); all other matches since 2002 kept")
    ax.set_title("Leave one tournament out: women's 2003 or 2007 gone and p is about 0.2")
    save(fig, "04_leave_one_out.png")


if __name__ == "__main__":
    main()
