# Mini Research: IronGate — AI-Powered Gym Access Control System

**Members**
Directo, Brix A.
Quimson, Jibreel A.
Madayag, Djaunathan Albert S.

**Information Assurance and Security 2 (IAS2)**
Submitted to: *(Instructor Name)*
Lorma Colleges | 3rd Year BSIT | May 2026

---

## Table of Contents

- Figure 1 — Landing Page
- Figure 2 — Admin Login Page
- Figure 3 — Dashboard
- Figure 4 — Members Page
- Figure 5 — Add Member & Face Capture
- Figure 6 — Member Profile
- Figure 7 — Entry Log
- Figure 8 — Gym Floor (Live Occupancy)
- Figure 9 — Payments
- Figure 10 — Analytics
- Figure 11 — Backups
- Figure 12 — Audit Log
- Figure 13 — Admin Accounts
- Figure 14 — Help & About
- Curriculum Vitae

---

## PRELIM

---

### Figure 1. Landing Page

The first page users see when visiting the system at `http://localhost:5000`.
Displays the **IronGate** brand as a professional gym website with full fitness services.

The landing page is divided into sections:
- **Hero** — tagline "Your Fitness Journey Starts at the Door", key stats (<1s check-in, 24/7 access, 0 cards, 100% contactless), and Staff Login button
- **Services** — nine cards covering the gym's offerings: Strength & Weight Training, Cardio Zone, Group Fitness Classes, Personal Training, Nutrition & Meal Plans, Protein Bar & Supplements, Body Composition Analysis, Locker Rooms & Showers, and AI Face Recognition Entry
- **Membership Plans** — three pricing tiers: Monthly (₱1,500), Quarterly (₱3,900), Annual (₱12,000) with feature descriptions
- **Technology** — six cards explaining the smart gym features: Instant Access Control, Attendance Analytics, Payment Tracking, Membership Freeze, Live Gym Floor, Private & Secure
- **How It Works** — six simplified steps: Approach Camera → Face Detected → Identity Verified → Membership Checked → Access Granted → Everything Logged
- **Tech Stack** — cards for Python, Flask, DeepFace, TensorFlow, OpenCV, VGG-Face, NumPy/Pandas, Pillow, Watchdog, JSON/CSV
- **Team** — Group 9 members with roles
- **CTA** — "Ready to train?" with links to Staff Login and Research Paper

The page is always accessible (even when logged in) and serves as the public-facing gym website.

---

### Figure 2. Admin Login Page

Located at `/login`. The only entry point into the admin panel.

Displays the **IronGate** logo, a username field, and a password field.
Successful login redirects to the Dashboard. Failed attempts increment a per-IP counter.
After **5 failed attempts**, the IP is locked out for **5 minutes** — a message shows the remaining lockout time.
Sessions expire automatically after **2 hours of inactivity**.

Passwords are never stored in plaintext — they are hashed with **SHA-256** before comparison.
A **← Back to Home** link returns to the landing page.

Default credentials on first run:
- **Username:** `admin`
- **Password:** `admin123`

---

### Figure 3. Dashboard

Located at `/dashboard`. The main control panel after login.

The top bar shows the system brand and the currently signed-in admin with a **Sign Out** link.

**Stats row** (7 cards, auto-refresh every 5 seconds):
- Total Members, Active, Expired, Suspended, Today's Entries, Granted Today, Denied Today

**Expiring Soon banner** — appears automatically when any active member has ≤ 7 days left on their membership. Shows each member's name and days remaining with a link to the Members page.

**Live camera feed** — streams the webcam in a compact 16:9 widescreen frame. Every 10 frames, the largest detected face is sent to DeepFace for identification. The result (name, access granted/denied, emotion, gender, age) is drawn as an overlay on the feed.

**Access banner** — appears below the feed showing the last recognition result in green (granted) or red (denied), auto-hides after 5 seconds.

**Processing indicator** — shows a spinner while DeepFace is running.

**Side panel** — lists system features and navigation links to all pages, plus an **+ Add Member** primary button.

---

### Figure 4. Members Page

Located at `/members`. Full list of all registered gym members.

**Search bar** — filters by name, membership type, status, contact number, or email in real time.

**Members table** columns:
- Row number, profile photo thumbnail, full name, membership type (Monthly / Quarterly / Annual), status (Active / Expired / Suspended / Frozen), start date, expiry date, days left (color-coded: red ≤7d, yellow ≤30d, green otherwise), total visits, contact number, and action buttons.

