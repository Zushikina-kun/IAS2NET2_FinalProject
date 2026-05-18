# 🏋️ Gym Membership System with Face Recognition

> **IAS2 Finals Project — Group 9**
> Lorma Colleges | 3rd Year BSIT | School Year 2025–2026

A full-stack web application that controls gym entry using real-time face recognition. The system identifies members via webcam, verifies their membership status, and grants or denies access automatically — no manual input needed.

---

## 👥 Group Members

| Role | Name |
|------|------|
| Leader | Directo, Brix A. |
| Member | Quimson, Jibreel A. |
| Member | Madayag, Djaunathan Albert S. |

---

## 🖥️ Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend language |
| Flask | 3.1+ | Web framework & HTTP server |
| DeepFace | 0.0.93+ | Face recognition, emotion, gender & age analysis |
| TensorFlow | 2.18+ | Deep learning backend for DeepFace |
| OpenCV | 4.10+ | Camera access, face detection (Haar Cascade) |
| Watchdog | 3.0+ | File system monitoring (auto-clears DeepFace cache) |
| Pandas | 2.2+ | DataFrame handling for DeepFace results |
| NumPy | 1.26+ | Numerical operations |
| Pillow | 10.0+ | Image handling |
| SciPy | 1.11+ | Scientific computing |
| HTML/CSS/JS | — | Frontend UI (no frameworks, pure vanilla) |
| JSON | — | Member data storage (`members.json`) |
| CSV | — | Entry log storage (`entry_log.csv`) |

---

## ✨ Features

### Core
- **Face Recognition** — Identifies registered members using VGG-Face model with cosine distance (threshold 0.35)
- **Membership Verification** — Checks active/expired/suspended status before granting entry
- **Access Control** — Green overlay = granted, Red overlay = denied
- **Emotion Detection** — Happy, Sad, Angry, Neutral, Fear, Disgust, Surprise
- **Gender & Age Estimation** — Predicted from face in real-time
- **Live Camera Overlay** — All info drawn directly on the video feed

### Management
- **Member CRUD** — Add, edit, view profile, suspend, renew, delete members
- **Face Registration** — Captures 50 face photos via webcam for new members
- **Member Search** — Filter by name, type, status, contact, or email
- **Member Profiles** — Detailed page with attendance history and stats
- **Visit Counter** — Tracks total visits per member automatically
- **Emergency Contact & Notes** — Additional member info fields

### Monitoring & Analytics
- **Live Dashboard** — 7 stat cards auto-refresh every 5 seconds
- **Expiry Alerts** — Warning banner when members have ≤7 days left
- **Entry Log** — All attempts logged with date filter and CSV export
- **Attendance Analytics** — Daily charts, hourly distribution, top visitors, emotion breakdown
- **Peak Hour Detection** — Shows busiest time of day

### Security
- **Login Rate Limiting** — 5 failed attempts → 5-minute lockout
- **Session Timeout** — Auto-logout after 2 hours of inactivity
- **Password Hashing** — SHA-256 hash comparison (not plaintext)
- **Security Headers** — X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy
- **HttpOnly + SameSite Cookies** — Session cookie hardening
- **Input Sanitization** — Folder names filtered to alphanumeric + underscore
- **Path Traversal Prevention** — Sanitized file access
- **Thread-safe Writes** — Locks on JSON and CSV file operations

### Data Management
- **Backup & Restore** — Create timestamped backups, restore with one click
- **CSV Export** — Download entry logs as CSV files
- **Auto-expiry Detection** — Expired members flagged automatically on page load

---

## 📋 Prerequisites

Before running this project, make sure you have:

1. **Python 3.10 or higher** — https://www.python.org/downloads/
   - ⚠️ During installation, **check "Add Python to PATH"**
2. **A working webcam** (built-in or USB)
3. **Internet connection** (first run only — downloads ~1.7 GB of AI model weights)

> **Note:** XAMPP is NOT required to run this project. It's fully self-contained in Python/Flask. You can place the folder anywhere on your machine.

---

## 🚀 How to Run

### Step 1 — Clone or Download

```bash
git clone https://github.com/Zushikina-kun/IAS2NET2_FinalProject.git
cd IAS2NET2_FinalProject
```

