"""
camera.py — Gym Membership System
Group 9 | Leader: Directo, Brix A.
Members: Quimson Jibreel A., Madayag Djaunathan Albert S.

Handles live camera feed, DeepFace recognition, and membership verification.
DeepFace runs in a background thread so the video stream is never blocked.
Entry is only granted to members with 'active' status.
"""

from deepface import DeepFace
import cv2
import os
import json
import threading
import time
from datetime import datetime, date

db_path        = "dataset"
MEMBERS_FILE   = "members.json"
ENTRY_LOG_FILE = "entry_log.csv"

# Ensure entry log exists with header
if not os.path.exists(ENTRY_LOG_FILE):
    import csv as csv_mod
    with open(ENTRY_LOG_FILE, "w", newline="") as f:
        writer = csv_mod.writer(f)
        writer.writerow(["Name", "Time", "Access", "Reason", "Emotion", "Gender", "Age", "Confidence"])


# ── Member registry helpers ───────────────────────────────────────────────────

def load_members():
    if not os.path.exists(MEMBERS_FILE):
        return []
    with open(MEMBERS_FILE, "r") as f:
        return json.load(f)


def get_member(folder_name):
    for m in load_members():
        if m["folder_name"] == folder_name:
            return m
    return None


def check_membership(folder_name):
    """Returns (access_granted: bool, reason: str, member: dict|None)"""
    member = get_member(folder_name)
    if member is None:
        return False, "Not a registered member", None

    status = member.get("status", "active")
    expiry = member.get("expiry_date", "")

    if status == "suspended":
        return False, "Membership suspended", member
    if status == "expired":
        return False, "Membership expired", member
    if status == "frozen":
        return False, "Membership frozen", member

    try:
        if datetime.strptime(expiry, "%Y-%m-%d").date() < date.today():
            return False, f"Expired on {expiry}", member
    except ValueError:
        pass

    return True, "Active member", member


_log_lock = threading.Lock()
_members_write_lock = threading.Lock()

def log_entry(name, access_result, reason, emotion, gender, age, confidence):
    import csv as csv_mod
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _log_lock:
        with open(ENTRY_LOG_FILE, "a", newline="") as f:
            writer = csv_mod.writer(f)
            writer.writerow([name, now, access_result, reason, emotion, gender, age, f"{confidence:.2f}"])

    # Increment total_visits counter for the member
    if access_result == "granted":
        try:
            with _members_write_lock:
                members_data = load_members()
                for m in members_data:
                    if m.get("full_name") == name:
                        m["total_visits"] = m.get("total_visits", 0) + 1
                        break
                with open(MEMBERS_FILE, "w") as f:
                    json.dump(members_data, f, indent=2)
        except Exception:
            pass  # Non-critical, don't break the flow


# ── Processing status overlay ─────────────────────────────────────────────────

_status_lock  = threading.Lock()
_status_msg   = ""
_status_since = 0.0


def set_status(msg):
    global _status_msg, _status_since
    with _status_lock:
        _status_msg   = msg
        _status_since = time.time()
    if msg:
        print(f"[camera] {msg}")


def get_status():
    with _status_lock:
        if _status_msg and (time.time() - _status_since) > 5:
            return ""
        return _status_msg


# ── Background camera thread ──────────────────────────────────────────────────

class CameraStream:
    def __init__(self, src=0):
        import platform
        self._cap = None

        if platform.system() == "Windows":
            # Try each index/backend combo until one actually delivers frames
            candidates = [
                (src,     cv2.CAP_DSHOW),
                (src + 1, cv2.CAP_DSHOW),
                (src,     cv2.CAP_MSMF),
                (src + 1, cv2.CAP_MSMF),
                (src,     cv2.CAP_ANY),
            ]
            for idx, backend in candidates:
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self._cap = cap
                        print(f"[camera] Using index={idx} backend={backend}")
                        break
                    cap.release()
            if self._cap is None:
                print("[camera] ERROR: No working camera found!")
                self._cap = cv2.VideoCapture(src)  # last resort
        else:
            self._cap = cv2.VideoCapture(src)

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS, 30)

        self._frame   = None
        self._lock    = threading.Lock()
        self._running = True

        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

        print("[camera] Waiting for camera to warm up...")
        deadline = time.time() + 10
        while time.time() < deadline:
            with self._lock:
                if self._frame is not None:
                    break
            time.sleep(0.1)
        print("[camera] Camera ready.")

    def _reader(self):
        while self._running:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._frame = frame
            else:
                time.sleep(0.05)

    def read(self):
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def stop(self):
        self._running = False
        self._thread.join(timeout=2)
        self._cap.release()


