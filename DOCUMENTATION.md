# Gym Membership System
### Project Documentation — IAS2 Finals Project
**Course:** Information Assurance and Security 2
**Year Level:** 3rd Year BSIT
**Group Number:** 9

| Role | Name |
|------|------|
| Leader | Directo, Brix A. |
| Member | Quimson, Jibreel A. |
| Member | Madayag, Djaunathan Albert S. |

---

## 1. Project Overview

The Gym Membership System is a full-stack web application that controls gym entry and verifies active members using real-time face recognition. Built with Python, Flask, and DeepFace, the system automatically identifies a person standing in front of the camera, checks their membership status, and grants or denies entry accordingly — all without any manual input.

The system is self-contained and runs entirely on a local machine. No PHP or external database is required.

---

## 2. Features

| Feature | Description |
|---------|-------------|
| Face Recognition | Identifies registered gym members using DeepFace (VGG-Face model) |
| Membership Verification | Checks if the identified member has an active, non-expired membership |
| Access Control | Grants or denies gym entry based on membership status |
| Emotion Detection | Detects dominant emotion (Happy, Sad, Angry, Neutral, Fear, Disgust, Surprise) |
| Gender Prediction | Predicts gender (Man / Woman) from face |
| Age Estimation | Estimates age as an integer |
| Live Camera Overlay | Displays name, access result, emotion, gender, and age directly on the video feed |
| Entry Logging | Logs every entry attempt (granted or denied) to a CSV file with timestamp |
| Member Management | Add, edit, renew, suspend, and remove members via the web UI |
| Face Registration | Captures 50 face photos via webcam to register a new member |
| Live Dashboard Stats | Real-time stats auto-refresh every 5 seconds |
| Member Thumbnails | Shows a profile photo from each member's dataset on the members page |
| Expiry Alerts | Dashboard warns when any active member has 7 or fewer days left |
| Date-filtered Entry Log | Entry log can be filtered by date |
| CSV Export | Export entry logs as downloadable CSV files |
| Admin Login | Username/password login with rate limiting and session timeout |
| Login Rate Limiting | Locks account after 5 failed attempts for 5 minutes |
| Session Timeout | Auto-logout after 2 hours of inactivity |
| Security Headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection |
| Member Search | Search/filter members by name, type, status, contact, or email |
| Member Profiles | Detailed member profile page with attendance history |
| Attendance Analytics | Charts showing daily entries, hourly distribution, top visitors, emotions |
| Data Backup & Restore | Create and restore backups of member data and entry logs |
| Visit Counter | Tracks total visits per member automatically |
| Suspend/Activate | Quick toggle to suspend or reactivate members |
| Emergency Contact | Store emergency contact info for each member |
| Member Notes | Add notes to member records |

---

## 3. System Architecture

```
[ Browser ]
     |
     v
[ Flask Server — http://localhost:5000 ]
     |
     ├── /                    → Login page (rate-limited)
     ├── /dashboard           → Live camera feed + stats
     ├── /video               → MJPEG camera stream
     ├── /members             → Member list with search & photos
     ├── /members/add         → Add new member + face capture
     ├── /members/edit/<name> → Edit member details
     ├── /members/profile/<n> → Detailed member profile + history
     ├── /members/renew/<name>→ Renew expired membership
     ├── /members/suspend/<n> → Toggle suspend/activate
     ├── /members/delete/<name>→ Remove member + dataset
     ├── /entry-log           → Entry log with date filter
     ├── /entry-log/export    → Download CSV export
     ├── /analytics           → Attendance analytics & charts
     ├── /register-face       → Register face for existing member
     ├── /capture-face        → Live capture progress page
     ├── /backups             → Backup management page
     ├── /backup              → Create backup (POST)
     ├── /backup/restore/<id> → Restore from backup (POST)
     ├── /member-photo/<name> → Serves member profile photo
     ├── /api/stats           → JSON endpoint for live dashboard stats
     ├── /recognition-status  → JSON endpoint for current detection state
     └── /logout              → Clears session
     |
     v
[ camera.py — Background Threads ]
     |
     ├── CameraStream         → Reads webcam frames continuously (daemon thread)
     ├── _deepface_worker     → Runs DeepFace in background (never blocks video)
     │     ├── DeepFace.find()    → Identifies person from dataset
     │     ├── check_membership() → Checks members.json for status
     │     └── DeepFace.analyze() → Emotion, gender, age
     └── generate_frames()    → Yields MJPEG frames with overlays drawn
```