**Action buttons per member:**
- **View** — opens the member's detailed profile
- **Edit** — opens the edit form
- **📷** — opens the add-more-photos capture page
- **💰** — opens the member's payment history
- **❄️ / Freeze / Unfreeze** — pauses or resumes the expiry countdown
- **Suspend / Renew** — toggles suspension or extends the membership
- **Remove** — deletes the member and their face dataset folder (with confirmation)

Membership status auto-updates on page load — expired dates are detected and status is set to Expired automatically.

---

### Figure 5. Add Member & Face Capture

**Add Member** — located at `/members/add`.

A form with two sections:
1. **Basic info** — full name (required), membership type, status, start date, expiry date (auto-calculated based on type)
2. **Personal info** — gender, birthday, address, contact number, email, emergency contact, notes

The expiry date auto-fills when the start date or membership type changes (monthly +1 month, quarterly +3 months, annual +1 year).

After saving, the system generates a folder name from the member's full name (e.g. `Juan_Dela_Cruz`) and redirects to the **Face Capture** page.

**Face Capture** — located at `/capture-stream` (streamed) with progress at `/capture-status`.

The webcam opens and the system automatically captures **50 face photos** when a face is detected in the frame. Each photo is:
- Cropped to the largest detected face
- Resized to **224×224 pixels**
- Enhanced with **CLAHE** (Contrast Limited Adaptive Histogram Equalization)
- Saved as a numbered JPEG in `dataset/<FolderName>/`

A progress bar shows captured / 50. The page redirects to the Members list automatically when done.
If the member already has photos (Add More Photos flow), the counter starts from the existing count.

---

### Figure 6. Member Profile

Located at `/members/profile/<folder_name>`.

**Profile header** — photo, full name, status pill, membership type, photo count, join date, and action buttons (Edit Member, Add More Photos).

**Stats row** (4 cards):
- Total Entries (granted), Denied, Total Visits, Face Photos

**Details grid** (2 cards):
- Membership Details — type, status, start date, expiry date, folder name
- Contact Information — phone, email, emergency contact, gender, birthday, address, notes

**Recent Entry History** — table of the last 50 access attempts for this member showing timestamp, access result (Granted/Denied), deny reason, detected emotion, and confidence score.

---

### Figure 7. Entry Log

Located at `/entry-log`. Every face recognition event is recorded here automatically.

**Date filter** — filter records by a specific date using a date picker. A Clear button resets to all records.

**Stats row** — Total entries, Granted count, Denied count for the current filter.

**Log table** columns:
- Row number, member name, timestamp, access result (color-coded pill), deny reason, detected emotion, detected gender, estimated age, confidence score (%)

**Export CSV** — downloads all visible records as a `.csv` file named with the date filter.
**Clear Log** — permanently deletes all entry records (with confirmation prompt).

Records are stored in `entry_log.csv` and are appended automatically by the face recognition engine.

---

### Figure 8. Gym Floor — Live Occupancy

Located at `/gym-floor`.

Shows who is **currently inside the gym** in real time.

Members are automatically **checked in** when face recognition grants them access. Each card shows:
- Member photo, full name, check-in time, and a **Check Out** button

The occupancy counter in the top-right updates every 10 seconds via the `/api/gym-status` endpoint.
Clicking **Check Out** calls `/api/checkout` and removes the member from the floor view.

The check-in state is **in-memory** — it resets when the server restarts.

---

### Figure 9. Payments

Located at `/payments`. All recorded membership payments.

**Summary stats** — Total collected (₱) and total transaction count.

**Payments table** columns:
- Row number, member name, amount (₱), payment method (Cash / GCash / Card / Bank Transfer — color-coded), description, date, recorded by (admin username)

**Record Payment** — located at `/payments/add`. Form fields: member selector, amount, payment method, payment date (defaults to today), description/notes.

**Member Payment History** — located at `/payments/member/<folder_name>`. Shows all payments for a single member with a running total.

Payments are stored in `payments.json` and every transaction is logged in the Audit Log.

---

### Figure 10. Analytics

Located at `/analytics`. Auto-generated insights from the entry log data.

**Summary stats** (4 cards):
- Total Members, Granted (last 30 days), Denied (last 30 days), Peak Hour

**Daily Entries chart** — bar chart of the last 30 days. Each bar represents total entries (granted + denied) for that day. Hover to see the exact date and counts.

**Hourly Distribution chart** — 24-bar chart showing entry volume by hour of day. The peak hour bar is highlighted in green.

**Top Visitors** — ranked list of the top 10 members by total granted entries, with a proportional bar indicator.

**Emotion Breakdown** — grid of detected emotions (Happy, Sad, Angry, Neutral, Fear, Disgust, Surprise) with emoji icons and counts from all entry log records.

---

### Figure 11. Backups

Located at `/backups`.

