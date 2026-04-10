from pynput import mouse
import time

class MouseHandler:
    def __init__(self, app_instance):
        self.app = app_instance
        self.mouse_listener = None
        self.getting_coords = False
        self._stop_timeout = 2.0  # Таймаут для остановки слушателя

    def on_mouse_click(self, x, y, button, pressed):
        """Обработчик клика мыши для получения координат"""
        if pressed and button == mouse.Button.left and self.getting_coords:
            self.app.root.after(0, lambda: self.set_coordinates(x, y))
            return False

    def set_coordinates(self, x, y):
        """Установить координаты в поля ввода"""
        self.app.x_var.set(str(x))
        self.app.y_var.set(str(y))
        self.getting_coords = False
        self.app.get_coords_btn.config(state="normal" if not self.app.is_running else "disabled",
                                      text="Указать место клика")
        self.stop_mouse_listener()

    def start_mouse_listener(self):
        """Запуск слушателя событий мыши"""
        try:
            if self.mouse_listener is None or not self.mouse_listener.is_alive():
                self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
                self.mouse_listener.start()
                # Ждем запуска
                time.sleep(0.1)
                if not self.mouse_listener.is_alive():
                    print("Ошибка: Слушатель мыши не запустился")
                    self.mouse_listener = None
        except Exception as e:
            print(f"Ошибка запуска слушателя мыши: {e}")
            self.mouse_listener = None

    def stop_mouse_listener(self):
        """Остановка слушателя событий мыши"""
        try:
            if self.mouse_listener and self.mouse_listener.is_alive():
                self.mouse_listener.stop()
                # Ждем завершения с таймаутом
                self.mouse_listener.join(timeout=self._stop_timeout)
                if self.mouse_listener.is_alive():
                    print("Предупреждение: Слушатель мыши не завершился вовремя")
                self.mouse_listener = None
        except Exception as e:
            print(f"Ошибка остановки слушателя мыши: {e}")
            self.mouse_listener = None