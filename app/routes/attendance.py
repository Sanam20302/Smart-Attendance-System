from flask import Blueprint, render_template, request, jsonify
from app.models import Attendance, Student, Subject
from app import db
from datetime import date, datetime

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/')
def list_attendance():
    subjects = Subject.query.order_by(Subject.name).all()
    students = Student.query.filter_by(is_active=True).order_by(Student.name).all()
    return render_template('attendance.html', subjects=subjects, students=students)


@attendance_bp.route('/api/records')
def api_records():
    filter_date = request.args.get('date')
    filter_subject = request.args.get('subject_id', type=int)
    filter_student = request.args.get('student_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Attendance.query

    if filter_date:
        try:
            d = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter_by(date=d)
        except ValueError:
            pass
    if filter_subject:
        query = query.filter_by(subject_id=filter_subject)
    if filter_student:
        query = query.filter_by(student_id=filter_student)

    query = query.order_by(Attendance.date.desc(), Attendance.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'records': [r.to_dict() for r in paginated.items],
        'total': paginated.total,
        'page': page,
        'pages': paginated.pages
    })


@attendance_bp.route('/api/mark', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    student_db_id = data.get('student_db_id')
    subject_id = data.get('subject_id')
    confidence = data.get('confidence', 0.0)
    today = date.today()
    now = datetime.now().time()

    if not student_db_id:
        return jsonify({'success': False, 'error': 'student_db_id required'}), 400

    student = Student.query.filter_by(student_id=student_db_id).first()
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404

    # Avoid duplicate for same student same day same subject
    existing = Attendance.query.filter_by(
        student_id=student.id,
        date=today,
        subject_id=subject_id
    ).first()

    if existing:
        return jsonify({'success': False, 'error': 'Attendance already marked', 'already_marked': True})

    record = Attendance(
        student_id=student.id,
        subject_id=subject_id,
        date=today,
        time_in=now,
        status='present',
        confidence=confidence,
        marked_by='face_recognition'
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({'success': True, 'record': record.to_dict(), 'message': f"Attendance marked for {student.name}"})


@attendance_bp.route('/api/manual', methods=['POST'])
def manual_mark():
    """Manually mark attendance for a student."""
    data = request.get_json()
    student_id = data.get('student_id', type=int) or data.get('student_id')
    subject_id = data.get('subject_id')
    mark_date_str = data.get('date')
    status = data.get('status', 'present')

    if not student_id:
        return jsonify({'success': False, 'error': 'student_id required'}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404

    try:
        mark_date = datetime.strptime(mark_date_str, '%Y-%m-%d').date() if mark_date_str else date.today()
    except ValueError:
        mark_date = date.today()

    existing = Attendance.query.filter_by(
        student_id=student.id,
        date=mark_date,
        subject_id=subject_id
    ).first()

    if existing:
        existing.status = status
        db.session.commit()
        return jsonify({'success': True, 'record': existing.to_dict(), 'message': 'Attendance updated'})

    record = Attendance(
        student_id=student.id,
        subject_id=subject_id,
        date=mark_date,
        time_in=datetime.now().time(),
        status=status,
        marked_by='manual'
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({'success': True, 'record': record.to_dict(), 'message': 'Attendance marked manually'})


@attendance_bp.route('/api/delete/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    record = Attendance.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Record deleted'})


# Subjects CRUD
@attendance_bp.route('/subjects')
def list_subjects():
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('subjects.html', subjects=subjects)


@attendance_bp.route('/subjects/add', methods=['POST'])
def add_subject():
    data = request.get_json()
    code = data.get('code', '').strip()
    name = data.get('name', '').strip()
    department = data.get('department', '').strip() or None
    instructor = data.get('instructor', '').strip() or None

    if not code or not name:
        return jsonify({'success': False, 'error': 'Code and Name are required'}), 400

    if Subject.query.filter_by(code=code).first():
        return jsonify({'success': False, 'error': 'Subject code already exists'}), 400

    subject = Subject(code=code, name=name, department=department, instructor=instructor)
    db.session.add(subject)
    db.session.commit()
    return jsonify({'success': True, 'subject': subject.to_dict()})


@attendance_bp.route('/subjects/<int:subject_id>/delete', methods=['DELETE'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    return jsonify({'success': True})


@attendance_bp.route('/subjects/api/list')
def subjects_api_list():
    subjects = Subject.query.order_by(Subject.name).all()
    return jsonify([s.to_dict() for s in subjects])
