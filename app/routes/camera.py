import cv2
import threading
import numpy as np
from flask import Blueprint, render_template, Response, request, jsonify, current_app
from app.models import Student, Department
from app import db
from app.face_utils import load_all_encodings, recognize_faces_in_frame, draw_recognition_results
from datetime import date, datetime

camera_bp = Blueprint('camera', __name__)

# Global camera state
_camera_lock = threading.Lock()
_active_sessions = {}  # session_id: CameraSession


class CameraSession:
    def __init__(self, closing_time=None, tolerance=0.5, app=None):
        self.closing_time = closing_time
        self.tolerance = tolerance
        self.cap = None
        self.running = False
        self.frame_count = 0
        self.marked_today = set()  # student_db_keys already marked this session
        self.last_results = []
        self.status_messages = []
        self.app = app

    def start(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            return False, "Cannot open camera"
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        return True, None

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def generate_frames(self):
        """Generator that yields MJPEG frames."""
        skip = 3
        frame_idx = 0
        known_encodings = {}
        student_names = {}

        with self.app.app_context():
            known_encodings = load_all_encodings(self.app.config['ENCODINGS_FOLDER'])
            students = Student.query.filter_by(is_active=True).all()
            student_names = {s.student_id: s.name for s in students}

        try:
            while self.running and self.cap and self.cap.isOpened():
                success, frame = self.cap.read()
                if not success:
                    break

                frame_idx += 1
                if frame_idx % skip == 0:
                    results = recognize_faces_in_frame(frame, known_encodings, self.tolerance)
                    self.last_results = results

                    # Auto-mark attendance for recognized faces
                    with self.app.app_context():
                        now_time = datetime.now().time()
                        is_closed = False
                        if self.closing_time:
                            closing_dt = datetime.strptime(self.closing_time, "%H:%M").time()
                            if now_time > closing_dt:
                                is_closed = True

                        if is_closed:
                            msg = f"⏰ auto-closed (Passed {self.closing_time})."
                            self.status_messages.insert(0, msg)
                            self.status_messages = self.status_messages[:20]
                            self.stop()
                        else:
                            for result in results:
                                key = result['student_db_key']
                                if key and key not in self.marked_today and result['confidence'] > 0.6:
                                    self._mark_attendance(key, result['confidence'])

                    frame = draw_recognition_results(frame, results, student_names)

                if frame is None or frame.size == 0:
                    continue

                # Encode and yield
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' +
                           buffer.tobytes() + b'\r\n')
        finally:
            self.stop()

    def _mark_attendance(self, student_db_key, confidence):
        """Mark attendance in the database."""
        try:
            student = Student.query.filter_by(student_id=student_db_key).first()
            if not student:
                return
            from app.models import Attendance
            today = date.today()
            existing = Attendance.query.filter_by(
                student_id=student.id,
                date=today
            ).first()
            if existing:
                self.marked_today.add(student_db_key)
                return
            record = Attendance(
                student_id=student.id,
                date=today,
                time_in=datetime.now().time(),
                status='present',
                confidence=confidence,
                marked_by='face_recognition'
            )
            db.session.add(record)
            db.session.commit()
            self.marked_today.add(student_db_key)
            msg = f"✅ Marked: {student.name} ({datetime.now().strftime('%H:%M:%S')})"
            self.status_messages.insert(0, msg)
            self.status_messages = self.status_messages[:20]  # Keep last 20
        except Exception as e:
            db.session.rollback()


# Global session (single camera)
_session = None
_session_lock = threading.Lock()


@camera_bp.route('/')
def camera_page():
    return render_template('camera.html')


@camera_bp.route('/start', methods=['POST'])
def start_camera():
    global _session
    data = request.get_json() or {}
    closing_time = data.get('closing_time')
    tolerance = float(data.get('tolerance', 0.5))

    with _session_lock:
        if _session and _session.running:
            return jsonify({'success': False, 'error': 'Camera already running'})

        app = current_app._get_current_object()
        _session = CameraSession(closing_time=closing_time, tolerance=tolerance, app=app)
        ok, err = _session.start()
        if not ok:
            _session = None
            return jsonify({'success': False, 'error': err})

    return jsonify({'success': True, 'message': 'Camera started'})


@camera_bp.route('/stop', methods=['POST'])
def stop_camera():
    global _session
    with _session_lock:
        if _session:
            _session.stop()
            _session = None
    return jsonify({'success': True, 'message': 'Camera stopped'})


@camera_bp.route('/feed')
def video_feed():
    global _session
    if not _session or not _session.running:
        # Return a blank frame if camera not started
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank, 'Camera not started', (150, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        ret, buffer = cv2.imencode('.jpg', blank)
        frame = buffer.tobytes()

        def gen_blank():
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        return Response(gen_blank(), mimetype='multipart/x-mixed-replace; boundary=frame')

    def gen():
        yield from _session.generate_frames()

    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


@camera_bp.route('/status')
def camera_status():
    global _session
    if not _session:
        return jsonify({'running': False, 'marked_count': 0, 'messages': []})

    return jsonify({
        'running': _session.running,
        'marked_count': len(_session.marked_today),
        'marked_students': list(_session.marked_today),
        'messages': _session.status_messages
    })
