"""Tkinter companion GUI for CyberGuard; shares the Database and validation classes."""
import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from mode_settings import current_mode, make_database, switch_mode
from incident_service import validate_incident, VALID_SEVERITIES, VALID_STATUSES

class CyberGuardDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CyberGuard | Desktop Incident Manager")
        self.geometry("1100x690")
        self.minsize(820, 520)
        self.configure(bg="#edf3fa")
        self.db = make_database()
        self._build()
        try:
            self.db.connect()
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Database connection", str(exc))
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build(self):
        header = tk.Frame(self, bg="#15294a", padx=22, pady=15)
        header.pack(fill="x")
        tk.Label(header, text="CYBERGUARD", font=("Segoe UI", 22, "bold"), fg="white", bg="#15294a").pack(side="left")
        tk.Label(header, text="Desktop Incident Manager", font=("Segoe UI", 12), fg="#b8d7ff", bg="#15294a").pack(side="left", padx=20)
        mode_bar = ttk.Frame(self, padding=(18, 8))
        mode_bar.pack(fill="x")
        ttk.Label(mode_bar, text="Storage mode:").pack(side="left")
        self.mode_value = tk.StringVar(value=current_mode())
        self.mode_picker = ttk.Combobox(mode_bar, values=("demo", "oracle"), textvariable=self.mode_value,
                                        state="readonly", width=12)
        self.mode_picker.pack(side="left", padx=8)
        ttk.Button(mode_bar, text="Switch mode", command=self.change_mode).pack(side="left")
        self.mode_info = ttk.Label(mode_bar, text="Demo: temporary data | Oracle: permanent data")
        self.mode_info.pack(side="left", padx=16)
        form = ttk.LabelFrame(self, text="Report a new incident", padding=12)
        form.pack(fill="x", padx=18, pady=12)
        self.fields = {}
        for i, (key, label) in enumerate((("title", "Title"), ("category", "Category"), ("reporter", "Reporter"))):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w", padx=5)
            widget = ttk.Entry(form, width=31)
            widget.grid(row=1, column=i, sticky="ew", padx=5, pady=(3,8))
            self.fields[key] = widget
        ttk.Label(form, text="Severity").grid(row=0, column=3, sticky="w", padx=5)
        self.severity = ttk.Combobox(form, values=VALID_SEVERITIES, state="readonly", width=14)
        self.severity.set("Medium")
        self.severity.grid(row=1, column=3, padx=5)
        ttk.Label(form, text="Description").grid(row=2, column=0, sticky="w", padx=5)
        self.description = ttk.Entry(form)
        self.description.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        ttk.Button(form, text="Save incident", command=self.add_incident).grid(row=3, column=3, padx=5)
        for i in range(3): form.columnconfigure(i, weight=1)
        actions = ttk.Frame(self, padding=(18, 4))
        actions.pack(fill="x")
        ttk.Button(actions, text="Refresh", command=self.refresh).pack(side="left", padx=(0,8))
        ttk.Button(actions, text="Export CSV", command=self.export_csv).pack(side="left", padx=8)
        ttk.Button(actions, text="Show analytics", command=self.analytics).pack(side="left", padx=8)
        ttk.Label(actions, text="Selected incident status:").pack(side="left", padx=(24,6))
        self.status = ttk.Combobox(actions, values=VALID_STATUSES, state="readonly", width=20)
        self.status.set("Under Investigation")
        self.status.pack(side="left")
        ttk.Button(actions, text="Update status", command=self.update_status).pack(side="left", padx=8)
        self.summary = ttk.Label(self, text="", padding=(18,8), font=("Segoe UI", 11, "bold"))
        self.summary.pack(fill="x")
        columns = ("ID", "Title", "Category", "Severity", "Status", "Reporter", "Created")
        frame = ttk.Frame(self, padding=(18,0,18,18))
        frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for name in columns:
            self.tree.heading(name, text=name)
            self.tree.column(name, width=120 if name != "Title" else 210, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def change_mode(self):
        requested = self.mode_value.get()
        previous = current_mode()
        if requested == previous:
            messagebox.showinfo("Storage mode", f"Already using {previous} mode.")
            return
        try:
            switch_mode(requested)
            new_db = make_database()
            new_db.connect()
            self.db.close()
            self.db = new_db
            self.refresh()
            messagebox.showinfo("Storage mode", f"Now using {requested} mode. Data is not copied between modes.")
        except Exception as exc:
            self.mode_value.set(previous)
            messagebox.showerror("Switch failed", f"Mode unchanged.\n\n{exc}")

    def refresh(self):
        try:
            self.rows = self.db.fetch_incidents()
            self.tree.delete(*self.tree.get_children())
            for r in self.rows:
                self.tree.insert("", "end", values=(r[0],r[1],r[3],r[4],r[5],r[6],str(r[7])[:19]))
            s = self.db.get_summary()
            self.summary.configure(text=f"Total: {s['total']}     Open: {s['open']}     Investigating: {s['investigating']}     Resolved: {s['resolved']}     High: {s['high']}")
        except Exception as exc: messagebox.showerror("Load error", str(exc))

    def add_incident(self):
        record = {key: widget.get().strip() for key, widget in self.fields.items()}
        record["severity"] = self.severity.get()
        record["description"] = self.description.get().strip()
        error = validate_incident(record)
        if error:
            messagebox.showwarning("Check form", error)
            return
        try:
            self.db.add_incident(**record)
            for widget in self.fields.values(): widget.delete(0, "end")
            self.description.delete(0, "end")
            self.refresh()
            messagebox.showinfo("Saved", "Incident saved successfully")
        except Exception as exc: messagebox.showerror("Save error", str(exc))

    def update_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select incident", "Select a row first")
            return
        incident_id = int(self.tree.item(selected[0], "values")[0])
        try:
            self.db.update_status(incident_id, self.status.get())
            self.refresh()
        except Exception as exc: messagebox.showerror("Update error", str(exc))

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="cyberguard_incidents.csv")
        if not path: return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(("ID", "Title", "Description", "Category", "Severity", "Status", "Reporter", "Created"))
                writer.writerows(self.db.fetch_incidents())
            messagebox.showinfo("Export complete", f"Saved to {path}")
        except Exception as exc: messagebox.showerror("Export error", str(exc))

    def analytics(self):
        try:
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            rows = self.db.fetch_incidents()
            if not rows:
                messagebox.showinfo("Analytics", "No incidents to analyze")
                return
            frame = pd.DataFrame(rows, columns=["id", "title", "description", "category", "severity", "status", "reporter", "created"])
            counts = frame["severity"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
            avg_id = float(np.mean(frame["id"].to_numpy()))
            fig, ax = plt.subplots(figsize=(7,4))
            ax.bar(counts.index, counts.values)
            ax.set_title(f"Incidents by severity | Total {len(frame)} | Average ID {avg_id:.1f}")
            ax.set_ylabel("Incident count")
            fig.tight_layout()
            plt.show()
        except Exception as exc: messagebox.showerror("Analytics error", str(exc))

    def on_close(self):
        self.db.close()
        self.destroy()

if __name__ == "__main__":
    CyberGuardDesktop().mainloop()
