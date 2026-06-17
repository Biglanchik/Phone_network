# server/api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from server.database import Database
import json

app = Flask(__name__)
CORS(app)
db = Database()

@app.route('/api/auth', methods=['POST'])
def auth():
    """Авторизация пользователя"""
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    
    if not login or not password:
        return jsonify({"success": False, "error": "Введите логин и пароль"}), 400
    
    user = db.authenticate(login, password)
    if user:
        return jsonify({"success": True, "user": user})
    else:
        return jsonify({"success": False, "error": "Неверный логин или пароль"}), 401

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Получить список клиентов (для обычного пользователя)"""
    search = request.args.get('search', '')
    limit = int(request.args.get('limit', 100))
    clients = db.get_clients(search, limit)
    return jsonify(clients)

@app.route('/api/clients/all', methods=['GET'])
def get_all_clients():
    """Получить всех клиентов (для администратора)"""
    search = request.args.get('search', '')
    limit = int(request.args.get('limit', 100))
    clients = db.get_all_clients(search, limit)
    return jsonify(clients)

@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    """Получить информацию о клиенте"""
    client = db.get_client(client_id)
    if client:
        return jsonify(client)
    return jsonify({"error": "Клиент не найден"}), 404

@app.route('/api/clients', methods=['POST'])
def create_client():
    """Создать нового клиента (администратор)"""
    data = request.get_json()
    full_name = data.get('full_name')
    login = data.get('login')
    password = data.get('password')
    tariff_id = data.get('tariff_id', 1)
    
    if not full_name or not login or not password:
        return jsonify({"success": False, "error": "Не все данные заполнены"}), 400
    
    success = db.create_client(full_name, login, password, tariff_id)
    if success:
        return jsonify({"success": True, "message": "Клиент создан"})
    return jsonify({"success": False, "error": "Клиент с таким логином уже существует"}), 400

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Удалить клиента (администратор)"""
    success = db.delete_client(client_id)
    if success:
        return jsonify({"success": True, "message": "Клиент удален"})
    return jsonify({"success": False, "error": "Не удалось удалить клиента"}), 400

@app.route('/api/clients/<int:client_id>/tariff', methods=['PUT'])
def update_client_tariff(client_id):
    """Изменить тариф клиента (администратор)"""
    data = request.get_json()
    tariff_id = data.get('tariff_id')
    
    if not tariff_id:
        return jsonify({"success": False, "error": "Укажите ID тарифа"}), 400
    
    success = db.update_client_tariff(client_id, tariff_id)
    if success:
        return jsonify({"success": True, "message": "Тариф обновлен"})
    return jsonify({"success": False, "error": "Не удалось обновить тариф"}), 400

@app.route('/api/clients/<int:client_id>/balance', methods=['GET'])
def get_balance(client_id):
    """Получить баланс клиента"""
    balance = db.get_client_balance(client_id)
    if balance is not None:
        return jsonify({"balance": balance})
    return jsonify({"error": "Клиент не найден"}), 404

@app.route('/api/clients/<int:client_id>/balance', methods=['POST'])
def update_balance(client_id):
    """Пополнить баланс (для обычного пользователя)"""
    data = request.get_json()
    amount = data.get('amount', 0)
    
    if amount <= 0:
        return jsonify({"success": False, "error": "Сумма должна быть больше 0"}), 400
    
    success = db.update_client_balance(client_id, amount)
    if success:
        new_balance = db.get_client_balance(client_id)
        return jsonify({"success": True, "balance": new_balance})
    return jsonify({"success": False, "error": "Ошибка пополнения"}), 500

