# Gym Membership System — Technical Documentation
### IAS2 Finals Project — Group 9
**Course:** Information Assurance and Security 2 | **Year:** 3rd Year BSIT | **SY:** 2025–2026

| Role | Name |
|------|------|
| Leader | Directo, Brix A. |
| Member | Quimson, Jibreel A. |
| Member | Madayag, Djaunathan Albert S. |

---

## 1. Overview

A professional gym access control system using real-time AI face recognition. Identifies members via webcam, verifies membership status, grants/denies entry, tracks payments, monitors gym occupancy, and provides business analytics — all without manual input.

---

## 2. Complete Feature List

| Category | Feature |
|----------|---------|
| **Recognition** | Face identification (VGG-Face, cosine distance ≤0.40) |
| **Recognition** | Emotion detection (7 emotions) |
| **Recognition** | Gender prediction, age estimation |
| **Recognition** | Live camera overlay with all info |
| **Access** | Auto grant/deny based on membership status |
| **Access** | Auto check-in to Gym Floor on granted entry |
| **Access** | 10-second cooldown per person (prevents spam) |
| **Members** | Add, edit, view profile, search, delete |
| **Members** | Gender, birthday, address, email, phone, emergency contact, notes |
| **Members** | Face registration (50 photos, 224×224, CLAHE normalized) |
| **Members** | Add more photos to improve accuracy |
| **Members** | Visit counter (auto-incremented) |
| **Membership** | Types: monthly, quarterly, annual |
| **Membership** | Statuses: active, expired, suspended, frozen |
| **Membership** | Auto-expiry detection on page load |
| **Membership** | Renew (extends from expiry or today) |
| **Membership** | Freeze/unfreeze (pauses expiry countdown) |
| **Membership** | Suspend/activate toggle |
| **Payments** | Record payments (cash, GCash, card, bank) |
| **Payments** | Per-member payment history with totals |
| **Payments** | Payment date, description, recorded-by tracking |
| **Monitoring** | Live dashboard (7 stats, 5s refresh) |
| **Monitoring** | Gym Floor (real-time occupancy) |
| **Monitoring** | Entry log with date filter + CSV export |
| **Monitoring** | Expiry alerts (≤7 days warning) |
| **Analytics** | Daily entries chart (30 days) |
| **Analytics** | Hourly distribution |
| **Analytics** | Top visitors ranking |
| **Analytics** | Emotion breakdown |
| **Analytics** | Peak hour detection |
| **Admin** | Multi-admin accounts (admins.json) |
| **Admin** | Roles: superadmin, staff |
| **Admin** | Create/delete admin accounts |
| **Admin** | Audit log (all actions tracked) |
| **Security** | SHA-256 password hashing |
| **Security** | Login rate limiting (5 attempts → 5min lockout) |
| **Security** | Session timeout (2hr inactivity) |
| **Security** | Security headers (nosniff, SAMEORIGIN, XSS, Referrer) |
| **Security** | HttpOnly + SameSite cookies |
| **Security** | Input sanitization, path traversal prevention |
| **Security** | Thread-safe file operations |
| **Data** | Backup all data files (members, payments, admins, logs) |
| **Data** | Restore from any backup |
| **Data** | Dataset normalizer utility (224×224, CLAHE, clean names) |
| **UI** | About page, Help page with FAQ |
| **UI** | Dark theme, responsive design |

---

## 3. Architecture

```
[ Browser — http://localhost:5000 ]
     |
     v
[ Flask Server (app.py) ]
     |
     ├── Auth: login, register, logout, rate limiting
     ├── Dashboard: live stats, camera feed
     ├── Members: CRUD, search, profiles, freeze, suspend
     ├── Payments: record, history, per-member view
     ├── Entry Log: view, filter, export CSV
     ├── Gym Floor: live occupancy, manual checkout
     ├── Analytics: charts, top visitors, emotions
     ├── Backups: create, restore (all data files)
     ├── Audit Log: admin action trail
     ├── Admin Accounts: create, delete, roles
     └── About / Help: info pages
     |
     v
[ camera.py — Background Threads ]
     ├── CameraStream (daemon) — reads webcam 640×480 @ 30fps
     ├── _deepface_worker (daemon) — runs DeepFace every 10 frames
     │     ├── DeepFace.find() → identity (cosine ≤ 0.40)
     │     ├── check_membership() → grant/deny
     │     ├── DeepFace.analyze() → emotion, gender, age
     │     └── Auto check-in → Gym Floor
     └── generate_frames() → MJPEG stream with overlays
```