_stream = CameraStream(0)

_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ── Shared detection state ────────────────────────────────────────────────────

_state_lock = threading.Lock()
_detected = {
    "name":       "",
    "full_name":  "",
    "access":     None,
    "reason":     "",
    "emotion":    "",
    "gender":     "",
    "age":        "",
    "confidence": 0.0,
    "membership": "",
    "expiry":     "",
}

# ── Background DeepFace worker ────────────────────────────────────────────────

_face_queue      = None
_face_queue_lock = threading.Lock()
_worker_busy     = False

_last_logged = {"name": None, "time": 0}
LOG_COOLDOWN = 10


def _deepface_worker():
    global _face_queue, _worker_busy

    while True:
        face_img = None
        with _face_queue_lock:
            if _face_queue is not None:
                face_img     = _face_queue
                _face_queue  = None
                _worker_busy = True

        if face_img is None:
            time.sleep(0.02)
            continue

        try:
            # ── Step 1: Identify the person ──────────────────────────────────
            set_status("Verifying member identity")
            result = DeepFace.find(
                face_img, db_path=db_path,
                enforce_detection=False, silent=True,
                distance_metric="cosine",
                threshold=0.40          # DeepFace default for cosine distance
            )

            folder_name = "Unknown"
            if len(result) > 0 and len(result[0]) > 0:
                top = result[0].iloc[0]
                identity_path = top['identity']
                dist = float(top.get('distance', 1.0))
                if dist > 0.40:
                    print(f"[camera] Weak match rejected: dist={dist:.3f}")
                    folder_name = "Unknown"
                else:
                    folder_name = os.path.basename(os.path.dirname(identity_path))
                    print(f"[camera] Match: {folder_name} dist={dist:.3f}")

            if folder_name != "Unknown":
                access, reason, member = check_membership(folder_name)
                full_name  = member["full_name"] if member else folder_name.replace("_", " ")
                membership = member.get("membership_type", "") if member else ""
                expiry     = member.get("expiry_date", "") if member else ""
            else:
                access, reason, full_name = False, "Face not recognized", ""
                membership, expiry = "", ""

            # ── Step 2: Analyze emotion, gender, age ─────────────────────────
            set_status("Analyzing face attributes")
            analysis = DeepFace.analyze(
                face_img,
                actions=['emotion', 'gender', 'age'],
                enforce_detection=False,
                silent=True
            )
            d        = analysis[0]
            dominant = d['dominant_emotion']
            emotion  = dominant.capitalize()
            conf     = d['emotion'].get(dominant, 0.0)

            # Gender — DeepFace returns {'Man': x, 'Woman': y}
            g_scores = d.get('gender', {})
            gender   = max(g_scores, key=g_scores.get) if g_scores else ""

            age      = str(int(d.get('age', 0))) if d.get('age') else ""

            # ── Update shared state ───────────────────────────────────────────
            with _state_lock:
                _detected.update({
                    "name":       folder_name,
                    "full_name":  full_name,
                    "access":     access,
                    "reason":     reason,
                    "emotion":    emotion,
                    "gender":     gender,
                    "age":        age,
                    "confidence": conf,
                    "membership": membership,
                    "expiry":     expiry,
                })

            # ── Log with cooldown ─────────────────────────────────────────────
            now = time.time()
            if folder_name != "Unknown":
                if (_last_logged["name"] != folder_name
                        or (now - _last_logged["time"]) > LOG_COOLDOWN):
                    log_entry(
                        full_name or folder_name,
                        "granted" if access else "denied",
                        reason, emotion, gender, age, conf
                    )
                    _last_logged["name"] = folder_name
                    _last_logged["time"] = now

                    # Auto check-in when access is granted
                    if access:
                        try:
                            from app import _checkin_lock, _checked_in
                            with _checkin_lock:
                                _checked_in[folder_name] = {
                                    "full_name": full_name,
                                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                        except ImportError:
                            pass

            set_status("")

        except Exception as e:
            print(f"[camera] DeepFace error: {type(e).__name__}: {e}")
            set_status("")
        finally:
            with _face_queue_lock:
                _worker_busy = False


_worker_thread = threading.Thread(target=_deepface_worker, daemon=True)
_worker_thread.start()


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_status_banner(frame, msg):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 36), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    dots = "." * (int(time.time() * 2) % 4)
    cv2.putText(frame, f"  {msg}{dots}", (8, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 136), 2)


