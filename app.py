"""
app.py — Gym Membership System
Group 9 | Leader: Directo, Brix A.
Members: Quimson Jibreel A., Madayag Djaunathan Albert S.

Flask application — controls gym entry and verifies active members
using DeepFace face recognition.
"""

from flask import (Flask, render_template, Response, request,
                   session, redirect, url_for, jsonify)
import os
import csv
import io
import json
import calendar
import threading
import shutil
import hashlib
import time as time_module
import cv2
from datetime import datetime, date, timedelta
from functools import wraps
from camera import generate_frames, _stream as _camera_stream
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "gym_secret_key_change_in_prod")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DATASET_PATH  = "dataset"
ENTRY_LOG     = "entry_log.csv"
MEMBERS_FILE  = "members.json"
ADMINS_FILE   = "admins.json"
PAYMENTS_FILE = "payments.json"
AUDIT_LOG     = "audit_log.csv"
BACKUP_DIR    = "backups"
CACHE_FILE    = os.path.join(
    DATASET_PATH,
    "ds_model_vggface_detector_opencv_aligned_normalization_base_expand_0.pkl"
)

# Rate limiting for login
_login_attempts = {}
_login_lock = threading.Lock()
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300  # 5 minutes

# File-level lock to prevent concurrent JSON corruption
_members_lock = threading.Lock()
_admins_lock = threading.Lock()

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

# Ensure admins file exists with default admin
def _init_admins():
    if not os.path.exists(ADMINS_FILE):
        default_admins = [{
            "username": "admin",
            "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
            "role": "superadmin",
            "full_name": "System Administrator",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }]
        with open(ADMINS_FILE, "w") as f:
            json.dump(default_admins, f, indent=2)

_init_admins()


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_members():
    with _members_lock:
        if not os.path.exists(MEMBERS_FILE):
            return []
        with open(MEMBERS_FILE, "r") as f:
            members = json.load(f)
        # Ensure all members have the expected keys (migration for older records)
        defaults = {"gender": "", "birthday": "", "address": "",
                    "emergency_contact": "", "notes": "", "total_visits": 0,
                    "registered_at": ""}
        for m in members:
            for key, val in defaults.items():
                if key not in m:
                    m[key] = val
        return members


def save_members(members):
    with _members_lock:
        with open(MEMBERS_FILE, "w") as f:
            json.dump(members, f, indent=2)


def get_member_by_folder(folder_name):
    for m in load_members():
        if m["folder_name"] == folder_name:
            return m
    return None


def is_logged_in():
    if session.get("admin") is not True:
        return False
    # Check session timeout (2 hours of inactivity)
    last_active = session.get("last_active")
    if last_active:
        try:
            last_dt = datetime.fromisoformat(last_active)
            if datetime.now() - last_dt > timedelta(hours=2):
                session.clear()
                return False
        except (ValueError, TypeError):
            pass
    session["last_active"] = datetime.now().isoformat()
    return True


def login_required(f):
    """Decorator to protect routes that require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def check_rate_limit(ip):
    """Returns (allowed: bool, seconds_remaining: int)"""
    with _login_lock:
        if ip not in _login_attempts:
            return True, 0
        attempts, lockout_time = _login_attempts[ip]
        if lockout_time and time_module.time() < lockout_time:
            remaining = int(lockout_time - time_module.time())
            return False, remaining
        if lockout_time and time_module.time() >= lockout_time:
            # Lockout expired, reset
            del _login_attempts[ip]
            return True, 0
        return True, 0


def record_login_attempt(ip, success):
    """Track failed login attempts for rate limiting."""
    with _login_lock:
        if success:
            _login_attempts.pop(ip, None)
            return
        if ip not in _login_attempts:
            _login_attempts[ip] = [1, None]
        else:
            _login_attempts[ip][0] += 1
        if _login_attempts[ip][0] >= MAX_LOGIN_ATTEMPTS:
            _login_attempts[ip][1] = time_module.time() + LOGIN_LOCKOUT_SECONDS


def clear_deepface_cache():
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
            print("[Watcher] Dataset changed — DeepFace cache cleared.")
        except (PermissionError, FileNotFoundError):
            print("[Watcher] Cache already gone or in use, skipping.")


# ── Admin helpers ─────────────────────────────────────────────────────────────

def load_admins():
    with _admins_lock:
        if not os.path.exists(ADMINS_FILE):
            return []
        with open(ADMINS_FILE, "r") as f:
            return json.load(f)


def save_admins(admins):
    with _admins_lock:
        with open(ADMINS_FILE, "w") as f:
            json.dump(admins, f, indent=2)


def get_admin(username):
    for a in load_admins():
        if a["username"] == username:
            return a
    return None


def get_current_admin():
    """Get the current logged-in admin's data."""
    username = session.get("user", "")
    return get_admin(username)


