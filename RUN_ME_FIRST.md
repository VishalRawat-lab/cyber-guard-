# CyberGuard Enhanced — Windows instructions

This package extends your uploaded CyberGuard files with a **Tkinter desktop GUI** and the missing Flask HTML/CSS files. It does not replace your BookTrail project.

## 1. Extract the ZIP
Extract to `D:\CyberGuard_Enhanced` (or another folder). Open that folder in VS Code.

## 2. Install packages
Open VS Code > Terminal > New Terminal (PowerShell):

```powershell
python --version
python -m pip install -r requirements.txt
```

Tkinter is normally included with the Windows Python installer. Check it with `python -m tkinter`.

## 3. Start Tkinter desktop application

```powershell
$env:TRACKER_DEMO="1"
python desktop_app.py
```

A window opens. Try adding an incident, changing its status, exporting a CSV, and clicking **Show analytics**.

## 4. Start Flask website
Open a SECOND terminal in the same folder:

```powershell
$env:TRACKER_DEMO="1"
python app.py
```

Open `http://127.0.0.1:5000` in your browser. Use any nonempty username and password for this college demo.

**Important:** Demo mode uses sample data in Python memory. The desktop and web programs run as separate processes, so demo changes do **not** sync between them. Restarting either app resets its demo changes.

## 5. Oracle mode (optional, only after your Oracle schema is ready)
Your uploaded `database_setup.sql` is NOT a complete database initializer. It assumes the `SYSTEM.INCIDENTS`, `SYSTEM.INCIDENT_AUDIT` tables and `SYSTEM.UPDATE_INCIDENT_STATUS` procedure already exist. It also assumes an `INCIDENT_USER` account exists and has appropriate privileges. Do not run it until those prerequisites are confirmed.

In EACH PowerShell terminal used to start the app:

```powershell
$env:TRACKER_DEMO="0"
$env:ORACLE_USER="INCIDENT_USER"
$env:ORACLE_PASSWORD=Read-Host "Oracle password"
$env:ORACLE_DSN="localhost:1521/freepdb1"
python desktop_app.py
```

For the website, replace the last command with `python app.py`. Never share your password in chat or commit it to files. The two apps share Oracle records when both connect to the same database.

## 6. Python syllabus demonstration
- Tkinter: windows, labels, Entry, Combobox, buttons, Treeview, events and message boxes (`desktop_app.py`)
- OOP: `CyberGuardDesktop` class, inheritance from `tk.Tk`, and `Database` class
- Functions, conditionals, loops and input validation: `incident_service.py`, `desktop_app.py`
- Exception handling: try/except blocks
- File handling: CSV export with `open()` and `csv.writer`
- Pandas: DataFrame and value counts; NumPy: mean; Matplotlib: bar chart
- Flask: routes, templates, forms and sessions (`app.py`)
- Oracle/PLSQL: optional database mode (`database.py`, `database_setup.sql`)

This covers these topics, not necessarily **every topic** in your college syllabus; check your official syllabus for any remaining units.

## Switching Demo / Oracle while the app is running
- Desktop: select Demo or Oracle in **Storage mode**, then click **Switch mode**.
- Website: after login, use the **Storage** selector above the page and click **Switch mode**.
- The choice is shared between both applications and saved in `mode_settings.json` (no passwords stored). Refresh the website or restart the desktop app if you switch from the other interface.
- Oracle switching checks both login and access to `SYSTEM.INCIDENTS`. If either fails, the current mode is kept.
- Before starting either app for Oracle mode, configure credentials in the **same PowerShell terminal**:
  ```powershell
  $env:ORACLE_USER="INCIDENT_USER"
  $env:ORACLE_PASSWORD=Read-Host "Oracle password"
  $env:ORACLE_DSN="localhost:1521/freepdb1"
  ```
- The existing `database_setup.sql` assumes Oracle tables, user and procedure already exist; the file does NOT create them. Oracle mode cannot work until those objects and grants are configured.
- Demo data and Oracle data are separate. Switching does NOT copy records. Demo records reset when the relevant Python process exits.
- Do not use real secrets in screenshots, commits, or shared ZIP files.