**Create Backup** — one click saves a timestamped snapshot of all five data files:
`members.json`, `admins.json`, `payments.json`, `entry_log.csv`, `audit_log.csv`

Each backup is stored in the `backups/` folder with a timestamp ID (e.g. `backup_20260519_112233`).

**Backup list** — shows each backup's date and the files it contains.

**Restore** — clicking Restore on any backup overwrites the current live data files with the backup copies. A confirmation prompt prevents accidental restores.

All backup and restore actions are recorded in the Audit Log.

---

### Figure 12. Audit Log

Located at `/audit-log`. **Superadmin-only.**

A complete, tamper-evident trail of every admin action in the system.

**Table columns:**
- Row number, timestamp, admin username, action type (color-coded pill), target (member name or resource), details

**Action types and colors:**
- `member_added` — green
- `member_deleted` — red
- `payment_recorded` — yellow
- `member_frozen / member_activated` — blue
- All others (edit, suspend, backup, restore) — grey

The log is append-only from the UI — it cannot be cleared through the interface.
Stored in `audit_log.csv` and written with a thread-safe lock to prevent corruption.

---

### Figure 13. Admin Accounts

Located at `/register`. **Superadmin-only.**

**Left panel — Create New Admin Account:**
- Full name, username (min 3 chars), password (min 6 chars), confirm password, role selector (Staff or Superadmin)
- Duplicate usernames are rejected
- Passwords are SHA-256 hashed before storage

**Right panel — Existing Accounts:**
- Lists all admin accounts with name, role pill (Superadmin = yellow, Staff = blue), username, and creation date
- A **Remove** button deletes any account except the currently signed-in admin's own account

**Roles:**
- **Superadmin** — full access including Audit Log, Admin Accounts management, and all member/payment operations
- **Staff** — can manage members, view entry log, analytics, payments, and backups; cannot access Audit Log or Admin Accounts

---

### Figure 14. Help & About

**Help** — located at `/help`.

A collapsible FAQ page with 14 questions covering:
- How to add a member and capture their face
- What to do when recognition fails
- How access control works
- Difference between Expired, Suspended, and Frozen
- How to renew a membership
- Multi-admin setup
- How to back up data
- Camera troubleshooting
- Login lockout recovery
- Exporting entry logs
- Recording payments
- What Freeze does
- Gym Floor behavior
- What the Audit Log tracks

Also includes a **Quick Navigation** reference grid of all URLs and an **Admin Roles** comparison.

---

**About** — located at `/about`.

Displays:
- System description and purpose
- Full feature list
- Technology stack grid (Python, Flask, DeepFace, TensorFlow, OpenCV, VGG-Face, Haar Cascade, CLAHE)
- Development team — Group 9 (Directo, Quimson, Madayag)
- Course information (IAS2, 3rd Year BSIT, Lorma Colleges, SY 2025–2026)
- Version and build date

---

## Curriculum Vitae

---

### DIRECTO, BRIX A.

**I. PERSONAL INFORMATION**
- Address: *(San Fernando, La Union)*
- Email: brix.directo@lorma.edu
- Role in Project: Group Leader

**II. EDUCATIONAL BACKGROUND**
- Tertiary: Lorma Colleges | 2022 – Present
  Bachelor of Science in Information Technology (3rd Year)

**III. INVOLVEMENT IN RESEARCH/RESEARCHES CONDUCTED**
- IAS2 Finals: IronGate — AI-Powered Gym Access Control System (Face Recognition, Flask, DeepFace, TensorFlow)

---

### QUIMSON, JIBREEL A.

**I. PERSONAL INFORMATION**
- Email: jibreel.quimson@lorma.edu
- Role in Project: Member

**II. EDUCATIONAL BACKGROUND**
- Tertiary: Lorma Colleges | 2022 – Present
  Bachelor of Science in Information Technology (3rd Year)

**III. INVOLVEMENT IN RESEARCH/RESEARCHES CONDUCTED**
- IAS2 Finals: IronGate — AI-Powered Gym Access Control System

---

### MADAYAG, DJAUNATHAN ALBERT S.

**I. PERSONAL INFORMATION**
- Email: djaunathan.madayag@lorma.edu
- Role in Project: Member

**II. EDUCATIONAL BACKGROUND**
- Tertiary: Lorma Colleges | 2022 – Present
  Bachelor of Science in Information Technology (3rd Year)

**III. INVOLVEMENT IN RESEARCH/RESEARCHES CONDUCTED**
- IAS2 Finals: IronGate — AI-Powered Gym Access Control System

---

*IronGate — AI Gym Access Control System | IAS2 Finals Project | Group 9 | Lorma Colleges | SY 2025–2026*
