from app import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    photo_path = db.Column(db.String(255), nullable=True)
    encoding_path = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attendances = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'year': self.year,
            'photo_path': self.photo_path,
            'is_active': self.is_active,
            'has_face_data': self.encoding_path is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }

    def __repr__(self):
        return f'<Department {self.code}: {self.name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    time_in = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    confidence = db.Column(db.Float, nullable=True)
    marked_by = db.Column(db.String(50), default='face_recognition')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_roll': self.student.student_id if self.student else None,
            'student_department': self.student.department if self.student else None,
            'date': self.date.isoformat() if self.date else None,
            'time_in': self.time_in.strftime('%H:%M:%S') if self.time_in else None,
            'status': self.status,
            'confidence': round(self.confidence * 100, 1) if self.confidence else None,
            'marked_by': self.marked_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Attendance Student:{self.student_id} Date:{self.date}>'
