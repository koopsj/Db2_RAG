#!/usr/bin/env python3
"""
Helper to obtain Netatmo OAuth2 tokens via Authorization Code flow
(password grant is deprecated/unavailable for many apps).

Steps:
1. Create/configure an app at https://dev.netatmo.com/apps/
   - Set a Redirect URI (e.g. http://localhost:8080/callback)
   - Note Client ID and Client Secret
2. Run:  python netatmo_oauth_helper.py --client-id ... --client-secret ... --redirect-uri ...
   It will print an authorization URL. Open it, log in, approve access.
3. After redirect, copy the full redirected URL (or just the `code` parameter) and paste it.
4. Script exchanges the code for access_token + refresh_token.

You can also pass values via env vars:
  NETATMO_CLIENT_ID, NETATMO_CLIENT_SECRET, NETATMO_REDIRECT_URI
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse

import requests

AUTH_URL = "https://api.netatmo.com/oauth2/authorize"
TOKEN_URL = "https://api.netatmo.com/oauth2/token"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id", default=os.getenv("NETATMO_CLIENT_ID"))
    ap.add_argument("--client-secret", default=os.getenv("NETATMO_CLIENT_SECRET"))
    ap.add_argument("--redirect-uri", default=os.getenv("NETATMO_REDIRECT_URI", "http://localhost:8080/callback"))
    ap.add_argument("--scope", default="read_station")
    ap.add_argument("--state", default="netatmo_state")
    args = ap.parse_args()

    if not args.client_id or not args.client_secret:
        print("Missing --client-id/--client-secret (or NETATMO_CLIENT_ID/NETATMO_CLIENT_SECRET)", file=sys.stderr)
        return 1

    params = {
        "client_id": args.client_id,
        "redirect_uri": args.redirect_uri,
        "scope": args.scope,
        "state": args.state,
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("\n1) Open this URL in your browser, log in to Netatmo, and approve access:\n")
    print(url)
    print("\n2) After approval you will be redirected to your redirect URI.")
    print("   Copy either the full redirected URL or just the 'code' value and paste it below.\n")

    raw = input("Redirected URL or code: ").strip()
    if not raw:
        print("No code provided.", file=sys.stderr)
        return 1

    code = raw
    if "code=" in raw:
        parsed = urllib.parse.urlparse(raw)
        qs = urllib.parse.parse_qs(parsed.query)
        code = (qs.get("code") or [""])[0]
    if not code:
        print("Could not extract authorization code.", file=sys.stderr)
        return 1

    data = {
        "grant_type": "authorization_code",
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "scope": args.scope,
        "code": code,
        "redirect_uri": args.redirect_uri,
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    print(f"\nToken endpoint: HTTP {resp.status_code}")
    try:
        payload = resp.json()
    except Exception:
        print(resp.text)
        return 1

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if resp.ok and payload.get("refresh_token"):
        print("\nSave this as NETATMO_REFRESH_TOKEN and use it with netatmo_to_db2.py")
        print("(Keep client_id/client_secret/refresh_token secret.)")
    else:
        print("\nToken exchange failed. Check code (single-use, short-lived), redirect_uri (must match app exactly), client credentials, and scopes.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