---

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.10 | Core backend language |
| Flask | Web framework / HTTP server |
| DeepFace | Face recognition, emotion, gender & age analysis |
| OpenCV | Camera access, face detection (Haar Cascade), image processing |
| Watchdog | Monitors dataset folder, clears DeepFace cache on changes |
| HTML / CSS / JavaScript | Frontend UI (no external frameworks) |
| JSON (members.json) | Member registry storage |
| CSV (entry_log.csv) | Entry log storage |

---

## 5. Project File Structure

```
IAS2NET2FinalProject/
│
├── app.py                  # Flask application — all routes and logic
├── camera.py               # Camera stream, DeepFace worker, overlays
├── members.json            # Member registry (name, membership, status, dates)
├── entry_log.csv           # Auto-generated entry log
├── database.sql            # Reference SQL schema (not required to run)
├── requirements.txt        # Python dependencies
├── run.bat                 # Double-click to start the server
├── DOCUMENTATION.md        # This file
│
├── dataset/                # Face image database (one folder per person)
│   ├── Brix_Directo/
│   │   ├── 0.jpg
│   │   └── ... (50 photos)
│   ├── Jibreel_Quimson/
│   ├── Djaunathan_Madayag/
│   ├── Christian_Pobre/
│   └── <Any_New_Member>/
│
├── backups/                # Data backup snapshots
│   └── 20260518_143000/    # Timestamped backup folders
│       ├── members.json
│       └── entry_log.csv
│
├── templates/              # Flask HTML templates (Jinja2)
│   ├── login.html          # Admin login page
│   ├── index.html          # Dashboard — camera feed + live stats
│   ├── members.html        # Member list with search & thumbnails
│   ├── add_member.html     # Add new member form
│   ├── edit_member.html    # Edit member details form
│   ├── member_profile.html # Detailed member profile + history
│   ├── entry_log.html      # Entry log table with date filter + export
│   ├── analytics.html      # Attendance analytics & charts
│   ├── backups.html        # Backup management page
│   ├── register_face.html  # Face registration form
│   ├── capture_face.html   # Live capture with progress bar
│   └── 404.html            # Error page
│
├── static/
│   └── style.css           # Global CSS variables
│
└── venv/                   # Python virtual environment (pre-installed)
```

---

## 6. Setup Guide (Fresh Machine)

### Step 1 — Prerequisites

- **Python 3.10+** — https://www.python.org/downloads/
  - During install, tick **"Add Python to PATH"**
- A working **webcam**
- A **stable internet connection** for first-time DeepFace model downloads (~1.7 GB total)

> XAMPP is **not required** to run this project. The system is fully self-contained in Flask.

---

### Step 2 — Place the Project

Copy the project folder anywhere on your machine. Recommended:

```
C:\xampp\htdocs\IAS2NET2FinalProject\
```

---

### Step 3 — Set Up the Python Virtual Environment

Open a terminal inside the project folder and run:

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

> Installation takes several minutes. TensorFlow and DeepFace are large packages.

---

### Step 4 — Pre-download DeepFace Model Weights (Recommended)

Run this once on a stable connection to pre-download all model weights:

```bash
venv\Scripts\python.exe -c "from deepface import DeepFace; import numpy as np; DeepFace.analyze(np.zeros((224,224,3), dtype='uint8'), actions=['emotion','gender','age'], enforce_detection=False)"
```

