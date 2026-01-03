import threading
import time
import random
import pyautogui

class ClickWorker:
    def __init__(self, app_instance):
        self.app = app_instance
        self.is_running = False
        self.click_thread = None
        self.stop_event = threading.Event()
        self.timer_thread = None
        self.timer_event = threading.Event()
    
    def validate_inputs(self, min_interval_var, max_interval_var, click_mode_var, 
                       x_var, y_var, timeout_enabled_var, timeout_var):
        """Проверка введенных данных"""
        try:
            min_val = int(min_interval_var.get())
            max_val = int(max_interval_var.get())
            
            if min_val <= 0 or max_val <= 0:
                raise ValueError("Интервал должен быть положительным числом")
            
            if min_val > 1000 * 60 * 60:
                raise ValueError("Минимальный интервал слишком большой (макс. 1 час)")
                
            if max_val > 1000 * 60 * 60 * 24:
                raise ValueError("Максимальный интервал слишком большой (макс. 24 часа)")
            
            if min_val > max_val:
                raise ValueError("Минимальный интервал не может быть больше максимального")
            
            if click_mode_var.get():
                if not x_var.get() or not y_var.get():
                    raise ValueError("Введите координаты или отключите режим указанных координат")
                
                x = int(x_var.get())
                y = int(y_var.get())
                
                if x < -10000 or x > 10000 or y < -10000 or y > 10000:
                    raise ValueError("Координаты должны быть в диапазоне ±10000")
                
                screen_width, screen_height = pyautogui.size()
                margin = 20
                
                # Предупреждение о координатах в углах
                if (x < margin and y < margin) or \
                   (x < margin and y > screen_height - margin) or \
                   (x > screen_width - margin and y < margin) or \
                   (x > screen_width - margin and y > screen_height - margin):
                    
                    from tkinter import messagebox
                    if not messagebox.askyesno("Предупреждение",
                                             f"Координаты ({x}, {y}) близко к углу экрана.\n" \
                                             "Это может вызвать срабатывание fail-safe.\n\n" \
                                             "Хотите продолжить?"):
                        return False
            
            # Проверка тайм-аута
            if timeout_enabled_var.get():
                try:
                    timeout_minutes = int(timeout_var.get())
                    if timeout_minutes <= 0:
                        raise ValueError("Время тайм-аута должно быть положительным числом")
                    if timeout_minutes > 1440:  # 24 часа в минутах
                        from tkinter import messagebox
                        if not messagebox.askyesno("Предупреждение",
                                                  f"Установлено большое время тайм-аута: {timeout_minutes} минут.\n" \
                                                  "Это более 24 часов.\n\n" \
                                                  "Хотите продолжить?"):
                            return False
                except ValueError as e:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка ввода", f"Некорректное время тайм-аута: {e}")
                    return False
            
            return True
            
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка ввода", str(e))
            return False
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка ввода", f"Некорректный ввод: {e}")
            return False
    
    def timeout_timer(self):
        """Таймер для автоматической остановки по тайм-ауту"""
        try:
            timeout_minutes = int(self.app.timeout_var.get())
            timeout_seconds = timeout_minutes * 60
            
            # Ждем указанное время
            if self.timer_event.wait(timeout=timeout_seconds):
                # Если событие было установлено (прервано), выходим
                return
            
            # Тайм-аут истек, останавливаем клики
            if self.is_running:
                print(f"Тайм-аут! Автоматическая остановка после {timeout_minutes} минут.")
                self.app.root.after(0, self.app.stop_clicking)
                
        except Exception as e:
            print(f"Ошибка в таймере: {e}")
    
    def click_loop(self):
        """Основной цикл кликов"""
        try:
            while self.is_running and not self.stop_event.is_set():
                min_interval = int(self.app.min_interval_var.get())
                max_interval = int(self.app.max_interval_var.get())
                interval = random.randint(min_interval, max_interval) / 1000.0
                
                if self.app.click_mode_var.get():
                    x = int(self.app.x_var.get())
                    y = int(self.app.y_var.get())
                    
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
            from tkinter import messagebox
            self.app.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.app.root.after(0, self.app.stop_clicking)