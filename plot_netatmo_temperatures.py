#!/usr/bin/env python3
"""
Generate temperature plots for all rooms/modules from Netatmo data stored in IBM Db2.

Requirements:
  pip install sqlalchemy ibm_db ibm_db_sa
  Optional (for PNG output): matplotlib

Configuration (environment variables, same style as netatmo_to_db2.py):
  DB2_HOST       - e.g. localhost
  DB2_PORT       - e.g. 50050
  DB2_DATABASE   - e.g. dbcdw
  DB2_USER       - e.g. db2inst1
  DB2_PASSWORD   - db password
  DB2_SCHEMA     - (optional) schema, e.g. DB2INST1
  DB2_TABLE      - (optional) table name, default NETATMO_MEASURES

Usage:
  python plot_netatmo_temperatures.py
  python plot_netatmo_temperatures.py --outdir /tmp/opencode/netatmo_plots
  python plot_netatmo_temperatures.py --format svg
  python plot_netatmo_temperatures.py --format png   # requires matplotlib
  python plot_netatmo_temperatures.py --combined      # also create one combined plot
"""
from __future__ import annotations

import argparse
import datetime
import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text


def env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def qualified_table_name() -> str:
    schema = env("DB2_SCHEMA")
    table = env("DB2_TABLE", "NETATMO_MEASURES")
    if schema:
        return f"{schema}.{table}"
    return table


def make_engine():
    host = env("DB2_HOST", required=True)
    port = env("DB2_PORT", required=True)
    db = env("DB2_DATABASE", required=True)
    user = env("DB2_USER", required=True)
    pwd = env("DB2_PASSWORD", required=True)
    url = f"ibm_db_sa://{user}:{pwd}@{host}:{port}/{db}"
    return create_engine(url, pool_pre_ping=True)


def safe_filename(s: str) -> str:
    s = (s or "unknown").strip()
    s = re.sub(r"[^\w\-\.]+", "_", s, flags=re.UNICODE)
    return s.strip("_") or "room"


def fetch_modules(engine, table: str) -> List[Dict[str, Any]]:
    q = text(f"""
        SELECT MODULE_NAME, MODULE_TYPE, MODULE_ID,
               COUNT(*) AS N,
               MIN(MEASURE_TIME_UTC) AS MIN_T,
               MAX(MEASURE_TIME_UTC) AS MAX_T
        FROM {table}
        WHERE TEMPERATURE IS NOT NULL
        GROUP BY MODULE_NAME, MODULE_TYPE, MODULE_ID
        ORDER BY MODULE_NAME
    """)
    with engine.connect() as conn:
        rows = conn.execute(q).mappings().all()
    return [dict(r) for r in rows]


def fetch_series(engine, table: str, module_id: Optional[str], module_name: Optional[str]) -> List[Tuple[datetime.datetime, float]]:
    # Prefer module_id for uniqueness; fall back to module_name
    if module_id:
        q = text(f"""
            SELECT MEASURE_TIME_UTC, TEMPERATURE
            FROM {table}
            WHERE MODULE_ID = :mid AND TEMPERATURE IS NOT NULL
            ORDER BY MEASURE_TIME_UTC
        """)
        params = {"mid": module_id}
    else:
        q = text(f"""
            SELECT MEASURE_TIME_UTC, TEMPERATURE
            FROM {table}
            WHERE MODULE_NAME = :mname AND TEMPERATURE IS NOT NULL
            ORDER BY MEASURE_TIME_UTC
        """)
        params = {"mname": module_name}
    with engine.connect() as conn:
        rows = conn.execute(q, params).all()
    out = []
    for t, v in rows:
        if t is None or v is None:
            continue
        if isinstance(t, str):
            try:
                t = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
        if hasattr(t, "to_pydatetime"):
            t = t.to_pydatetime()
        if isinstance(t, datetime.datetime) and t.tzinfo is not None:
            t = t.replace(tzinfo=None)
        try:
            out.append((t, float(v)))
        except Exception:
            pass
    return out


