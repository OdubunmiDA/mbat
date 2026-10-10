#!/usr/bin/env python3
"""Step 12 - Figures for the README and data descriptor (paper/figures/).

  fig1_national_oud_rx.png      national Medicaid OUD buprenorphine prescriptions per quarter,
                                transmucosal vs extended-release (one axis, two direct-labeled lines)
  fig2_state_rate_heatmap.png   OUD prescriptions per 1,000 Medicaid enrollees (MBES), state x year,
                                one-hue sequential ramp
  fig3_unwinding_index.png      national enrollment and OUD prescriptions indexed to 2023Q1 = 100

Every figure carries a DRAFT stamp until the author has verified the release; regenerate with
--final to remove it (the publish gate refuses DRAFT stamps).
Palette: dataviz reference palette (categorical slots 1-2, blue sequential ramp).
"""
import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "paper", "figures")
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
S1, S2 = "#2a78d6", "#eb6834"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SHORT_SOURCE = "Sources: CMS SDUD and CMS enrollment data; MBAT v1.0 draft."
SOURCE = ("Source: CMS State Drug Utilization Data (2016-2025 as re-released July 2026; 2026Q1 preliminary), "
          "MBAT v1.0 draft. Suppressed SDUD cells contribute zero (lower bound).")


def style(ax):
    ax.set_facecolor(SURF)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def stamp(fig, final):
    if not final:
        fig.text(0.99, 0.985, "DRAFT - not verified", ha="right", va="top", fontsize=9,
                 color="#e34948", fontweight="bold")


def fig1(p, final):
    rel = p[p.data_status != "sdud_not_yet_released"]
    n = rel.groupby("yq")[["rx_oud_transmucosal", "rx_oud_extended"]].sum() / 1e3
    x = np.arange(len(n))
    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=SURF)
    style(ax)
    for col, color, lab in [("rx_oud_transmucosal", S1, "Sublingual / buccal"), ("rx_oud_extended", S2, "Extended-release injection or implant")]:
        y = n[col].values
        ax.plot(x[:-1], y[:-1], color=color, linewidth=2)
        ax.plot(x[-2:], y[-2:], color=color, linewidth=2, linestyle=(0, (2, 2)))
        ax.text(x[-1] + 0.6, y[-1], lab, color=INK, fontsize=9, va="center")
    ax.annotate("2026Q1 preliminary\n(incomplete state submissions)", xy=(x[-1], n.rx_oud_transmucosal.iloc[-1]),
                xytext=(x[-1] - 13, n.rx_oud_transmucosal.iloc[-1] - 650), fontsize=8, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ticks = [i for i, k in enumerate(n.index) if k.endswith("Q1")]
    ax.set_xticks(ticks, [n.index[i][:4] for i in ticks])
    ax.set_xlim(-1, len(n) + 14)
    ax.set_ylim(0, None)
    ax.set_ylabel("Prescriptions per quarter (thousands)", color=INK2, fontsize=9)
    ax.set_title("Medicaid-paid buprenorphine prescriptions for OUD, 50 states + DC", loc="left", color=INK, fontsize=12)
    fig.text(0.01, 0.01, SOURCE, fontsize=7, color=MUTED)
    stamp(fig, final)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(os.path.join(FIG, "fig1_national_oud_rx.png"), dpi=200)
    plt.close(fig)


def fig2(p, final):
    f = p[p.data_status == "sdud_released"]
    a = f.groupby(["state", "year"]).agg(rx=("rx_oud_total", "sum"), en=("mbes_medicaid", "sum"), nq=("mbes_medicaid", "count"))
    a = a[a.nq == 4]
    m = (a.rx / a.en * 1000 / 4).unstack()  # mean quarterly rate per 1,000 enrollees
    m = m.loc[m[2024].sort_values(ascending=False).index] if 2024 in m else m
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    fig, ax = plt.subplots(figsize=(7.5, 11), facecolor=SURF)
    ax.set_facecolor(SURF)
    vmax = float(np.nanpercentile(m.values, 95))  # cap so a few very high states do not wash out the rest
    im = ax.imshow(m.values, aspect="auto", cmap=cmap, interpolation="nearest", vmin=0, vmax=vmax)
    ax.set_yticks(range(len(m)), m.index, fontsize=7.5, color=INK2)
    ax.set_xticks(range(len(m.columns)), m.columns, fontsize=8.5, color=INK2)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(m.columns)), minor=True)
    ax.set_yticks(np.arange(-.5, len(m)), minor=True)
    ax.grid(which="minor", color=SURF, linewidth=1.2)
    ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label(f"OUD buprenorphine prescriptions per 1,000 enrollees per quarter (scale capped at {vmax:.0f}, 95th pct)",
                 fontsize=8, color=INK2)
    cb.ax.tick_params(labelsize=8, colors=INK2, length=0)
    cb.outline.set_visible(False)
    ax.set_title("OUD buprenorphine prescribing rate by state and year\n(sorted by 2024 rate; blank = incomplete enrollment year)",
                 loc="left", fontsize=11, color=INK)
    fig.text(0.01, 0.005, "Denominator: CMS MBES total Medicaid enrollees (available through 2025Q2). " + SHORT_SOURCE,
             fontsize=6.5, color=MUTED)
    stamp(fig, final)
    fig.tight_layout(rect=(0, 0.015, 1, 0.98))
    fig.savefig(os.path.join(FIG, "fig2_state_rate_heatmap.png"), dpi=200)
    plt.close(fig)


