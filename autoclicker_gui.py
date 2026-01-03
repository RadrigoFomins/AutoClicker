import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import keyboard
from config import APP_TITLE
from styles import setup_styles
from click_worker import ClickWorker
from mouse_handler import MouseHandler

class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("302x448")
        self.root.resizable(False, False)
        
        # Устанавливаем белый фон для всего окна
        self.root.configure(bg='white')
        
        # Инициализация компонентов
        self.is_running = False
        self.always_on_top = False
        self.hotkeys_registered = False
        
        # Инициализация обработчиков
        self.click_worker = ClickWorker(self)
        self.mouse_handler = MouseHandler(self)
        
        # Создаем кастомный стиль
        setup_styles()
        
        # Основной фрейм с белым фоном
        main_frame = ttk.Frame(root, padding="12")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Устанавливаем белый фон для основного фрейма
        main_frame.configure(style='White.TFrame')
        
        # Конфигурация веса строк
        root.grid_rowconfigure(0, weight=1)
        
        # Создание виджетов
        self.create_widgets(main_frame)
        
        # Инициализация режима координат
        self.toggle_coords_mode()
        
        # Включаем режим "Поверх всех окон" по умолчанию
        self.root.after(100, self.initialize_always_on_top)
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Привязываем горячие клавиши с небольшой задержкой
        self.root.after(200, self.setup_hotkeys)
    
    def create_widgets(self, parent):
        """Создание всех виджетов интерфейса"""
        # Интервал кликов
        interval_frame = ttk.LabelFrame(
            parent, 
            text="Интервал между кликов (мс)", 
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
            parent, 
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
            parent, 
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
            parent, 
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
        buttons_frame = ttk.Frame(parent, style='White.TFrame')
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
    
    def lock_all_settings(self, lock=True):
        """Блокировка или разблокировка всех настроек"""
        state = "disabled" if lock else "normal"
        
        # Блокируем поля интервалов
        self.min_interval_entry.config(state=state)
        self.max_interval_entry.config(state=state)
        
        # Блокируем чекбокс режима координат
        self.use_coords_check.config(state=state)
        
        # Блокируем поля координат
        if self.click_mode_var.get():
            self.x_entry.config(state=state)
            self.y_entry.config(state=state)
            self.get_coords_btn.config(state=state)
        
        # Блокируем чекбокс тайм-аута
        self.timeout_check.config(state=state)
        
        # Блокируем поле ввода тайм-аута
        if self.timeout_enabled_var.get():
            self.timeout_entry.config(state=state)
        
        # НЕ блокируем чекбокс "Поверх всех окон" - он должен быть доступен всегда
        # self.always_on_top_check.config(state=state)
    
    def toggle_timeout_mode(self):
        """Включить/выключить поле ввода времени тайм-аута"""
        if self.timeout_enabled_var.get():
            self.timeout_entry.config(state="normal" if not self.is_running else "disabled")
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
    
    def start_getting_coords(self):
        """Начать процесс получения координат следующего клика"""
        if self.mouse_handler.getting_coords:
            self.cancel_getting_coords()
            return
            
        if not self.click_mode_var.get():
            messagebox.showwarning("Внимание", "Включите режим 'Указанные координаты'")
            return
            
        self.mouse_handler.getting_coords = True
        self.get_coords_btn.config(state="disabled", text="Кликните в нужном месте...")
        
        self.mouse_handler.start_mouse_listener()
    
    def cancel_getting_coords(self):
        """Отмена процесса получения координат"""
        self.mouse_handler.getting_coords = False
        self.get_coords_btn.config(state="normal" if not self.is_running else "disabled", 
                                  text="Указать место клика")
        self.mouse_handler.stop_mouse_listener()
    
    def toggle_coords_mode(self):
        """Включить/выключить поля ввода координат в зависимости от режима"""
        if self.click_mode_var.get():
            # Включаем режим указанных координат
            self.x_entry.config(state="normal" if not self.is_running else "disabled")
            self.y_entry.config(state="normal" if not self.is_running else "disabled")
            self.get_coords_btn.config(state="normal" if not self.is_running else "disabled")
        else:
            # Выключаем режим указанных координат
            self.x_entry.config(state="disabled")
            self.y_entry.config(state="disabled")
            self.get_coords_btn.config(state="disabled")
            
            # Если был активен процесс получения координат, отменяем его
            if self.mouse_handler.getting_coords:
                self.cancel_getting_coords()
    
    def start_clicking(self):
        """Запуск кликов"""
        if self.is_running:
            return
            
        if not self.click_worker.validate_inputs(
            self.min_interval_var, self.max_interval_var, self.click_mode_var,
            self.x_var, self.y_var, self.timeout_enabled_var, self.timeout_var
        ):
            return
        
        if self.mouse_handler.getting_coords:
            self.cancel_getting_coords()
        
        # Полностью останавливаем предыдущий поток, если он есть
        if self.click_worker.click_thread and self.click_worker.click_thread.is_alive():
            self.stop_clicking()
            time.sleep(0.1)
        
        # Сбрасываем событие остановки
        self.click_worker.stop_event.clear()
        
        # Устанавливаем флаг запуска
        self.is_running = True
        self.click_worker.is_running = True
        
        # Блокируем все настройки, кроме настроек окна
        self.lock_all_settings(True)
        
        # Обновляем состояние кнопок
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # Создаем новый поток для кликов
        self.click_worker.click_thread = threading.Thread(target=self.click_worker.click_loop, daemon=True)
        self.click_worker.click_thread.start()
        
        # Запускаем таймер, если включен тайм-аут
        if self.timeout_enabled_var.get():
            # Сбрасываем событие таймера
            self.click_worker.timer_event.clear()
            # Запускаем таймер в отдельном потоке
            self.click_worker.timer_thread = threading.Thread(target=self.click_worker.timeout_timer, daemon=True)
            self.click_worker.timer_thread.start()
    
    def stop_clicking(self):
        """Остановка кликов"""
        # Устанавливаем флаг остановки
        self.is_running = False
        self.click_worker.is_running = False
        self.click_worker.stop_event.set()
        self.click_worker.timer_event.set()  # Останавливаем таймер
        
        # Ждем завершения потоков
        if self.click_worker.click_thread and self.click_worker.click_thread.is_alive():
            self.click_worker.click_thread.join(timeout=2.0)
            
            if self.click_worker.click_thread.is_alive():
                print("Предупреждение: Поток кликов не завершился вовремя")
                self.click_worker.click_thread = None
        
        if self.click_worker.timer_thread and self.click_worker.timer_thread.is_alive():
            self.click_worker.timer_thread.join(timeout=1.0)
            
            if self.click_worker.timer_thread.is_alive():
                print("Предупреждение: Поток таймера не завершился вовремя")
                self.click_worker.timer_thread = None
        
        # Разблокируем все настройки
        self.lock_all_settings(False)
        
        # Обновляем состояние кнопок в основном потоке
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        # Восстанавливаем состояние полей в зависимости от режимов
        self.toggle_coords_mode()
        self.toggle_timeout_mode()
    
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
        
        # Закрываем окно
        self.root.destroy()