def is_superadmin():
    """Check if current user is a superadmin."""
    admin = get_current_admin()
    return admin and admin.get("role") == "superadmin"


# ── Payment helpers ───────────────────────────────────────────────────────────

_payments_lock = threading.Lock()

def load_payments():
    with _payments_lock:
        if not os.path.exists(PAYMENTS_FILE):
            return []
        with open(PAYMENTS_FILE, "r") as f:
            return json.load(f)


def save_payments(payments):
    with _payments_lock:
        with open(PAYMENTS_FILE, "w") as f:
            json.dump(payments, f, indent=2)


def get_member_payments(folder_name):
    return [p for p in load_payments() if p.get("folder_name") == folder_name]


# ── Audit log helpers ─────────────────────────────────────────────────────────

_audit_lock = threading.Lock()

def log_audit(action, target, details=""):
    """Log an admin action to the audit trail."""
    import csv as csv_mod
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    admin_user = session.get("user", "system")
    with _audit_lock:
        file_exists = os.path.exists(AUDIT_LOG)
        with open(AUDIT_LOG, "a", newline="") as f:
            writer = csv_mod.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Admin", "Action", "Target", "Details"])
            writer.writerow([now, admin_user, action, target, details])


# ── Check-in/Check-out state ─────────────────────────────────────────────────

_checkin_lock = threading.Lock()
_checked_in = {}  # folder_name -> {"time": datetime_str, "full_name": str}


# ── Dataset watcher ───────────────────────────────────────────────────────────

class DatasetChangeHandler(FileSystemEventHandler):
    def on_created(self, _event):  clear_deepface_cache()
    def on_deleted(self, _event):  clear_deepface_cache()
    def on_moved(self, _event):    clear_deepface_cache()


_observer = Observer()
_observer.schedule(DatasetChangeHandler(), path=DATASET_PATH, recursive=True)
_observer.daemon = True
_observer.start()

# ── Face capture state ────────────────────────────────────────────────────────

capture_state = {}


