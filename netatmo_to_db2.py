#!/usr/bin/env python3
"""
Read data from a Netatmo weather station and push it into IBM Db2.

Requirements:
  pip install requests sqlalchemy ibm_db ibm_db_sa

Configuration (environment variables recommended):
  NETATMO_CLIENT_ID        - Netatmo app client id
  NETATMO_CLIENT_SECRET    - Netatmo app client secret
  NETATMO_REFRESH_TOKEN    - OAuth2 refresh token (recommended)
  # OR (less preferred) username/password grant:
  NETATMO_USERNAME         - Netatmo account email
  NETATMO_PASSWORD         - Netatmo account password
  NETATMO_DEVICE_ID        - (optional) specific station/device id (_id/mac)

  DB2_HOST                 - e.g. localhost
  DB2_PORT                 - e.g. 50050
  DB2_DATABASE             - e.g. dbcdw
  DB2_USER                 - e.g. db2inst1
  DB2_PASSWORD             - db password
  DB2_SCHEMA               - (optional) schema, default DB2_USER/current schema
  DB2_TABLE                - (optional) target table, default NETATMO_MEASURES

Usage:
  python netatmo_to_db2.py
  python netatmo_to_db2.py --create-table
  python netatmo_to_db2.py --once
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests
from sqlalchemy import create_engine, text

NETATMO_TOKEN_URL = "https://api.netatmo.com/oauth2/token"
NETATMO_STATIONS_URL = "https://api.netatmo.com/api/getstationsdata"
NETATMO_MEASURE_URL = "https://api.netatmo.com/api/getmeasure"


def env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def get_access_token(session: requests.Session) -> str:
    """Obtain an access token using refresh_token (preferred) or password grant."""
    client_id = env("NETATMO_CLIENT_ID", required=True)
    client_secret = env("NETATMO_CLIENT_SECRET", required=True)
    refresh_token = env("NETATMO_REFRESH_TOKEN")
    if refresh_token:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    else:
        username = env("NETATMO_USERNAME", required=True)
        password = env("NETATMO_PASSWORD", required=True)
        data = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password,
            "scope": "read_station",
        }
    resp = session.post(NETATMO_TOKEN_URL, data=data, timeout=30)
    if not resp.ok:
        detail = resp.text
        try:
            detail = json.dumps(resp.json(), ensure_ascii=False)
        except Exception:
            pass
        raise RuntimeError(
            f"Token request failed: {resp.status_code} {resp.reason}. "
            f"Response: {detail}. "
            "Check NETATMO_CLIENT_ID/SECRET, grant type/credentials, refresh token validity, and Netatmo app scopes/authorization."
        )
    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {payload}")
    return token


def fetch_stations_data(session: requests.Session, access_token: str, device_id: Optional[str] = None) -> Dict[str, Any]:
    params = {"access_token": access_token}
    if device_id:
        params["device_id"] = device_id
    resp = session.get(NETATMO_STATIONS_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _ts_to_utc(ts: Optional[int]) -> Optional[datetime]:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        return None


def flatten_measures(stations_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten getstationsdata response into row dicts per module/dashboard reading."""
    rows: List[Dict[str, Any]] = []
    body = stations_payload.get("body", {})
    devices = body.get("devices", []) or []
    for dev in devices:
        station_id = dev.get("_id")
        station_name = dev.get("station_name") or dev.get("module_name")
        home_name = dev.get("home_name")
        modules = [dev] + (dev.get("modules", []) or [])
        for mod in modules:
            module_id = mod.get("_id")
            module_name = mod.get("module_name")
            module_type = mod.get("type")
            dashboard = mod.get("dashboard_data") or {}
            if not dashboard:
                continue
            ts = _ts_to_utc(dashboard.get("time_utc"))
            row: Dict[str, Any] = {
                "station_id": station_id,
                "station_name": station_name,
                "home_name": home_name,
                "module_id": module_id,
                "module_name": module_name,
                "module_type": module_type,
                "measure_time_utc": ts,
                "raw_dashboard": json.dumps(dashboard, ensure_ascii=False),
            }
            # Common dashboard fields (store when present)
            for key in [
                "Temperature", "Humidity", "CO2", "Noise", "Pressure", "AbsolutePressure",
                "min_temp", "max_temp", "temp_trend", "pressure_trend",
                "Rain", "sum_rain_1", "sum_rain_24",
                "WindStrength", "WindAngle", "GustStrength", "GustAngle", "max_wind_str", "max_wind_angle", "date_max_wind_str",
                "health_idx",
            ]:
                if key in dashboard:
                    row[key] = dashboard.get(key)
            rows.append(row)
    return rows


