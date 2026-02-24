from flask import Blueprint, render_template, request, jsonify, send_file
from app.models import Attendance, Student, Subject
from app import db
from datetime import date, datetime, timedelta
from sqlalchemy import func
import io
import csv

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
def reports_page():
    subjects = Subject.query.order_by(Subject.name).all()
    students = Student.query.filter_by(is_active=True).order_by(Student.name).all()
    return render_template('reports.html', subjects=subjects, students=students)


@reports_bp.route('/api/summary')
def api_summary():
    """Summary stats for a date range."""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    subject_id = request.args.get('subject_id', type=int)

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else (date.today() - timedelta(days=30))
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else date.today()
    except ValueError:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

    query = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    )
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    records = query.all()
    total_records = len(records)
    unique_students = len(set(r.student_id for r in records))
    by_status = {}
    for r in records:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    # Daily trend
    daily = {}
    for r in records:
        key = r.date.isoformat()
        daily[key] = daily.get(key, 0) + 1

    # Sort daily
    daily_sorted = sorted(daily.items())
    chart_labels = [d[0] for d in daily_sorted]
    chart_data = [d[1] for d in daily_sorted]

    return jsonify({
        'total_records': total_records,
        'unique_students': unique_students,
        'by_status': by_status,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })


@reports_bp.route('/api/student_report')
def student_report():
    """Per-student attendance summary for a date range."""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    subject_id = request.args.get('subject_id', type=int)

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else (date.today() - timedelta(days=30))
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else date.today()
    except ValueError:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

    query = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    )
    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    records = query.all()
    student_map = {}
    for r in records:
        sid = r.student_id
        if sid not in student_map:
            student_map[sid] = {
                'student_id': r.student.student_id if r.student else '',
                'name': r.student.name if r.student else 'Unknown',
                'department': r.student.department if r.student else '',
                'present': 0,
                'absent': 0,
                'late': 0,
                'total': 0
            }
        student_map[sid]['total'] += 1
        status = r.status or 'present'
        student_map[sid][status] = student_map[sid].get(status, 0) + 1

    rows = sorted(student_map.values(), key=lambda x: x['name'])
    for row in rows:
        row['attendance_pct'] = round((row['present'] / row['total']) * 100, 1) if row['total'] > 0 else 0.0

    return jsonify(rows)


@reports_bp.route('/api/export_csv')
def export_csv():
    """Export attendance records as CSV."""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    subject_id = request.args.get('subject_id', type=int)

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else (date.today() - timedelta(days=30))
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else date.today()
    except ValueError:
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

    query = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date, Attendance.student_id)

    if subject_id:
        query = query.filter_by(subject_id=subject_id)

    records = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Name', 'Department', 'Subject', 'Date', 'Time In', 'Status', 'Confidence (%)', 'Marked By'])
    for r in records:
        writer.writerow([
            r.student.student_id if r.student else '',
            r.student.name if r.student else '',
            r.student.department if r.student else '',
            r.subject.name if r.subject else '',
            r.date.isoformat() if r.date else '',
            r.time_in.strftime('%H:%M:%S') if r.time_in else '',
            r.status,
            f"{r.confidence * 100:.1f}" if r.confidence else '',
            r.marked_by
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{start_date}_{end_date}.csv'
    )
