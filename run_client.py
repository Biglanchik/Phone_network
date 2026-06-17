# run_client.py
import sys
import os

# Добавляем текущую папку в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from client.gui import PhoneNetworkClient

if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneNetworkClient(root)
    root.mainloop()