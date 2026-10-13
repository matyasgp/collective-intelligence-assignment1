"""Statistics and figures for the report, made from the BehaviorSpace output.

Reads   sweep_results.csv   (experiment decoy-saturation-sweep, one row per run)
        timeseries.csv      (experiment regime-timeseries, one row per tick)
Writes  summary_table_ci.csv            mean and 95% CI of both outcomes for every setting
        <out>/fig_sweep.pdf / .png      heatmap + slices with error bars and tipping points
        <out>/fig_timeseries.pdf / .png one representative run per regime
Usage:  python make_figures.py [out-folder] [--dark]    (default out-folder: latex)
        --dark: light text on the dark slide background (for the presentation; the report uses the default)
"""
import csv
import math
import os
import statistics
import sys
from collections import defaultdict
from statistics import NormalDist

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SWEEP_CSV = "sweep_results.csv"
ARGS = [a for a in sys.argv[1:] if a != "--dark"]
OUT = ARGS[0] if ARGS else "latex"
DARK = "--dark" in sys.argv
SLIDE_BG = "#16181c"                 # background of the presentation slides
if DARK:
    plt.style.use("dark_background")
    plt.rcParams.update({"figure.facecolor": SLIDE_BG, "axes.facecolor": SLIDE_BG, "savefig.facecolor": SLIDE_BG})
LINE = "white" if DARK else "black"  # wave-launch markers in the time series
TIMESERIES_CSV = "timeseries.csv"
SLICES = [(20, "tab:red"), (50, "tab:orange"), (80, "tab:blue")]   # sensor levels in the line plot
COLLAPSE = 3      # tipping point = decoy share where mean bases destroyed first reaches 3 of 4
REGIME_COLORS = ["tab:blue", "tab:orange", "tab:red", "tab:purple", "tab:gray"]   # one per decoy share, low to high
REGIME_NAMES = {0: "holds", 16: "just below tipping", 36: "collapse", 68: "recovering", 84: "too few armed drones"}
plt.rcParams.update({"font.size": 8})


def read_table(path):
    """BehaviorSpace table output -> list of dicts (the first 6 lines are metadata)."""
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f.readlines()[6:]))


def t_975(df):
    """Student t quantile for a two-sided 95% interval (Cornish-Fisher expansion, error < 0.001)."""
    z = NormalDist().inv_cdf(0.975)
    return (z + (z**3 + z) / (4 * df) + (5 * z**5 + 16 * z**3 + 3 * z) / (96 * df**2)
            + (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) / (384 * df**3))


def mean_ci(values):
    """Mean and half-width of its 95% confidence interval."""
    n = len(values)
    return statistics.mean(values), t_975(n - 1) * statistics.stdev(values) / math.sqrt(n)


def tipping_point(points):
    """First decoy share where the mean reaches COLLAPSE (linear interpolation), or None."""
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if y0 >= COLLAPSE:
            return x0
        if y1 >= COLLAPSE:
            return x0 + (COLLAPSE - y0) / (y1 - y0) * (x1 - x0)
    return None


def edges(centres):
    """Cell edges around evenly spaced cell centres (for the heatmap)."""
    step = centres[1] - centres[0]
    return [c - step / 2 for c in centres] + [centres[-1] + step / 2]


# --------------------------------------------------------------- the sweep --
cells = defaultdict(lambda: {"bases": [], "hits": []})
for run in sorted(read_table(SWEEP_CSV), key=lambda r: int(r["[run number]"])):   # runs in launch order
    key = (float(run["decoy-ratio"]), float(run["sensor-discrimination"]))
    cells[key]["bases"].append(float(run["bases-destroyed"]))
    cells[key]["hits"].append(float(run["lethal-hits"]))
decoys = sorted({d for d, s in cells})
sensors = sorted({s for d, s in cells})
bases = {k: mean_ci(v["bases"]) for k, v in cells.items()}
hits = {k: mean_ci(v["hits"]) for k, v in cells.items()}
# The spec asks for 20 repetitions: the CSV also gives the statistics of the first 20 runs of every
# setting (each run has its own random seed). The figures and the report use all 100.
REQUIRED_REPS = 20
bases20 = {k: mean_ci(v["bases"][:REQUIRED_REPS]) for k, v in cells.items()}
hits20 = {k: mean_ci(v["hits"][:REQUIRED_REPS]) for k, v in cells.items()}

with open("summary_table_ci.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["decoy-ratio", "sensor-discrimination", "runs",
                "bases-destroyed-mean", "bases-destroyed-ci95", "lethal-hits-mean", "lethal-hits-ci95",
                "runs-20", "bases-destroyed-mean-20", "bases-destroyed-ci95-20",
                "lethal-hits-mean-20", "lethal-hits-ci95-20"])
    for k in sorted(cells):
        w.writerow([f"{k[0]:g}", f"{k[1]:g}", len(cells[k]["bases"]),
                    f"{bases[k][0]:.3f}", f"{bases[k][1]:.3f}", f"{hits[k][0]:.3f}", f"{hits[k][1]:.3f}",
                    REQUIRED_REPS, f"{bases20[k][0]:.3f}", f"{bases20[k][1]:.3f}",
                    f"{hits20[k][0]:.3f}", f"{hits20[k][1]:.3f}"])

fig, (ax_map, ax_line) = plt.subplots(1, 2, figsize=(8, 2.9), gridspec_kw={"width_ratios": [1, 1.15]})

