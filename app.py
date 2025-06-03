from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tutor_booking.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    if not hasattr(app, 'db_created'):
        db.create_all()
        # Додаємо тестових репетиторів із subject, level, about, img
        if not User.query.filter_by(username='tutor1').first():
            t1 = User(
                username='tutor1',
                password=generate_password_hash('12345'),
                is_tutor=True,
                subject='Англійська мова',
                level='Дорослі',
                about='Розмовна англійська, підготовка до IELTS.',
                img='https://randomuser.me/api/portraits/women/45.jpg'
            )
            t2 = User(
                username='tutor2',
                password=generate_password_hash('12345'),
                is_tutor=True,
                subject='Математика',
                level='Школа',
                about='Готую до ЗНО, працюю з учнями 8-11 класів.',
                img='https://randomuser.me/api/portraits/men/33.jpg'
            )
            db.session.add_all([t1, t2])
            db.session.commit()
        app.db_created = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_tutor = 'is_tutor' in request.form
        subject = request.form['subject'] if is_tutor else ""
        level = request.form['level'] if is_tutor else ""
        about = request.form['about'] if is_tutor else ""
        # img та інші — за бажанням
        if User.query.filter_by(username=username).first():
            flash('Користувач уже існує')
            return redirect(url_for('register'))
        user = User(
            username=username,
            password=generate_password_hash(password),
            is_tutor=is_tutor,
            subject=subject,
            level=level,
            about=about,
            img="https://randomuser.me/api/portraits/lego/2.jpg"
        )
        db.session.add(user)
        db.session.commit()
        flash('Реєстрація успішна. Увійдіть.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('tutors'))
        flash('Невірний логін або пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/tutors')
@login_required
def tutors():
    tutors = User.query.filter_by(is_tutor=True).all()
    return render_template('tutors.html', tutors=tutors)

@app.route('/book/<int:tutor_id>', methods=['GET', 'POST'])
@login_required
def book(tutor_id):
    tutor = User.query.get_or_404(tutor_id)
    if request.method == 'POST':
        date_part = request.form['date']
        time_part = request.form['time']
        date_time = f"{date_part} {time_part}"
        price = 300
        booking = Booking(student_id=current_user.id, tutor_id=tutor.id, date=date_time)
        db.session.add(booking)
        db.session.commit()
        flash(f'Бронювання створено. Вартість заняття: {price} грн')
        return redirect(url_for('my_bookings'))
    return render_template('book.html', tutor=tutor)

@app.route('/my_bookings', methods=['GET', 'POST'])
@login_required
def my_bookings():
    if current_user.is_tutor:
        bookings = Booking.query.filter_by(tutor_id=current_user.id).all()
        bookings_info = [
            {
                'id': booking.id,
                'username': User.query.get(booking.student_id).username if User.query.get(booking.student_id) else "Невідомо",
                'date': booking.date,
                'status': booking.status
            }
            for booking in bookings
        ]
        return render_template('my_bookings.html', bookings=bookings_info, is_tutor=True)
    else:
        bookings = Booking.query.filter_by(student_id=current_user.id).all()
        bookings_info = []
        for booking in bookings:
            tutor = User.query.get(booking.tutor_id)
            bookings_info.append({
                'id': booking.id,
                'tutor_name': tutor.username if tutor else "Невідомо",
                'subject': tutor.subject if tutor and tutor.subject else 'Не вказано',
                'tutor_img': tutor.img if tutor and tutor.img else 'https://randomuser.me/api/portraits/lego/2.jpg',
                'date': booking.date,
                'status': booking.status
            })
        return render_template('my_bookings.html', bookings=bookings_info, is_tutor=False)

@app.route('/delete_booking/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # Дозволити видаляти заявку або учню (автору заявки), або викладачу (на кого подано заявку)
    if booking.student_id == current_user.id or booking.tutor_id == current_user.id:
        db.session.delete(booking)
        db.session.commit()
        flash('Заявку видалено')
    else:
        flash('Ви не маєте прав для видалення цієї заявки')
    return redirect(url_for('my_bookings'))

@app.route('/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.student_id != current_user.id:
        flash('Ви не маєте прав для редагування цієї заявки')
        return redirect(url_for('my_bookings'))
    if request.method == 'POST':
        date_part = request.form['date']
        time_part = request.form['time']
        booking.date = f"{date_part} {time_part}"
        db.session.commit()
        flash('Заявку оновлено')
        return redirect(url_for('my_bookings'))
    return render_template('edit_booking.html', booking=booking)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)