This downloads to `C:\Users\<YourName>\.deepface\weights\`:

| File | Size | Purpose |
|------|------|---------|
| vgg_face_weights.h5 | ~580 MB | Face recognition |
| facial_expression_model_weights.h5 | ~21 MB | Emotion detection |
| gender_model_weights.h5 | ~534 MB | Gender prediction |
| age_model_weights.h5 | ~539 MB | Age estimation |

---

### Step 5 — Start the Server

**Option A — Double-click `run.bat`**

**Option B — Terminal:**
```bash
venv\Scripts\python.exe app.py
```

You should see:
```
[camera] Camera ready.
 * Running on http://127.0.0.1:5000
```

---

### Step 6 — Open the Application

Go to: **http://localhost:5000**

Login with:
- **Username:** `admin`
- **Password:** `admin123`

---

## 7. How the System Works

### Entry Verification Flow

```
Person stands in front of camera
        |
        v
OpenCV Haar Cascade detects face region
        |
        v
Every 5 frames → face crop sent to background DeepFace worker
        |
        v
DeepFace.find() compares face against dataset/
  ├── Match found (distance ≤ 0.35) → folder_name = member identity
  └── No match / weak match         → folder_name = "Unknown"
        |
        v
check_membership(folder_name)
  ├── Status = active + not expired → ACCESS GRANTED (green overlay)
  ├── Status = expired              → ACCESS DENIED  (red overlay)
  ├── Status = suspended            → ACCESS DENIED  (red overlay)
  └── Not in members.json           → ACCESS DENIED  (red overlay)
        |
        v
DeepFace.analyze() → emotion, gender, age
        |
        v
Result drawn on camera overlay + shown in dashboard banner
        |
        v
Entry logged to entry_log.csv (with 10-second cooldown per person)
        |
        v
