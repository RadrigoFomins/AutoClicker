import sys
sys.dont_write_bytecode = True

import tkinter as tk
from config import check_single_instance, cleanup_single_instance, APP_TITLE
from autoclicker_gui import AutoClickerGUI

def main():
    # Всегда проверяем, не запущена ли уже программа
    if not check_single_instance():
        # Программа уже запущена - показываем сообщение и завершаемся
        import os
        import ctypes
        
        if os.name == 'nt':
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
    app = AutoClickerGUI(root)
    
    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Устанавливаем обработчик завершения
    import atexit
    atexit.register(cleanup_single_instance)
    
    root.mainloop()

if __name__ == "__main__":
    main()