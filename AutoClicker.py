import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import pyautogui
import keyboard
from pynput import mouse

# Константы программы
APP_NAME = "Auto Clicker"
APP_VERSION = "1.0.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# Проверка запущенного экземпляра
def check_single_instance(app_name=APP_NAME):
    """Проверяет, запущен ли уже экземпляр программы"""
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            
            # Создаем уникальное имя для мьютекса
            mutex_name = f"Global\\{app_name}_Mutex_{os.getpid()}"
            
            # Пытаемся найти окно программы по заголовку
            hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
            if hwnd:
                # Если окно найдено, активируем его
                if ctypes.windll.user32.IsIconic(hwnd):
                    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                else:
                    ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
                
                # Активируем окно
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                
                return False  # Программа уже запущена
            
            # Простая проверка по процессам (альтернативный метод)
            try:
                import psutil
                current_pid = os.getpid()
                current_name = os.path.basename(sys.argv[0])
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['pid'] != current_pid:
                            proc_name = proc.info['name'].lower()
                            if 'python' in proc_name or 'autoclicker' in proc_name.lower() or current_name.lower() in proc_name:
                                # Проверяем аргументы процесса
                                cmdline = ' '.join(proc.cmdline()).lower()
                                if 'clicker' in cmdline or current_name.lower() in cmdline:
                                    return False
                    except:
                        pass
            except ImportError:
                # Если psutil не установлен, пропускаем эту проверку
                pass
                
        else:  # Linux/Mac
            # Простая проверка по lock файлу
            lock_file = os.path.join(os.path.expanduser("~"), f".{app_name}.lock")
            
            if os.path.exists(lock_file):
                try:
                    with open(lock_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Проверяем, жив ли процесс
                    os.kill(pid, 0)  # Сигнал 0 только проверяет существование
                    return False  # Процесс уже запущен
                except (OSError, ValueError):
                    # Процесс не существует или файл поврежден
                    os.remove(lock_file)
            
            # Создаем новый lock файл
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
    except Exception as e:
        # В случае ошибки разрешаем запуск
        print(f"Ошибка проверки экземпляра: {e}")
    
    return True  # Разрешаем запуск

def cleanup_single_instance(app_name=APP_NAME):
    """Очистка ресурсов при завершении программы"""
    try:
        if os.name != 'nt':
            # Удаляем lock файл для Linux/Mac
            lock_file = os.path.join(os.path.expanduser("~"), f".{app_name}.lock")
            if os.path.exists(lock_file):
                os.remove(lock_file)
    except:
        pass

class AutoClicker:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("302x448")
        self.root.resizable(False, False)
        
        # Устанавливаем белый фон для всего окна
        self.root.configure(bg='white')
        
        self.is_running = False
        self.click_thread = None
        self.getting_coords = False
        self.mouse_listener = None
        self.always_on_top = False
        self.hotkeys_registered = False
        self.stop_event = threading.Event()  # Событие для корректной остановки потока
        self.timer_thread = None  # Поток для таймера
        self.timer_event = threading.Event()  # Событие для таймера
        
        # Создаем кастомный стиль
        self.setup_styles()
        
        # Основной фрейм с белым фоном
        main_frame = ttk.Frame(root, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Устанавливаем белый фон для основного фрейма
        main_frame.configure(style='White.TFrame')
        
        # Конфигурация веса строк
        root.grid_rowconfigure(0, weight=1)
        
        # Интервал кликов
        interval_frame = ttk.LabelFrame(
            main_frame, 
            text="Интервал между кликами (мс)", 
            padding="8",
            style="White.TLabelframe"
        )
        interval_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Минимальный интервал
        ttk.Label(interval_frame, text="Мин.:", style="White.TLabel").grid(row=0, column=0, padx=(0, 5))
        self.min_interval_var = tk.StringVar(value="30000")
        self.min_interval_entry = ttk.Entry(
            interval_frame, 
            textvariable=self.min_interval_var, 
            width=10,
            font=('Segoe UI', 9)
        )
        self.min_interval_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Максимальный интервал
        ttk.Label(interval_frame, text="Макс.:", style="White.TLabel").grid(row=0, column=2, padx=(10, 5))
        self.max_interval_var = tk.StringVar(value="35000")
        self.max_interval_entry = ttk.Entry(
            interval_frame, 
            textvariable=self.max_interval_var, 
            width=10,
            font=('Segoe UI', 9)
        )
        self.max_interval_entry.grid(row=0, column=3, padx=(0, 5))
        
        # Блок "Режим клика" (с координатами внутри)
        mode_frame = ttk.LabelFrame(
            main_frame, 
            text="Режим клика", 
            padding="8",
            style="White.TLabelframe"
        )
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Переключатель режима (строка 1)
        self.click_mode_var = tk.BooleanVar(value=False)
        self.use_coords_check = ttk.Checkbutton(
            mode_frame, 
            text="Указанные координаты", 
            variable=self.click_mode_var,
            command=self.toggle_coords_mode,
            style="White.TCheckbutton",
            takefocus=0
        )
        self.use_coords_check.grid(row=0, column=0, sticky=tk.W, columnspan=4, pady=(0, 8))
        
        # Координаты (строка 2)
        coords_frame = ttk.Frame(mode_frame, style='White.TFrame')
        coords_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # X координата
        ttk.Label(coords_frame, text="X:", style="White.TLabel").grid(row=0, column=0, padx=(0, 5))
        self.x_var = tk.StringVar(value="")
        self.x_entry = ttk.Entry(
            coords_frame, 
            textvariable=self.x_var, 
            width=10,
            font=('Segoe UI', 9),
            state="disabled"
        )
        self.x_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Y координата
        ttk.Label(coords_frame, text="Y:", style="White.TLabel").grid(row=0, column=2, padx=(10, 5))
        self.y_var = tk.StringVar(value="")
        self.y_entry = ttk.Entry(
            coords_frame, 
            textvariable=self.y_var, 
            width=10,
            font=('Segoe UI', 9),
            state="disabled"
        )
        self.y_entry.grid(row=0, column=3, padx=(0, 5))
        
        # Кнопка для получения координат следующего клика (строка 3)
        self.get_coords_btn = ttk.Button(
            mode_frame, 
            text="Указать место клика", 
            command=self.start_getting_coords,
            width=20,
            style="Accent.TButton",
            state="disabled"
        )
        self.get_coords_btn.grid(row=2, column=0, columnspan=4)
        
        # Блок тайм-аута
        timeout_frame = ttk.LabelFrame(
            main_frame, 
            text="Тайм-аут", 
            padding="8",
            style="White.TLabelframe"
        )
        timeout_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Галочка включения тайм-аута
        self.timeout_enabled_var = tk.BooleanVar(value=False)
        self.timeout_check = ttk.Checkbutton(
            timeout_frame, 
            text="Время работы (мин):", 
            variable=self.timeout_enabled_var,
            command=self.toggle_timeout_mode,
            style="White.TCheckbutton",
            takefocus=0
        )
        self.timeout_check.grid(row=0, column=0, sticky=tk.W)
        
        # Поле для ввода времени
        self.timeout_var = tk.StringVar(value="60")
        self.timeout_entry = ttk.Entry(
            timeout_frame, 
            textvariable=self.timeout_var, 
            width=10,
            font=('Segoe UI', 9),
            state="disabled"  # По умолчанию неактивно
        )
        self.timeout_entry.grid(row=0, column=1, padx=(10, 0))
        
        # Настройки окна
        window_frame = ttk.LabelFrame(
            main_frame, 
            text="Настройки окна", 
            padding="8",
            style="White.TLabelframe"
        )
        window_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 12))
        
        # Галочка "Поверх всех окон"
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.always_on_top_check = ttk.Checkbutton(
            window_frame, 
            text="Поверх всех окон", 
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            style="White.TCheckbutton",
            takefocus=0
        )
        self.always_on_top_check.grid(row=0, column=0, sticky=tk.W)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame, style='White.TFrame')
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=(12, 15))
        
        # Кнопка Старт - зеленая
        self.start_btn = ttk.Button(
            buttons_frame, 
            text="СТАРТ (F6)", 
            command=self.start_clicking, 
            width=12,
            style="Start.TButton"
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Кнопка Стоп - серая и НЕАКТИВНАЯ при запуске
        self.stop_btn = ttk.Button(
            buttons_frame, 
            text="СТОП (F7)", 
            command=self.stop_clicking, 
            width=12,
            style="Stop.TButton",
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=1)
        
        # Инициализация режима координат
        self.toggle_coords_mode()
        
        # Включаем режим "Поверх всех окон" по умолчанию
        self.root.after(100, self.initialize_always_on_top)
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Привязываем горячие клавиши с небольшой задержкой
        self.root.after(200, self.setup_hotkeys)
    
    def setup_styles(self):
        """Настройка кастомных стилей для интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основные цвета
        bg_color = 'white'
        fg_color = '#333333'
        border_color = '#cccccc'
        green_color = '#28a745'
        green_hover = '#218838'
        green_active = '#1e7e34'
        gray_color = '#6c757d'
        gray_hover = '#5a6268'
        gray_active = '#545b62'
        disabled_color = '#e9ecef'
        disabled_gray_color = '#adb5bd'
        
        # Стиль для белого фона
        style.configure('White.TFrame', background=bg_color)
        
        # Общий стиль фрейма с белым фоном
        style.configure('White.TLabelframe', 
                       background=bg_color,
                       foreground=fg_color,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=border_color)
        
        style.configure('White.TLabelframe.Label', 
                       background=bg_color,
                       foreground=fg_color,
                       font=('Segoe UI', 10, 'bold'))
        
        # Стиль для меток
        style.configure('White.TLabel',
                       background=bg_color,
                       foreground=fg_color,
                       font=('Segoe UI', 10))
        
        # Стиль для чекбоксов
        style.configure('White.TCheckbutton',
                       background=bg_color,
                       foreground=fg_color,
                       font=('Segoe UI', 10))
        
        # Убираем все эффекты при наведении/нажатии
        style.map('White.TCheckbutton',
                 background=[], 
                 foreground=[('disabled', '#888888')])
        
        # Стиль для разделителя
        style.configure('White.TSeparator',
                       background=border_color)
        
        # Кнопка Старт (зеленая)
        style.configure('Start.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=6,
                       relief='flat',
                       background=green_color,
                       foreground='white',
                       borderwidth=0,
                       focusthickness=0,
                       focuscolor='none')
        
        style.map('Start.TButton',
                 background=[('active', green_hover), 
                            ('pressed', green_active),
                            ('disabled', disabled_color)],
                 relief=[('pressed', 'sunken'), ('active', 'raised')],
                 foreground=[('disabled', '#888888')])
        
        # Кнопка Стоп (серая)
        style.configure('Stop.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=6,
                       relief='flat',
                       background=gray_color,
                       foreground='white',
                       borderwidth=0,
                       focusthickness=0,
                       focuscolor='none')
        
        style.map('Stop.TButton',
                 background=[('active', gray_hover), 
                            ('pressed', gray_active),
                            ('disabled', disabled_gray_color)],
                 relief=[('pressed', 'sunken'), ('active', 'raised')],
                 foreground=[('disabled', '#ffffff')])
        
        # Кнопки акцента (дополнительные)
        style.configure('Accent.TButton',
                       font=('Segoe UI', 10),
                       padding=6,
                       relief='flat',
                       background='#f8f9fa',
                       foreground=fg_color,
                       borderwidth=1,
                       bordercolor=border_color,
                       focusthickness=0,
                       focuscolor='none')
        
        style.map('Accent.TButton',
                 background=[('active', '#e2e6ea'), 
                            ('pressed', '#dae0e5'),
                            ('disabled', '#f8f9fa')],
                 relief=[('pressed', 'sunken'), ('active', 'raised')],
                 foreground=[('disabled', '#888888')])
        
        # Стиль для полей ввода
        style.configure('TEntry',
                       fieldbackground='white',
                       foreground=fg_color,
                       bordercolor=border_color,
                       lightcolor=border_color,
                       darkcolor=border_color,
                       padding=5,
                       insertcolor=fg_color)
        
        style.map('TEntry',
                 fieldbackground=[('disabled', '#f8f9fa')],
                 foreground=[('disabled', '#888888')],
                 bordercolor=[('focus', '#007bff'), 
                             ('active', '#007bff')])
    
    def toggle_timeout_mode(self):
        """Включить/выключить поле ввода времени тайм-аута"""
        if self.timeout_enabled_var.get():
            self.timeout_entry.config(state="normal")
        else:
            self.timeout_entry.config(state="disabled")
    
    def initialize_always_on_top(self):
        """Инициализация режима 'Поверх всех окон' при запуске"""
        self.always_on_top = self.always_on_top_var.get()
        self.root.attributes('-topmost', self.always_on_top)
    
    def toggle_always_on_top(self):
        """Переключение режима 'Поверх всех окон'"""
        self.always_on_top = self.always_on_top_var.get()
        self.root.attributes('-topmost', self.always_on_top)
    
    def setup_hotkeys(self):
        """Настройка горячих клавиш"""
        try:
            # Используем after для безопасного вызова из GUI-потока
            def safe_start():
                if self.root.winfo_exists():
                    self.start_clicking()
            
            def safe_stop():
                if self.root.winfo_exists():
                    self.stop_clicking()
            
            keyboard.add_hotkey('F6', lambda: self.root.after(0, safe_start))
            keyboard.add_hotkey('F7', lambda: self.root.after(0, safe_stop))
            
            self.hotkeys_registered = True
            
        except Exception as e:
            print(f"Ошибка настройки горячих клавиш: {e}")
            self.hotkeys_registered = False
    
    def on_mouse_click(self, x, y, button, pressed):
        """Обработчик клика мыши для получения координат"""
        if pressed and button == mouse.Button.left and self.getting_coords:
            self.root.after(0, lambda: self.set_coordinates(x, y))
            return False
    
    def start_mouse_listener(self):
        """Запуск слушателя событий мыши"""
        if self.mouse_listener is None or not self.mouse_listener.is_alive():
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
            self.mouse_listener.start()
    
    def stop_mouse_listener(self):
        """Остановка слушателя событий мыши"""
        if self.mouse_listener and self.mouse_listener.is_alive():
            self.mouse_listener.stop()
            self.mouse_listener = None
    
    def set_coordinates(self, x, y):
        """Установить координаты в поля ввода"""
        self.x_var.set(str(x))
        self.y_var.set(str(y))
        self.getting_coords = False
        self.get_coords_btn.config(state="normal", text="Указать место клика")
        self.stop_mouse_listener()
    
    def start_getting_coords(self):
        """Начать процесс получения координат следующего клика"""
        if self.getting_coords:
            self.cancel_getting_coords()
            return
            
        if not self.click_mode_var.get():
            messagebox.showwarning("Внимание", "Включите режим 'Указанные координаты'")
            return
            
        self.getting_coords = True
        self.get_coords_btn.config(state="disabled", text="Кликните в нужном месте...")
        
        self.start_mouse_listener()
    
    def cancel_getting_coords(self):
        """Отмена процесса получения координат"""
        self.getting_coords = False
        self.get_coords_btn.config(state="normal", text="Указать место клика")
        self.stop_mouse_listener()
    
    def toggle_coords_mode(self):
        """Включить/выключить поля ввода координат в зависимости от режима"""
        if self.click_mode_var.get():
            # Включаем режим указанных координат
            self.x_entry.config(state="normal")
            self.y_entry.config(state="normal")
            self.get_coords_btn.config(state="normal")
        else:
            # Выключаем режим указанных координат
            self.x_entry.config(state="disabled")
            self.y_entry.config(state="disabled")
            self.get_coords_btn.config(state="disabled")
            
            # Если был активен процесс получения координат, отменяем его
            if self.getting_coords:
                self.cancel_getting_coords()
    
    def validate_inputs(self):
        """Проверка введенных данных"""
        try:
            min_val = int(self.min_interval_var.get())
            max_val = int(self.max_interval_var.get())
            
            if min_val <= 0 or max_val <= 0:
                raise ValueError("Интервал должен быть положительным числом")
            
            if min_val > 1000 * 60 * 60:
                raise ValueError("Минимальный интервал слишком большой (макс. 1 час)")
                
            if max_val > 1000 * 60 * 60 * 24:
                raise ValueError("Максимальный интервал слишком большой (макс. 24 часа)")
            
            if min_val > max_val:
                raise ValueError("Минимальный интервал не может быть больше максимального")
            
            if self.click_mode_var.get():
                if not self.x_var.get() or not self.y_var.get():
                    raise ValueError("Введите координаты или отключите режим указанных координат")
                
                x = int(self.x_var.get())
                y = int(self.y_var.get())
                
                if x < -10000 or x > 10000 or y < -10000 or y > 10000:
                    raise ValueError("Координаты должны быть в диапазоне ±10000")
                
                screen_width, screen_height = pyautogui.size()
                margin = 20
                
                # Предупреждение о координатах в углах
                if (x < margin and y < margin) or \
                   (x < margin and y > screen_height - margin) or \
                   (x > screen_width - margin and y < margin) or \
                   (x > screen_width - margin and y > screen_height - margin):
                    
                    if not messagebox.askyesno("Предупреждение",
                                             f"Координаты ({x}, {y}) близко к углу экрана.\n" \
                                             "Это может вызвать срабатывание fail-safe.\n\n" \
                                             "Хотите продолжить?"):
                        return False
            
            # Проверка тайм-аута
            if self.timeout_enabled_var.get():
                try:
                    timeout_minutes = int(self.timeout_var.get())
                    if timeout_minutes <= 0:
                        raise ValueError("Время тайм-аута должно быть положительным числом")
                    if timeout_minutes > 1440:  # 24 часа в минутах
                        if not messagebox.askyesno("Предупреждение",
                                                  f"Установлено большое время тайм-аута: {timeout_minutes} минут.\n" \
                                                  "Это более 24 часов.\n\n" \
                                                  "Хотите продолжить?"):
                            return False
                except ValueError as e:
                    messagebox.showerror("Ошибка ввода", f"Некорректное время тайм-аута: {e}")
                    return False
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return False
        except Exception as e:
            messagebox.showerror("Ошибка ввода", f"Некорректный ввод: {e}")
            return False
    
    def timeout_timer(self):
        """Таймер для автоматической остановки по тайм-ауту"""
        try:
            timeout_minutes = int(self.timeout_var.get())
            timeout_seconds = timeout_minutes * 60
            
            # Ждем указанное время
            if self.timer_event.wait(timeout=timeout_seconds):
                # Если событие было установлено (прервано), выходим
                return
            
            # Тайм-аут истек, останавливаем клики
            if self.is_running:
                print(f"Тайм-аут! Автоматическая остановка после {timeout_minutes} минут.")
                self.root.after(0, self.stop_clicking)
                
        except Exception as e:
            print(f"Ошибка в таймере: {e}")
    
    def click_loop(self):
        """Основной цикл кликов - улучшенная версия"""
        try:
            while self.is_running and not self.stop_event.is_set():
                min_interval = int(self.min_interval_var.get())
                max_interval = int(self.max_interval_var.get())
                interval = random.randint(min_interval, max_interval) / 1000.0
                
                if self.click_mode_var.get():
                    x = int(self.x_var.get())
                    y = int(self.y_var.get())
                    
                    try:
                        # ОТКЛЮЧАЕМ FAIL-SAFE для точности
                        pyautogui.FAILSAFE = False
                        
                        # 1. Получаем ТОЧНЫЕ текущие координаты
                        current_x, current_y = pyautogui.position()
                        
                        # 2. Кликаем по абсолютным координатам
                        pyautogui.click(x=x, y=y)
                        
                        # 3. Если курсор сместился во время клика, возвращаем его
                        new_x, new_y = pyautogui.position()
                        if abs(new_x - current_x) > 5 or abs(new_y - current_y) > 5:
                            # Курсор сместился - возвращаем на место
                            pyautogui.moveTo(current_x, current_y, duration=0)
                        
                        # ВКЛЮЧАЕМ FAIL-SAFE обратно
                        pyautogui.FAILSAFE = True
                        
                    except Exception as e:
                        # Всегда включаем fail-safe обратно при ошибке
                        pyautogui.FAILSAFE = True
                        print(f"Ошибка при клике: {e}")
                        
                else:
                    # Обычный клик в текущей позиции
                    pyautogui.click()
                
                # Пауза с возможностью прерывания
                self.stop_event.wait(timeout=interval)
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.root.after(0, self.stop_clicking)
    
    def start_clicking(self):
        """Запуск кликов"""
        if self.is_running:
            return
            
        if not self.validate_inputs():
            return
        
        if self.getting_coords:
            self.cancel_getting_coords()
        
        # Полностью останавливаем предыдущий поток, если он есть
        if self.click_thread and self.click_thread.is_alive():
            self.stop_clicking()
            # Даем время на завершение
            time.sleep(0.1)
        
        # Сбрасываем событие остановки
        self.stop_event.clear()
        

        # Устанавливаем флаг запуска
        self.is_running = True
        
        # Обновляем состояние кнопок
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # Создаем новый поток для кликов
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
        
        # Запускаем таймер, если включен тайм-аут
        if self.timeout_enabled_var.get():
            # Сбрасываем событие таймера
            self.timer_event.clear()
            # Запускаем таймер в отдельном потоке
            self.timer_thread = threading.Thread(target=self.timeout_timer, daemon=True)
            self.timer_thread.start()
    
    def stop_clicking(self):
        """Остановка кликов"""
        # Устанавливаем флаг остановки
        self.is_running = False
        self.stop_event.set()
        self.timer_event.set()  # Останавливаем таймер
        
        # ВСЕГДА включаем fail-safe обратно при остановке
        pyautogui.FAILSAFE = True
        
        # Ждем завершения потоков
        if self.click_thread and self.click_thread.is_alive():
            self.click_thread.join(timeout=2.0)
            
            if self.click_thread.is_alive():
                print("Предупреждение: Поток кликов не завершился вовремя")
                # Сбрасываем ссылку на поток
                self.click_thread = None
        
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1.0)
            
            if self.timer_thread.is_alive():
                print("Предупреждение: Поток таймера не завершился вовремя")
                # Сбрасываем ссылку на поток
                self.timer_thread = None
        
        # Обновляем состояние кнопок в основном потоке
        self.root.after(0, lambda: self.start_btn.config(state="normal"))
        self.root.after(0, lambda: self.stop_btn.config(state="disabled"))
    
    def on_closing(self):
        """Обработка закрытия окна"""
        # Останавливаем клики
        self.stop_clicking()
        
        # Отменяем получение координат
        self.cancel_getting_coords()
        
        # Удаляем горячие клавиши
        try:
            if self.hotkeys_registered:
                keyboard.remove_hotkey('F6')
                keyboard.remove_hotkey('F7')
        except:
            pass
        
        # Очищаем ресурсы проверки экземпляра
        cleanup_single_instance()
        
        # Закрываем окно
        self.root.destroy()
        sys.exit(0)

def main():
    # Всегда проверяем, не запущена ли уже программа
    if not check_single_instance():
        # Программа уже запущена - показываем сообщение и завершаемся
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"{APP_TITLE} уже запущен!\n\n"
                "Повторный запуск программы невозможен.\n"
                "Закройте существующее окно программы или проверьте запущенные процессы.",
                APP_TITLE,
                0x30  # MB_ICONEXCLAMATION | MB_OK
            )
        else:
            print(f"{APP_TITLE} уже запущен!")
            print("Повторный запуск программы невозможен.")
            print("Закройте существующее окно программы или проверьте запущенные процессы.")
        sys.exit(0)
    
    root = tk.Tk()
    app = AutoClicker(root)
    
    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()