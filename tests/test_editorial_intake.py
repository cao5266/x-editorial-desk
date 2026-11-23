import sqlite3
import unittest
from datetime import datetime, timezone

from scripts import editorial_intake as intake
from scripts import editorial_source_reader as reader


class IntakeTests(unittest.TestCase):
    healthy = {"active": 2, "errors": 0, "unknown": 0}

    def test_empty_requires_healthy_coverage(self):
        self.assertEqual(intake.status(self.healthy, 0, False), "empty")
        self.assertEqual(intake.status({**self.healthy, "errors": 1}, 0, False), "partial")
        self.assertEqual(intake.status({"active": 1, "errors": 1, "unknown": 0}, 0, False), "failed")
        self.assertEqual(intake.status({**self.healthy, "unknown": 2}, 0, False), "partial")
        self.assertEqual(intake.status({**self.healthy, "active": 0}, 0, False), "no_sources")
        self.assertEqual(intake.status(self.healthy, 1, True), "partial")
        self.assertEqual(intake.status(self.healthy, 1, False), "ok")

    def test_transport_failure_does_not_become_empty_or_save_stderr(self):
        batch = intake.decode("miniflux", 255, b"", failure="ssh_failed")
        self.assertEqual(batch, {"source": "miniflux", "status": "failed", "reason": "ssh_failed"})
        self.assertEqual(intake.decode("radar", 0, b"not JSON")["reason"], "invalid_export")
        self.assertEqual(intake.decode("radar", 0, b'{"items":[]}')["reason"], "invalid_export")

    def test_url_projection_omits_private_or_ambiguous_links(self):
        self.assertEqual(reader.public_url("https://EXAMPLE.org/a/?utm_source=x#part"), "https://example.org/a/")
        for url in ("http://localhost/page", "https://10.0.0.1/a", "https://u:p@example.org/a", "https://example.org/a?token=private", "https://example.org/a?id=1", "file:///tmp/a"):
            self.assertIsNone(reader.public_url(url))

    def test_exact_duplicate_keeps_both_references_but_not_watch_edits(self):
        def ref(source, id, url):
            return {"source": source, "id": id, "url": url}
        base = "https://example.org/changelog"
        inputs = [ref("miniflux", "1", base + "/"), ref("radar", "2", base),
                  ref("changedetection", "3:100", base), ref("changedetection", "3:200", base),
                  ref("radar", "4", None)]
        self.assertEqual([[r["id"] for r in g] for g in intake.group(inputs)],
                         [["1", "2"], ["3:100"], ["3:200"], ["4"]])

    def test_radar_counts_ingestion_separately_from_published_and_runs(self):
        db = sqlite3.connect(":memory:")
        db.executescript("""
            CREATE TABLE sources(id,name,enabled,last_status,last_run_at,interval_sec);
            CREATE TABLE runs(source_id,started_at,status,inserted);
            CREATE TABLE items(id,source_id,title,url,published_at,first_seen_at);
            INSERT INTO sources VALUES ('s','source',1,'ok','2026-11-23T06:56:00Z',600);
            INSERT INTO runs VALUES ('s','2026-11-23T06:56:00Z','ok',0);
            INSERT INTO items VALUES (1,'s','old','https://example.org/old','2026-11-19T00:00:00Z','2026-11-23T06:00:00Z');
        """)
        start = datetime(2026, 11, 22, 7, tzinfo=timezone.utc)
        end = datetime(2026, 11, 23, 7, tzinfo=timezone.utc)
        result = reader.radar(db, start, end)
        self.assertEqual(result["health"], {"active": 1, "errors": 0, "unknown": 0})
        self.assertEqual(result["details"]["runs_by_status"], {"ok": 1})
        self.assertEqual(result["items"][0]["published"], "2026-11-19T00:00:00Z")

    def test_watch_first_snapshot_is_not_a_change(self):
        result = reader.watch_history("100,base.txt\n200,new.txt\n300,next.txt\n", 99, 300)
        self.assertEqual(result, (1, [(200, 100)]))


if __name__ == "__main__":
    unittest.main()
