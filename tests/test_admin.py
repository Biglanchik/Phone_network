# tests/test_admin.py
import unittest
import json
import tempfile
import os
from server.database import Database
from server.api import app

class TestAdminAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.db = Database(self.db_path)
        
        import server.api
        server.api.db = self.db
    
    def tearDown(self):
        self.temp_db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_admin_auth(self):
        """Тест авторизации админа"""
        response = self.app.post('/api/auth',
            json={'login': 'admin', 'password': 'admin123'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'admin')
    
    def test_create_client(self):
        """Тест создания клиента"""
        response = self.app.post('/api/clients',
            json={
                'full_name': 'Тестовый Клиент',
                'login': 'testuser',
                'password': 'test123',
                'tariff_id': 1
            })
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_delete_client(self):
        """Тест удаления клиента"""
        # Сначала создаем
        self.app.post('/api/clients',
            json={
                'full_name': 'Test Delete',
                'login': 'testdelete',
                'password': 'test123'
            })
        
        # Получаем клиента
        response = self.app.get('/api/clients/all')
        clients = json.loads(response.data)
        
        test_client = None
        for c in clients:
            if c['login'] == 'testdelete':
                test_client = c
                break
        
        if test_client:
            response = self.app.delete(f"/api/clients/{test_client['id']}")
            data = json.loads(response.data)
            self.assertTrue(data['success'])
    
    def test_update_client_tariff(self):
        """Тест изменения тарифа клиента"""
        response = self.app.put('/api/clients/1/tariff',
            json={'tariff_id': 2})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_set_balance(self):
        """Тест установки баланса"""
        response = self.app.put('/api/clients/1/balance/set',
            json={'amount': 500.0})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_create_tariff(self):
        """Тест создания тарифа"""
        response = self.app.post('/api/tariffs',
            json={
                'name': 'Premium',
                'description': 'Премиум тариф',
                'minute_price': 0.3
            })
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_delete_tariff(self):
        """Тест удаления тарифа"""
        # Сначала создаем
        self.app.post('/api/tariffs',
            json={
                'name': 'Test Tariff',
                'minute_price': 0.1
            })
        
        # Получаем список
        response = self.app.get('/api/tariffs')
        tariffs = json.loads(response.data)
        
        test_tariff = None
        for t in tariffs:
            if t['name'] == 'Test Tariff':
                test_tariff = t
                break
        
        if test_tariff:
            response = self.app.delete(f"/api/tariffs/{test_tariff['id']}")
            data = json.loads(response.data)
            self.assertTrue(data['success'])
    
    def test_get_statistics(self):
        """Тест получения статистики"""
        response = self.app.get('/api/statistics')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_clients', data)
        self.assertIn('total_devices', data)
        self.assertIn('total_calls', data)
        self.assertIn('total_revenue', data)


if __name__ == '__main__':
    unittest.main()