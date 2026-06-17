# server/database.py
import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

class Database:
    def __init__(self, db_path: str = "phone_network.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация БД - создание таблиц и добавление тестовых данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Создание таблиц
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS tariffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                minute_price REAL NOT NULL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                login TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                tariff_id INTEGER,
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tariff_id) REFERENCES tariffs(id)
            );
            
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                phone_number TEXT UNIQUE NOT NULL,
                device_type TEXT CHECK(device_type IN ('home', 'mobile')),
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_device_id INTEGER NOT NULL,
                receiver_device_id INTEGER NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds INTEGER DEFAULT 0,
                cost REAL DEFAULT 0,
                status TEXT CHECK(status IN ('started', 'ended', 'failed')) DEFAULT 'started',
                FOREIGN KEY (caller_device_id) REFERENCES devices(id),
                FOREIGN KEY (receiver_device_id) REFERENCES devices(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_calls_caller ON calls(caller_device_id);
            CREATE INDEX IF NOT EXISTS idx_calls_receiver ON calls(receiver_device_id);
            CREATE INDEX IF NOT EXISTS idx_devices_client ON devices(client_id);
            CREATE INDEX IF NOT EXISTS idx_devices_number ON devices(phone_number);
        """)
        
        # ДОБАВЛЯЕМ КОЛОНКУ role ЕСЛИ ЕЕ НЕТ
        try:
            cursor.execute("ALTER TABLE clients ADD COLUMN role TEXT DEFAULT 'user'")
        except sqlite3.OperationalError:
            # Колонка уже существует
            pass
        
        # Добавление тестовых тарифов
        tariffs = [
            (1, 'Эконом', '1 руб/мин', 1.0),
            (2, 'Стандарт', '0.7 руб/мин', 0.7),
            (3, 'Бизнес', '0.5 руб/мин', 0.5),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO tariffs (id, name, description, minute_price) VALUES (?, ?, ?, ?)",
            tariffs
        )
        
        # Добавление тестового клиента
        password_hash = hashlib.sha256("password123".encode()).hexdigest()
        
        # Проверяем есть ли уже клиент с id=1
        cursor.execute("SELECT id FROM clients WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO clients (id, full_name, login, password_hash, tariff_id, balance, role) "
                "VALUES (1, 'Иван Иванов', 'ivan', ?, 1, 100.0, 'user')",
                (password_hash,)
            )
        
        # Добавление администратора
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        cursor.execute("SELECT id FROM clients WHERE id = 2")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO clients (id, full_name, login, password_hash, tariff_id, balance, role) "
                "VALUES (2, 'Администратор', 'admin', ?, 1, 1000.0, 'admin')",
                (admin_hash,)
            )
        
        # Добавление устройства для клиента
        cursor.execute("SELECT id FROM devices WHERE phone_number = '79991234567'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO devices (client_id, phone_number, device_type) "
                "VALUES (1, '79991234567', 'mobile')"
            )
        
        # Добавление устройства для администратора
        cursor.execute("SELECT id FROM devices WHERE phone_number = '79990000001'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO devices (client_id, phone_number, device_type) "
                "VALUES (2, '79990000001', 'mobile')"
            )
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    # --- АВТОРИЗАЦИЯ ---
    def authenticate(self, login: str, password: str) -> Optional[Dict]:
        """Аутентификация пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT id, full_name, login, tariff_id, balance, role FROM clients "
            "WHERE login = ? AND password_hash = ?",
            (login, password_hash)
        )
        
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    # --- КЛИЕНТЫ ---
    def get_clients(self, search: str = "", limit: int = 100) -> List[Dict]:
        """Получить список клиентов с поиском по имени или логину (без админов)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT c.id, c.full_name, c.login, c.balance, c.role, t.name as tariff_name,
                   COUNT(d.id) as devices_count
            FROM clients c
            LEFT JOIN tariffs t ON c.tariff_id = t.id
            LEFT JOIN devices d ON c.id = d.client_id AND d.is_active = 1
            WHERE (c.full_name LIKE ? OR c.login LIKE ?) AND c.role != 'admin'
            GROUP BY c.id
            ORDER BY c.full_name
            LIMIT ?
        """
        search_pattern = f"%{search}%"
        cursor.execute(query, (search_pattern, search_pattern, limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_all_clients(self, search: str = "", limit: int = 100) -> List[Dict]:
        """Получить всех клиентов включая админов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT c.id, c.full_name, c.login, c.balance, c.role, t.name as tariff_name,
                   COUNT(d.id) as devices_count
            FROM clients c
            LEFT JOIN tariffs t ON c.tariff_id = t.id
            LEFT JOIN devices d ON c.id = d.client_id AND d.is_active = 1
            WHERE c.full_name LIKE ? OR c.login LIKE ?
            GROUP BY c.id
            ORDER BY c.full_name
            LIMIT ?
        """
        search_pattern = f"%{search}%"
        cursor.execute(query, (search_pattern, search_pattern, limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_client(self, client_id: int) -> Optional[Dict]:
        """Получить информацию о клиенте"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id, c.full_name, c.login, c.balance, c.tariff_id, c.role,
                   t.name as tariff_name, t.minute_price
            FROM clients c
            LEFT JOIN tariffs t ON c.tariff_id = t.id
            WHERE c.id = ?
        """, (client_id,))
        
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    def create_client(self, full_name: str, login: str, password: str, tariff_id: int = 1) -> bool:
        """Создать нового клиента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO clients (full_name, login, password_hash, tariff_id, balance, role) "
                "VALUES (?, ?, ?, ?, 0, 'user')",
                (full_name, login, password_hash, tariff_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def delete_client(self, client_id: int) -> bool:
        """Удалить клиента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, что это не админ
        cursor.execute("SELECT role FROM clients WHERE id = ?", (client_id,))
        result = cursor.fetchone()
        if result and result['role'] == 'admin':
            conn.close()
            return False
        
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    def update_client_tariff(self, client_id: int, tariff_id: int) -> bool:
        """Изменить тариф клиента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE clients SET tariff_id = ? WHERE id = ? AND role != 'admin'",
            (tariff_id, client_id)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    def update_client_balance(self, client_id: int, amount: float) -> bool:
        """Обновить баланс клиента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE clients SET balance = balance + ? WHERE id = ?",
            (amount, client_id)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    def set_client_balance(self, client_id: int, amount: float) -> bool:
        """Установить точный баланс клиента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE clients SET balance = ? WHERE id = ? AND role != 'admin'",
            (amount, client_id)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    # --- УСТРОЙСТВА ---
    def get_devices(self, client_id: Optional[int] = None, 
                    phone: str = "", limit: int = 100) -> List[Dict]:
        """Получить список устройств"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT d.id, d.phone_number, d.device_type, d.is_active,
                   c.full_name as client_name, c.id as client_id
            FROM devices d
            JOIN clients c ON d.client_id = c.id
            WHERE (d.phone_number LIKE ?)
        """
        params = [f"%{phone}%"]
        
        if client_id is not None:
            query += " AND d.client_id = ?"
            params.append(client_id)
        
        query += " ORDER BY d.phone_number LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def add_device(self, client_id: int, phone_number: str, device_type: str) -> bool:
        """Добавить новое устройство"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO devices (client_id, phone_number, device_type) "
                "VALUES (?, ?, ?)",
                (client_id, phone_number, device_type)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def delete_device(self, device_id: int) -> bool:
        """Удалить устройство (мягкое удаление)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE devices SET is_active = 0 WHERE id = ?",
            (device_id,)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    def update_device(self, device_id: int, device_type: str) -> bool:
        """Обновить устройство"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE devices SET device_type = ? WHERE id = ?",
            (device_type, device_id)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    # --- ЗВОНКИ ---
    def add_call(self, caller_number: str, receiver_number: str, 
                 duration_seconds: int) -> Dict:
        """Добавить звонок и списать деньги"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Найти устройства
            cursor.execute(
                "SELECT d.id, d.client_id, c.tariff_id, t.minute_price "
                "FROM devices d "
                "LEFT JOIN clients c ON d.client_id = c.id "
                "LEFT JOIN tariffs t ON c.tariff_id = t.id "
                "WHERE d.phone_number = ? AND d.is_active = 1",
                (caller_number,)
            )
            caller = cursor.fetchone()
            
            cursor.execute(
                "SELECT id FROM devices WHERE phone_number = ? AND is_active = 1",
                (receiver_number,)
            )
            receiver = cursor.fetchone()
            
            if not caller or not receiver:
                return {"success": False, "error": "Устройство не найдено или неактивно"}
            
            # Расчет стоимости
            minute_price = caller['minute_price'] or 1.0
            cost = (duration_seconds / 60) * minute_price
            
            # Проверка баланса
            cursor.execute("SELECT balance FROM clients WHERE id = ?", (caller['client_id'],))
            client_balance = cursor.fetchone()['balance']
            
            if client_balance < cost:
                return {"success": False, "error": "Недостаточно средств на балансе"}
            
            # Добавление звонка
            cursor.execute("""
                INSERT INTO calls (caller_device_id, receiver_device_id, 
                                  duration_seconds, cost, status, end_time)
                VALUES (?, ?, ?, ?, 'ended', CURRENT_TIMESTAMP)
            """, (caller['id'], receiver['id'], duration_seconds, cost))
            
            # Списание денег
            cursor.execute(
                "UPDATE clients SET balance = balance - ? WHERE id = ?",
                (cost, caller['client_id'])
            )
            
            conn.commit()
            
            return {
                "success": True,
                "cost": cost,
                "duration": duration_seconds,
                "caller": caller_number,
                "receiver": receiver_number
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def get_calls(self, client_id: Optional[int] = None,
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None,
                  limit: int = 100) -> List[Dict]:
        """Получить список звонков с фильтрацией"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT c.id, c.start_time, c.end_time, c.duration_seconds, c.cost, c.status,
                   d1.phone_number as caller_number, 
                   d2.phone_number as receiver_number,
                   cl.full_name as caller_name
            FROM calls c
            JOIN devices d1 ON c.caller_device_id = d1.id
            JOIN devices d2 ON c.receiver_device_id = d2.id
            JOIN clients cl ON d1.client_id = cl.id
            WHERE 1=1
        """
        params = []
        
        if client_id is not None:
            query += " AND d1.client_id = ?"
            params.append(client_id)
        
        if start_date:
            query += " AND c.start_time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND c.start_time <= ?"
            params.append(end_date)
        
        query += " ORDER BY c.start_time DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_client_balance(self, client_id: int) -> Optional[float]:
        """Получить баланс клиента"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT balance FROM clients WHERE id = ?", (client_id,))
        result = cursor.fetchone()
        conn.close()
        return result['balance'] if result else None
    
    # --- ТАРИФЫ (административные функции) ---
    def get_tariffs(self) -> List[Dict]:
        """Получить все тарифы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tariffs ORDER BY minute_price")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def add_tariff(self, name: str, description: str, minute_price: float) -> bool:
        """Добавить новый тариф"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO tariffs (name, description, minute_price) VALUES (?, ?, ?)",
                (name, description, minute_price)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_tariff(self, tariff_id: int, name: str, description: str, minute_price: float) -> bool:
        """Обновить тариф"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE tariffs SET name = ?, description = ?, minute_price = ? WHERE id = ?",
            (name, description, minute_price, tariff_id)
        )
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    def delete_tariff(self, tariff_id: int) -> bool:
        """Удалить тариф"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, что тариф не используется клиентами
        cursor.execute("SELECT COUNT(*) as count FROM clients WHERE tariff_id = ?", (tariff_id,))
        count = cursor.fetchone()['count']
        if count > 0:
            conn.close()
            return False
        
        cursor.execute("DELETE FROM tariffs WHERE id = ?", (tariff_id,))
        conn.commit()
        affected = cursor.rowcount > 0
        conn.close()
        return affected
    
    # --- СТАТИСТИКА ---
    def get_statistics(self) -> Dict:
        """Получить статистику системы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Количество клиентов
        cursor.execute("SELECT COUNT(*) as count FROM clients WHERE role != 'admin'")
        stats['total_clients'] = cursor.fetchone()['count']
        
        # Количество устройств
        cursor.execute("SELECT COUNT(*) as count FROM devices WHERE is_active = 1")
        stats['total_devices'] = cursor.fetchone()['count']
        
        # Количество звонков
        cursor.execute("SELECT COUNT(*) as count FROM calls")
        stats['total_calls'] = cursor.fetchone()['count']
        
        # Общая выручка
        cursor.execute("SELECT SUM(cost) as total FROM calls")
        stats['total_revenue'] = cursor.fetchone()['total'] or 0
        
        # Средний баланс клиентов
        cursor.execute("SELECT AVG(balance) as avg FROM clients WHERE role != 'admin'")
        stats['avg_balance'] = cursor.fetchone()['avg'] or 0
        
        conn.close()
        return stats