"""Database access layer. Demo mode uses sample records; Oracle mode uses python-oracledb."""
import os
from datetime import datetime, timedelta

class Database:
    # Shared demo storage keeps additions and status changes visible across requests.
    _shared_demo_incidents = None
    _shared_demo_audit = None

    def __init__(self, username="INCIDENT_USER", password="", dsn="localhost:1521/freepdb1", demo_mode=True):
        self.username, self.password, self.dsn = username, password, dsn
        self.demo_mode = demo_mode
        self.connection = None

    def connect(self):
        if self.demo_mode:
            if Database._shared_demo_incidents is None:
                now = datetime.now()
                Database._shared_demo_incidents = [
                    (1042, "Suspicious login attempts", "Repeated failed logins from an unfamiliar IP.", "Unauthorized Access", "High", "Under Investigation", "Alex Morgan", now - timedelta(hours=2)),
                    (1041, "Suspicious email reported", "Employee reported an email asking for credentials.", "Phishing", "Medium", "Open", "Jamie Lee", now - timedelta(hours=5)),
                    (1040, "Malware detected on workstation", "Endpoint alert flagged a suspicious executable.", "Malware", "High", "Resolved", "Taylor Reed", now - timedelta(days=1)),
                    (1039, "Unusual outbound traffic", "Traffic spike to an unfamiliar external host.", "Network Attack", "Low", "Open", "Sam Patel", now - timedelta(days=2)),
                    (1038, "Access permission review", "Review of unexpected access to a shared folder.", "Unauthorized Access", "Medium", "Under Investigation", "Alex Morgan", now - timedelta(days=3)),
                    (1037, "Potential data exposure", "Sensitive file appeared in an unapproved location.", "Data Breach", "High", "Open", "Jordan Kim", now - timedelta(days=4)),
                    (1036, "Endpoint update failure", "Security updates failed on a test machine.", "Other", "Low", "Resolved", "Jamie Lee", now - timedelta(days=5)),
                    (1035, "Reported phishing attachment", "Suspicious attachment isolated for review.", "Phishing", "Medium", "Resolved", "Sam Patel", now - timedelta(days=6)),
                ]
                Database._shared_demo_audit = [
                    (501, 1042, "STATUS UPDATE", now - timedelta(minutes=22), "Status changed from Open to Under Investigation"),
                    (500, 1040, "INSERT", now - timedelta(days=1), "Incident created"),
                    (499, 1039, "INSERT", now - timedelta(days=2), "Incident created"),
                ]
            return
        try:
            import oracledb
        except ImportError as exc:
            raise RuntimeError("Oracle driver missing. Run: python -m pip install oracledb") from exc
        self.connection = oracledb.connect(user=self.username, password=self.password, dsn=self.dsn)

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def fetch_incidents(self):
        if self.demo_mode:
            return sorted(Database._shared_demo_incidents or [], key=lambda r: r[7], reverse=True)
        with self.connection.cursor() as cur:
            cur.execute("""SELECT incident_id, title, description, category, severity, status, reporter, created_at
                           FROM SYSTEM.INCIDENTS ORDER BY created_at DESC""")
            return cur.fetchall()

    def get_summary(self):
        rows = self.fetch_incidents()
        return {
            "total": len(rows),
            "open": sum(r[5] == "Open" for r in rows),
            "investigating": sum(r[5] == "Under Investigation" for r in rows),
            "resolved": sum(r[5] == "Resolved" for r in rows),
            "high": sum(r[4] == "High" for r in rows),
        }

    def add_incident(self, title, description, category, severity, reporter):
        if self.demo_mode:
            rows = Database._shared_demo_incidents if Database._shared_demo_incidents is not None else []
            new_id = max([r[0] for r in rows], default=1042) + 1
            created = datetime.now()
            rows.insert(0, (new_id, title, description, category, severity, "Open", reporter, created))
            Database._shared_demo_audit.insert(0, (max([a[0] for a in Database._shared_demo_audit], default=500) + 1,
                                        new_id, "INSERT", created, "Incident created"))
            return
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO SYSTEM.INCIDENTS
                           (title, description, category, severity, status, reporter)
                           VALUES (:title, :description, :category, :severity, 'Open', :reporter)""",
                        title=title, description=description, category=category,
                        severity=severity, reporter=reporter)
        self.connection.commit()

    def update_status(self, incident_id, new_status):
        if self.demo_mode:
            for i, row in enumerate(Database._shared_demo_incidents or []):
                if row[0] == incident_id:
                    old_status = row[5]
                    Database._shared_demo_incidents[i] = row[:5] + (new_status,) + row[6:]
                    Database._shared_demo_audit.insert(0, (max([a[0] for a in Database._shared_demo_audit], default=500) + 1,
                                                incident_id, "STATUS UPDATE", datetime.now(),
                                                f"Status changed from {old_status} to {new_status}"))
                    return
            raise ValueError(f"Incident #{incident_id} was not found.")
        with self.connection.cursor() as cur:
            cur.callproc("SYSTEM.UPDATE_INCIDENT_STATUS", [int(incident_id), new_status])
        self.connection.commit()

    def fetch_audit(self):
        if self.demo_mode:
            return list(Database._shared_demo_audit or [])
        with self.connection.cursor() as cur:
            cur.execute("""SELECT audit_id, incident_id, action, action_time, details
                           FROM SYSTEM.INCIDENT_AUDIT ORDER BY action_time DESC""")
            return cur.fetchall()

    def counts_by_severity(self):
        rows = self.fetch_incidents()
        return {key: sum(r[4] == key for r in rows) for key in ("High", "Medium", "Low")}

    def counts_by_status(self):
        rows = self.fetch_incidents()
        return {key: sum(r[5] == key for r in rows)
                for key in ("Open", "Under Investigation", "Resolved")}
