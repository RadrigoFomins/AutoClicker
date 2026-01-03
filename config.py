import sys
import os

# Константы программы
APP_NAME = "Auto Clicker"
APP_VERSION = "1.0.3"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

def check_single_instance(app_name=APP_NAME):
    """Проверяет, запущен ли уже экземпляр программы"""
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            
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