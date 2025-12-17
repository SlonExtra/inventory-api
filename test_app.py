import pytest
from app import create_app
from models import db

@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_add_item(client):
    response = client.post("/items", json={
        "name": "Test Item",
        "quantity": 10,
        "price": 100.0,
        "category": "Electronics",
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Test Item"

    response = client.post("/items", json={
        "name": "Test Item",
        "quantity": -5,
        "price": 100.0,
        "category": "Electronics",
    })
    assert response.status_code == 400


def test_get_items(client):
    # Добавляем тестовые данные
    client.post('/items', json={
        'name': 'Item 1',
        'quantity': 5,
        'price': 50.0,
        'category': 'Books'
    })
    
    client.post('/items', json={
        'name': 'Item 2',
        'quantity': 3,
        'price': 30.0,
        'category': 'Electronics'
    })
    
    # Получаем все товары
    response = client.get('/items')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    
    # Фильтрация по категории
    response = client.get('/items?category=Books')
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['category'] == 'Books'

def test_update_item(client):
    # Добавляем товар
    response = client.post('/items', json={
        'name': 'Test Item',
        'quantity': 10,
        'price': 100.0,
        'category': 'Electronics'
    })
    item_id = response.get_json()['id']
    
    # Обновляем товар
    response = client.put(f'/items/{item_id}', json={
        'name': 'Updated Item',
        'quantity': 20,
        'price': 150.0
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Updated Item'
    assert data['quantity'] == 20

def test_delete_item(client):
    # Добавляем товар
    response = client.post('/items', json={
        'name': 'Test Item',
        'quantity': 10,
        'price': 100.0,
        'category': 'Electronics'
    })
    item_id = response.get_json()['id']
    
    # Удаляем товар
    response = client.delete(f'/items/{item_id}')
    assert response.status_code == 200
    
    # Проверяем, что товар удален
    response = client.get(f'/items/{item_id}')
    assert response.status_code == 404

def test_report_summary(client):
    # Добавляем тестовые данные
    client.post('/items', json={
        'name': 'Item 1',
        'quantity': 5,
        'price': 50.0,
        'category': 'Books'
    })
    
    client.post('/items', json={
        'name': 'Item 2',
        'quantity': 0,
        'price': 30.0,
        'category': 'Electronics'
    })
    
    # Генерируем отчет
    response = client.get('/reports/summary')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'total_inventory_value' in data
    assert 'categories' in data
    assert 'low_stock_items' in data
    
    # Проверяем CSV формат
    response = client.get('/reports/summary?format=csv')
    assert response.status_code == 200
    assert 'text/csv' in response.content_type