def iter_station_modules(stations_payload: Dict[str, Any]):
    """Yield (device_id, station_name, home_name, module_id, module_name, module_type, data_types)."""
    body = stations_payload.get("body", {})
    devices = body.get("devices", []) or []
    for dev in devices:
        device_id = dev.get("_id")
        station_name = dev.get("station_name") or dev.get("module_name")
        home_name = dev.get("home_name")
        modules = [dev] + (dev.get("modules", []) or [])
        for mod in modules:
            data_types = mod.get("data_type") or []
            if not data_types:
                continue
            yield (
                device_id,
                station_name,
                home_name,
                mod.get("_id"),
                mod.get("module_name"),
                mod.get("type"),
                list(data_types),
            )


def fetch_historical_measures(
    session: requests.Session,
    access_token: str,
    device_id: str,
    module_id: str,
    scale: str,
    mtypes: List[str],
    date_begin: int,
    date_end: int,
) -> List[Dict[str, Any]]:
    params = {
        "access_token": access_token,
        "device_id": device_id,
        "scale": scale,
        "type": ",".join(mtypes),
        "date_begin": date_begin,
        "date_end": date_end,
        "optimize": "false",
        "real_time": "false",
    }
    # For main/indoor module, module_id is same as device_id and must not be passed in some cases;
    # Netatmo accepts omitting module_id for station, but safer: include when different.
    if module_id and module_id != device_id:
        params["module_id"] = module_id
    resp = session.get(NETATMO_MEASURE_URL, params=params, timeout=60)
    if not resp.ok:
        raise RuntimeError(f"getmeasure failed {resp.status_code}: {resp.text}")
    payload = resp.json()
    body = payload.get("body")
    if body is None:
        return []
    # optimize=false -> list of {beg_time, step_time, value: [[...], ...]}
    if isinstance(body, dict):
        # sometimes optimized form {timestamp: [values]}
        out = []
        for ts, vals in body.items():
            if isinstance(vals, list):
                out.append({"beg_time": int(ts), "step_time": 0, "value": [vals]})
        return out
    if isinstance(body, list):
        return body
    return []


def flatten_historical(stations_payload: Dict[str, Any], session: requests.Session, access_token: str,
                       date_begin: int, date_end: int, scale: str = "30min") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen_meta = {}
    for device_id, station_name, home_name, module_id, module_name, module_type, data_types in iter_station_modules(stations_payload):
        meta = {
            "station_id": device_id,
            "station_name": station_name,
            "home_name": home_name,
            "module_id": module_id,
            "module_name": module_name,
            "module_type": module_type,
        }
        # getmeasure 'type' must be subset of available types for module
        try:
            chunks = fetch_historical_measures(session, access_token, device_id, module_id, scale, data_types, date_begin, date_end)
        except Exception as e:
            print(f"History fetch failed for module {module_name} ({module_id}): {e}", file=sys.stderr)
            continue
        for chunk in chunks:
            beg = int(chunk.get("beg_time", 0))
            step = int(chunk.get("step_time", 0) or 0)
            values = chunk.get("value") or []
            for i, vals in enumerate(values):
                ts = beg + i * step
                row = dict(meta)
                row["measure_time_utc"] = _ts_to_utc(ts)
                raw = {"beg_time": beg, "step_time": step, "types": data_types, "values": vals}
                row["raw_dashboard"] = json.dumps(raw, ensure_ascii=False)
                for idx, t in enumerate(data_types):
                    if idx < len(vals):
                        row[t] = vals[idx]
                rows.append(row)
    return rows


def make_engine():
    host = env("DB2_HOST", required=True)
    port = env("DB2_PORT", required=True)
    db = env("DB2_DATABASE", required=True)
    user = env("DB2_USER", required=True)
    pwd = env("DB2_PASSWORD", required=True)
    url = f"ibm_db_sa://{user}:{pwd}@{host}:{port}/{db}"
    return create_engine(url, pool_pre_ping=True)


def qualified_table_name() -> str:
    schema = env("DB2_SCHEMA")
    table = env("DB2_TABLE", "NETATMO_MEASURES")
    if schema:
        return f"{schema}.{table}"
    return table


