# client/gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from datetime import datetime

class PhoneNetworkClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Телефонная сеть - Клиент")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)
        
        self.api_url = "http://localhost:5000/api"
        self.current_user = None
        self.is_admin = False
        
        self.show_login()
    
    def show_login(self):
        """Окно авторизации"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(expand=True)
        
        ttk.Label(frame, text="Телефонная сеть", font=("Arial", 24)).pack(pady=20)
        
        ttk.Label(frame, text="Логин:").pack(pady=5)
        self.login_entry = ttk.Entry(frame, width=30)
        self.login_entry.pack(pady=5)
        
        ttk.Label(frame, text="Пароль:").pack(pady=5)
        self.password_entry = ttk.Entry(frame, width=30, show="*")
        self.password_entry.pack(pady=5)
        
        ttk.Button(frame, text="Войти", command=self.login).pack(pady=20)
        
        ttk.Label(frame, text="Тестовые данные:", font=("Arial", 9), foreground="gray").pack()
        ttk.Label(frame, text="ivan / password123 (пользователь)", font=("Arial", 9), foreground="gray").pack()
        ttk.Label(frame, text="admin / admin123 (администратор)", font=("Arial", 9), foreground="gray").pack()
        
        self.root.bind('<Return>', lambda e: self.login())
    
    def login(self):
        """Авторизация"""
        login = self.login_entry.get()
        password = self.password_entry.get()
        
        if not login or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        
        try:
            response = requests.post(
                f"{self.api_url}/auth",
                json={"login": login, "password": password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.current_user = data['user']
                    self.is_admin = self.current_user.get('role') == 'admin'
                    self.show_main()
                else:
                    messagebox.showerror("Ошибка", data.get('error', 'Ошибка авторизации'))
            else:
                messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка", "Не удается подключиться к серверу\nУбедитесь, что сервер запущен")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def show_main(self):
        """Главное окно"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Верхняя панель
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text=f"Пользователь: {self.current_user['full_name']}",
                  font=("Arial", 12)).pack(side=tk.LEFT)
        
        ttk.Label(top_frame, text=f"Баланс: {self.current_user['balance']:.2f} руб.",
                  font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=20)
        
        ttk.Button(top_frame, text="Обновить баланс", 
                   command=self.refresh_balance).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="Пополнить баланс", 
                   command=self.replenish_balance).pack(side=tk.LEFT, padx=5)
        
        if self.is_admin:
            ttk.Label(top_frame, text="[АДМИН]",
                      font=("Arial", 10, "bold"), foreground="red").pack(side=tk.LEFT, padx=10)
        
        ttk.Button(top_frame, text="Выход", command=self.logout).pack(side=tk.RIGHT)
        
        # Вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка "Устройства"
        self.devices_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.devices_tab, text="Устройства")
        self.create_devices_tab()
        
        # Вкладка "Звонки"
        self.calls_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.calls_tab, text="Звонки")
        self.create_calls_tab()
        
        # Вкладка "Новый звонок"
        self.new_call_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.new_call_tab, text="Новый звонок")
        self.create_new_call_tab()
        
        # Вкладка "Клиенты"
        self.clients_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.clients_tab, text="Клиенты")
        self.create_clients_tab()
        
        # Если админ - добавляем админ-вкладки
        if self.is_admin:
            self.admin_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.admin_tab, text="Админ панель")
            self.create_admin_tab()
        
        # Загрузка данных
        self.load_devices()
        self.load_calls()
        self.load_clients()
        if self.is_admin:
            self.load_tariffs_admin()
            self.load_statistics()
    
    def create_devices_tab(self):
        """Вкладка управления устройствами"""
        frame = self.devices_tab
        
        tools = ttk.Frame(frame)
        tools.pack(fill=tk.X, pady=5)
        
        ttk.Label(tools, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.device_search = ttk.Entry(tools, width=20)
        self.device_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(tools, text="Найти", command=self.load_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools, text="Обновить", command=self.load_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools, text="Добавить устройство", 
                   command=self.add_device_dialog).pack(side=tk.LEFT, padx=5)
        
        self.devices_tree = ttk.Treeview(frame, columns=("id", "number", "type", "status", "client"), 
                                         show="headings", height=15)
        self.devices_tree.heading("id", text="ID")
        self.devices_tree.heading("number", text="Номер")
        self.devices_tree.heading("type", text="Тип")
        self.devices_tree.heading("status", text="Статус")
        self.devices_tree.heading("client", text="Владелец")
        self.devices_tree.column("id", width=50)
        self.devices_tree.column("number", width=150)
        self.devices_tree.column("type", width=100)
        self.devices_tree.column("status", width=100)
        self.devices_tree.column("client", width=200)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.devices_tree.yview)
        self.devices_tree.configure(yscrollcommand=scrollbar.set)
        
        self.devices_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_calls_tab(self):
        """Вкладка истории звонков"""
        frame = self.calls_tab
        
        tools = ttk.Frame(frame)
        tools.pack(fill=tk.X, pady=5)
        
        ttk.Button(tools, text="Обновить", command=self.load_calls).pack(side=tk.LEFT, padx=5)
        ttk.Label(tools, text="Показать:").pack(side=tk.LEFT, padx=5)
        self.calls_limit = ttk.Spinbox(tools, from_=10, to=200, width=10, value=50)
        self.calls_limit.pack(side=tk.LEFT, padx=5)
        ttk.Button(tools, text="Применить", command=self.load_calls).pack(side=tk.LEFT, padx=5)
        
        self.calls_tree = ttk.Treeview(frame, columns=("id", "caller", "receiver", "duration", "cost", "time", "status"),
                                       show="headings", height=15)
        self.calls_tree.heading("id", text="ID")
        self.calls_tree.heading("caller", text="Звонивший")
        self.calls_tree.heading("receiver", text="Получатель")
        self.calls_tree.heading("duration", text="Длит. (сек)")
        self.calls_tree.heading("cost", text="Стоимость")
        self.calls_tree.heading("time", text="Время")
        self.calls_tree.heading("status", text="Статус")
        self.calls_tree.column("id", width=50)
        self.calls_tree.column("caller", width=150)
        self.calls_tree.column("receiver", width=150)
        self.calls_tree.column("duration", width=100)
        self.calls_tree.column("cost", width=100)
        self.calls_tree.column("time", width=200)
        self.calls_tree.column("status", width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.calls_tree.yview)
        self.calls_tree.configure(yscrollcommand=scrollbar.set)
        
        self.calls_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_new_call_tab(self):
        """Вкладка создания нового звонка"""
        frame = self.new_call_tab
        
        main_frame = ttk.Frame(frame, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        form = ttk.Frame(main_frame)
        form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        ttk.Label(form, text="Регистрация звонка", font=("Arial", 16)).pack(pady=10)
        
        ttk.Label(form, text="Номер звонящего:").pack(pady=5)
        self.call_caller = ttk.Entry(form, width=30)
        self.call_caller.pack(pady=5)
        ttk.Label(form, text="Например: 79991234567", font=("Arial", 8), foreground="gray").pack()
        
        ttk.Label(form, text="Номер получателя:").pack(pady=5)
        self.call_receiver = ttk.Entry(form, width=30)
        self.call_receiver.pack(pady=5)
        
        ttk.Label(form, text="Длительность (секунды):").pack(pady=5)
        self.call_duration = ttk.Entry(form, width=30)
        self.call_duration.insert(0, "60")
        self.call_duration.pack(pady=5)
        
        ttk.Button(form, text="Зарегистрировать звонок", 
                   command=self.make_call, width=30).pack(pady=20)
        
        ttk.Label(form, text="Стоимость будет списана с баланса автоматически",
                  font=("Arial", 9), foreground="gray").pack()
        
        info = ttk.Frame(main_frame)
        info.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20)
        
        ttk.Label(info, text="Информация", font=("Arial", 14)).pack(pady=10)
        
        self.tariff_info = scrolledtext.ScrolledText(info, width=40, height=20, wrap=tk.WORD)
        self.tariff_info.pack(fill=tk.BOTH, expand=True)
        
        self.load_tariff_info()
    
    def create_clients_tab(self):
        """Вкладка управления клиентами"""
        frame = self.clients_tab
        
        tools = ttk.Frame(frame)
        tools.pack(fill=tk.X, pady=5)
        
        ttk.Label(tools, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.client_search = ttk.Entry(tools, width=20)
        self.client_search.pack(side=tk.LEFT, padx=5)
        ttk.Button(tools, text="Найти", command=self.load_clients).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools, text="Обновить", command=self.load_clients).pack(side=tk.LEFT, padx=5)
        
        if self.is_admin:
            ttk.Button(tools, text="Создать клиента", 
                       command=self.create_client_dialog).pack(side=tk.LEFT, padx=5)
        
        self.clients_tree = ttk.Treeview(frame, columns=("id", "name", "login", "tariff", "balance", "devices", "role"),
                                         show="headings", height=15)
        self.clients_tree.heading("id", text="ID")
        self.clients_tree.heading("name", text="ФИО")
        self.clients_tree.heading("login", text="Логин")
        self.clients_tree.heading("tariff", text="Тариф")
        self.clients_tree.heading("balance", text="Баланс")
        self.clients_tree.heading("devices", text="Устройств")
        self.clients_tree.heading("role", text="Роль")
        self.clients_tree.column("id", width=50)
        self.clients_tree.column("name", width=200)
        self.clients_tree.column("login", width=150)
        self.clients_tree.column("tariff", width=150)
        self.clients_tree.column("balance", width=100)
        self.clients_tree.column("devices", width=80)
        self.clients_tree.column("role", width=80)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=scrollbar.set)
        
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Правая кнопка для админа
        if self.is_admin:
            self.clients_tree.bind('<Double-Button-1>', self.show_client_actions)
    
    def create_admin_tab(self):
        """Админ панель"""
        frame = self.admin_tab
        
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая часть - управление тарифами
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="Управление тарифами", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Форма добавления тарифа
        form_frame = ttk.LabelFrame(left_frame, text="Добавить тариф", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(form_frame, text="Название:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.tariff_name_entry = ttk.Entry(form_frame, width=20)
        self.tariff_name_entry.grid(row=0, column=1, pady=2, padx=5)
        
        ttk.Label(form_frame, text="Описание:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.tariff_desc_entry = ttk.Entry(form_frame, width=20)
        self.tariff_desc_entry.grid(row=1, column=1, pady=2, padx=5)
        
        ttk.Label(form_frame, text="Цена за минуту:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.tariff_price_entry = ttk.Entry(form_frame, width=20)
        self.tariff_price_entry.grid(row=2, column=1, pady=2, padx=5)
        
        ttk.Button(form_frame, text="Добавить тариф", command=self.add_tariff).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Список тарифов
        list_frame = ttk.LabelFrame(left_frame, text="Существующие тарифы", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tariffs_tree = ttk.Treeview(list_frame, columns=("id", "name", "desc", "price"),
                                         show="headings", height=8)
        self.tariffs_tree.heading("id", text="ID")
        self.tariffs_tree.heading("name", text="Название")
        self.tariffs_tree.heading("desc", text="Описание")
        self.tariffs_tree.heading("price", text="Цена/мин")
        self.tariffs_tree.column("id", width=50)
        self.tariffs_tree.column("name", width=120)
        self.tariffs_tree.column("desc", width=150)
        self.tariffs_tree.column("price", width=80)
        self.tariffs_tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Удалить тариф", command=self.delete_tariff).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_tariffs_admin).pack(side=tk.LEFT, padx=5)
        
        # Правая часть - статистика
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="Статистика системы", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.stats_text = scrolledtext.ScrolledText(right_frame, width=40, height=25, wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(right_frame, text="Обновить статистику", command=self.load_statistics).pack(pady=5)
    
    def load_devices(self):
        """Загрузка устройств"""
        search = self.device_search.get()
        
        try:
            response = requests.get(
                f"{self.api_url}/devices",
                params={"phone": search, "limit": 200},
                timeout=5
            )
            
            if response.status_code == 200:
                devices = response.json()
                self.devices_tree.delete(*self.devices_tree.get_children())
                
                for device in devices:
                    status = "Активно" if device['is_active'] else "Неактивно"
                    self.devices_tree.insert("", tk.END, values=(
                        device['id'],
                        device['phone_number'],
                        device['device_type'],
                        status,
                        device['client_name']
                    ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить устройства: {e}")
    
    def load_calls(self):
        """Загрузка истории звонков"""
        limit = self.calls_limit.get() or 50
        
        try:
            response = requests.get(
                f"{self.api_url}/calls",
                params={"limit": limit},
                timeout=5
            )
            
            if response.status_code == 200:
                calls = response.json()
                self.calls_tree.delete(*self.calls_tree.get_children())
                
                for call in calls:
                    status_ru = {
                        'started': 'Начат',
                        'ended': 'Завершен',
                        'failed': 'Ошибка'
                    }.get(call['status'], call['status'])
                    
                    duration = call['duration_seconds'] or 0
                    time_str = call['start_time'][:19].replace('T', ' ') if call['start_time'] else ''
                    
                    self.calls_tree.insert("", tk.END, values=(
                        call['id'],
                        call['caller_number'],
                        call['receiver_number'],
                        duration,
                        f"{call['cost']:.2f}",
                        time_str,
                        status_ru
                    ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить звонки: {e}")
    
    def load_clients(self):
        """Загрузка клиентов"""
        search = self.client_search.get()
        
        try:
            url = f"{self.api_url}/clients/all" if self.is_admin else f"{self.api_url}/clients"
            response = requests.get(
                url,
                params={"search": search, "limit": 100},
                timeout=5
            )
            
            if response.status_code == 200:
                clients = response.json()
                self.clients_tree.delete(*self.clients_tree.get_children())
                
                for client in clients:
                    # Не показываем админов в обычном режиме
                    if not self.is_admin and client.get('role') == 'admin':
                        continue
                    
                    role_display = "Админ" if client.get('role') == 'admin' else "Пользователь"
                    self.clients_tree.insert("", tk.END, values=(
                        client['id'],
                        client['full_name'],
                        client['login'],
                        client['tariff_name'] or 'Не указан',
                        f"{client['balance']:.2f}",
                        client['devices_count'] or 0,
                        role_display
                    ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить клиентов: {e}")
    
    def load_tariff_info(self):
        """Загрузка информации о тарифе"""
        try:
            response = requests.get(f"{self.api_url}/clients/{self.current_user['id']}", timeout=5)
            if response.status_code == 200:
                client = response.json()
                info = f"Ваш тариф: {client.get('tariff_name', 'Не указан')}\n"
                info += f"Цена за минуту: {client.get('minute_price', 1.0):.2f} руб.\n"
                info += f"\nТелефонная сеть регистрирует звонки\n"
                info += f"и автоматически списывает средства\n"
                info += f"с баланса в соответствии с тарифом.\n"
                info += f"\nТекущий баланс: {client.get('balance', 0):.2f} руб."
                self.tariff_info.delete(1.0, tk.END)
                self.tariff_info.insert(1.0, info)
        except Exception:
            self.tariff_info.delete(1.0, tk.END)
            self.tariff_info.insert(1.0, "Не удалось загрузить информацию о тарифе")
    
    def refresh_balance(self):
        """Обновить баланс"""
        try:
            response = requests.get(
                f"{self.api_url}/clients/{self.current_user['id']}",
                timeout=5
            )
            if response.status_code == 200:
                client = response.json()
                self.current_user['balance'] = client['balance']
                messagebox.showinfo("Успех", f"Баланс: {client['balance']:.2f} руб.")
                self.show_main()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить баланс: {e}")
    
    def replenish_balance(self):
        """Пополнить баланс"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Пополнение баланса")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Сумма пополнения (руб.):").pack(pady=20)
        amount_entry = ttk.Entry(dialog, width=20)
        amount_entry.pack(pady=10)
        amount_entry.insert(0, "100")
        
        def do_replenish():
            try:
                amount = float(amount_entry.get())
                if amount <= 0:
                    messagebox.showerror("Ошибка", "Сумма должна быть положительной")
                    return
                
                response = requests.post(
                    f"{self.api_url}/clients/{self.current_user['id']}/balance",
                    json={"amount": amount},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.current_user['balance'] = data['balance']
                        messagebox.showinfo("Успех", f"Баланс пополнен. Новый баланс: {data['balance']:.2f} руб.")
                        dialog.destroy()
                        self.show_main()
                    else:
                        messagebox.showerror("Ошибка", data.get('error', 'Ошибка пополнения'))
                else:
                    messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное число")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(dialog, text="Пополнить", command=do_replenish).pack(pady=10)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack()
    
    def add_device_dialog(self):
        """Диалог добавления устройства"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление устройства")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Номер телефона:").pack(pady=10)
        phone_entry = ttk.Entry(dialog, width=30)
        phone_entry.pack(pady=5)
        ttk.Label(dialog, text="Формат: 79991234567", font=("Arial", 8), foreground="gray").pack()
        
        ttk.Label(dialog, text="Тип устройства:").pack(pady=10)
        type_var = tk.StringVar(value="mobile")
        ttk.Radiobutton(dialog, text="Мобильный", variable=type_var, value="mobile").pack()
        ttk.Radiobutton(dialog, text="Домашний", variable=type_var, value="home").pack()
        
        def do_add():
            phone = phone_entry.get().strip()
            if not phone:
                messagebox.showerror("Ошибка", "Введите номер телефона")
                return
            
            try:
                response = requests.post(
                    f"{self.api_url}/devices",
                    json={
                        "client_id": self.current_user['id'],
                        "phone_number": phone,
                        "device_type": type_var.get()
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        messagebox.showinfo("Успех", "Устройство добавлено")
                        dialog.destroy()
                        self.load_devices()
                    else:
                        messagebox.showerror("Ошибка", data.get('error', 'Ошибка'))
                else:
                    messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(dialog, text="Добавить", command=do_add).pack(pady=10)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack()
    
    def make_call(self):
        """Совершить звонок"""
        caller = self.call_caller.get().strip()
        receiver = self.call_receiver.get().strip()
        duration_str = self.call_duration.get().strip()
        
        if not caller or not receiver:
            messagebox.showerror("Ошибка", "Введите номера звонящего и получателя")
            return
        
        try:
            duration = int(duration_str)
            if duration <= 0:
                messagebox.showerror("Ошибка", "Длительность должна быть больше 0")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную длительность")
            return
        
        try:
            response = requests.post(
                f"{self.api_url}/calls",
                json={
                    "caller_number": caller,
                    "receiver_number": receiver,
                    "duration_seconds": duration
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    messagebox.showinfo("Успех", 
                        f"Звонок зарегистрирован!\n"
                        f"Длительность: {data['duration']} сек.\n"
                        f"Стоимость: {data['cost']:.2f} руб.")
                    self.load_calls()
                    self.load_tariff_info()
                    self.refresh_balance()
                else:
                    messagebox.showerror("Ошибка", data.get('error', 'Ошибка звонка'))
            else:
                error_data = response.json()
                messagebox.showerror("Ошибка", error_data.get('error', f'Ошибка сервера: {response.status_code}'))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    # --- АДМИНИСТРАТИВНЫЕ ФУНКЦИИ ---
    
    def create_client_dialog(self):
        """Диалог создания клиента"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание клиента")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Создание нового клиента", font=("Arial", 14)).pack(pady=10)
        
        form = ttk.Frame(dialog, padding=10)
        form.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form, text="ФИО:").pack(anchor=tk.W, pady=2)
        name_entry = ttk.Entry(form, width=30)
        name_entry.pack(pady=5, fill=tk.X)
        
        ttk.Label(form, text="Логин:").pack(anchor=tk.W, pady=2)
        login_entry = ttk.Entry(form, width=30)
        login_entry.pack(pady=5, fill=tk.X)
        
        ttk.Label(form, text="Пароль:").pack(anchor=tk.W, pady=2)
        pass_entry = ttk.Entry(form, width=30, show="*")
        pass_entry.pack(pady=5, fill=tk.X)
        
        ttk.Label(form, text="Тариф:").pack(anchor=tk.W, pady=2)
        tariff_var = tk.StringVar(value="1")
        tariff_frame = ttk.Frame(form)
        tariff_frame.pack(fill=tk.X, pady=5)
        
        tariffs = self.get_tariffs_list()
        for t in tariffs:
            ttk.Radiobutton(tariff_frame, text=f"{t['name']} ({t['minute_price']} руб/мин)", 
                           variable=tariff_var, value=str(t['id'])).pack(anchor=tk.W)
        
        def do_create():
            name = name_entry.get().strip()
            login = login_entry.get().strip()
            password = pass_entry.get().strip()
            tariff_id = int(tariff_var.get())
            
            if not name or not login or not password:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            
            try:
                response = requests.post(
                    f"{self.api_url}/clients",
                    json={
                        "full_name": name,
                        "login": login,
                        "password": password,
                        "tariff_id": tariff_id
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        messagebox.showinfo("Успех", "Клиент создан")
                        dialog.destroy()
                        self.load_clients()
                    else:
                        messagebox.showerror("Ошибка", data.get('error', 'Ошибка'))
                else:
                    messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(form, text="Создать клиента", command=do_create).pack(pady=20)
        ttk.Button(form, text="Отмена", command=dialog.destroy).pack()
    
    def show_client_actions(self, event):
        """Показать действия для клиента (админ)"""
        selected = self.clients_tree.selection()
        if not selected:
            return
        
        item = self.clients_tree.item(selected[0])
        client_id = item['values'][0]
        client_name = item['values'][1]
        current_tariff = item['values'][3]
        current_balance = float(item['values'][4].replace(',', '.'))
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Действия с клиентом: {client_name}")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Клиент: {client_name}", font=("Arial", 14)).pack(pady=10)
        
        # Изменение тарифа
        tariff_frame = ttk.LabelFrame(dialog, text="Изменить тариф", padding=10)
        tariff_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(tariff_frame, text=f"Текущий тариф: {current_tariff}").pack(anchor=tk.W)
        
        ttk.Label(tariff_frame, text="Новый тариф:").pack(anchor=tk.W, pady=5)
        tariff_var = tk.StringVar()
        tariff_combo = ttk.Combobox(tariff_frame, textvariable=tariff_var, state="readonly", width=30)
        
        tariffs = self.get_tariffs_list()
        tariff_combo['values'] = [f"{t['id']}: {t['name']} ({t['minute_price']} руб/мин)" for t in tariffs]
        tariff_combo.pack(pady=5)
        
        def do_change_tariff():
            if not tariff_var.get():
                messagebox.showerror("Ошибка", "Выберите тариф")
                return
            
            tariff_id = int(tariff_var.get().split(':')[0])
            
            try:
                response = requests.put(
                    f"{self.api_url}/clients/{client_id}/tariff",
                    json={"tariff_id": tariff_id},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        messagebox.showinfo("Успех", "Тариф изменен")
                        self.load_clients()
                    else:
                        messagebox.showerror("Ошибка", data.get('error', 'Ошибка'))
                else:
                    messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(tariff_frame, text="Изменить тариф", command=do_change_tariff).pack(pady=5)
        
        # Изменение баланса
        balance_frame = ttk.LabelFrame(dialog, text="Изменить баланс", padding=10)
        balance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(balance_frame, text=f"Текущий баланс: {current_balance:.2f} руб.").pack(anchor=tk.W)
        
        ttk.Label(balance_frame, text="Новый баланс:").pack(anchor=tk.W, pady=5)
        balance_entry = ttk.Entry(balance_frame, width=20)
        balance_entry.pack(pady=5)
        balance_entry.insert(0, str(current_balance))
        
        def do_set_balance():
            try:
                amount = float(balance_entry.get())
                if amount < 0:
                    messagebox.showerror("Ошибка", "Баланс не может быть отрицательным")
                    return
                
                response = requests.put(
                    f"{self.api_url}/clients/{client_id}/balance/set",
                    json={"amount": amount},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        messagebox.showinfo("Успех", "Баланс обновлен")
                        self.load_clients()
                    else:
                        messagebox.showerror("Ошибка", data.get('error', 'Ошибка'))
                else:
                    messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное число")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(balance_frame, text="Установить баланс", command=do_set_balance).pack(pady=5)
        
        # Удаление клиента
        delete_frame = ttk.LabelFrame(dialog, text="Опасные действия", padding=10)
        delete_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def do_delete():
            if messagebox.askyesno("Подтверждение", f"Удалить клиента {client_name}?"):
                try:
                    response = requests.delete(
                        f"{self.api_url}/clients/{client_id}",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            messagebox.showinfo("Успех", "Клиент удален")
                            dialog.destroy()
                            self.load_clients()
                        else:
                            messagebox.showerror("Ошибка", data.get('error', 'Ошибка'))
                    else:
                        messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))
        
        ttk.Button(delete_frame, text="Удалить клиента", command=do_delete).pack(pady=5)
        
        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)
    
    def get_tariffs_list(self):
        """Получить список тарифов"""
        try:
            response = requests.get(f"{self.api_url}/tariffs", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def load_tariffs_admin(self):
        """Загрузка тарифов для админа"""
        if not self.is_admin:
            return
        
        try:
            response = requests.get(f"{self.api_url}/tariffs", timeout=5)
            if response.status_code == 200:
                tariffs = response.json()
                self.tariffs_tree.delete(*self.tariffs_tree.get_children())
                
                for t in tariffs:
                    self.tariffs_tree.insert("", tk.END, values=(
                        t['id'],
                        t['name'],
                        t['description'] or '',
                        f"{t['minute_price']:.2f}"
                    ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить тарифы: {e}")
    
    def add_tariff(self):
        """Добавить новый тариф (админ)"""
        name = self.tariff_name_entry.get().strip()
        description = self.tariff_desc_entry.get().strip()
        price_str = self.tariff_price_entry.get().strip()
        
        if not name or not price_str:
            messagebox.showerror("Ошибка", "Заполните название и цену")
            return
        
        try:
            price = float(price_str)
            if price <= 0:
                messagebox.showerror("Ошибка", "Цена должна быть больше 0")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную цену")
            return
        
        try:
            response = requests.post(
                f"{self.api_url}/tariffs",
                json={
                    "name": name,
                    "description": description,
                    "minute_price": price
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    messagebox.showinfo("Успех", "Тариф создан")
                    self.tariff_name_entry.delete(0, tk.END)
                    self.tariff_desc_entry.delete(0, tk.END)
                    self.tariff_price_entry.delete(0, tk.END)
                    self.load_tariffs_admin()
                else:
                    messagebox.showerror("Ошибка", data.get('error', 'Ошибка'))
            else:
                messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def delete_tariff(self):
        """Удалить тариф (админ)"""
        selected = self.tariffs_tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите тариф")
            return
        
        item = self.tariffs_tree.item(selected[0])
        tariff_id = item['values'][0]
        tariff_name = item['values'][1]
        
        if not messagebox.askyesno("Подтверждение", f"Удалить тариф {tariff_name}?"):
            return
        
        try:
            response = requests.delete(
                f"{self.api_url}/tariffs/{tariff_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    messagebox.showinfo("Успех", "Тариф удален")
                    self.load_tariffs_admin()
                else:
                    messagebox.showerror("Ошибка", data.get('error', 'Ошибка'))
            else:
                messagebox.showerror("Ошибка", f"Ошибка сервера: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def load_statistics(self):
        """Загрузка статистики (админ)"""
        if not self.is_admin:
            return
        
        try:
            response = requests.get(f"{self.api_url}/statistics", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                
                text = "СТАТИСТИКА СИСТЕМЫ\n"
                text += "=" * 40 + "\n\n"
                text += f"Всего клиентов: {stats.get('total_clients', 0)}\n"
                text += f"Всего устройств: {stats.get('total_devices', 0)}\n"
                text += f"Всего звонков: {stats.get('total_calls', 0)}\n"
                text += f"Общая выручка: {stats.get('total_revenue', 0):.2f} руб.\n"
                text += f"Средний баланс клиентов: {stats.get('avg_balance', 0):.2f} руб.\n"
                
                self.stats_text.delete(1.0, tk.END)
                self.stats_text.insert(1.0, text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить статистику: {e}")
    
    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.current_user = None
            self.is_admin = False
            self.show_login()


if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneNetworkClient(root)
    root.mainloop()