def _draw_overlay(frame, x, y, w, h, access, name, full_name,
                  reason, emotion, gender, age, confidence):
    """Draw bounding box + all labels. Flips below box if face is near top."""
    if access is True:
        color       = (0, 220, 80)
        access_text = "ACCESS GRANTED"
    elif access is False:
        color       = (50, 50, 255)
        access_text = "ACCESS DENIED"
    else:
        color       = (160, 160, 160)
        access_text = ""

    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    display_name = full_name if full_name else name.replace("_", " ")

    # Build label lines
    lines = []
    if display_name:
        lines.append((display_name,       color,          0.65, 2))
    if access_text:
        lines.append((access_text,        color,          0.55, 2))
    if reason:
        lines.append((reason,             (200,200,200),  0.48, 1))
    if emotion:
        lines.append((f"{emotion}  {confidence:.1f}%", (0,220,255), 0.48, 1))
    if gender or age:
        demo = f"{gender}  Age ~{age}" if gender and age else (gender or f"Age ~{age}")
        lines.append((demo,               (255,200,80),   0.48, 1))

    line_h = 20  # pixels per line
    total_h = len(lines) * line_h

    if y > total_h + 8:
        # Draw above the box (bottom-up)
        base = y - 8
        for text, col, scale, thick in reversed(lines):
            cv2.putText(frame, text, (x, base),
                        cv2.FONT_HERSHEY_SIMPLEX, scale, col, thick)
            base -= line_h
    else:
        # Draw below the box
        base = y + h + line_h
        for text, col, scale, thick in lines:
            cv2.putText(frame, text, (x, base),
                        cv2.FONT_HERSHEY_SIMPLEX, scale, col, thick)
            base += line_h


# ── Main frame generator ──────────────────────────────────────────────────────

def generate_frames():
    global _face_queue
    frame_count = 0

    while True:
        frame = _stream.read()

        if frame is None:
            import numpy as np
            placeholder = np.zeros((480, 640, 3), dtype='uint8')
            cv2.putText(placeholder, "Camera initializing...", (120, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 136), 2)
            _, buf = cv2.imencode('.jpg', placeholder)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                   + buf.tobytes() + b'\r\n')
            time.sleep(0.1)
            continue

        frame_count += 1
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = _face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=6, minSize=(100, 100),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        # Every 10 frames, send a face crop to the background worker
        with _face_queue_lock:
            busy = _worker_busy
        if frame_count % 10 == 0 and len(faces) > 0 and not busy:
            # Pick the largest face (most likely the real person, not background noise)
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            # Only process if face is reasonably large (at least 120x120 pixels)
            if w >= 120 and h >= 120:
                # Add padding around the face crop for better recognition
                pad_x = int(w * 0.15)
                pad_y = int(h * 0.15)
                y1 = max(0, y - pad_y)
                y2 = min(frame.shape[0], y + h + pad_y)
                x1 = max(0, x - pad_x)
                x2 = min(frame.shape[1], x + w + pad_x)
                face_crop = frame[y1:y2, x1:x2].copy()
                # Resize to 224x224 to match dataset images
                face_crop = cv2.resize(face_crop, (224, 224), interpolation=cv2.INTER_LANCZOS4)
                with _face_queue_lock:
                    _face_queue = face_crop

        # Read latest detection result
        with _state_lock:
            d = dict(_detected)

        # Draw overlay only on the largest detected face (ignore small false positives)
        if len(faces) > 0:
            largest = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest
            if w >= 100 and h >= 100:
                _draw_overlay(
                    frame, x, y, w, h,
                    d["access"], d["name"], d["full_name"],
                    d["reason"], d["emotion"], d["gender"],
                    d["age"],    d["confidence"]
                )

        status = get_status()
        if status:
            _draw_status_banner(frame, status)

        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
