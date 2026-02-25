from flask import Blueprint, render_template, request, jsonify
from app.models import Attendance, Student, Department
from app import db
from datetime import date, datetime

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/')
def list_attendance():
    departments = Department.query.order_by(Department.name).all()
    students = Student.query.filter_by(is_active=True).order_by(Student.name).all()
    return render_template('attendance.html', departments=departments, students=students)


@attendance_bp.route('/api/records')
def api_records():
    filter_date = request.args.get('date')
    filter_department = request.args.get('department')
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
    if filter_department:
        query = query.join(Student).filter(Student.department == filter_department)
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
    confidence = data.get('confidence', 0.0)
    today = date.today()
    now = datetime.now().time()

    if not student_db_id:
        return jsonify({'success': False, 'error': 'student_db_id required'}), 400

    student = Student.query.filter_by(student_id=student_db_id).first()
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404

    # Avoid duplicate for same student same day
    existing = Attendance.query.filter_by(
        student_id=student.id,
        date=today
    ).first()

    if existing:
        return jsonify({'success': False, 'error': 'Attendance already marked', 'already_marked': True})

    record = Attendance(
        student_id=student.id,
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
    student_id = data.get('student_id')
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
        date=mark_date
    ).first()

    if existing:
        existing.status = status
        db.session.commit()
        return jsonify({'success': True, 'record': existing.to_dict(), 'message': 'Attendance updated'})

    record = Attendance(
        student_id=student.id,
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


# Departments CRUD
@attendance_bp.route('/departments')
def list_departments():
    departments = Department.query.order_by(Department.name).all()
    return render_template('departments.html', departments=departments)


@attendance_bp.route('/departments/add', methods=['POST'])
def add_department():
    data = request.get_json()
    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'success': False, 'error': 'Code and Name are required'}), 400

    if Department.query.filter_by(code=code).first():
        return jsonify({'success': False, 'error': 'Department code already exists'}), 400

    department = Department(code=code, name=name)
    db.session.add(department)
    db.session.commit()
    return jsonify({'success': True, 'department': department.to_dict()})


@attendance_bp.route('/departments/<int:department_id>/delete', methods=['DELETE'])
def delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    db.session.delete(department)
    db.session.commit()
    return jsonify({'success': True})


@attendance_bp.route('/departments/api/list')
def departments_api_list():
    departments = Department.query.order_by(Department.name).all()
    return jsonify([d.to_dict() for d in departments])
