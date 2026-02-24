from flask import Blueprint, render_template, redirect, url_for
from app.models import Student, Attendance, Subject
from app import db
from datetime import date, datetime, timedelta
from sqlalchemy import func

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    today = date.today()
    total_students = Student.query.filter_by(is_active=True).count()
    today_attendance = Attendance.query.filter_by(date=today).count()
    total_subjects = Subject.query.count()

    # Attendance percentage today
    attendance_pct = 0
    if total_students > 0:
        attendance_pct = round((today_attendance / total_students) * 100, 1)

    # Recent attendance (last 10)
    recent = (
        Attendance.query
        .filter_by(date=today)
        .order_by(Attendance.created_at.desc())
        .limit(10)
        .all()
    )

    # Last 7 days attendance data for chart
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Attendance.query.filter_by(date=day).count()
        chart_labels.append(day.strftime('%b %d'))
        chart_data.append(count)

    stats = {
        'total_students': total_students,
        'today_attendance': today_attendance,
        'total_subjects': total_subjects,
        'attendance_pct': attendance_pct,
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_attendance=recent,
        chart_labels=chart_labels,
        chart_data=chart_data,
        today=today.strftime('%B %d, %Y')
    )
