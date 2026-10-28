import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from mode_settings import current_mode, make_database, switch_mode
from incident_service import validate_incident, VALID_SEVERITIES, VALID_STATUSES

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-demo-secret-change-me")

def demo_mode():
    return current_mode() == "demo"


def make_db():
    return make_database()


@app.route("/mode", methods=["POST"])
def change_mode():
    if not session.get("username"):
        return redirect(url_for("login"))
    requested = request.form.get("mode", "")
    try:
        switch_mode(requested)
        flash(f"Switched to {requested.title()} mode.", "success")
    except Exception as exc:
        flash(f"Mode unchanged: {exc}", "error")
    return redirect(url_for("dashboard"))


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper

@app.context_processor
def shared_template_values():
    return {"demo_mode": demo_mode(), "storage_mode": current_mode()}

@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("username"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Enter a username and password to continue.", "error")
        else:
            # This is a college-project demo login. Oracle mode still uses the
            # credentials configured in environment variables for DB access.
            if not demo_mode():
                try:
                    db = make_db()
                    db.connect()
                    db.close()
                except Exception as exc:
                    flash(f"Oracle connection failed: {exc}", "error")
                    return render_template("login.html")
            session["username"] = username
            flash("Welcome back. You are signed in.", "success")
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = make_db()
    try:
        db.connect()
        rows = db.fetch_incidents()
        summary = db.get_summary()
        severity_counts = db.counts_by_severity()
        status_counts = db.counts_by_status()
        return render_template("dashboard.html", incidents=rows[:6], summary=summary,
                               severity_counts=severity_counts, status_counts=status_counts,
                               username=session["username"])
    except Exception as exc:
        flash(f"Could not load dashboard: {exc}", "error")
        return render_template("dashboard.html", incidents=[], summary={}, severity_counts={},
                               status_counts={}, username=session["username"])
    finally:
        db.close()

@app.route("/incidents")
@login_required
def incidents():
    db = make_db()
    try:
        db.connect()
        rows = db.fetch_incidents()
    except Exception as exc:
        rows = []
        flash(f"Could not load incidents: {exc}", "error")
    finally:
        db.close()
    return render_template("incidents.html", incidents=rows, username=session["username"])

@app.route("/incidents/new", methods=["GET", "POST"])
@login_required
def add_incident():
    record = {}
    if request.method == "POST":
        record = {k: request.form.get(k, "").strip() for k in
                  ("title", "description", "category", "severity", "reporter")}
        error = validate_incident(record)
        if error:
            flash(error, "error")
        else:
            db = make_db()
            try:
                db.connect()
                db.add_incident(**record)
                flash("Incident report saved.", "success")
                return redirect(url_for("incidents"))
            except Exception as exc:
                flash(f"Could not save incident: {exc}", "error")
            finally:
                db.close()
    return render_template("add_incident.html", record=record, severities=VALID_SEVERITIES,
                           username=session["username"])

@app.route("/incidents/<int:incident_id>/status", methods=["POST"])
@login_required
def update_status(incident_id):
    status = request.form.get("status", "")
    if status not in VALID_STATUSES:
        flash("Please select a valid status.", "error")
        return redirect(request.referrer or url_for("incidents"))
    db = make_db()
    try:
        db.connect()
        db.update_status(incident_id, status)
        flash(f"Incident #{incident_id} status updated.", "success")
    except Exception as exc:
        flash(f"Could not update status: {exc}", "error")
    finally:
        db.close()
    return redirect(request.referrer or url_for("incidents"))

@app.route("/audit")
@login_required
def audit():
    db = make_db()
    try:
        db.connect()
        rows = db.fetch_audit()
    except Exception as exc:
        rows = []
        flash(f"Could not load audit history: {exc}", "error")
    finally:
        db.close()
    return render_template("audit.html", rows=rows, username=session["username"])

@app.route("/analytics")
@login_required
def analytics():
    db = make_db()
    try:
        db.connect()
        rows = db.fetch_incidents()
        summary = db.get_summary()
        severity_counts = db.counts_by_severity()
        status_counts = db.counts_by_status()
        # Use Pandas and NumPy to demonstrate syllabus topics in a real feature.
        import pandas as pd
        import numpy as np
        if rows:
            frame = pd.DataFrame(rows, columns=[
                "incident_id", "title", "description", "category", "severity",
                "status", "reporter", "created_at"
            ])
            summary["average_incident_id"] = round(float(np.mean(frame["incident_id"].to_numpy())), 1)
            summary["categories_count"] = int(frame["category"].nunique())
            # Matplotlib creates a chart image from the same database records.
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from pathlib import Path
            chart_dir = Path(app.static_folder) / "generated"
            chart_dir.mkdir(parents=True, exist_ok=True)
            order = ["High", "Medium", "Low"]
            counts = frame["severity"].value_counts().reindex(order, fill_value=0)
            fig, ax = plt.subplots(figsize=(6.5, 3.1))
            bars = ax.bar(counts.index, counts.values)
            ax.set_title("Incidents by severity", loc="left", pad=14, fontsize=12, fontweight="bold")
            ax.set_ylabel("Number of incidents")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", alpha=0.2)
            ax.set_axisbelow(True)
            ax.bar_label(bars, padding=3)
            fig.tight_layout()
            fig.savefig(chart_dir / "severity_chart.png", dpi=140, bbox_inches="tight")
            plt.close(fig)
        else:
            summary["average_incident_id"] = 0
            summary["categories_count"] = 0
    except Exception as exc:
        summary, severity_counts, status_counts = {}, {}, {}
        flash(f"Could not load analytics: {exc}", "error")
    finally:
        db.close()
    return render_template("analytics.html", summary=summary, severity_counts=severity_counts,
                           status_counts=status_counts, username=session["username"])

if __name__ == "__main__":
    app.run(debug=True)
