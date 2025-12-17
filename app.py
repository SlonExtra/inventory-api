from flask import Flask, request, jsonify, make_response
from models import db, Item
import csv
import io

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://inventory_user:STRONG_PASSWORD@localhost:5432/inventory_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def home():
    return jsonify({'message': 'Inventory API'})

# 1. Добавление товара
@app.route('/items', methods=['POST'])
def add_item():
    data = request.get_json()
    
    # Проверка данных
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    quantity = data.get('quantity')
    price = data.get('price')
    category = data.get('category')
    
    # Валидация
    if not all([name, quantity, price, category]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if quantity < 0:
        return jsonify({'error': 'Quantity cannot be negative'}), 400
    
    if price <= 0:
        return jsonify({'error': 'Price must be greater than 0'}), 400
    
    # Создание товара
    item = Item(
        name=name,
        quantity=quantity,
        price=price,
        category=category
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify(item.to_dict()), 201

# 2. Получение списка товаров
@app.route('/items', methods=['GET'])
def get_items():
    category = request.args.get('category')
    
    if category:
        items = Item.query.filter_by(category=category).all()
    else:
        items = Item.query.all()
    
    return jsonify([item.to_dict() for item in items])

# 3. Обновление товара
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    data = request.get_json()
    
    # Проверка данных
    quantity = data.get('quantity', item.quantity)
    price = data.get('price', item.price)
    
    if quantity < 0:
        return jsonify({'error': 'Quantity cannot be negative'}), 400
    
    if price <= 0:
        return jsonify({'error': 'Price must be greater than 0'}), 400
    
    # Обновление полей
    item.name = data.get('name', item.name)
    item.quantity = quantity
    item.price = price
    item.category = data.get('category', item.category)
    
    db.session.commit()
    
    return jsonify(item.to_dict())

# 4. Удаление товара
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item deleted'})

# 5. Генерация отчетов
@app.route('/reports/summary', methods=['GET'])
def generate_report():
    items = Item.query.all()
    
    # Общая стоимость
    total_value = sum(item.quantity * item.price for item in items)
    
    # Разбивка по категориям
    categories = {}
    for item in items:
        if item.category not in categories:
            categories[item.category] = {
                'count': 0,
                'total_value': 0
            }
        categories[item.category]['count'] += 1
        categories[item.category]['total_value'] += item.quantity * item.price
    
    # Товары с нулевым или отрицательным количеством
    low_stock_items = [
        item.to_dict() for item in items 
        if item.quantity <= 0
    ]
    
    report = {
        'total_inventory_value': total_value,
        'categories': categories,
        'low_stock_items': low_stock_items
    }
    
    # Проверяем формат запроса
    format_type = request.args.get('format', 'json')
    
    if format_type == 'csv':
        # Создаем CSV отчет
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['Category', 'Item Count', 'Total Value'])
        for category, data in categories.items():
            writer.writerow([category, data['count'], data['total_value']])
        
        writer.writerow([])
        writer.writerow(['Total Inventory Value', total_value])
        
        if low_stock_items:
            writer.writerow([])
            writer.writerow(['Low Stock Items'])
            writer.writerow(['ID', 'Name', 'Quantity', 'Price', 'Category'])
            for item in low_stock_items:
                writer.writerow([
                    item['id'],
                    item['name'],
                    item['quantity'],
                    item['price'],
                    item['category']
                ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=inventory_report.csv'
        return response
    
    # По умолчанию возвращаем JSON
    return jsonify(report)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)