def generate_capture_frames(name, target=50):
    save_path = os.path.join(DATASET_PATH, name)
    os.makedirs(save_path, exist_ok=True)

    # Find the next available file number (for appending more photos)
    existing = [f for f in os.listdir(save_path) if f.endswith(".jpg")]
    start_count = len(existing)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    count = 0
    capture_state[name] = {"count": 0, "total": target, "done": False, "existing": start_count}

    while count < target:
        frame = _camera_stream.read()
        if frame is None:
            import time
            time.sleep(0.05)
            continue

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray  = cv2.equalizeHist(gray)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(100, 100))

        if len(faces) > 0:
            # Pick the largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            if w >= 80 and h >= 80:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 136), 2)
                face_img = frame[y:y+h, x:x+w]
                # Normalize: resize to 224x224 and enhance contrast
                face_img = cv2.resize(face_img, (224, 224), interpolation=cv2.INTER_LANCZOS4)
                lab = cv2.cvtColor(face_img, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                face_img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
                file_num = start_count + count
                cv2.imwrite(os.path.join(save_path, f"{file_num}.jpg"), face_img,
                            [cv2.IMWRITE_JPEG_QUALITY, 95])
                count += 1
                capture_state[name]["count"] = count

        cv2.putText(frame, f"Capturing: {count}/{target}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 136), 2)
        cv2.putText(frame, "Keep your face in frame", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        if start_count > 0:
            cv2.putText(frame, f"({start_count} existing + {count} new)", (10, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 100), 1)

        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
               + buffer.tobytes() + b'\r\n')

    capture_state[name]["done"] = True
    clear_deepface_cache()


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/")
def landing():
    """Public landing page."""
    if is_logged_in():
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        allowed, remaining = check_rate_limit(ip)

        if not allowed:
            error = f"Too many failed attempts. Try again in {remaining} seconds."
        else:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            admin = get_admin(username)
            if admin and admin["password_hash"] == password_hash:
                record_login_attempt(ip, success=True)
                session.permanent = True
                session["admin"] = True
                session["user"]  = username
                session["role"]  = admin.get("role", "staff")
                session["last_active"] = datetime.now().isoformat()
                return redirect(url_for("dashboard"))
            else:
                record_login_attempt(ip, success=False)
                error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Admin registration — only superadmins can create new accounts."""
    if not is_logged_in():
        return redirect(url_for("login"))
    if not is_superadmin():
        return redirect(url_for("dashboard"))

    error = None
    success = None

    if request.method == "POST":
        username  = request.form.get("username", "").strip().lower()
        password  = request.form.get("password", "")
        confirm   = request.form.get("confirm_password", "")
        full_name = request.form.get("full_name", "").strip()
        role      = request.form.get("role", "staff")

        if not username or not password or not full_name:
            error = "All fields are required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif get_admin(username):
            error = f"Username '{username}' already exists."
        elif role not in ("staff", "superadmin"):
            error = "Invalid role."
        else:
            admins = load_admins()
            admins.append({
                "username": username,
                "password_hash": hashlib.sha256(password.encode()).hexdigest(),
                "role": role,
                "full_name": full_name,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            save_admins(admins)
            success = f"Account '{username}' created successfully as {role}."

    admins = load_admins()
    return render_template("register_admin.html", error=error, success=success,
                           admins=admins, is_super=True)


@app.route("/admin/delete/<username>", methods=["POST"])
@login_required
def delete_admin(username):
    """Delete an admin account (superadmin only, can't delete yourself)."""
    if not is_superadmin():
        return redirect(url_for("dashboard"))
    if username == session.get("user"):
        return redirect(url_for("register"))  # Can't delete yourself
    admins = [a for a in load_admins() if a["username"] != username]
    save_admins(admins)
    return redirect(url_for("register"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


# ── Main pages ────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    members = load_members()
    total     = len(members)
    active    = sum(1 for m in members if m.get("status") == "active")
    expired   = sum(1 for m in members if m.get("status") == "expired")
    suspended = sum(1 for m in members if m.get("status") == "suspended")
    frozen    = sum(1 for m in members if m.get("status") == "frozen")

    # Members expiring within 7 days
    expiring_soon = []
    today = date.today()
    for m in members:
        if m.get("status") == "active":
            try:
                exp = datetime.strptime(m["expiry_date"], "%Y-%m-%d").date()
                days_left = (exp - today).days
                if 0 <= days_left <= 7:
                    expiring_soon.append({"name": m["full_name"], "days": days_left})
            except (ValueError, KeyError):
                pass

    # Today's entries
    today_entries = 0
    if os.path.exists(ENTRY_LOG):
        today_str = date.today().strftime("%Y-%m-%d")
        with open(ENTRY_LOG, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2 and row[1].startswith(today_str):
                    today_entries += 1

    return render_template("index.html",
                           user=session["user"],
                           total=total,
                           active=active,
                           expired=expired,
                           suspended=suspended,
                           frozen=frozen,
                           today_entries=today_entries,
                           expiring_soon=expiring_soon)


@app.route("/video")
@login_required
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ── Members management ────────────────────────────────────────────────────────

@app.route("/members")
@login_required
def members_list():
    members = load_members()
    today = date.today()
    changed = False
    for m in members:
        if m.get("status") == "active":
            try:
                exp = datetime.strptime(m["expiry_date"], "%Y-%m-%d").date()
                if exp < today:
                    m["status"] = "expired"
                    changed = True
                m["days_left"] = (exp - today).days
            except (ValueError, KeyError):
                m["days_left"] = None
        elif m.get("status") == "frozen":
            # Frozen members: show days_left but don't auto-expire
            try:
                exp = datetime.strptime(m["expiry_date"], "%Y-%m-%d").date()
                m["days_left"] = (exp - today).days
            except (ValueError, KeyError):
                m["days_left"] = None
        else:
            m["days_left"] = None
    if changed:
        save_members(members)

    # Search filter
    search = request.args.get("search", "").strip().lower()
    if search:
        members = [m for m in members
                   if search in m.get("full_name", "").lower()
                   or search in m.get("membership_type", "").lower()
                   or search in m.get("status", "").lower()
                   or search in m.get("contact", "").lower()
                   or search in m.get("email", "").lower()]

    return render_template("members.html", members=members, search=search)


@app.route("/members/add", methods=["GET", "POST"])
@login_required
def add_member():
    if request.method == "POST":
        full_name       = request.form.get("full_name", "").strip()
        membership_type = request.form.get("membership_type", "monthly")
        status          = request.form.get("status", "active")
        start_date      = request.form.get("start_date", "")
        expiry_date     = request.form.get("expiry_date", "")
        contact         = request.form.get("contact", "").strip()
        email           = request.form.get("email", "").strip()
        emergency_contact = request.form.get("emergency_contact", "").strip()
        notes           = request.form.get("notes", "").strip()
        gender          = request.form.get("gender", "").strip()
        birthday        = request.form.get("birthday", "").strip()
        address         = request.form.get("address", "").strip()

        if not full_name:
            return render_template("add_member.html", error="Full name is required.")

        # Validate dates
        if start_date and expiry_date:
            try:
                s = datetime.strptime(start_date, "%Y-%m-%d").date()
                e = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                if e <= s:
                    return render_template("add_member.html",
                                           error="Expiry date must be after start date.")
            except ValueError:
                return render_template("add_member.html",
                                       error="Invalid date format.")

        # Generate folder name from full name
        folder_name = "_".join(w.capitalize() for w in full_name.split())
        folder_name = "".join(c for c in folder_name if c.isalnum() or c == "_")

        members = load_members()
        if any(m["folder_name"] == folder_name for m in members):
            return render_template("add_member.html",
                                   error=f"A member with folder '{folder_name}' already exists.")

        members.append({
            "folder_name":       folder_name,
            "full_name":         full_name,
            "membership_type":   membership_type,
            "status":            status,
            "start_date":        start_date,
            "expiry_date":       expiry_date,
            "contact":           contact,
            "email":             email,
            "emergency_contact": emergency_contact,
            "notes":             notes,
            "gender":            gender,
            "birthday":          birthday,
            "address":           address,
            "registered_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_visits":      0,
        })
        save_members(members)

        # Store for face capture
        session["capture_name"] = folder_name
        log_audit("member_added", full_name, f"Type: {membership_type}, Expiry: {expiry_date}")
        return redirect(url_for("capture_face"))

    return render_template("add_member.html", error=None)


@app.route("/members/edit/<folder_name>", methods=["GET", "POST"])
@login_required
def edit_member(folder_name):
    members = load_members()
    member  = next((m for m in members if m["folder_name"] == folder_name), None)
    if not member:
        return redirect(url_for("members_list"))

    if request.method == "POST":
        member["full_name"]         = request.form.get("full_name", member["full_name"]).strip()
        member["membership_type"]   = request.form.get("membership_type", member["membership_type"])
        member["status"]            = request.form.get("status", member["status"])
        member["start_date"]        = request.form.get("start_date", member["start_date"])
        member["expiry_date"]       = request.form.get("expiry_date", member["expiry_date"])
        member["contact"]           = request.form.get("contact", member.get("contact", "")).strip()
        member["email"]             = request.form.get("email", member.get("email", "")).strip()
        member["emergency_contact"] = request.form.get("emergency_contact", member.get("emergency_contact", "")).strip()
        member["notes"]             = request.form.get("notes", member.get("notes", "")).strip()
        member["gender"]            = request.form.get("gender", member.get("gender", "")).strip()
        member["birthday"]          = request.form.get("birthday", member.get("birthday", "")).strip()
        member["address"]           = request.form.get("address", member.get("address", "")).strip()
        save_members(members)
        return redirect(url_for("members_list"))

    return render_template("edit_member.html", member=member)


@app.route("/members/delete/<folder_name>", methods=["POST"])
@login_required
def delete_member(folder_name):
    # Get name before deleting
    member = get_member_by_folder(folder_name)
    member_name = member["full_name"] if member else folder_name
    # Remove from member registry
    members = [m for m in load_members() if m["folder_name"] != folder_name]
    save_members(members)
    # Remove face dataset folder so DeepFace no longer recognizes them
    dataset_folder = os.path.join(DATASET_PATH, folder_name)
    if os.path.exists(dataset_folder):
        shutil.rmtree(dataset_folder, ignore_errors=True)
    clear_deepface_cache()
    log_audit("member_deleted", member_name, f"Folder: {folder_name}")
    return redirect(url_for("members_list"))


@app.route("/members/suspend/<folder_name>", methods=["POST"])
@login_required
def suspend_member(folder_name):
    """Toggle suspend/activate a member."""
    members = load_members()
    member = next((m for m in members if m["folder_name"] == folder_name), None)
    if member:
        if member["status"] == "suspended":
            member["status"] = "active"
            log_audit("member_activated", member["full_name"], "Unsuspended")
        else:
            member["status"] = "suspended"
            log_audit("member_suspended", member["full_name"], "")
        save_members(members)
    return redirect(url_for("members_list"))


# ── Entry log ─────────────────────────────────────────────────────────────────

@app.route("/entry-log")
@login_required
def entry_log():
    date_filter = request.args.get("date", "")  # e.g. "2026-05-01"

    records = []
    if os.path.exists(ENTRY_LOG):
        with open(ENTRY_LOG, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                while len(row) < 8:   # Name,Time,Access,Reason,Emotion,Gender,Age,Confidence
                    row.append("")
                if date_filter and not row[1].startswith(date_filter):
                    continue
                records.append(row)

    records.reverse()  # newest first
    return render_template("entry_log.html", records=records,
                           date_filter=date_filter,
                           today=date.today().strftime("%Y-%m-%d"))


@app.route("/entry-log/clear", methods=["POST"])
@login_required
def clear_entry_log():
    with open(ENTRY_LOG, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Time", "Access", "Reason", "Emotion", "Gender", "Age", "Confidence"])
    return redirect(url_for("entry_log"))


@app.route("/entry-log/export")
@login_required
def export_entry_log():
    """Export entry log as downloadable CSV file."""
    if not os.path.exists(ENTRY_LOG):
        return redirect(url_for("entry_log"))

    date_filter = request.args.get("date", "")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Time", "Access", "Reason", "Emotion", "Gender", "Age", "Confidence"])

    with open(ENTRY_LOG, "r") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if date_filter and len(row) >= 2 and not row[1].startswith(date_filter):
                continue
            writer.writerow(row)

    output.seek(0)
    filename = f"entry_log_{date_filter or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── Analytics / Reports ───────────────────────────────────────────────────────

@app.route("/analytics")
@login_required
def analytics():
    """Attendance analytics and reports page."""
    members = load_members()

    # Gather entry log data
    daily_counts = {}  # date_str -> {"granted": n, "denied": n}
    member_visits = {}  # name -> count
    hourly_dist = [0] * 24  # hour -> count
    emotion_counts = {}

    if os.path.exists(ENTRY_LOG):
        with open(ENTRY_LOG, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) < 3:
                    continue
                name = row[0]
                timestamp = row[1]
                access = row[2]

                # Daily counts
                day_str = timestamp[:10] if len(timestamp) >= 10 else ""
                if day_str:
                    if day_str not in daily_counts:
                        daily_counts[day_str] = {"granted": 0, "denied": 0}
                    if access == "granted":
                        daily_counts[day_str]["granted"] += 1
                    else:
                        daily_counts[day_str]["denied"] += 1

                # Member visit counts
                if access == "granted" and name:
                    member_visits[name] = member_visits.get(name, 0) + 1

                # Hourly distribution
                try:
                    hour = int(timestamp[11:13])
                    hourly_dist[hour] += 1
                except (ValueError, IndexError):
                    pass

                # Emotion counts
                if len(row) >= 5 and row[4]:
                    emotion = row[4]
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

    # Sort daily counts by date (last 30 days)
    today = date.today()
    last_30 = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    daily_data = []
    for d in last_30:
        counts = daily_counts.get(d, {"granted": 0, "denied": 0})
        daily_data.append({"date": d, "granted": counts["granted"], "denied": counts["denied"]})

    # Top visitors
    top_visitors = sorted(member_visits.items(), key=lambda x: x[1], reverse=True)[:10]

    # Peak hours
    peak_hour = hourly_dist.index(max(hourly_dist)) if any(hourly_dist) else 0

    return render_template("analytics.html",
                           daily_data=daily_data,
                           top_visitors=top_visitors,
                           hourly_dist=hourly_dist,
                           emotion_counts=emotion_counts,
                           peak_hour=peak_hour,
                           total_members=len(members))


# ── Face registration ─────────────────────────────────────────────────────────

@app.route("/members/add-photos/<folder_name>")
@login_required
def add_photos(folder_name):
    """Start capturing additional photos for an existing member."""
    member = get_member_by_folder(folder_name)
    if not member:
        return redirect(url_for("members_list"))
    session["capture_name"] = folder_name
    session["capture_target"] = 30  # fewer photos when adding to existing set
    return redirect(url_for("capture_face"))


@app.route("/register-face", methods=["GET", "POST"])
@login_required
def register_face():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            return render_template("register_face.html",
                                   error="Name is required.", user=session["user"])
        safe_name = "".join(c for c in name if c.isalnum() or c == "_")
        if not safe_name:
            return render_template("register_face.html",
                                   error="Invalid name.", user=session["user"])
        session["capture_name"] = safe_name
        return redirect(url_for("capture_face"))

    return render_template("register_face.html", user=session["user"], error=None)


@app.route("/capture-face")
@login_required
def capture_face():
    if not session.get("capture_name"):
        return redirect(url_for("dashboard"))
    return render_template("capture_face.html",
                           name=session["capture_name"], user=session["user"])


@app.route("/capture-stream")
@login_required
def capture_stream():
    if not session.get("capture_name"):
        return redirect(url_for("login"))
    name = session["capture_name"]
    target = session.get("capture_target", 50)
    return Response(generate_capture_frames(name, target=target),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/capture-status")
@login_required
def capture_status():
    name  = session.get("capture_name", "")
    state = capture_state.get(name, {"count": 0, "total": 50, "done": False, "existing": 0})
    return jsonify(state)


# ── Status API ────────────────────────────────────────────────────────────────

@app.route("/recognition-status")
@login_required
def recognition_status():
    from camera import get_status, _detected, _state_lock
    with _state_lock:
        d = dict(_detected)
    return jsonify({
        "status":     get_status(),
        "name":       d.get("full_name") or d.get("name", ""),
        "access":     d.get("access"),
        "reason":     d.get("reason", ""),
        "membership": d.get("membership", ""),
        "gender":     d.get("gender", ""),
        "age":        d.get("age", ""),
        "emotion":    d.get("emotion", ""),
    })


@app.route("/api/stats")
@login_required
def api_stats():
    """Live stats endpoint — polled by the dashboard every few seconds."""
    members   = load_members()
    today     = date.today()
    today_str = today.strftime("%Y-%m-%d")

    total     = len(members)
    active    = sum(1 for m in members if m.get("status") == "active")
    expired   = sum(1 for m in members if m.get("status") == "expired")
    suspended = sum(1 for m in members if m.get("status") == "suspended")

    today_entries   = 0
    today_granted   = 0
    today_denied    = 0
    if os.path.exists(ENTRY_LOG):
        with open(ENTRY_LOG, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 3 and row[1].startswith(today_str):
                    today_entries += 1
                    if row[2] == "granted":
                        today_granted += 1
                    else:
                        today_denied += 1

    expiring_soon = []
    for m in members:
        if m.get("status") == "active":
            try:
                exp = datetime.strptime(m["expiry_date"], "%Y-%m-%d").date()
                days_left = (exp - today).days
                if 0 <= days_left <= 7:
                    expiring_soon.append({"name": m["full_name"], "days": days_left})
            except (ValueError, KeyError):
                pass

    return jsonify({
        "total":         total,
        "active":        active,
        "expired":       expired,
        "suspended":     suspended,
        "today_entries": today_entries,
        "today_granted": today_granted,
        "today_denied":  today_denied,
        "expiring_soon": expiring_soon,
    })


@app.route("/member-photo/<folder_name>")
def member_photo(folder_name):
    """Serve the first captured photo from a member's dataset as their profile pic."""
    from flask import send_from_directory
    safe   = "".join(c for c in folder_name if c.isalnum() or c == "_")
    folder = os.path.abspath(os.path.join(DATASET_PATH, safe))
    if os.path.isdir(folder):
        jpgs = sorted([f for f in os.listdir(folder) if f.lower().endswith(".jpg")])
        if jpgs:
            return send_from_directory(folder, jpgs[0], mimetype="image/jpeg")
    # Fallback — grey circle SVG placeholder
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36">'
        b'<circle cx="18" cy="18" r="18" fill="#1f2937"/>'
        b'<text x="18" y="23" text-anchor="middle" font-size="14" '
        b'font-family="sans-serif" fill="#64748b">?</text></svg>'
    )
    from flask import Response as FlaskResponse
    return FlaskResponse(svg, mimetype="image/svg+xml")


# ── Membership renewal ────────────────────────────────────────────────────────

@app.route("/members/renew/<folder_name>", methods=["POST"])
@login_required
def renew_member(folder_name):
    members = load_members()
    member  = next((m for m in members if m["folder_name"] == folder_name), None)
    if not member:
        return redirect(url_for("members_list"))

    mtype = member.get("membership_type", "monthly")
    today = date.today()

    # Extend from today (or from current expiry if still in future)
    try:
        current_expiry = datetime.strptime(member["expiry_date"], "%Y-%m-%d").date()
        base = current_expiry if current_expiry >= today else today
    except (ValueError, KeyError):
        base = today

    # Calculate new expiry using calendar math
    if mtype == "monthly":
        month = base.month + 1
        year  = base.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day   = min(base.day, calendar.monthrange(year, month)[1])
        new_expiry = date(year, month, day)
    elif mtype == "quarterly":
        month = base.month + 3
        year  = base.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day   = min(base.day, calendar.monthrange(year, month)[1])
        new_expiry = date(year, month, day)
    else:  # annual
        try:
            new_expiry = date(base.year + 1, base.month, base.day)
        except ValueError:
            # Handle Feb 29 -> Feb 28
            new_expiry = date(base.year + 1, base.month, 28)

    member["expiry_date"] = new_expiry.strftime("%Y-%m-%d")
    member["status"]      = "active"
    save_members(members)
    log_audit("member_renewed", member["full_name"],
              f"New expiry: {member['expiry_date']}, Type: {mtype}")
    return redirect(url_for("members_list"))


# ── Backup & Restore ──────────────────────────────────────────────────────────

@app.route("/backup", methods=["POST"])
@login_required
def create_backup():
    """Create a backup of all data files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subdir = os.path.join(BACKUP_DIR, timestamp)
    os.makedirs(backup_subdir, exist_ok=True)

    for src_file in [MEMBERS_FILE, ENTRY_LOG, PAYMENTS_FILE, ADMINS_FILE, AUDIT_LOG]:
        if os.path.exists(src_file):
            shutil.copy2(src_file, os.path.join(backup_subdir, os.path.basename(src_file)))

    log_audit("backup_created", timestamp, "")
    return jsonify({"success": True, "backup_id": timestamp})


@app.route("/backups")
@login_required
def list_backups():
    """List available backups."""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
            path = os.path.join(BACKUP_DIR, name)
            if os.path.isdir(path):
                files = os.listdir(path)
                backups.append({
                    "id": name,
                    "date": f"{name[:4]}-{name[4:6]}-{name[6:8]} {name[9:11]}:{name[11:13]}:{name[13:15]}",
                    "files": files
                })
    return render_template("backups.html", backups=backups)


@app.route("/backup/restore/<backup_id>", methods=["POST"])
@login_required
def restore_backup(backup_id):
    """Restore from a backup."""
    safe_id = "".join(c for c in backup_id if c.isalnum() or c == "_")
    backup_path = os.path.join(BACKUP_DIR, safe_id)
    if not os.path.isdir(backup_path):
        return jsonify({"success": False, "error": "Backup not found"}), 404

    # Restore all files that exist in the backup
    restore_map = {
        "members.json": MEMBERS_FILE,
        "entry_log.csv": ENTRY_LOG,
        "payments.json": PAYMENTS_FILE,
        "admins.json": ADMINS_FILE,
    }
    for backup_name, dest_path in restore_map.items():
        src = os.path.join(backup_path, backup_name)
        if os.path.exists(src):
            shutil.copy2(src, dest_path)

    log_audit("backup_restored", safe_id, "")
    return jsonify({"success": True})


# ── Member profile / attendance history ───────────────────────────────────────

@app.route("/members/profile/<folder_name>")
@login_required
def member_profile(folder_name):
    """Detailed member profile with attendance history."""
    member = get_member_by_folder(folder_name)
    if not member:
        return redirect(url_for("members_list"))

    # Get this member's entry history
    entries = []
    total_granted = 0
    total_denied = 0
    if os.path.exists(ENTRY_LOG):
        with open(ENTRY_LOG, "r") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 3:
                    # Match by full name
                    if row[0] == member["full_name"]:
                        while len(row) < 8:
                            row.append("")
                        entries.append(row)
                        if row[2] == "granted":
                            total_granted += 1
                        else:
                            total_denied += 1

    entries.reverse()  # newest first

    # Count photos in dataset
    dataset_folder = os.path.join(DATASET_PATH, folder_name)
    photo_count = 0
    if os.path.isdir(dataset_folder):
        photo_count = len([f for f in os.listdir(dataset_folder) if f.lower().endswith(".jpg")])

    return render_template("member_profile.html",
                           member=member,
                           entries=entries[:50],  # last 50 entries
                           total_granted=total_granted,
                           total_denied=total_denied,
                           photo_count=photo_count)


# ── Payment tracking ──────────────────────────────────────────────────────────

@app.route("/payments")
@login_required
def payments_list():
    """View all payments with filters."""
    payments = load_payments()
    payments.reverse()  # newest first

    # Filter by member
    member_filter = request.args.get("member", "")
    if member_filter:
        payments = [p for p in payments if p.get("folder_name") == member_filter]

    members = load_members()
    return render_template("payments.html", payments=payments[:100],
                           members=members, member_filter=member_filter)


@app.route("/payments/add", methods=["GET", "POST"])
@login_required
def add_payment():
    """Record a new payment."""
    members = load_members()

    if request.method == "POST":
        folder_name = request.form.get("folder_name", "")
        amount      = request.form.get("amount", "0")
        method      = request.form.get("method", "cash")
        description = request.form.get("description", "").strip()
        payment_date = request.form.get("payment_date", date.today().strftime("%Y-%m-%d"))

        member = next((m for m in members if m["folder_name"] == folder_name), None)
        if not member:
            return render_template("add_payment.html", members=members,
                                   error="Please select a valid member.")

        try:
            amount_float = float(amount)
            if amount_float <= 0:
                raise ValueError()
        except ValueError:
            return render_template("add_payment.html", members=members,
                                   error="Amount must be a positive number.")

        payments = load_payments()
        payment_id = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(payments)}"
        payments.append({
            "id": payment_id,
            "folder_name": folder_name,
            "full_name": member["full_name"],
            "amount": amount_float,
            "method": method,
            "description": description,
            "date": payment_date,
            "recorded_by": session.get("user", ""),
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        save_payments(payments)
        log_audit("payment_recorded", member["full_name"],
                  f"₱{amount_float:.2f} via {method}")
        return redirect(url_for("payments_list"))

    return render_template("add_payment.html", members=members, error=None)


@app.route("/payments/member/<folder_name>")
@login_required
def member_payments(folder_name):
    """View payment history for a specific member."""
    member = get_member_by_folder(folder_name)
    if not member:
        return redirect(url_for("payments_list"))
    payments = get_member_payments(folder_name)
    payments.reverse()
    total_paid = sum(p.get("amount", 0) for p in payments)
    return render_template("member_payments.html", member=member,
                           payments=payments, total_paid=total_paid)


# ── Membership freeze ─────────────────────────────────────────────────────────

@app.route("/members/freeze/<folder_name>", methods=["POST"])
@login_required
def freeze_member(folder_name):
    """Freeze a membership — pauses the expiry countdown."""
    members = load_members()
    member = next((m for m in members if m["folder_name"] == folder_name), None)
    if not member:
        return redirect(url_for("members_list"))

    if member.get("status") == "frozen":
        # Unfreeze — add back the remaining days
        frozen_on = member.get("frozen_on", "")
        if frozen_on:
            try:
                frozen_date = datetime.strptime(frozen_on, "%Y-%m-%d").date()
                days_frozen = (date.today() - frozen_date).days
                old_expiry = datetime.strptime(member["expiry_date"], "%Y-%m-%d").date()
                new_expiry = old_expiry + timedelta(days=days_frozen)
                member["expiry_date"] = new_expiry.strftime("%Y-%m-%d")
            except (ValueError, KeyError):
                pass
        member["status"] = "active"
        member.pop("frozen_on", None)
        log_audit("membership_unfrozen", member["full_name"],
                  f"Expiry extended to {member['expiry_date']}")
    else:
        # Freeze
        member["status"] = "frozen"
        member["frozen_on"] = date.today().strftime("%Y-%m-%d")
        log_audit("membership_frozen", member["full_name"], "")

    save_members(members)
    return redirect(url_for("members_list"))


# ── Check-in / Check-out ──────────────────────────────────────────────────────

@app.route("/gym-floor")
@login_required
def gym_floor():
    """View who's currently checked in at the gym."""
    with _checkin_lock:
        current = dict(_checked_in)
    return render_template("gym_floor.html", checked_in=current)


@app.route("/api/checkin", methods=["POST"])
@login_required
def manual_checkin():
    """Manually check in a member."""
    folder_name = request.form.get("folder_name", "")
    member = get_member_by_folder(folder_name)
    if not member:
        return jsonify({"success": False, "error": "Member not found"}), 404

    with _checkin_lock:
        _checked_in[folder_name] = {
            "full_name": member["full_name"],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    return jsonify({"success": True})


@app.route("/api/checkout", methods=["POST"])
@login_required
def manual_checkout():
    """Manually check out a member."""
    folder_name = request.form.get("folder_name", "")
    with _checkin_lock:
        if folder_name in _checked_in:
            del _checked_in[folder_name]
    return jsonify({"success": True})


@app.route("/api/gym-status")
@login_required
def gym_status():
    """API: current gym occupancy."""
    with _checkin_lock:
        return jsonify({
            "count": len(_checked_in),
            "members": list(_checked_in.values())
        })


# ── Audit log ─────────────────────────────────────────────────────────────────

@app.route("/audit-log")
@login_required
def audit_log_page():
    """View admin audit trail."""
    if not is_superadmin():
        return redirect(url_for("dashboard"))

    records = []
    if os.path.exists(AUDIT_LOG):
        with open(AUDIT_LOG, "r") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                while len(row) < 5:
                    row.append("")
                records.append(row)
    records.reverse()
    return render_template("audit_log.html", records=records[:200])


# ── About & Help pages ─────────────────────────────────────────────────────────

@app.route("/about")
@login_required
def about():
    return render_template("about.html")


@app.route("/help")
@login_required
def help_page():
    return render_template("help.html")


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(_e):
    return render_template("500.html"), 500


# ── Context processor for CSRF-like token ─────────────────────────────────────

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    try:
        app.run(debug=debug_mode, port=5000, use_reloader=False)
    finally:
        _observer.stop()
        _observer.join()
        _camera_stream.stop()
