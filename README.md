# 🏋️ IronGate — AI Gym Access Control System

> **IAS2 Finals Project — Group 9**
> Lorma Colleges | 3rd Year BSIT | School Year 2025–2026

A professional gym access control system powered by real-time AI face recognition. Automatically identifies members via webcam, verifies membership status, and grants or denies entry — no cards, no PINs, no manual check-in needed.

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
| Flask | 3.0+ | Web framework & HTTP server |
| DeepFace | 0.0.93+ | Face recognition, emotion, gender & age analysis |
| TensorFlow | 2.18+ | Deep learning backend |
| OpenCV | 4.10+ | Camera access, face detection (Haar Cascade), CLAHE |
| Watchdog | 3.0+ | File system monitoring (auto-clears DeepFace cache) |
| Pandas | 2.2+ | DataFrame handling for DeepFace results |
| NumPy | 1.26+ | Numerical operations |
| HTML/CSS/JS | — | Frontend UI (vanilla, no frameworks) |
| JSON | — | Data storage (members, admins, payments) |
| CSV | — | Entry log & audit trail |

---

## ✨ Features

### 🔐 Access Control & Recognition
- **AI Face Recognition** — VGG-Face model with cosine distance matching (threshold 0.40)
- **Membership Verification** — Real-time status check before granting entry
- **Emotion Detection** — Happy, Sad, Angry, Neutral, Fear, Disgust, Surprise
- **Gender & Age Estimation** — Predicted from face
- **Live Camera Overlay** — Name, access result, emotion, demographics drawn on feed
- **Auto Check-in** — Granted members automatically appear on Gym Floor

### 👥 Member Management
- **Full CRUD** — Add, edit, view profile, suspend, freeze, renew, delete
- **Face Registration** — Captures 50 normalized face photos (224×224, CLAHE enhanced)
- **Add More Photos** — Append additional photos to improve recognition accuracy
- **Member Search** — Filter by name, type, status, contact, email
- **Member Profiles** — Detailed page with attendance history and stats
- **Visit Counter** — Tracks total visits per member automatically
- **Extended Info** — Gender, birthday, address, email, phone, emergency contact, notes

### 💰 Business Operations
- **Payment Tracking** — Record payments (cash, GCash, card, bank transfer)
- **Payment History** — Per-member payment records with totals
- **Membership Freeze** — Pause expiry countdown (medical leave, vacation)
- **Membership Types** — Monthly, quarterly, annual with auto-renewal math
- **Expiry Alerts** — Dashboard warns when members have ≤7 days left
- **CSV Export** — Download entry logs as CSV files

