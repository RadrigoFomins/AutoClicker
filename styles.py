import tkinter as tk
from tkinter import ttk

def setup_styles():
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