Or download the ZIP and extract it to any folder (e.g., `C:\xampp\htdocs\IAS2NET2FinalProject\`).

### Step 2 — Create Virtual Environment

```bash
python -m venv venv
```

### Step 3 — Activate Virtual Environment

**Windows (CMD):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

> ⏱️ This takes 5–15 minutes depending on your internet speed. TensorFlow alone is ~500 MB.

### Step 5 — (Optional) Pre-download AI Model Weights

Run this once to download all DeepFace models ahead of time:

```bash
python -c "from deepface import DeepFace; import numpy as np; DeepFace.analyze(np.zeros((224,224,3), dtype='uint8'), actions=['emotion','gender','age'], enforce_detection=False)"
```

Downloads to `~/.deepface/weights/` (~1.7 GB total):
- `vgg_face_weights.h5` — 580 MB (face recognition)
- `gender_model_weights.h5` — 534 MB (gender prediction)
- `age_model_weights.h5` — 539 MB (age estimation)
- `facial_expression_model_weights.h5` — 21 MB (emotion detection)

### Step 6 — Start the Server

**Option A — Double-click `run.bat`** (Windows only)

**Option B — Terminal:**
```bash
python app.py
```

You should see:
```
[camera] Using index=0 backend=700
[camera] Waiting for camera to warm up...
[camera] Camera ready.
 * Running on http://127.0.0.1:5000
```

### Step 7 — Open in Browser

Go to: **http://localhost:5000**

Login credentials:
| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

---

## 📁 Project Structure

```
IAS2NET2_FinalProject/
├── app.py                  # Flask app — all routes, auth, logic
├── camera.py               # Camera stream, DeepFace worker, overlays
├── members.json            # Member registry (auto-managed)
├── entry_log.csv           # Entry log (auto-generated at runtime)
├── database.sql            # Reference SQL schema (not used at runtime)
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows quick-start script
├── README.md               # This file
├── DOCUMENTATION.md        # Full technical documentation
│
├── dataset/                # Face photos (one folder per member)
│   ├── Brix_Directo/      # 50+ .jpg face crops
│   ├── Jibreel_Quimson/
│   ├── Djaunathan_Madayag/
│   └── ...
│
├── backups/                # Data backup snapshots (auto-created)
├── templates/              # HTML templates (Jinja2)
│   ├── login.html
│   ├── index.html          # Dashboard
│   ├── members.html
│   ├── add_member.html
│   ├── edit_member.html
│   ├── member_profile.html
│   ├── entry_log.html
│   ├── analytics.html
│   ├── backups.html
│   ├── register_face.html
│   ├── capture_face.html
│   └── 404.html
│
└── static/
    └── style.css           # Global CSS variables
```

---

## 🔄 How It Works

```
Person stands in front of camera
        ↓
OpenCV detects face (Haar Cascade)
        ↓
Every 5 frames → face crop sent to DeepFace (background thread)
        ↓
DeepFace.find() → matches against dataset/ (cosine distance ≤ 0.35)
        ↓
check_membership() → active / expired / suspended
        ↓
DeepFace.analyze() → emotion, gender, age
        ↓
Result shown on camera overlay + dashboard banner
        ↓
Entry logged to CSV (10-second cooldown per person)
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera shows "initializing" forever | Kill stale Python processes: `taskkill /IM python.exe /F` then restart |
| All faces show "Unknown" | Delete `~/.deepface/weights/vgg_face_weights.h5` and restart (re-downloads) |
| "Address already in use" on port 5000 | `netstat -ano \| findstr :5000` then `taskkill /PID <PID> /F` |
| Login locked out | Wait 5 minutes, or restart the server to reset rate limits |
| Emotion/gender/age not showing | Delete model weights in `~/.deepface/weights/` and restart |
| `pip install` fails on TensorFlow | Make sure you're using Python 3.10–3.12 (not 3.13+) |
| Camera not detected | Try a different USB port, or check if another app is using the webcam |

---

## 🌐 Access Points

| URL | Description |
|-----|-------------|
| http://localhost:5000 | Login page |
| http://localhost:5000/dashboard | Main dashboard with live camera |
| http://localhost:5000/members | Member list with search |
| http://localhost:5000/entry-log | Entry log with date filter |
| http://localhost:5000/analytics | Attendance analytics & charts |
| http://localhost:5000/backups | Backup management |
| http://localhost:5000/members/add | Add new member |
| http://localhost:5000/register-face | Register face for existing member |

---

## 📝 Notes

- The system runs **entirely locally** — no cloud services, no external APIs, no database server needed
- First startup is slow (~30–60 seconds) as TensorFlow loads the AI models into memory
- The webcam feed runs at 640×480 @ 30fps; DeepFace processes every 5th frame to avoid blocking
- Face recognition works best with **50+ training photos** per person in varied lighting
- The recognition threshold (0.35 cosine distance) is stricter than default to reduce false matches
- All data is stored in flat files (`members.json`, `entry_log.csv`) — no database setup required

---

## 📄 License

This project was created for academic purposes as part of the IAS2 Finals requirement at Lorma Colleges.

---

*Built with ❤️ by Group 9 — Directo, Quimson, Madayag*
