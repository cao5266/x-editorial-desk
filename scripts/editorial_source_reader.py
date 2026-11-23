"""Read selected fields on the existing collection host; write one JSON object to stdout."""

import collections
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit, urlunsplit


LIMIT = 500
UTC = timezone.utc


def public_url(raw):
    try:
        u = urlsplit(raw or "")
        host = (u.hostname or "").lower()
        if (u.scheme not in {"http", "https"} or u.username is not None or u.port is not None
                or not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,63}", host)
                or host.endswith((".localhost", ".local", ".internal", ".lan", ".test"))
                or any(not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}
                       for k, _ in parse_qsl(u.query, keep_blank_values=True))
                or re.search(r"(?i)(?:^|[/;])(?:api[_-]?key|password|access[_-]?token|secret)[=/]", u.path)):
            return None
        return urlunsplit((u.scheme, host, u.path or "/", "", ""))
    except ValueError:
        return None


def iso(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def payload(items, health, details):
    return {"count": len(items), "items": items[:LIMIT], "health": health, "details": details}


def miniflux(start, end):
    sql = f"""
    WITH active AS (SELECT id,title,checked_at,parsing_error_count FROM feeds WHERE NOT disabled),
    recent AS (
      SELECT e.id::text AS id, f.title AS outlet, e.title, e.url,
        e.published_at AS published, e.created_at AS seen
      FROM entries e JOIN active f ON f.id=e.feed_id
      WHERE e.created_at >= '{iso(start)}' AND e.created_at < '{iso(end)}'
    )
    SELECT json_build_object(
      'count', (SELECT count(*) FROM recent),
      'items', COALESCE((SELECT json_agg(r ORDER BY r.seen DESC,r.id) FROM
        (SELECT * FROM recent ORDER BY seen DESC,id LIMIT {LIMIT}) r), '[]'::json),
      'health', (SELECT json_build_object('active',count(*),
        'errors',count(*) FILTER (WHERE parsing_error_count>0),
        'unknown',count(*) FILTER (WHERE COALESCE(parsing_error_count,0)=0 AND
          (checked_at IS NULL OR checked_at < ('{iso(end)}'::timestamptz - interval '24 hours')))) FROM active),
      'details', json_build_object('configured',(SELECT count(*) FROM feeds),
        'last_check',(SELECT max(checked_at) FROM active),
        'published_in_window',(SELECT count(*) FROM recent WHERE published >= '{iso(start)}' AND published < '{iso(end)}'),
        'feed_states',(SELECT COALESCE(json_agg(json_build_object('id',id,'outlet',title,'checked',checked_at,
          'error_count',parsing_error_count) ORDER BY id), '[]'::json) FROM active)));
    """
    cmd = ["sudo", "-n", "docker", "exec", "-i", "ai-monitor-db-1", "sh", "-c",
           'PGCLIENTENCODING=UTF8 PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=10000" '
           'psql -X -v ON_ERROR_STOP=1 -qAt -U "$POSTGRES_USER" -d "$POSTGRES_DB"']
    return json.loads(subprocess.run(cmd, input=sql.encode(), capture_output=True, check=True, timeout=15).stdout)


def radar(db, start, end):
    db.row_factory = sqlite3.Row
    window = (start.timestamp(), end.timestamp())
    sources = [dict(r) for r in db.execute("""
      SELECT id, name AS outlet, last_status, last_run_at, interval_sec
      FROM sources WHERE enabled=1 ORDER BY id
    """)]
    health = {"active": len(sources), "errors": 0, "unknown": 0}
    for s in sources:
        recent_enough = s["last_run_at"] and datetime.fromisoformat(s["last_run_at"]) >= (
            end - timedelta(seconds=max(1800, 3 * (s["interval_sec"] or 0))))
        if s["last_status"] not in ("ok", None, ""):
            health["errors"] += 1
        elif not recent_enough or s["last_status"] != "ok":
            health["unknown"] += 1
    runs = db.execute("""
      SELECT r.status, count(*) AS n, count(CASE WHEN r.status='ok' AND r.inserted=0 THEN 1 END) AS zero
      FROM runs r JOIN sources s ON s.id=r.source_id AND s.enabled=1
      WHERE unixepoch(r.started_at,'subsec') >= ? AND unixepoch(r.started_at,'subsec') < ? GROUP BY r.status
    """, window).fetchall()
    selection = """
      FROM items i JOIN sources s ON s.id=i.source_id AND s.enabled=1
      WHERE unixepoch(i.first_seen_at,'subsec') >= ? AND unixepoch(i.first_seen_at,'subsec') < ?
    """
    count = db.execute("SELECT count(*) " + selection, window).fetchone()[0]
    published = db.execute("SELECT count(*) " + selection + """
      AND unixepoch(i.published_at,'subsec') >= ? AND unixepoch(i.published_at,'subsec') < ?
    """, window * 2).fetchone()[0]
    items = [dict(r) for r in db.execute("""
      SELECT CAST(i.id AS text) AS id, s.name AS outlet, i.title, i.url,
        i.published_at AS published, i.first_seen_at AS seen
    """ + selection + " ORDER BY i.first_seen_at DESC,i.id DESC LIMIT ?", (*window, LIMIT))]
    return {"count": count, "items": items, "health": health, "details": {
        "sources": sources, "runs_by_status": {r["status"]: r["n"] for r in runs},
        "successful_runs_with_zero_inserts": sum(r["zero"] for r in runs), "published_in_window": published,
    }}


def watch_history(data, start, end):
    times = [int(line.split(",", 1)[0]) for line in data.splitlines() if line]
    if not times:
        return 0, []
    return int(start <= times[0] < end), [(t, p) for p, t in zip(times, times[1:]) if start <= t < end]


def changedetection(root, start, end):
    files = sorted(root.glob("*/watch.json"))
    if not root.is_dir() or not (root / "changedetection.json").is_file():
        raise ValueError("unknown datastore layout")
    health = {"active": 0, "errors": 0, "unknown": 0}
    baseline, paused, unreadable = 0, 0, 0
    items, states = [], []
    for f in files:
        try:
            w = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(w, dict) or not isinstance(w.get("paused"), bool):
                raise ValueError("invalid watch")
        except (OSError, ValueError):
            unreadable += 1
            continue
        if w["paused"]:
            paused += 1
            continue
        health["active"] += 1
        checked = w.get("last_checked") or 0
        errored = bool(w.get("last_error")) or (f.parent / "last-error.txt").is_file()
        check_status = w.get("last_check_status")
        errored = errored or (isinstance(check_status, int) and check_status >= 400)
        try:
            n, changes = watch_history((f.parent / "history.txt").read_text(encoding="utf-8"),
                                       start.timestamp(), end.timestamp())
            history_ok = True
        except (OSError, ValueError):
            n, changes, history_ok = 0, [], False
        baseline += n
        if errored:
            state = "error"
            health["errors"] += 1
        elif not history_ok or checked < end.timestamp() - 86400:
            state = "unknown"
            health["unknown"] += 1
        else:
            state = "recent_check"
        states.append({"id": f.parent.name, "url": public_url(w.get("url")), "state": state,
                       "http_status": check_status,
                       "checked": iso(datetime.fromtimestamp(checked, UTC)) if checked else None})
        for t, prev in changes:
            items.append({"id": f"{f.parent.name}:{t}", "watch_id": f.parent.name, "outlet": "page_watch",
                          "title": w.get("title") or "", "url": w.get("url"), "published": None,
                          "seen": iso(datetime.fromtimestamp(t, UTC)),
                          "previous_snapshot": iso(datetime.fromtimestamp(prev, UTC)),
                          "snapshot_ts": t, "previous_snapshot_ts": prev})
    items.sort(key=lambda row: (row["seen"], row["id"]), reverse=True)
    if not files:
        raise ValueError("no watch files found in expected layout")
    return payload(items, health, {"configured": len(files), "paused": paused, "baseline_only": baseline,
                                     "unreadable_watches": unreadable, "watch_states": states})


def main():
    source, start, end = sys.argv[1:]
    start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if source == "miniflux":
        data = miniflux(start, end)
    elif source == "radar":
        with sqlite3.connect("file:/opt/freebie-radar-test/data/radar.db?mode=ro", uri=True) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")
            data = radar(db, start, end)
    elif source == "changedetection":
        data = changedetection(Path("/datastore"), start, end)
    else:
        raise ValueError("unknown source")
    for item in data["items"]:
        item["url"] = public_url(item["url"])
    print(json.dumps(data, ensure_ascii=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error, subprocess.SubprocessError):
        # No exception payload, environment values or upstream error bodies leave the server.
        raise SystemExit(20) from None