Member's total_visits counter incremented (on granted access)
```

### Recognition Accuracy

- DeepFace uses the **VGG-Face** model with **cosine distance**
- Threshold is set to **0.35** (stricter than the default 0.40) to reduce false matches
- Matches with distance > 0.35 are rejected and shown as "Unknown"
- More photos per person = better accuracy. Minimum recommended: **50 photos**

---

## 8. Member Management

### Membership Types

| Type | Duration |
|------|----------|
| Monthly | 1 month from start date |
| Quarterly | 3 months from start date |
| Annual | 1 year from start date |

### Membership Statuses

| Status | Entry Result |
|--------|-------------|
| Active (not expired) | ACCESS GRANTED |
| Active (date expired) | ACCESS DENIED — auto-detected on members page load |
| Expired | ACCESS DENIED |
| Suspended | ACCESS DENIED |

### Renewing a Membership

On the Members page, expired or suspended members show a **Renew** button. Clicking it extends the membership from the current expiry date (or today if already past) by the member's plan duration.

### Suspending a Member

Active members show a **Suspend** button. Suspended members are denied entry until reactivated. Click Suspend again (or Renew) to reactivate.

### Deleting a Member

Removing a member from the Members page also **deletes their face dataset folder** so DeepFace can no longer recognize them. The DeepFace cache is cleared automatically.

### Member Profile

Click **View** on any member to see their detailed profile including:
- Membership details and contact info
- Total visits and entry history
- Number of face photos in their dataset
- Last 50 entry log records for that member

---

## 9. Registering New Faces

### Via Add Member (recommended)

1. Go to **Members → + Add Member**
2. Fill in full name, membership type, dates, contact, emergency contact
3. Click **Save & Capture Face**
4. The camera opens — keep your face in frame
5. 50 photos are auto-captured with a progress bar
6. On completion, you're redirected to the Members page

### Via Register Face (for existing members)

1. Go to **Register Face** from the dashboard
2. Enter the member's exact folder name (e.g. `Juan_Dela_Cruz`)
3. 50 photos are captured and saved to `dataset/<folder_name>/`

### Tips for Best Recognition Accuracy

- Face the camera directly in good, even lighting
- Avoid hats, sunglasses, or heavy shadows
- Slightly vary your angle across the 50 shots
- Avoid blurry or dark photos — the capture only saves when a face is detected
- If recognition is wrong, re-register with fresh photos

---

## 10. Entry Log

- File: `entry_log.csv`
- Columns: `Name, Time, Access, Reason, Emotion, Gender, Age, Confidence`
- Each person is logged with a **10-second cooldown** to avoid spam entries
- The web UI shows the log newest-first with granted/denied stats
- Can be filtered by date using the date picker
- Can be **exported as CSV** via the Export button
- Can be cleared via the **Clear Log** button

Example row:
```
Brix Directo,2026-05-06 10:23:11,granted,Active member,Happy,Man,22,94.50
```

---

## 11. Live Dashboard

The dashboard auto-refreshes every 5 seconds via `/api/stats` and shows:

| Stat | Description |
|------|-------------|
| Total Members | All registered members |
| Active | Members with active status |
| Expired | Members with expired status |
| Suspended | Members with suspended status |
| Today's Entries | Total entry attempts today |
| Granted Today | Successful entries today |
| Denied Today | Denied entries today |

A pulsing green dot on "Today's Entries" indicates live updates.

An orange warning banner appears automatically when any active member has **7 or fewer days** until expiry.

---

## 12. Analytics

The Analytics page (`/analytics`) provides visual insights:

| Chart | Description |
|-------|-------------|
| Daily Entries (30 days) | Bar chart of granted/denied entries per day |
| Hourly Distribution | Shows which hours are busiest |
| Top Visitors | Ranked list of most frequent members |
| Emotion Breakdown | Distribution of detected emotions |
| Peak Hour | The busiest hour of the day |

---

## 13. Backup & Restore

The system includes a data backup feature accessible from the dashboard:

- **Create Backup**: Saves a timestamped copy of `members.json` and `entry_log.csv`
- **Restore**: Overwrites current data with a previous backup
- Backups are stored in the `backups/` directory
- Each backup is a folder named with the timestamp (e.g., `20260518_143000`)

---

## 14. Security Features

| Feature | Implementation |
|---------|----------------|
| Admin login | Username + SHA-256 hashed password comparison |
| Login rate limiting | 5 failed attempts → 5-minute lockout per IP |
| Session timeout | Auto-logout after 2 hours of inactivity |
| Route protection | All routes use `@login_required` decorator |
| Security headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy |
| Input sanitization | Member folder names filtered to alphanumeric + underscore only |
| Path traversal prevention | `member-photo` route sanitizes folder name before file access |
| Concurrent write protection | `members.json` writes use a threading lock |
| Entry log write protection | CSV writes use a threading lock with proper quoting |
| Flask secret key | Reads from `FLASK_SECRET_KEY` environment variable |
| Flask debug mode | Reads from `FLASK_DEBUG` environment variable (off by default) |
| Session cookies | HttpOnly + SameSite=Lax |
| Dataset cache management | DeepFace `.pkl` cache auto-cleared on dataset changes via Watchdog |
| Date validation | Expiry date must be after start date |

---

## 15. Python Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| flask | >=3.1.0 | Web framework |
| deepface | >=0.0.99 | Face recognition, emotion, gender, age |
| opencv-python | >=4.13.0 | Camera access, face detection, image processing |
| numpy | >=2.2.0 | Numerical operations |
| pillow | >=12.0.0 | Image handling |
| tensorflow | >=2.21.0 | Deep learning backend for DeepFace |
| tf-keras | >=2.21.0 | Keras compatibility layer |
| pandas | >=2.3.0 | DataFrame handling for DeepFace results |
| scipy | >=1.11.0 | Scientific computing |
| watchdog | >=3.0.0 | File system monitoring for dataset folder |

---

## 16. Troubleshooting

### Camera shows "initializing" and never loads

Another process is holding the webcam. Kill all stale Python processes:

```powershell
Get-Process python | Stop-Process -Force
```

Then restart the server. The system automatically tries multiple camera backends (DSHOW, MSMF) and indices (0, 1) until one works.

---

### Face recognized as wrong person

The recognition threshold may need tightening, or the person needs more training photos. Steps to fix:

1. Go to **Register Face**, enter the person's folder name, and recapture 50 fresh photos
2. Make sure photos are taken in varied lighting and slight angle changes
3. The system uses a cosine distance threshold of 0.35 — matches above this are rejected as "Unknown"

---

### All faces show as "Unknown"

The VGG-Face weights file is missing or corrupted. Delete and re-download:

```bash
del "%USERPROFILE%\.deepface\weights\vgg_face_weights.h5"
```

Restart the server. It will re-download (~580 MB) on startup.

---

### Emotion / gender / age not showing

Model weights are missing. Delete and re-download:

```bash
del "%USERPROFILE%\.deepface\weights\facial_expression_model_weights.h5"
del "%USERPROFILE%\.deepface\weights\gender_model_weights.h5"
del "%USERPROFILE%\.deepface\weights\age_model_weights.h5"
```

Restart the server.

---

### "Address already in use" on port 5000

A stale Flask process is still running. Find and kill it:

```bash
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

