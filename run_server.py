# run_server.py
import sys
import os

# Добавляем текущую папку в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.api import app

if __name__ == "__main__":
    print("=" * 50)
    print("Запуск сервера телефонной сети...")
    print("Сервер доступен по адресу: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)