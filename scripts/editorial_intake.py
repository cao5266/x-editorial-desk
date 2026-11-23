"""Run the read-only adapters from the editor workstation. No scheduler or publishing."""

import argparse
import concurrent.futures
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "miniflux": "python3 -",
    "changedetection": "sudo -n docker exec -i ai-monitor-changedetection-1 python3 -",
    "radar": "sudo -n python3 -",
}


def status(health, count, limited):
    if not health["active"]:
        return "partial" if limited else "no_sources"
    if health["errors"] == health["active"] and not count:
        return "failed"
    if limited or health["errors"] or health["unknown"]:
        return "partial"
    return "ok" if count else "empty"


def decode(source, code, stdout, failure=None):
    result = {"source": source, "status": "failed"}
    if code:
        return {**result, "reason": failure or ("ssh_failed" if code == 255 else "remote_reader_failed")}
    try:
        data = json.loads(stdout)
        health = data["health"]
        count, items, details = (data[k] for k in ("count", "items", "details"))
        if (type(count) is not int or not isinstance(items, list) or count < len(items)
                or not isinstance(details, dict)
                or any(type(health[k]) is not int or health[k] < 0 for k in ("active", "errors", "unknown"))
                or health["errors"] + health["unknown"] > health["active"]
                or any(not isinstance(i, dict) or not isinstance(i.get("id"), str) for i in items)):
            raise ValueError("invalid payload")
        truncated = count > len(items)
        state = status(health, count, truncated or bool(details.get("unreadable_watches")))
        return {"source": source, "status": state, "count": count, "exported": len(items),
                "truncated": truncated, "health": health, "details": details,
                "items": [{**item, "source": source} for item in items]}
    except (ValueError, TypeError, KeyError, UnicodeError):
        return {**result, "reason": "invalid_export"}


def group(items):
    """Group equivalent article URLs; different snapshots of one page are not one event."""
    groups = {}
    for item in items:
        key = (item["source"], item["id"])
        if item.get("url") and item["source"] != "changedetection":
            u = urlsplit(item["url"])
            key = ("url", urlunsplit((u.scheme, u.netloc, u.path.rstrip("/") or "/", u.query, "")))
        groups.setdefault(key, []).append(item)
    return list(groups.values())


def fetch(source, args, script, start, end):
    cmd = ["ssh", "-T", "-i", str(args.key), "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
           "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8", args.ssh_target,
           f"{COMMANDS[source]} {source} {start} {end}"]
    try:
        p = subprocess.run(cmd, input=script, capture_output=True, timeout=30)
        return decode(source, p.returncode, p.stdout)
    except subprocess.TimeoutExpired:
        return decode(source, 1, b"", failure="timeout")
    except OSError:
        return decode(source, 1, b"", failure="ssh_unavailable")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hours", type=int, choices=(24, 48), default=24)
    parser.add_argument("--key", type=Path, default=ROOT / ".local-secrets/kakacodex.pem")
    parser.add_argument("--ssh-target", default="ubuntu@101.34.76.198")
    parser.add_argument("--end", help="ISO timestamp with timezone; defaults to now")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*", args.ssh_target):
        parser.error("--ssh-target must be user@hostname")
    args.key = args.key.resolve()
    if not args.key.is_file():
        parser.error("SSH identity file not found")
    now = datetime.now(timezone.utc)
    try:
        end = datetime.fromisoformat(args.end) if args.end else now
        if end.tzinfo is None or end > now:
            raise ValueError
        end = end.astimezone(timezone.utc).replace(microsecond=0)
    except ValueError:
        parser.error("--end must be a non-future ISO timestamp with timezone")
    start = end - timedelta(hours=args.hours)
    script = ROOT.joinpath("scripts/editorial_source_reader.py").read_bytes().replace(b"\r\n", b"\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(fetch, name, args, script, start.isoformat(), end.isoformat()) for name in COMMANDS]
        batches = [job.result() for job in jobs]
    items = [i for b in batches for i in b.pop("items", [])]
    print(json.dumps({"schema": 1, "start": start.isoformat(), "end": end.isoformat(),
                      "checked_at": now.isoformat(), "sources": batches, "groups": group(items)},
                     ensure_ascii=True, indent=2))
    return int(any(b["status"] == "failed" for b in batches))


if __name__ == "__main__":
    raise SystemExit(main())
