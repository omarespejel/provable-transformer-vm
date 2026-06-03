#!/usr/bin/env python3
"""Generate paper figures for proof-pressure boundary selection.

The figures are intentionally driven by checked repository TSV evidence rather
than hand-entered plotting rows. They summarize proof-byte scaling and the
opening/decommitment mechanism behind the observed savings; they do not encode
or imply a proving-speed win.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

os.environ.setdefault("SOURCE_DATE_EPOCH", "1779667200")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = ROOT / "docs" / "paper" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

MAIN_EVIDENCE_TSV = (
    ROOT
    / "docs"
    / "engineering"
    / "evidence"
    / "zkai-proof-pressure-main-evidence-2026-05.tsv"
)
SLOPE_TABLE_TSV = (
    ROOT
    / "docs"
    / "engineering"
    / "evidence"
    / "zkai-proof-pressure-slope-table-2026-05.tsv"
)
SECTION_DELTA_TSV = (
    ROOT
    / "docs"
    / "engineering"
    / "evidence"
    / "zkai-attention-kv-fused-softmax-table-section-delta-2026-05.tsv"
)
MLP_ATTRIBUTION_TSV = (
    ROOT
    / "docs"
    / "engineering"
    / "evidence"
    / "zkai-attention-derived-d128-mlp-fusion-attribution-2026-05.tsv"
)

SEQUENCE_ROW_ORDER = (
    "d64_h2_seq32_to_seq64",
    "d64_h4_seq32_to_seq64",
    "d128_h2_seq32_to_seq64",
    "d128_h4_seq32_to_seq64",
)
SEQUENCE_LABELS = {
    "d64_h2_seq32_to_seq64": "d64 h2",
    "d64_h4_seq32_to_seq64": "d64 h4",
    "d128_h2_seq32_to_seq64": "d128 h2",
    "d128_h4_seq32_to_seq64": "d128 h4",
}
SLOPE_ROW_ORDER = (
    "d64_h1_to_h4_seq16_head_axis",
    "d64_h2_seq32_to_seq64_sequence_axis",
    "d64_h4_seq32_to_seq64_sequence_axis",
    "d128_h2_seq32_to_seq64_sequence_axis",
    "d128_h4_seq32_to_seq64_sequence_axis",
    "d64_to_d128_h1_seq16_width_axis",
    "d64_to_d128_h2_seq32_width_axis",
    "d128_to_d256_h2_seq32_width_axis",
)
SLOPE_LABELS = {
    "d64_h1_to_h4_seq16_head_axis": "d64 seq16\nh1 to h4",
    "d64_h2_seq32_to_seq64_sequence_axis": "d64 h2\nseq32 to 64",
    "d64_h4_seq32_to_seq64_sequence_axis": "d64 h4\nseq32 to 64",
    "d128_h2_seq32_to_seq64_sequence_axis": "d128 h2\nseq32 to 64",
    "d128_h4_seq32_to_seq64_sequence_axis": "d128 h4\nseq32 to 64",
    "d64_to_d128_h1_seq16_width_axis": "h1 seq16\nd64 to 128",
    "d64_to_d128_h2_seq32_width_axis": "h2 seq32\nd64 to 128",
    "d128_to_d256_h2_seq32_width_axis": "h2 seq32\nd128 to 256",
}

COLORS = {
    "lookup": "#0072B2",
    "trace": "#009E73",
    "fused": "#D55E00",
    "split": "#999999",
    "head": "#44AA99",
    "sequence": "#4477AA",
    "width": "#CC6677",
    "opening": "#117733",
    "other": "#88CCEE",
}


plt.style.use("tableau-colorblind10")
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "zkai-proof-pressure-boundaries-2026-05",
        "savefig.bbox": "tight",
    }
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def float_field(row: dict[str, str], key: str) -> float:
    value = row.get(key, "").strip()
    if not value:
        raise ValueError(f"missing numeric field {key!r} in row {row!r}")
    return float(value)


def write_figure(fig: plt.Figure, stem: str) -> None:
    pdf_path = FIGURE_DIR / f"{stem}.pdf"
    svg_path = FIGURE_DIR / f"{stem}.svg"
    png_path = FIGURE_DIR / f"{stem}.png"
    fig.savefig(pdf_path)
    fig.savefig(svg_path)
    normalize_svg(svg_path)
    fig.savefig(png_path, dpi=300)
    print(f"wrote {pdf_path}")
    print(f"wrote {svg_path}")
    print(f"wrote {png_path}")


def normalize_svg(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")


def write_tsv(stem: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    tsv_path = FIGURE_DIR / f"{stem}.tsv"
    with tsv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"wrote {tsv_path}")


def ordered_rows(rows: list[dict[str, str]], key: str, order: tuple[str, ...]) -> list[dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    duplicates: list[str] = []
    for row_number, row in enumerate(rows, start=2):
        if key not in row:
            raise SystemExit(f"missing key {key!r} in TSV row {row_number}: {row!r}")
        row_id = row[key]
        if row_id in by_id:
            duplicates.append(row_id)
            continue
        by_id[row_id] = row
    if duplicates:
        raise SystemExit(f"duplicate {key!r} values in TSV: {sorted(set(duplicates))}")
    missing = [row_id for row_id in order if row_id not in by_id]
    if missing:
        raise SystemExit(f"missing expected rows in TSV: {missing}")
    return [by_id[row_id] for row_id in order]


def render_growth_factor_figure() -> None:
    rows = ordered_rows(read_tsv(MAIN_EVIDENCE_TSV), "row_id", SEQUENCE_ROW_ORDER)
    labels = [SEQUENCE_LABELS[row["row_id"]] for row in rows]
    lookup = [float_field(row, "lookup_growth") for row in rows]
    trace = [float_field(row, "trace_growth") for row in rows]
    fused = [float_field(row, "fused_proof_growth") for row in rows]

    x = list(range(len(rows)))
    width = 0.24
    fig, ax = plt.subplots(figsize=(7.2, 3.4), constrained_layout=True)
    bars = [
        ax.bar([i - width for i in x], lookup, width, label="Lookup claims", color=COLORS["lookup"]),
        ax.bar(x, trace, width, label="Trace rows", color=COLORS["trace"]),
        ax.bar([i + width for i in x], fused, width, label="Fused proof payload bytes", color=COLORS["fused"]),
    ]

    ax.axhline(1.0, color="#555555", linewidth=0.8, linestyle=":")
    ax.set_ylabel("Growth factor, seq32 to seq64")
    ax.set_xlabel("Checked sequence-axis profile")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 4.55)
    ax.grid(axis="y", color="#BBBBBB", linewidth=0.6, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, ncols=3, loc="upper center", bbox_to_anchor=(0.5, 1.18))

    write_tsv(
        "proof-pressure-growth-factors-2026-05",
        ["row_id", "label", "lookup_growth", "trace_growth", "fused_proof_growth"],
        [
            {
                "row_id": row["row_id"],
                "label": label,
                "lookup_growth": f"{lookup_growth:.6f}",
                "trace_growth": f"{trace_growth:.6f}",
                "fused_proof_growth": f"{fused_growth:.6f}",
            }
            for row, label, lookup_growth, trace_growth, fused_growth in zip(
                rows, labels, lookup, trace, fused
            )
        ],
    )

    for bar_group in bars:
        for bar in bar_group:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.08,
                f"{height:.2f}x",
                ha="center",
                va="bottom",
                fontsize=7,
                rotation=0,
            )

    write_figure(fig, "proof-pressure-growth-factors-2026-05")


def render_boundary_selection_figure() -> None:
    rows = ordered_rows(read_tsv(SLOPE_TABLE_TSV), "row_id", SLOPE_ROW_ORDER)
    labels = [SLOPE_LABELS[row["row_id"]] for row in rows]
    ratios = [float_field(row, "target_fused_to_split_ratio") for row in rows]
    savings = [int(float_field(row, "target_saving_bytes")) for row in rows]
    axes = [row["axis"] for row in rows]
    colors = [COLORS["sequence"] if axis == "sequence" else COLORS[axis] for axis in axes]

    fig, ax = plt.subplots(figsize=(7.6, 3.8), constrained_layout=True)
    x = list(range(len(rows)))
    ax.scatter(x, ratios, s=70, c=colors, edgecolor="#222222", linewidth=0.5, zorder=3)
    ax.plot(x, ratios, color="#777777", linewidth=0.8, alpha=0.45, zorder=2)
    ax.axhline(1.0, color="#222222", linewidth=1.0, linestyle="--")
    ax.set_ylabel("Fused proof payload bytes / matched split frontier")
    ax.set_xlabel("Boundary stress row")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylim(0.84, 1.01)
    ax.grid(axis="y", color="#BBBBBB", linewidth=0.6, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for i, (ratio, saving) in enumerate(zip(ratios, savings)):
        ax.text(
            i,
            ratio - 0.008,
            f"{saving:,} B",
            ha="center",
            va="top",
            fontsize=7,
            color="#333333",
        )

    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["head"], markeredgecolor="#222222", label="Head axis", markersize=7),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["sequence"], markeredgecolor="#222222", label="Sequence axis", markersize=7),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["width"], markeredgecolor="#222222", label="Width axis", markersize=7),
    ]
    ax.legend(handles=handles, frameon=False, ncols=3, loc="upper center", bbox_to_anchor=(0.5, 1.18))
    write_tsv(
        "proof-pressure-boundary-selection-2026-05",
        ["row_id", "label", "axis", "target_fused_to_split_ratio", "target_saving_bytes"],
        [
            {
                "row_id": row["row_id"],
                "label": label.replace("\n", " "),
                "axis": axis,
                "target_fused_to_split_ratio": f"{ratio:.6f}",
                "target_saving_bytes": saving,
            }
            for row, label, axis, ratio, saving in zip(rows, labels, axes, ratios, savings)
        ],
    )
    write_figure(fig, "proof-pressure-boundary-selection-2026-05")


def render_mechanism_figure() -> None:
    section_rows = read_tsv(SECTION_DELTA_TSV)
    if not section_rows:
        raise SystemExit(f"SECTION_DELTA_TSV is empty: {SECTION_DELTA_TSV}")
    total_saving = sum(int(float_field(row, "fused_saves_vs_source_plus_sidecar_bytes")) for row in section_rows)
    opening_saving = sum(int(float_field(row, "opening_bucket_savings_bytes")) for row in section_rows)
    non_opening_saving = total_saving - opening_saving
    if total_saving <= 0:
        raise SystemExit(
            "non-positive attention total saving from "
            f"{SECTION_DELTA_TSV}: total_saving={total_saving}, "
            f"opening_saving={opening_saving}"
        )

    mlp_rows = read_tsv(MLP_ATTRIBUTION_TSV)
    if not mlp_rows:
        raise SystemExit(f"MLP_ATTRIBUTION_TSV is empty: {MLP_ATTRIBUTION_TSV}")
    mlp_row = mlp_rows[0]
    mlp_total = int(float_field(mlp_row, "typed_saving_vs_separate_bytes"))
    mlp_opening = int(float_field(mlp_row, "opening_plumbing_saved_bytes"))
    mlp_non_opening = mlp_total - mlp_opening
    if mlp_total <= 0:
        raise SystemExit(
            "non-positive MLP total saving from "
            f"{MLP_ATTRIBUTION_TSV}: mlp_total={mlp_total}, "
            f"mlp_opening={mlp_opening}"
        )

    labels = ["Attention + LogUp\nserialized section delta", "d128 MLP-side\nlocal typed accounting"]
    opening_values = [opening_saving, mlp_opening]
    other_values = [non_opening_saving, mlp_non_opening]
    totals = [total_saving, mlp_total]

    fig, ax = plt.subplots(figsize=(6.4, 3.4), constrained_layout=True)
    x = list(range(len(labels)))
    ax.bar(x, opening_values, color=COLORS["opening"], label="Opening and decommitment material")
    ax.bar(x, other_values, bottom=opening_values, color=COLORS["other"], label="Other saved bytes")
    ax.set_ylabel("Saved bytes")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", color="#BBBBBB", linewidth=0.6, alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncols=2)

    for i, (opening, total) in enumerate(zip(opening_values, totals)):
        share = opening / total
        ax.text(
            i,
            total + max(totals) * 0.035,
            f"{share:.1%} opening",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#333333",
        )
        ax.text(
            i,
            opening / 2,
            f"{opening:,}",
            ha="center",
            va="center",
            fontsize=8,
            color="white",
        )

    write_tsv(
        "proof-pressure-opening-mechanism-2026-05",
        ["surface", "opening_saved_bytes", "other_saved_bytes", "total_saved_bytes", "opening_share"],
        [
            {
                "surface": label.replace("\n", " "),
                "opening_saved_bytes": opening,
                "other_saved_bytes": other,
                "total_saved_bytes": total,
                "opening_share": f"{opening / total:.6f}",
            }
            for label, opening, other, total in zip(labels, opening_values, other_values, totals)
        ],
    )
    write_figure(fig, "proof-pressure-opening-mechanism-2026-05")


def main() -> None:
    render_growth_factor_figure()
    render_boundary_selection_figure()
    render_mechanism_figure()


if __name__ == "__main__":
    main()
