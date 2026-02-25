from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app.models import Student, Department
from app import db
from app.face_utils import encode_face_from_image, save_encoding, allowed_file
import os
import uuid

students_bp = Blueprint('students', __name__)


@students_bp.route('/')
def list_students():
    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template('students.html', students=students)


@students_bp.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip() or None
        department = request.form.get('department', '').strip() or None
        year = request.form.get('year', type=int)
        photo = request.files.get('photo')

        # Validation
        if not student_id or not name:
            return jsonify({'success': False, 'error': 'Student ID and Name are required'}), 400

        if Student.query.filter_by(student_id=student_id).first():
            return jsonify({'success': False, 'error': 'Student ID already exists'}), 400

        if email and Student.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400

        photo_path = None
        encoding_path = None

        if photo and photo.filename and allowed_file(photo.filename):
            filename = secure_filename(f"{student_id}_{uuid.uuid4().hex[:8]}{os.path.splitext(photo.filename)[1]}")
            photo_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_save_path)
            photo_path = f"student_photos/{filename}"

            # Generate face encoding
            encoding, err = encode_face_from_image(photo_save_path)
            if err:
                return jsonify({'success': False, 'error': f'Face encoding error: {err}'}), 400

            enc_path, enc_err = save_encoding(
                encoding, student_id, current_app.config['ENCODINGS_FOLDER']
            )
            if enc_err:
                return jsonify({'success': False, 'error': f'Could not save face data: {enc_err}'}), 500
            encoding_path = enc_path

        student = Student(
            student_id=student_id,
            name=name,
            email=email,
            department=department,
            year=year,
            photo_path=photo_path,
            encoding_path=encoding_path
        )
        db.session.add(student)
        db.session.commit()

        return jsonify({'success': True, 'student': student.to_dict(), 'message': 'Student added successfully!'})

    departments = Department.query.order_by(Department.name).all()
    return render_template('add_student.html', departments=departments)


@students_bp.route('/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict())


@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form.get('name', student.name).strip()
        student.email = request.form.get('email', '').strip() or None
        student.department = request.form.get('department', '').strip() or None
        student.year = request.form.get('year', type=int)

        photo = request.files.get('photo')
        if photo and photo.filename and allowed_file(photo.filename):
            filename = secure_filename(f"{student.student_id}_{uuid.uuid4().hex[:8]}{os.path.splitext(photo.filename)[1]}")
            photo_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_save_path)
            student.photo_path = f"student_photos/{filename}"

            encoding, err = encode_face_from_image(photo_save_path)
            if err:
                return jsonify({'success': False, 'error': f'Face encoding error: {err}'}), 400

            enc_path, enc_err = save_encoding(
                encoding, student.student_id, current_app.config['ENCODINGS_FOLDER']
            )
            if not enc_err:
                student.encoding_path = enc_path

        db.session.commit()
        return jsonify({'success': True, 'student': student.to_dict(), 'message': 'Student updated successfully!'})

    departments = Department.query.order_by(Department.name).all()
    return render_template('edit_student.html', student=student, departments=departments)


@students_bp.route('/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    # Remove photo and encoding files
    if student.photo_path:
        full_path = os.path.join(current_app.static_folder, student.photo_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    if student.encoding_path and os.path.exists(student.encoding_path):
        os.remove(student.encoding_path)

    db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Student deleted successfully'})


@students_bp.route('/api/list')
def api_list():
    students = Student.query.filter_by(is_active=True).order_by(Student.name).all()
    return jsonify([s.to_dict() for s in students])
