#!/usr/bin/env python3
"""Generate the statement-validity companion figure for the zkML paper package."""

from __future__ import annotations

import csv
import os
from pathlib import Path

os.environ.setdefault("SOURCE_DATE_EPOCH", "1779667200")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = ROOT / "docs" / "paper" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

STEM = "zkml-statement-validity-boundary-2026-05"

plt.style.use("tableau-colorblind10")
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["STIX Two Text", "Times New Roman", "DejaVu Serif"],
        "font.size": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "zkml-statement-validity-boundary-2026-05",
        "savefig.bbox": "tight",
    }
)


def add_box(ax: plt.Axes, xy: tuple[float, float], width: float, height: float, title: str, body: list[str], color: str) -> None:
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=1.2,
        edgecolor=color,
        facecolor="#FFFFFF",
    )
    ax.add_patch(box)
    ax.text(x + width / 2, y + height - 0.08, title, ha="center", va="top", weight="bold", color=color)
    for i, line in enumerate(body):
        ax.text(x + 0.05, y + height - 0.18 - 0.09 * i, line, ha="left", va="top", color="#222222")


def add_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], label: str) -> None:
    arrow = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14, linewidth=1.2, color="#555555")
    ax.add_patch(arrow)
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2 + 0.05
    ax.text(mid_x, mid_y, label, ha="center", va="bottom", fontsize=8, color="#444444")


def write_tsv() -> None:
    rows = [
        {
            "layer": "raw_proof_verification",
            "question": "Does this proof verify for this verifier relation and public instance?",
            "examples": "proof bytes; verification key; public inputs",
        },
        {
            "layer": "typed_statement_boundary",
            "question": "What is this proof allowed to mean?",
            "examples": "model; input; output; policy; table identity; verifier domain",
        },
        {
            "layer": "application_claim",
            "question": "Which deployment event or decision may consume the artifact?",
            "examples": "receipt id; action policy; audit record; settlement context",
        },
    ]
    tsv_path = FIGURE_DIR / f"{STEM}.tsv"
    with tsv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["layer", "question", "examples"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {tsv_path}")


def normalize_svg(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.4, 2.9), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    add_box(
        ax,
        (0.03, 0.25),
        0.23,
        0.5,
        "Raw proof",
        ["proof bytes", "verification key", "public instance"],
        "#4477AA",
    )
    add_box(
        ax,
        (0.37, 0.18),
        0.29,
        0.64,
        "Typed statement boundary",
        ["model and input", "output and policy", "table identity", "verifier domain"],
        "#117733",
    )
    add_box(
        ax,
        (0.77, 0.25),
        0.21,
        0.5,
        "Application claim",
        ["receipt meaning", "allowed action", "audit context"],
        "#AA4499",
    )

    add_arrow(ax, (0.275, 0.5), (0.36, 0.5), "verify")
    add_arrow(ax, (0.67, 0.5), (0.76, 0.5), "bind")

    ax.text(
        0.5,
        0.06,
        "Proof validity answers a cryptographic question. Statement validity binds the proof to the claim an application consumes.",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#333333",
    )

    write_tsv()
    for ext in ("pdf", "svg", "png"):
        path = FIGURE_DIR / f"{STEM}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300)
        else:
            fig.savefig(path)
            if ext == "svg":
                normalize_svg(path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
