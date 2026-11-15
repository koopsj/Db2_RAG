#!/usr/bin/env python3
"""
Generate temperature (and humidity) plots for all rooms/modules from Netatmo data stored in IBM Db2.

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
  python plot_netatmo_temperatures.py --no-humidity   # plot temperature only

Note: per-room plots show Temperature as a solid line (left axis, °C) and Humidity as a dotted line (right axis, %) when available.
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
        WHERE TEMPERATURE IS NOT NULL OR HUMIDITY IS NOT NULL
        GROUP BY MODULE_NAME, MODULE_TYPE, MODULE_ID
        ORDER BY MODULE_NAME
    """)
    with engine.connect() as conn:
        rows = conn.execute(q).mappings().all()
    return [dict(r) for r in rows]


def fetch_series(engine, table: str, module_id: Optional[str], module_name: Optional[str]) -> List[Tuple[datetime.datetime, Optional[float], Optional[float]]]:
    # Returns (time, temperature, humidity)
    if module_id:
        q = text(f"""
            SELECT MEASURE_TIME_UTC, TEMPERATURE, HUMIDITY
            FROM {table}
            WHERE MODULE_ID = :mid AND (TEMPERATURE IS NOT NULL OR HUMIDITY IS NOT NULL)
            ORDER BY MEASURE_TIME_UTC
        """)
        params = {"mid": module_id}
    else:
        q = text(f"""
            SELECT MEASURE_TIME_UTC, TEMPERATURE, HUMIDITY
            FROM {table}
            WHERE MODULE_NAME = :mname AND (TEMPERATURE IS NOT NULL OR HUMIDITY IS NOT NULL)
            ORDER BY MEASURE_TIME_UTC
        """)
        params = {"mname": module_name}
    with engine.connect() as conn:
        rows = conn.execute(q, params).all()
    out = []
    for t, temp, hum in rows:
        if t is None:
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
        tv = hv = None
        try:
            if temp is not None:
                tv = float(temp)
        except Exception:
            tv = None
        try:
            if hum is not None:
                hv = float(hum)
        except Exception:
            hv = None
        if tv is None and hv is None:
            continue
        out.append((t, tv, hv))
    return out


