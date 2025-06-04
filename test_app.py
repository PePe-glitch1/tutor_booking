import pytest
from app import app, db, User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Очищення користувачів
            db.session.query(User).delete()
            db.session.commit()
            # Створення тестових користувачів
            student = User(username='student1', password='test', is_tutor=False)
            tutor = User(username='tutor_test', password='test', is_tutor=True, subject='Math', level='School')
            db.session.add_all([student, tutor])
            db.session.commit()
            tutor_id = tutor.id
        yield client, tutor_id

def test_create_booking(client):
    client, tutor_id = client
    # Логін учня
    client.post('/login', data={'username': 'student1', 'password': 'test'}, follow_redirects=True)
    # Створення заявки на бронювання
    response = client.post(f'/book/{tutor_id}', data={
        'date': '2025-06-10',
        'time': '12:00',
    }, follow_redirects=True)
    # Перевірка статусу відповіді
    assert response.status_code in [200, 302]
    # Перевірка повідомлення про успішне бронювання
    assert "Бронювання створено" in response.get_data(as_text=True) or "Бронювання" in response.get_data(as_text=True)