def create_table(engine) -> None:
    # Adjust types/precision to your Db2 version and needs.
    ddl = f"""
    CREATE TABLE {qualified_table_name()} (
        STATION_ID        VARCHAR(64),
        STATION_NAME      VARCHAR(256),
        HOME_NAME         VARCHAR(256),
        MODULE_ID         VARCHAR(64),
        MODULE_NAME       VARCHAR(256),
        MODULE_TYPE       VARCHAR(64),
        MEASURE_TIME_UTC  TIMESTAMP,
        TEMPERATURE       DOUBLE,
        HUMIDITY          INTEGER,
        CO2               INTEGER,
        NOISE             INTEGER,
        PRESSURE          DOUBLE,
        ABSOLUTE_PRESSURE DOUBLE,
        MIN_TEMP          DOUBLE,
        MAX_TEMP          DOUBLE,
        TEMP_TREND        VARCHAR(32),
        PRESSURE_TREND    VARCHAR(32),
        RAIN              DOUBLE,
        SUM_RAIN_1        DOUBLE,
        SUM_RAIN_24       DOUBLE,
        WIND_STRENGTH     INTEGER,
        WIND_ANGLE        INTEGER,
        GUST_STRENGTH     INTEGER,
        GUST_ANGLE        INTEGER,
        MAX_WIND_STR      INTEGER,
        MAX_WIND_ANGLE    INTEGER,
        DATE_MAX_WIND_STR TIMESTAMP,
        HEALTH_IDX        INTEGER,
        RAW_DASHBOARD     CLOB(64K),
        INGESTED_AT_UTC   TIMESTAMP DEFAULT CURRENT TIMESTAMP
    )
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def insert_rows(engine, rows: Iterable[Dict[str, Any]]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    # Upsert-like dedupe: skip if same module_id and measure_time_utc already stored.
    # (Db2 MERGE could be used if a unique key/constraint exists.)
    insert_sql = text(f"""
        INSERT INTO {qualified_table_name()} (
            STATION_ID, STATION_NAME, HOME_NAME, MODULE_ID, MODULE_NAME, MODULE_TYPE,
            MEASURE_TIME_UTC, TEMPERATURE, HUMIDITY, CO2, NOISE, PRESSURE, ABSOLUTE_PRESSURE,
            MIN_TEMP, MAX_TEMP, TEMP_TREND, PRESSURE_TREND,
            RAIN, SUM_RAIN_1, SUM_RAIN_24,
            WIND_STRENGTH, WIND_ANGLE, GUST_STRENGTH, GUST_ANGLE, MAX_WIND_STR, MAX_WIND_ANGLE, DATE_MAX_WIND_STR,
            HEALTH_IDX, RAW_DASHBOARD
        )
        SELECT
            :STATION_ID, :STATION_NAME, :HOME_NAME, :MODULE_ID, :MODULE_NAME, :MODULE_TYPE,
            :MEASURE_TIME_UTC, :TEMPERATURE, :HUMIDITY, :CO2, :NOISE, :PRESSURE, :ABSOLUTE_PRESSURE,
            :MIN_TEMP, :MAX_TEMP, :TEMP_TREND, :PRESSURE_TREND,
            :RAIN, :SUM_RAIN_1, :SUM_RAIN_24,
            :WIND_STRENGTH, :WIND_ANGLE, :GUST_STRENGTH, :GUST_ANGLE, :MAX_WIND_STR, :MAX_WIND_ANGLE, :DATE_MAX_WIND_STR,
            :HEALTH_IDX, :RAW_DASHBOARD
        FROM SYSIBM.SYSDUMMY1
        WHERE NOT EXISTS (
            SELECT 1 FROM {qualified_table_name()} t
            WHERE t.MODULE_ID = :MODULE_ID
              AND t.MEASURE_TIME_UTC = :MEASURE_TIME_UTC
        )
    """)

    def _to_int(v):
        if v is None or v == "":
            return None
        try:
            return int(v)
        except Exception:
            try:
                return int(float(v))
            except Exception:
                return None

    def _to_float(v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except Exception:
            return None

    def _to_str(v):
        if v is None:
            return None
        return str(v)

    def norm(r: Dict[str, Any]) -> Dict[str, Any]:
        d = _ts_to_utc(r.get("date_max_wind_str")) if "date_max_wind_str" in r else None
        mt = r.get("measure_time_utc")
        if mt is not None and not isinstance(mt, datetime):
            mt = _ts_to_utc(mt)
        return {
            "STATION_ID": _to_str(r.get("station_id")),
            "STATION_NAME": _to_str(r.get("station_name")),
            "HOME_NAME": _to_str(r.get("home_name")),
            "MODULE_ID": _to_str(r.get("module_id")),
            "MODULE_NAME": _to_str(r.get("module_name")),
            "MODULE_TYPE": _to_str(r.get("module_type")),
            "MEASURE_TIME_UTC": mt,
            "TEMPERATURE": _to_float(r.get("Temperature")),
            "HUMIDITY": _to_int(r.get("Humidity")),
            "CO2": _to_int(r.get("CO2")),
            "NOISE": _to_int(r.get("Noise")),
            "PRESSURE": _to_float(r.get("Pressure")),
            "ABSOLUTE_PRESSURE": _to_float(r.get("AbsolutePressure")),
            "MIN_TEMP": _to_float(r.get("min_temp")),
            "MAX_TEMP": _to_float(r.get("max_temp")),
            "TEMP_TREND": _to_str(r.get("temp_trend")),
            "PRESSURE_TREND": _to_str(r.get("pressure_trend")),
            "RAIN": _to_float(r.get("Rain")),
            "SUM_RAIN_1": _to_float(r.get("sum_rain_1")),
            "SUM_RAIN_24": _to_float(r.get("sum_rain_24")),
            "WIND_STRENGTH": _to_int(r.get("WindStrength")),
            "WIND_ANGLE": _to_int(r.get("WindAngle")),
            "GUST_STRENGTH": _to_int(r.get("GustStrength")),
            "GUST_ANGLE": _to_int(r.get("GustAngle")),
            "MAX_WIND_STR": _to_int(r.get("max_wind_str")),
            "MAX_WIND_ANGLE": _to_int(r.get("max_wind_angle")),
            "DATE_MAX_WIND_STR": d,
            "HEALTH_IDX": _to_int(r.get("health_idx")),
            "RAW_DASHBOARD": _to_str(r.get("raw_dashboard")),
        }

    params = [norm(r) for r in rows]
    inserted = 0
    with engine.begin() as conn:
        for p in params:
            result = conn.execute(insert_sql, p)
            rc = result.rowcount
            if rc is not None and rc > 0:
                inserted += rc
            elif rc == -1:
                # driver may not report; assume attempted/possibly inserted when not deduped
                inserted += 1
    return inserted


def run_once(engine, with_history: bool = False, history_days: int = 30, history_scale: str = "30min") -> int:
    device_id = env("NETATMO_DEVICE_ID")
    with requests.Session() as session:
        token = get_access_token(session)
        payload = fetch_stations_data(session, token, device_id=device_id)
        rows = flatten_measures(payload)
        if with_history:
            now = int(datetime.now(timezone.utc).timestamp())
            date_begin = now - history_days * 24 * 3600
            hist_rows = flatten_historical(payload, session, token, date_begin, now, scale=history_scale)
            print(f"Fetched {len(hist_rows)} historical readings ({history_days}d, scale={history_scale})")
            rows.extend(hist_rows)
    inserted = insert_rows(engine, rows)
    print(f"Fetched/processed {len(rows)} rows total; insert attempted (new rows best-effort): {inserted}")
    return inserted


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch Netatmo weather data and store in Db2.")
    ap.add_argument("--create-table", action="store_true", help="Create target table and exit")
    ap.add_argument("--once", action="store_true", help="Run one fetch/insert cycle and exit")
    ap.add_argument("--interval", type=int, default=int(env("POLL_INTERVAL_SECONDS", "300")), help="Polling interval seconds (default 300)")
    ap.add_argument("--with-history", action="store_true", help="Also fetch historical measures (getmeasure) and insert")
    ap.add_argument("--history-days", type=int, default=int(env("HISTORY_DAYS", "30")), help="Days of history to fetch when --with-history (default 30)")
    ap.add_argument("--history-scale", default=env("HISTORY_SCALE", "30min"), help="Scale for historical data: max,30min,1hour,3hours,1day,1week,1month (default 30min)")
    args = ap.parse_args()

    try:
        engine = make_engine()
        if args.create_table:
            try:
                create_table(engine)
                print(f"Created table {qualified_table_name()}")
            except Exception as e:
                print(f"Create table failed (may already exist): {e}", file=sys.stderr)
                return 1
            return 0

        if args.once:
            run_once(engine, with_history=args.with_history, history_days=args.history_days, history_scale=args.history_scale)
            return 0

        print(f"Starting Netatmo -> Db2 poller (interval {args.interval}s, table {qualified_table_name()})")
        while True:
            try:
                run_once(engine, with_history=args.with_history, history_days=args.history_days, history_scale=args.history_scale)
            except Exception as e:
                print(f"Cycle error: {e}", file=sys.stderr)
            time.sleep(max(30, args.interval))
    except KeyboardInterrupt:
        print("Stopped.")
        return 0
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