---

## 4. Data Files

| File | Format | Purpose |
|------|--------|---------|
| `members.json` | JSON array | Member registry with all personal info |
| `admins.json` | JSON array | Admin accounts with hashed passwords |
| `payments.json` | JSON array | Payment transaction records |
| `entry_log.csv` | CSV | Every entry attempt (name, time, access, emotion, etc.) |
| `audit_log.csv` | CSV | Admin action trail (timestamp, admin, action, target) |
| `dataset/` | Folders of JPGs | Face photos per member (224×224 normalized) |

---

## 5. API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/stats` | GET | Live dashboard stats (JSON) |
| `/recognition-status` | GET | Current face detection state (JSON) |
| `/api/gym-status` | GET | Current gym occupancy (JSON) |
| `/api/checkin` | POST | Manual member check-in |
| `/api/checkout` | POST | Manual member check-out |
| `/capture-status` | GET | Face capture progress (JSON) |
| `/backup` | POST | Create data backup |
| `/backup/restore/<id>` | POST | Restore from backup |

---

## 6. Security Implementation

| Layer | Implementation |
|-------|----------------|
| Authentication | SHA-256 hashed passwords, multi-admin accounts |
| Authorization | Role-based (superadmin/staff), `@login_required` decorator |
| Rate limiting | 5 failed logins → 5-minute IP lockout |
| Session | 2-hour timeout, HttpOnly, SameSite=Lax |
| Headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy |
| Input | Folder names: alphanumeric + underscore only |
| Files | Path traversal prevention, thread locks on all writes |
| Audit | Every admin action logged with timestamp and username |

---

## 7. Setup Guide

See **README.md** for step-by-step installation instructions.

**Quick start:**
```bash
git clone https://github.com/Zushikina-kun/IAS2NET2_FinalProject.git
cd IAS2NET2_FinalProject
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Open http://localhost:5000 — Login: admin / admin123
```

---

## 8. Dataset Management

- Each member has a folder in `dataset/` with 50+ face photos
- Photos are 224×224 pixels, JPEG, CLAHE contrast-enhanced
- Run `python normalize_dataset.py` to clean up and normalize all images
- DeepFace cache (`.pkl`) auto-clears when dataset changes
- More photos + varied lighting = better recognition accuracy

---

## 9. Membership Statuses

| Status | Entry | Description |
|--------|-------|-------------|
| Active | ✅ Granted | Valid membership, not expired |
| Expired | ❌ Denied | Date passed (auto-detected) |
| Suspended | ❌ Denied | Manually paused by admin |
| Frozen | ❌ Denied | Temporarily paused, expiry countdown stopped |

---

## 10. Admin Roles

| Role | Permissions |
|------|-------------|
| **Superadmin** | Everything: members, payments, backups, admin accounts, audit log |
| **Staff** | Members, payments, entry log, analytics, backups. Cannot manage admins or view audit log. |

---

## 11. Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera "initializing" forever | Kill stale Python processes, restart |
| All faces "Unknown" | Delete `~/.deepface/weights/vgg_face_weights.h5`, restart |
| Wrong person identified | Add more photos via member profile, run `normalize_dataset.py` |
| Port 5000 in use | `netstat -ano \| findstr :5000` → `taskkill /PID <PID> /F` |
| Login locked out | Wait 5 minutes or restart server |
| Gender/birthday not saving | Fixed in v2.0 — `load_members()` auto-migrates old records |

---

*Lorma Colleges — IAS2 Finals Project — Group 9 — May 2026*