grid = [[bases[(d, s)][0] for d in decoys] for s in sensors]
mesh = ax_map.pcolormesh(edges(decoys), edges(sensors), grid, cmap="Reds", vmin=0, vmax=4)
fig.colorbar(mesh, ax=ax_map, label="mean bases destroyed (of 4)")
ax_map.set_xlabel("decoy share of wave budget (%)")
ax_map.set_ylabel("decoy recognition (%)")
ax_map.set_title("(a) mean bases destroyed", fontsize=8)

for sensor, color in SLICES:
    means = [bases[(d, sensor)][0] for d in decoys]
    cis = [bases[(d, sensor)][1] for d in decoys]
    ax_line.errorbar(decoys, means, yerr=cis, color=color, marker=".", markersize=4,
                     capsize=2, linewidth=1.2, label=f"recognition {sensor}%")
    tp = tipping_point(list(zip(decoys, means)))
    if tp is not None:
        ax_line.axvline(tp, color=color, linestyle="--", linewidth=0.9)
ax_line.axhline(COLLAPSE, color="gray", linestyle=":", linewidth=0.9)
ax_line.set_xlim(0, 100)
ax_line.set_ylim(0, 4.2)
ax_line.set_xlabel("decoy share of wave budget (%)")
ax_line.set_ylabel("mean bases destroyed (± 95% CI)")
ax_line.set_title(f"(b) dotted: collapse ({COLLAPSE} of 4); dashed: tipping point", fontsize=8)
ax_line.legend(loc="upper right", fontsize=7)
ax_line.grid(alpha=0.3)
fig.tight_layout()
os.makedirs(OUT, exist_ok=True)
fig.savefig(f"{OUT}/fig_sweep.pdf")
fig.savefig(f"{OUT}/fig_sweep.png", dpi=200)

all_ci = [ci for _, ci in bases.values()]
print(f"Sweep: {len(cells)} settings x {len(next(iter(cells.values()))['bases'])} runs")
print(f"  95% CI half-width of bases destroyed: median {statistics.median(all_ci):.2f}, max {max(all_ci):.2f}")
print(f"  95% CI half-width of lethal hits:     median {statistics.median(ci for _, ci in hits.values()):.2f}, "
      f"max {max(ci for _, ci in hits.values()):.2f}")
print(f"Tipping point (mean bases destroyed reaches {COLLAPSE}), baseline at 0% decoys and peak:")
for s in sensors:
    means = [bases[(d, s)] for d in decoys]
    tp = tipping_point([(d, m) for d, (m, _) in zip(decoys, means)])
    peak_d, (peak, peak_ci) = max(zip(decoys, means), key=lambda x: x[1][0])
    print(f"  sensor {s:3.0f}%: tipping {'%5.1f%%' % tp if tp is not None else ' none '}  "
          f"baseline {means[0][0]:.2f} +/- {means[0][1]:.2f}  peak {peak:.2f} +/- {peak_ci:.2f} at {peak_d:g}%  "
          f"lethal hits {hits[(0, s)][0]:.1f} -> {hits[(peak_d, s)][0]:.1f}")

# ------------------------------------------------------------ time series --
ticks = defaultdict(list)
for row in read_table(TIMESERIES_CSV):
    ticks[int(row["[run number]"])].append(row)
regimes = defaultdict(list)
for run, rows in ticks.items():
    regimes[float(rows[0]["decoy-ratio"])].append(run)

def final(run, metric):
    return float(ticks[run][-1][metric])

def representative(runs):
    """The run with the median number of destroyed bases (ties: lethal hits closest to the mean)."""
    median = statistics.median(final(r, "bases-destroyed") for r in runs)
    mean_hits = statistics.mean(final(r, "lethal-hits") for r in runs)
    return min(runs, key=lambda r: (abs(final(r, "bases-destroyed") - median),
                                    abs(final(r, "lethal-hits") - mean_hits), r))

fig, ax_health = plt.subplots(figsize=(8, 1.9))
print("Time series (one representative run per regime; averages over all runs of the regime):")
for (decoy, runs), color in zip(sorted(regimes.items()), REGIME_COLORS):
    run = representative(runs)
    rows = ticks[run]
    t = [int(r["[step]"]) for r in rows]
    ax_health.step(t, [float(r["total-base-health"]) for r in rows], where="post", color=color,
                   label=f"{decoy:g}% decoys: {REGIME_NAMES.get(round(decoy), '')}")
    waves = [int(r["[step]"]) for prev, r in zip(rows, rows[1:]) if r["wave"] != prev["wave"]]
    raining = statistics.mean(float(r["ifelse-value raining? [ 1 ] [ 0 ]"]) for r in rows)
    print(f"  {decoy:4g}% decoys: run {run} destroyed {final(run, 'bases-destroyed'):g} bases | "
          f"regime means: bases destroyed {statistics.mean(final(r, 'bases-destroyed') for r in runs):.2f}, "
          f"armed drones shot down {statistics.mean(final(r, 'lethal-shot-down') for r in runs):.1f}, "
          f"decoys shot down {statistics.mean(final(r, 'decoys-shot-down') for r in runs):.1f} | "
          f"waves at {waves}, raining {raining:.0%} of this run")
for w in waves:
    ax_health.axvline(w, color=LINE, linestyle=":", linewidth=0.8)
ax_health.grid(alpha=0.3)
ax_health.set_ylabel("total base health")
ax_health.set_ylim(0, 420)
ax_health.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=7)   # outside, right of the plot
ax_health.set_xlabel("tick")
fig.tight_layout()
fig.savefig(f"{OUT}/fig_timeseries.pdf")
fig.savefig(f"{OUT}/fig_timeseries.png", dpi=200)
print(f"Wrote summary_table_ci.csv, {OUT}/fig_sweep.pdf/.png, {OUT}/fig_timeseries.pdf/.png")