def plot_svg(series: List[Tuple[datetime.datetime, float]], title: str, outpath: str) -> None:
    if not series:
        return
    xs = [p[0] for p in series]
    ys = [p[1] for p in series]
    W, H, pl, pr, pt, pb = 900, 360, 70, 30, 40, 60
    xmin, xmax = min(xs), max(xs)
    ymin = min(ys) - 0.5
    ymax = max(ys) + 0.5
    if xmax == xmin:
        xmax = xmin + datetime.timedelta(seconds=1)
    if ymax == ymin:
        ymax = ymin + 1.0

    def sx(x):
        return pl + (x - xmin).total_seconds() / (xmax - xmin).total_seconds() * (W - pl - pr)

    def sy(y):
        return H - pb - (y - ymin) / (ymax - ymin) * (H - pt - pb)

    pts = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in zip(xs, ys))
    # x ticks ~6
    total_sec = max(1.0, (xmax - xmin).total_seconds())
    step_sec = max(3600, int(total_sec / 6 / 3600) * 3600)
    ticks = []
    t = xmin
    while t <= xmax:
        ticks.append(t)
        t += datetime.timedelta(seconds=step_sec)
    if not ticks or ticks[-1] < xmax:
        ticks.append(xmax)
    gridy = [ymin + i * (ymax - ymin) / 5 for i in range(6)]

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">']
    svg.append('<rect width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{W/2}" y="20" text-anchor="middle" font-size="16" font-weight="bold">{esc(title)}</text>')
    for gy in gridy:
        y = sy(gy)
        svg.append(f'<line x1="{pl}" y1="{y:.2f}" x2="{W-pr}" y2="{y:.2f}" stroke="#ddd"/>')
        svg.append(f'<text x="{pl-8}" y="{y+4:.2f}" text-anchor="end" font-size="11">{gy:.1f}°C</text>')
    for tx in ticks:
        x = sx(tx)
        svg.append(f'<line x1="{x:.2f}" y1="{H-pb}" x2="{x:.2f}" y2="{H-pb+5}" stroke="#333"/>')
        fmt = "%m-%d %H:%M" if total_sec <= 3 * 86400 else "%Y-%m-%d"
        svg.append(f'<text x="{x:.2f}" y="{H-pb+18}" text-anchor="middle" font-size="10">{tx.strftime(fmt)}</text>')
    svg.append(f'<polyline fill="none" stroke="#d62728" stroke-width="2" points="{pts}"/>')
    r = 2.5 if len(xs) < 200 else 1.5
    for x, y in zip(xs, ys):
        svg.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="{r}" fill="#d62728"/>')
    svg.append(f'<line x1="{pl}" y1="{H-pb}" x2="{W-pr}" y2="{H-pb}" stroke="#333"/>')
    svg.append(f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{H-pb}" stroke="#333"/>')
    svg.append('</svg>')
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


def plot_png(series: List[Tuple[datetime.datetime, float]], title: str, outpath: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    xs = [p[0] for p in series]
    ys = [p[1] for p in series]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(xs, ys, marker="o", markersize=3, linewidth=1.2, color="#d62728")
    ax.set_title(title)
    ax.set_ylabel("Temperature (°C)")
    ax.set_xlabel("Time (UTC)")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


def plot_combined_svg(all_series: List[Tuple[str, List[Tuple[datetime.datetime, float]]]], outpath: str) -> None:
    # Simple combined SVG with distinct colors
    colors = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b", "#17becf", "#e377c2"]
    nonempty = [(n, s) for n, s in all_series if s]
    if not nonempty:
        return
    all_x = [p[0] for _, s in nonempty for p in s]
    all_y = [p[1] for _, s in nonempty for p in s]
    W, H, pl, pr, pt, pb = 1000, 420, 70, 160, 40, 60
    xmin, xmax = min(all_x), max(all_x)
    ymin, ymax = min(all_y) - 0.5, max(all_y) + 0.5
    if xmax == xmin:
        xmax = xmin + datetime.timedelta(seconds=1)
    if ymax == ymin:
        ymax = ymin + 1.0

    def sx(x):
        return pl + (x - xmin).total_seconds() / (xmax - xmin).total_seconds() * (W - pl - pr)

    def sy(y):
        return H - pb - (y - ymin) / (ymax - ymin) * (H - pt - pb)

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">']
    svg.append('<rect width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{(W-pr)/2+pl/2}" y="20" text-anchor="middle" font-size="16" font-weight="bold">All rooms – Temperature (UTC)</text>')
    gridy = [ymin + i * (ymax - ymin) / 5 for i in range(6)]
    for gy in gridy:
        y = sy(gy)
        svg.append(f'<line x1="{pl}" y1="{y:.2f}" x2="{W-pr}" y2="{y:.2f}" stroke="#eee"/>')
        svg.append(f'<text x="{pl-8}" y="{y+4:.2f}" text-anchor="end" font-size="11">{gy:.1f}°C</text>')
    total_sec = max(1.0, (xmax - xmin).total_seconds())
    step_sec = max(3600, int(total_sec / 6 / 3600) * 3600)
    t = xmin
    while t <= xmax:
        x = sx(t)
        svg.append(f'<text x="{x:.2f}" y="{H-pb+18}" text-anchor="middle" font-size="10">{t.strftime("%m-%d %H:%M")}</text>')
        t += datetime.timedelta(seconds=step_sec)
    for i, (name, s) in enumerate(nonempty):
        c = colors[i % len(colors)]
        pts = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in s)
        svg.append(f'<polyline fill="none" stroke="{c}" stroke-width="1.8" points="{pts}"/>')
        ly = pt + 20 + i * 18
        svg.append(f'<line x1="{W-pr+10}" y1="{ly-4}" x2="{W-pr+30}" y2="{ly-4}" stroke="{c}" stroke-width="2"/>')
        svg.append(f'<text x="{W-pr+35}" y="{ly}" font-size="11">{esc(name)}</text>')
    svg.append(f'<line x1="{pl}" y1="{H-pb}" x2="{W-pr}" y2="{H-pb}" stroke="#333"/>')
    svg.append(f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{H-pb}" stroke="#333"/>')
    svg.append('</svg>')
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate temperature plots for all rooms from Db2 Netatmo data.")
    ap.add_argument("--outdir", default=env("PLOT_OUTDIR", "/tmp/opencode/netatmo_plots"), help="Output directory for plots")
    ap.add_argument("--format", choices=["svg", "png"], default="svg", help="Output format (png requires matplotlib)")
    ap.add_argument("--combined", action="store_true", help="Also generate a combined plot of all rooms")
    ap.add_argument("--table", default=None, help="Override qualified table name (e.g. DB2INST1.NETATMO_MEASURES)")
    args = ap.parse_args()

    try:
        engine = make_engine()
        table = args.table or qualified_table_name()
        os.makedirs(args.outdir, exist_ok=True)

        modules = fetch_modules(engine, table)
        if not modules:
            print(f"No modules with temperature data found in {table}")
            return 1

        all_series = []
        for m in modules:
            name = m.get("MODULE_NAME") or m.get("MODULE_ID") or "unknown"
            mid = m.get("MODULE_ID")
            series = fetch_series(engine, table, mid, name)
            if not series:
                print(f"Skip {name}: no points")
                continue
            label = f"{name} ({m.get('MODULE_TYPE')})" if m.get("MODULE_TYPE") else name
            title = f"{label} – Temperature (UTC)"
            fname = safe_filename(name) + ("_temperature." + args.format)
            outpath = os.path.join(args.outdir, fname)
            if args.format == "png":
                try:
                    plot_png(series, title, outpath)
                except Exception as e:
                    print(f"PNG failed for {name} ({e}), falling back to SVG", file=sys.stderr)
                    outpath = os.path.splitext(outpath)[0] + ".svg"
                    plot_svg(series, title, outpath)
            else:
                plot_svg(series, title, outpath)
            print(f"Wrote {outpath} ({len(series)} points, {series[0][0]} -> {series[-1][0]})")
            all_series.append((name, series))

        if args.combined and all_series:
            cpath = os.path.join(args.outdir, "all_rooms_temperature." + ("svg" if args.format != "png" else "svg"))
            # combined as SVG for simplicity
            cpath = os.path.join(args.outdir, "all_rooms_temperature.svg")
            plot_combined_svg(all_series, cpath)
            print(f"Wrote {cpath} (combined)")

        print(f"Done. {len(all_series)} room plot(s) in {args.outdir}")
        return 0
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