@app.route('/api/clients/<int:client_id>/balance/set', methods=['PUT'])
def set_balance(client_id):
    """Установить точный баланс (администратор)"""
    data = request.get_json()
    amount = data.get('amount', 0)
    
    if amount < 0:
        return jsonify({"success": False, "error": "Баланс не может быть отрицательным"}), 400
    
    success = db.set_client_balance(client_id, amount)
    if success:
        return jsonify({"success": True, "message": "Баланс обновлен"})
    return jsonify({"success": False, "error": "Не удалось обновить баланс"}), 400

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Получить список устройств"""
    client_id = request.args.get('client_id')
    phone = request.args.get('phone', '')
    limit = int(request.args.get('limit', 100))
    
    if client_id:
        client_id = int(client_id)
    
    devices = db.get_devices(client_id, phone, limit)
    return jsonify(devices)

@app.route('/api/devices', methods=['POST'])
def add_device():
    """Добавить устройство"""
    data = request.get_json()
    client_id = data.get('client_id')
    phone_number = data.get('phone_number')
    device_type = data.get('device_type', 'mobile')
    
    if not client_id or not phone_number:
        return jsonify({"success": False, "error": "Не все данные заполнены"}), 400
    
    success = db.add_device(client_id, phone_number, device_type)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Такой номер уже существует"}), 400

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Удалить устройство"""
    success = db.delete_device(device_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Устройство не найдено"}), 404

@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """Обновить устройство"""
    data = request.get_json()
    device_type = data.get('device_type')
    
    if not device_type:
        return jsonify({"success": False, "error": "Укажите тип устройства"}), 400
    
    success = db.update_device(device_id, device_type)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Устройство не найдено"}), 404

@app.route('/api/calls', methods=['POST'])
def add_call():
    """Зарегистрировать звонок"""
    data = request.get_json()
    caller = data.get('caller_number')
    receiver = data.get('receiver_number')
    duration = int(data.get('duration_seconds', 0))
    
    if not caller or not receiver or duration <= 0:
        return jsonify({"success": False, "error": "Неверные данные звонка"}), 400
    
    result = db.add_call(caller, receiver, duration)
    if result.get('success'):
        return jsonify(result)
    return jsonify({"success": False, "error": result.get('error', 'Ошибка')}), 400

@app.route('/api/calls', methods=['GET'])
def get_calls():
    """Получить историю звонков"""
    client_id = request.args.get('client_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 100))
    
    if client_id:
        client_id = int(client_id)
    
    calls = db.get_calls(client_id, start_date, end_date, limit)
    return jsonify(calls)

# --- АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ---

@app.route('/api/tariffs', methods=['GET'])
def get_tariffs():
    """Получить все тарифы"""
    tariffs = db.get_tariffs()
    return jsonify(tariffs)

@app.route('/api/tariffs', methods=['POST'])
def create_tariff():
    """Создать новый тариф (администратор)"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    minute_price = data.get('minute_price')
    
    if not name or minute_price is None:
        return jsonify({"success": False, "error": "Не все данные заполнены"}), 400
    
    if minute_price <= 0:
        return jsonify({"success": False, "error": "Цена должна быть больше 0"}), 400
    
    success = db.add_tariff(name, description, minute_price)
    if success:
        return jsonify({"success": True, "message": "Тариф создан"})
    return jsonify({"success": False, "error": "Ошибка создания тарифа"}), 400

@app.route('/api/tariffs/<int:tariff_id>', methods=['PUT'])
def update_tariff(tariff_id):
    """Обновить тариф (администратор)"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    minute_price = data.get('minute_price')
    
    if not name or minute_price is None:
        return jsonify({"success": False, "error": "Не все данные заполнены"}), 400
    
    if minute_price <= 0:
        return jsonify({"success": False, "error": "Цена должна быть больше 0"}), 400
    
    success = db.update_tariff(tariff_id, name, description, minute_price)
    if success:
        return jsonify({"success": True, "message": "Тариф обновлен"})
    return jsonify({"success": False, "error": "Тариф не найден"}), 404

@app.route('/api/tariffs/<int:tariff_id>', methods=['DELETE'])
def delete_tariff(tariff_id):
    """Удалить тариф (администратор)"""
    success = db.delete_tariff(tariff_id)
    if success:
        return jsonify({"success": True, "message": "Тариф удален"})
    return jsonify({"success": False, "error": "Тариф используется клиентами или не найден"}), 400

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Получить статистику системы (администратор)"""
    stats = db.get_statistics()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)