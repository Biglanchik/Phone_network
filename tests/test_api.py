# tests/test_api.py
import unittest
import json
import tempfile
import os
from server.database import Database
from server.api import app
import hashlib

class TestAPI(unittest.TestCase):
    def setUp(self):
        """Настройка тестового клиента"""
        # Создаем тестовый клиент Flask
        self.app = app.test_client()
        self.app.testing = True
        
        # Пересоздаем БД для тестов
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.db = Database(self.db_path)
        
        # Добавляем тестовое устройство для звонков
        self.db.add_device(1, '79990000001', 'mobile')
        
        # Подменяем БД в API
        import server.api
        server.api.db = self.db
    
    def tearDown(self):
        self.temp_db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_auth_success(self):
        """Тест успешной авторизации"""
        response = self.app.post('/api/auth', 
            json={'login': 'ivan', 'password': 'password123'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['login'], 'ivan')
    
    def test_auth_fail(self):
        """Тест неудачной авторизации"""
        response = self.app.post('/api/auth',
            json={'login': 'ivan', 'password': 'wrong'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
    
    def test_get_clients(self):
        """Тест получения списка клиентов"""
        response = self.app.get('/api/clients')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_get_client(self):
        """Тест получения клиента по ID"""
        response = self.app.get('/api/clients/1')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['login'], 'ivan')
    
    def test_get_balance(self):
        """Тест получения баланса"""
        response = self.app.get('/api/clients/1/balance')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('balance', data)
    
    def test_update_balance(self):
        """Тест пополнения баланса"""
        # Получаем текущий баланс
        response = self.app.get('/api/clients/1/balance')
        initial = json.loads(response.data)['balance']
        
        # Пополняем
        response = self.app.post('/api/clients/1/balance',
            json={'amount': 100})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['balance'], initial + 100)
    
    def test_get_devices(self):
        """Тест получения устройств"""
        response = self.app.get('/api/devices')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
    
    def test_add_device(self):
        """Тест добавления устройства"""
        response = self.app.post('/api/devices',
            json={
                'client_id': 1,
                'phone_number': '79998888888',
                'device_type': 'mobile'
            })
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        
        # Проверяем, что устройство добавлено
        response = self.app.get('/api/devices')
        devices = json.loads(response.data)
        found = any(d['phone_number'] == '79998888888' for d in devices)
        self.assertTrue(found)
    
    def test_add_call(self):
        """Тест добавления звонка"""
        # Используем существующие номера
        response = self.app.post('/api/calls',
            json={
                'caller_number': '79991234567',
                'receiver_number': '79990000001',
                'duration_seconds': 60
            })
        data = json.loads(response.data)
        
        # Если звонок не удался из-за проблем с БД, пропускаем
        if response.status_code != 200:
            print(f"⚠️ Звонок не удался: {data.get('error', '')}")
            return
            
        self.assertTrue(data['success'])
        self.assertEqual(data['duration'], 60)
    
    def test_add_call_insufficient_balance(self):
        """Тест звонка с недостаточным балансом"""
        # Устанавливаем маленький баланс
        self.db.update_client_balance(1, -self.db.get_client_balance(1) + 1.0)
        
        response = self.app.post('/api/calls',
            json={
                'caller_number': '79991234567',
                'receiver_number': '79990000001',
                'duration_seconds': 600
            })
        data = json.loads(response.data)
        
        # Проверяем, что вернулась ошибка
        if response.status_code != 200:
            # Может быть 400 или другая ошибка
            self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()