### 📊 Analytics & Monitoring
- **Live Dashboard** — 7+ stat cards auto-refresh every 5 seconds
- **Gym Floor** — Real-time occupancy view (who's currently inside)
- **Attendance Analytics** — Daily charts, hourly distribution, top visitors
- **Emotion Breakdown** — Distribution of detected emotions over time
- **Peak Hour Detection** — Shows busiest time of day

### 🔑 Admin & Security
- **Multi-Admin System** — Multiple accounts with role-based access
- **Roles** — Superadmin (full access) vs Staff (member management only)
- **Admin Registration** — Superadmins create/delete other accounts
- **Login Rate Limiting** — 5 failed attempts → 5-minute lockout
- **Session Timeout** — Auto-logout after 2 hours of inactivity
- **Password Hashing** — SHA-256 (never stored in plaintext)
- **Security Headers** — X-Content-Type-Options, X-Frame-Options, XSS-Protection
- **Audit Log** — Full trail of every admin action (who did what, when)
- **Data Backup & Restore** — Timestamped snapshots of all data files

---

## 📋 Prerequisites

1. **Python 3.10–3.12** — https://www.python.org/downloads/
   - ⚠️ Check **"Add Python to PATH"** during installation
2. **A working webcam** (built-in or USB)
3. **Internet connection** (first run only — downloads ~1.7 GB of AI model weights)

> **XAMPP is NOT required.** The system is fully self-contained in Python/Flask.

---

## 🚀 How to Run

### Step 1 — Clone or Download

```bash
git clone https://github.com/Zushikina-kun/IAS2NET2_FinalProject.git
cd IAS2NET2_FinalProject
```

### Step 2 — Create & Activate Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows CMD
# or: venv\Scripts\Activate.ps1   (PowerShell)
# or: source venv/bin/activate    (macOS/Linux)
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — (Optional) Pre-download AI Models

```bash
python -c "from deepface import DeepFace; import numpy as np; DeepFace.analyze(np.zeros((224,224,3), dtype='uint8'), actions=['emotion','gender','age'], enforce_detection=False)"
```

### Step 5 — Start the Server

```bash
python app.py
# or double-click run.bat (Windows)
```

### Step 6 — Open in Browser

**http://localhost:5000**

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

---

## 📁 Project Structure

```
IAS2NET2_FinalProject/
├── app.py                  # Flask app — all routes & business logic
├── camera.py               # Camera stream, DeepFace worker, overlays
├── normalize_dataset.py    # Dataset cleanup & normalization utility
├── members.json            # Member registry
├── admins.json             # Admin accounts (auto-created on first run)
├── payments.json           # Payment records
├── entry_log.csv           # Entry log (auto-generated)
├── audit_log.csv           # Admin audit trail (auto-generated)
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows quick-start
├── README.md               # This file
├── DOCUMENTATION.md        # Full technical documentation
│
├── dataset/                # Face photos (one folder per member, 224×224 normalized)
├── backups/                # Timestamped data snapshots
├── templates/              # 15 HTML templates (Jinja2)
└── static/                 # CSS
```

---

## 🌐 All Pages

| URL | Description | Access |
|-----|-------------|--------|
| `/` | Landing page (public) | Public |
| `/login` | Admin login | Public |
| `/dashboard` | Live camera + stats | All admins |
| `/members` | Member list with search | All admins |
| `/members/add` | Register new member | All admins |
| `/members/profile/<name>` | Detailed member profile | All admins |
| `/members/edit/<name>` | Edit member details | All admins |
| `/entry-log` | Entry log with date filter & export | All admins |
| `/gym-floor` | Live gym occupancy | All admins |
| `/payments` | Payment records | All admins |
| `/payments/add` | Record a payment | All admins |
| `/analytics` | Attendance charts & insights | All admins |
| `/backups` | Backup & restore data | All admins |
| `/audit-log` | Admin action trail | Superadmin only |
| `/register` | Manage admin accounts | Superadmin only |
| `/register-face` | Register face for existing member | All admins |
| `/mini-research` | Research document | Public |
| `/help` | FAQ & user guide | All admins |
| `/about` | System info & credits | All admins |

---

## 🔄 How It Works

```
Person stands in front of camera
        ↓
OpenCV detects face (Haar Cascade, minNeighbors=6, minSize=100×100)
        ↓
Every 10 frames → largest face cropped, resized to 224×224, sent to DeepFace
        ↓
DeepFace.find() → matches against dataset/ (cosine distance ≤ 0.40)
        ↓
check_membership() → active / expired / suspended / frozen
        ↓
DeepFace.analyze() → emotion, gender, age
        ↓
Result shown on camera overlay + dashboard banner
        ↓
Entry logged to CSV + member auto-checked into Gym Floor
```

---

## 🛠️ Utilities

### Normalize Dataset
Cleans up filenames, resizes all images to 224×224, applies CLAHE contrast enhancement:
```bash
python normalize_dataset.py
```

---

## 🛡️ Security Features

| Feature | Details |
|---------|---------|
| Password hashing | SHA-256 |
| Rate limiting | 5 attempts → 5min lockout per IP |
| Session timeout | 2 hours inactivity |
| Security headers | nosniff, SAMEORIGIN, XSS-Protection, Referrer-Policy |
| HttpOnly cookies | SameSite=Lax |
| Input sanitization | Alphanumeric + underscore only for folder names |
| Path traversal prevention | Sanitized file access |
| Thread-safe writes | Locks on all JSON/CSV operations |
| Audit trail | Every admin action logged with timestamp |
| Role-based access | Superadmin vs Staff permissions |

---

## 📝 Notes

- Runs **entirely locally** — no cloud, no external APIs, no database server
- First startup takes ~30–60 seconds (TensorFlow model loading)
- Webcam runs at 640×480; DeepFace processes every 10th frame
- Best accuracy with **50+ training photos** per person in varied lighting
- Recognition threshold: 0.40 cosine distance (DeepFace default)
- All data stored in flat files — no database setup required
- Gym Floor check-in state is in-memory (resets on server restart)

---

## 📄 License

Academic project — IAS2 Finals, Lorma Colleges, SY 2025–2026.

---

*Built by Group 9 — Directo, Quimson, Madayag | IronGate v2.0*
