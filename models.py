from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_tutor = db.Column(db.Boolean, default=False)
    subject = db.Column(db.String(100), default="Не вказано")
    level = db.Column(db.String(100), default="Усі категорії")
    about = db.Column(db.String(255), default="")
    img = db.Column(db.String(255), default="https://randomuser.me/api/portraits/lego/2.jpg")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Заплановано")