def plot_svg(series: List[Tuple[datetime.datetime, Optional[float], Optional[float]]], title: str, outpath: str, show_humidity: bool = True) -> None:
    if not series:
        return
    xs = [p[0] for p in series]
    tpts = [(p[0], p[1]) for p in series if p[1] is not None]
    hpts = [(p[0], p[2]) for p in series if show_humidity and p[2] is not None]
    if not tpts and not hpts:
        return
    ys_t = [v for _, v in tpts] if tpts else [0.0]
    ys_h = [v for _, v in hpts] if hpts else [0.0]
    W, H, pl, pr, pt, pb = 920, 360, 70, 60, 40, 60
    xmin, xmax = min(xs), max(xs)
    ymin_t = min(ys_t) - 0.5 if tpts else 0.0
    ymax_t = max(ys_t) + 0.5 if tpts else 1.0
    if hpts:
        ymin_h = max(0.0, min(ys_h) - 5.0)
        ymax_h = min(100.0, max(ys_h) + 5.0)
        if ymax_h <= ymin_h:
            ymin_h, ymax_h = 0.0, 100.0
    else:
        ymin_h, ymax_h = 0.0, 100.0
    if xmax == xmin:
        xmax = xmin + datetime.timedelta(seconds=1)
    if ymax_t == ymin_t:
        ymax_t = ymin_t + 1.0

    def sx(x):
        return pl + (x - xmin).total_seconds() / (xmax - xmin).total_seconds() * (W - pl - pr)

    def sy_t(y):
        return H - pb - (y - ymin_t) / (ymax_t - ymin_t) * (H - pt - pb)

    def sy_h(y):
        return H - pb - (y - ymin_h) / (ymax_h - ymin_h) * (H - pt - pb)

    total_sec = max(1.0, (xmax - xmin).total_seconds())
    step_sec = max(3600, int(total_sec / 6 / 3600) * 3600)
    ticks = []
    t = xmin
    while t <= xmax:
        ticks.append(t)
        t += datetime.timedelta(seconds=step_sec)
    if not ticks or ticks[-1] < xmax:
        ticks.append(xmax)
    gridy = [ymin_t + i * (ymax_t - ymin_t) / 5 for i in range(6)]

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">']
    svg.append('<rect width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{W/2}" y="20" text-anchor="middle" font-size="16" font-weight="bold">{esc(title)}</text>')
    # left axis grid (temperature)
    for gy in gridy:
        y = sy_t(gy)
        svg.append(f'<line x1="{pl}" y1="{y:.2f}" x2="{W-pr}" y2="{y:.2f}" stroke="#ddd"/>')
        svg.append(f'<text x="{pl-8}" y="{y+4:.2f}" text-anchor="end" font-size="11" fill="#d62728">{gy:.1f}°C</text>')
    # right axis (humidity)
    if hpts:
        gridh = [ymin_h + i * (ymax_h - ymin_h) / 5 for i in range(6)]
        for gh in gridh:
            y = sy_h(gh)
            svg.append(f'<text x="{W-pr+8}" y="{y+4:.2f}" text-anchor="start" font-size="11" fill="#1f77b4">{gh:.0f}%</text>')
    # x ticks
    for tx in ticks:
        x = sx(tx)
        svg.append(f'<line x1="{x:.2f}" y1="{H-pb}" x2="{x:.2f}" y2="{H-pb+5}" stroke="#333"/>')
        fmt = "%m-%d %H:%M" if total_sec <= 3 * 86400 else "%Y-%m-%d"
        svg.append(f'<text x="{x:.2f}" y="{H-pb+18}" text-anchor="middle" font-size="10">{tx.strftime(fmt)}</text>')
    # temperature (solid)
    if tpts:
        pts_t = " ".join(f"{sx(x):.2f},{sy_t(y):.2f}" for x, y in tpts)
        svg.append(f'<polyline fill="none" stroke="#d62728" stroke-width="2" points="{pts_t}"/>')
        r = 2.5 if len(tpts) < 200 else 1.5
        for x, y in tpts:
            svg.append(f'<circle cx="{sx(x):.2f}" cy="{sy_t(y):.2f}" r="{r}" fill="#d62728"/>')
    # humidity (dotted)
    if hpts:
        pts_h = " ".join(f"{sx(x):.2f},{sy_h(y):.2f}" for x, y in hpts)
        svg.append(f'<polyline fill="none" stroke="#1f77b4" stroke-width="2" stroke-dasharray="4 4" points="{pts_h}"/>')
        r = 2.0 if len(hpts) < 200 else 1.2
        for x, y in hpts:
            svg.append(f'<circle cx="{sx(x):.2f}" cy="{sy_h(y):.2f}" r="{r}" fill="#1f77b4"/>')
    # legend
    lx, ly = pl + 10, pt + 10
    svg.append(f'<rect x="{lx-6}" y="{ly-10}" width="170" height="{34 if hpts else 18}" fill="white" stroke="#ccc"/>')
    svg.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+20}" y2="{ly}" stroke="#d62728" stroke-width="2"/>')
    svg.append(f'<text x="{lx+26}" y="{ly+4}" font-size="11">Temperature (°C)</text>')
    if hpts:
        svg.append(f'<line x1="{lx}" y1="{ly+16}" x2="{lx+20}" y2="{ly+16}" stroke="#1f77b4" stroke-width="2" stroke-dasharray="4 4"/>')
        svg.append(f'<text x="{lx+26}" y="{ly+20}" font-size="11">Humidity (%)</text>')

    svg.append(f'<line x1="{pl}" y1="{H-pb}" x2="{W-pr}" y2="{H-pb}" stroke="#333"/>')
    svg.append(f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{H-pb}" stroke="#333"/>')
    if hpts:
        svg.append(f'<line x1="{W-pr}" y1="{pt}" x2="{W-pr}" y2="{H-pb}" stroke="#333"/>')
    svg.append('</svg>')
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


def plot_png(series: List[Tuple[datetime.datetime, Optional[float], Optional[float]]], title: str, outpath: str, show_humidity: bool = True) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    xs = [p[0] for p in series]
    tpts = [(p[0], p[1]) for p in series if p[1] is not None]
    hpts = [(p[0], p[2]) for p in series if show_humidity and p[2] is not None]
    fig, ax = plt.subplots(figsize=(10, 4))
    if tpts:
        ax.plot([x for x, _ in tpts], [y for _, y in tpts], marker="o", markersize=3, linewidth=1.2, color="#d62728", label="Temperature (°C)")
    ax.set_ylabel("Temperature (°C)", color="#d62728")
    ax.tick_params(axis="y", labelcolor="#d62728")
    ax.set_xlabel("Time (UTC)")
    ax.grid(True, alpha=0.3)
    if hpts:
        ax2 = ax.twinx()
        ax2.plot([x for x, _ in hpts], [y for _, y in hpts], linestyle=":", marker="o", markersize=2.5, linewidth=1.2, color="#1f77b4", label="Humidity (%)")
        ax2.set_ylabel("Humidity (%)", color="#1f77b4")
        ax2.tick_params(axis="y", labelcolor="#1f77b4")
        # combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc="best")
    elif tpts:
        ax.legend(loc="best")
    ax.set_title(title)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


def plot_combined_svg(all_series: List[Tuple[str, List[Tuple[datetime.datetime, Optional[float], Optional[float]]]]], outpath: str, show_humidity: bool = True) -> None:
    # Combined plot: temperature (solid) and humidity (dotted, same room color) on dual axes
    colors = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b", "#17becf", "#e377c2"]
    prepared = []
    for name, s in all_series:
        t = [(p[0], p[1]) for p in s if p[1] is not None]
        h = [(p[0], p[2]) for p in s if show_humidity and p[2] is not None]
        if t or h:
            prepared.append((name, t, h))
    if not prepared:
        return
    all_x = [p[0] for _, t, h in prepared for p in (t + h)]
    all_y_t = [p[1] for _, t, _ in prepared for p in t]
    all_y_h = [p[1] for _, _, h in prepared for p in h]
    if not all_y_t:
        all_y_t = [0.0]
    W, H, pl, pr, pt, pb = 1040, 460, 70, 250, 45, 60
    xmin, xmax = min(all_x), max(all_x)
    ymin_t, ymax_t = min(all_y_t) - 0.5, max(all_y_t) + 0.5
    if all_y_h:
        ymin_h = max(0.0, min(all_y_h) - 5.0)
        ymax_h = min(100.0, max(all_y_h) + 5.0)
        if ymax_h <= ymin_h:
            ymin_h, ymax_h = 0.0, 100.0
    else:
        ymin_h, ymax_h = 0.0, 100.0
    if xmax == xmin:
        xmax = xmin + datetime.timedelta(seconds=1)
    if ymax_t == ymin_t:
        ymax_t = ymin_t + 1.0

    def sx(x):
        return pl + (x - xmin).total_seconds() / (xmax - xmin).total_seconds() * (W - pl - pr)

    def sy_t(y):
        return H - pb - (y - ymin_t) / (ymax_t - ymin_t) * (H - pt - pb)

    def sy_h(y):
        return H - pb - (y - ymin_h) / (ymax_h - ymin_h) * (H - pt - pb)

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif">']
    svg.append('<rect width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{(W-pr)/2+pl/2}" y="22" text-anchor="middle" font-size="16" font-weight="bold">All rooms – Temperature &amp; Humidity (UTC)</text>')
    gridy = [ymin_t + i * (ymax_t - ymin_t) / 5 for i in range(6)]
    for gy in gridy:
        y = sy_t(gy)
        svg.append(f'<line x1="{pl}" y1="{y:.2f}" x2="{W-pr}" y2="{y:.2f}" stroke="#eee"/>')
        svg.append(f'<text x="{pl-8}" y="{y+4:.2f}" text-anchor="end" font-size="11" fill="#333">{gy:.1f}°C</text>')
    if show_humidity and all_y_h:
        gridh = [ymin_h + i * (ymax_h - ymin_h) / 5 for i in range(6)]
        for gh in gridh:
            y = sy_h(gh)
            svg.append(f'<text x="{W-pr+8}" y="{y+4:.2f}" text-anchor="start" font-size="11" fill="#333">{gh:.0f}%</text>')
    total_sec = max(1.0, (xmax - xmin).total_seconds())
    step_sec = max(3600, int(total_sec / 6 / 3600) * 3600)
    t = xmin
    while t <= xmax:
        x = sx(t)
        svg.append(f'<text x="{x:.2f}" y="{H-pb+18}" text-anchor="middle" font-size="10">{t.strftime("%m-%d %H:%M")}</text>')
        t += datetime.timedelta(seconds=step_sec)

    # plot series (humidity dotted, same color as room; temp solid)
    for i, (name, ts, hs) in enumerate(prepared):
        c = colors[i % len(colors)]
        if ts:
            pts = " ".join(f"{sx(x):.2f},{sy_t(y):.2f}" for x, y in ts)
            svg.append(f'<polyline fill="none" stroke="{c}" stroke-width="1.8" points="{pts}"/>')
        if hs:
            pts = " ".join(f"{sx(x):.2f},{sy_h(y):.2f}" for x, y in hs)
            svg.append(f'<polyline fill="none" stroke="{c}" stroke-width="1.8" stroke-dasharray="4 4" points="{pts}"/>')

    # legend: per room temp (solid) + humidity (dotted) in same color
    legend_x = W - pr + 40
    legend_y = pt + 10
    # headers
    svg.append(f'<text x="{legend_x}" y="{legend_y}" font-size="11" font-weight="bold">Legend</text>')
    ly = legend_y + 16
    for i, (name, ts, hs) in enumerate(prepared):
        c = colors[i % len(colors)]
        if ts:
            svg.append(f'<line x1="{legend_x}" y1="{ly-4}" x2="{legend_x+22}" y2="{ly-4}" stroke="{c}" stroke-width="2"/>')
            svg.append(f'<text x="{legend_x+28}" y="{ly}" font-size="10">{esc(name)} – Temp (°C)</text>')
            ly += 15
        if hs:
            svg.append(f'<line x1="{legend_x}" y1="{ly-4}" x2="{legend_x+22}" y2="{ly-4}" stroke="{c}" stroke-width="2" stroke-dasharray="4 4"/>')
            svg.append(f'<text x="{legend_x+28}" y="{ly}" font-size="10">{esc(name)} – Humidity (%)</text>')
            ly += 15
        ly += 3

    svg.append(f'<line x1="{pl}" y1="{H-pb}" x2="{W-pr}" y2="{H-pb}" stroke="#333"/>')
    svg.append(f'<line x1="{pl}" y1="{pt}" x2="{pl}" y2="{H-pb}" stroke="#333"/>')
    if show_humidity and all_y_h:
        svg.append(f'<line x1="{W-pr}" y1="{pt}" x2="{W-pr}" y2="{H-pb}" stroke="#333"/>')
    svg.append('</svg>')
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate temperature and humidity plots for all rooms from Db2 Netatmo data.")
    ap.add_argument("--outdir", default=env("PLOT_OUTDIR", "/tmp/opencode/netatmo_plots"), help="Output directory for plots")
    ap.add_argument("--format", choices=["svg", "png"], default="svg", help="Output format (png requires matplotlib)")
    ap.add_argument("--combined", action="store_true", help="Also generate a combined plot (temperature per room)")
    ap.add_argument("--no-humidity", action="store_true", help="Plot temperature only (omit humidity)")
    ap.add_argument("--table", default=None, help="Override qualified table name (e.g. DB2INST1.NETATMO_MEASURES)")
    args = ap.parse_args()

    try:
        engine = make_engine()
        table = args.table or qualified_table_name()
        os.makedirs(args.outdir, exist_ok=True)
        show_humidity = not args.no_humidity

        modules = fetch_modules(engine, table)
        if not modules:
            print(f"No modules with temperature/humidity data found in {table}")
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
            has_h = any(p[2] is not None for p in series) and show_humidity
            title = f"{label} – Temperature{' & Humidity' if has_h else ''} (UTC)"
            suffix = "_temp_humidity." if has_h else "_temperature."
            fname = safe_filename(name) + suffix + args.format
            outpath = os.path.join(args.outdir, fname)
            if args.format == "png":
                try:
                    plot_png(series, title, outpath, show_humidity=show_humidity)
                except Exception as e:
                    print(f"PNG failed for {name} ({e}), falling back to SVG", file=sys.stderr)
                    outpath = os.path.splitext(outpath)[0] + ".svg"
                    plot_svg(series, title, outpath, show_humidity=show_humidity)
            else:
                plot_svg(series, title, outpath, show_humidity=show_humidity)
            print(f"Wrote {outpath} ({len(series)} points, {series[0][0]} -> {series[-1][0]})")
            all_series.append((name, series))

        if args.combined and all_series:
            cname = "all_rooms_temp_humidity.svg" if show_humidity else "all_rooms_temperature.svg"
            cpath = os.path.join(args.outdir, cname)
            plot_combined_svg(all_series, cpath, show_humidity=show_humidity)
            print(f"Wrote {cpath} (combined)")

        print(f"Done. {len(all_series)} room plot(s) in {args.outdir}")
        return 0
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
