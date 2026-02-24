# 🎓 FaceAttend — Automatic Face Recognition Attendance System

A web-based attendance tracking system that uses deep learning face recognition to automatically mark student attendance in real time.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Flask](https://img.shields.io/badge/Flask-2.3%2B-lightgrey) ![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 📸 **Live Face Recognition** — Webcam-based real-time detection and recognition
- ✅ **Auto Attendance Marking** — Marks attendance the moment a student is recognized
- 👩‍🎓 **Student Management** — Add, edit, and delete students with face photo registration
- 📚 **Subject Management** — Organize attendance sessions by subject/course
- 📋 **Attendance Records** — Filter, view, manually adjust, or delete records
- 📊 **Reports & Analytics** — Date-range summaries, trend charts, and per-student statistics
- 📥 **CSV Export** — Download attendance data as spreadsheets

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, SQLAlchemy, Flask-Migrate |
| Face Recognition | `face_recognition` (dlib), OpenCV |
| Database | SQLite (file-based, zero config) |
| Frontend | Bootstrap 5, Chart.js, Vanilla JS |

---

## 📋 Prerequisites

- Python **3.9+** (tested up to 3.13)
- `git`
- A working **webcam** for live attendance

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/attendence_system.git
cd attendence_system
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install system dependencies (Linux)

```bash
sudo apt update
sudo apt install -y cmake build-essential libopenblas-dev liblapack-dev \
                   libx11-dev libatlas-base-dev python3-dev
```

> **macOS:** `brew install cmake` is sufficient.  
> **Windows:** Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and [CMake](https://cmake.org/download/).

### 4. Install Python packages

```bash
pip install setuptools wheel        # install build tools first
pip install -r requirements.txt     # then the rest
```

> ⏳ `dlib` (required by `face_recognition`) compiles from source and **takes 5–15 minutes** on first install. This is normal.

### 5. Run the app

```bash
python run.py
```

Open your browser at **[http://localhost:5000](http://localhost:5000)**

---

## 🗂️ Project Structure

```
attendence_system/
├── run.py                   # Entry point
├── config.py                # App configuration
├── requirements.txt
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Student, Subject, Attendance models
│   ├── face_utils.py        # Face encoding & recognition utilities
│   └── routes/
│       ├── main.py          # Dashboard
│       ├── students.py      # Student CRUD + photo upload
│       ├── attendance.py    # Attendance records + subjects
│       ├── camera.py        # Live MJPEG stream + auto-marking
│       └── reports.py       # Analytics + CSV export
├── app/templates/           # Jinja2 HTML templates
└── static/
    ├── css/style.css        # Dark glassmorphism design
    └── student_photos/      # Uploaded student photos (auto-created)
data/
└── encodings/               # Face encodings stored as .pkl (auto-created)
```

---

## 📖 Usage Guide

### Step 1 — Add Subjects
Go to **Subjects** in the sidebar → add the courses you teach (e.g., `CS301 – Data Structures`).

### Step 2 — Register Students
Go to **Students → Add Student**
- Fill in the student's ID, name, department, and year
- Upload a **clear, well-lit, frontal face photo**
- The system auto-generates and stores the face encoding

### Step 3 — Take Attendance
Go to **Live Attendance**
- Select the subject (optional)
- Adjust tolerance if needed (lower = stricter matching)
- Click **Start Session** — the webcam opens and recognition begins
- Attendance is marked automatically when a student is recognized with > 60% confidence

### Step 4 — View Records & Reports
- **Attendance Records** — filter by date, subject, or student; manually mark or delete entries
- **Reports** — generate summaries for any date range, view trends, export CSV

---

## ⚙️ Configuration

Edit `config.py` to adjust behaviour:

| Setting | Default | Description |
|---|---|---|
| `FACE_RECOGNITION_TOLERANCE` | `0.5` | Match strictness. Lower = stricter (0.4–0.6 recommended) |
| `FRAME_SKIP` | `3` | Process every Nth frame. Higher = faster, less accurate |
| `UPLOAD_FOLDER` | `static/student_photos` | Where student photos are saved |
| `ENCODINGS_FOLDER` | `data/encodings` | Where face encodings (`.pkl`) are stored |

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot import 'setuptools.build_meta'` | Run `pip install setuptools wheel` first, then retry |
| `dlib` build fails | Install system deps: `sudo apt install cmake build-essential libopenblas-dev` |
| `face_recognition_models` missing | Run `pip install git+https://github.com/ageitgey/face_recognition_models` |
| Camera not opening | Check webcam permissions; try changing camera index in `camera.py` from `0` to `1` |
| CSS not loading | Ensure `static_folder='../static'` is set in `app/__init__.py` |

---

## 📄 License

MIT — free to use for educational and personal projects.