def fig3(p, final):
    f = p[(p.year >= 2021) & (p.data_status != "sdud_not_yet_released")]
    full = f.groupby("yq").filter(lambda g: g.pi_medicaid.notna().all())
    n = full.groupby("yq")[["pi_medicaid", "rx_oud_total"]].sum()
    n = n[n.index != "2026Q1"]
    idx = n / n.loc["2023Q1"] * 100
    x = np.arange(len(idx))
    fig, ax = plt.subplots(figsize=(9, 4.4), facecolor=SURF)
    style(ax)
    for col, color, lab in [("pi_medicaid", S1, "Total Medicaid enrollment (CMS PI)"), ("rx_oud_total", S2, "OUD buprenorphine prescriptions")]:
        ax.plot(x, idx[col].values, color=color, linewidth=2)
        ax.text(x[-1] + 0.4, idx[col].values[-1], lab, color=INK, fontsize=9, va="center")
    k = list(idx.index).index("2023Q2")
    ax.axvline(k - 0.5, color=MUTED, linewidth=0.8, linestyle=(0, (3, 3)))
    ax.text(k - 0.4, ax.get_ylim()[1], "Unwinding terminations begin (April 2023)", fontsize=8, color=INK2, va="top")
    ax.axhline(100, color=GRID, linewidth=1)
    ax.set_xticks(x[::4], [i[:4] for i in idx.index[::4]])
    ax.set_xlim(-0.5, len(x) + 7)
    ax.set_ylabel("Index, 2023Q1 = 100", color=INK2, fontsize=9)
    ax.set_title("Medicaid enrollment and buprenorphine prescribing through unwinding", loc="left", color=INK, fontsize=12)
    fig.text(0.01, 0.01, "States with complete PI enrollment in every quarter shown; 2026Q1 excluded (preliminary). " + SHORT_SOURCE,
             fontsize=7, color=MUTED)
    stamp(fig, final)
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    fig.savefig(os.path.join(FIG, "fig3_unwinding_index.png"), dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="omit the DRAFT stamp (only after author verification)")
    a = ap.parse_args()
    os.makedirs(FIG, exist_ok=True)
    p = pd.read_csv(os.path.join(ROOT, "data", "processed", "mbat_panel_state_quarter.csv"))
    fig1(p, a.final)
    fig2(p, a.final)
    fig3(p, a.final)
    print("figures written to", os.path.relpath(FIG, ROOT))


if __name__ == "__main__":
    main()