---

### Stats on dashboard not updating

The `/api/stats` endpoint requires an active session. If you were logged out (session timeout after 2 hours), log back in and the stats will resume updating.

---

### Member photo thumbnail broken

The member's dataset folder name in `members.json` must exactly match the folder name in `dataset/`. Check for typos or capitalization differences.

---

### Login locked out

After 5 failed login attempts, the system locks the IP for 5 minutes. Wait for the lockout to expire, or restart the server to clear the in-memory rate limit state.

---

## 17. Registered Members

| Full Name | Folder | Membership | Status |
|-----------|--------|------------|--------|
| Brix Directo | Brix_Directo | Annual | Active |
| Jibreel Quimson | Jibreel_Quimson | Monthly | Active |
| Djaunathan Madayag | Djaunathan_Madayag | Quarterly | Active |
| Christian Pobre | Christian_Pobre | Monthly | Active |
| Brix Arquisal Directo | Brix_Arquisal_Directo | Annual | Active |
| Mark Allen Almodovar | Mark_Allen_Almodovar | Annual | Active |

---

## 18. System Flow Diagram

```
User opens browser → http://localhost:5000
        |
        v
  login.html (rate-limited, 5 attempts max)
  ┌──────────────────────┐
  │  Username + Password │ → admin / admin123
  └──────────────────────┘
        |
        v (login success → session set, 2hr timeout)
  index.html — Dashboard
  ┌──────────────────────────────────────────┐
  │  Live camera feed (MJPEG stream)         │
  │  7 live stat cards (refresh every 5s)    │
  │  Expiring soon alert (if applicable)     │
  │  Access granted/denied banner            │
  │  Navigation: Members, Entry Log,         │
  │    Analytics, Register Face, Backups     │
  └──────────────────────────────────────────┘
        |
        v (face detected)
  camera.py background worker
  ┌──────────────────────────────────────────┐
  │  DeepFace.find()    → identity           │
  │  check_membership() → grant / deny       │
  │  DeepFace.analyze() → emotion/gender/age │
  │  log_entry()        → entry_log.csv      │
  │  increment visits   → members.json       │
  └──────────────────────────────────────────┘
        |
        v
  Camera overlay updated + dashboard banner shown
```

---

*Documentation prepared for IAS2 Finals Project — Group 9 — 3rd Year BSIT*
*Lorma Colleges — School Year 2025–2026*
