import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import numpy as np
import os
import sounddevice as sd
import queue
import time
import simpleaudio as sa
import wave
import json
import shutil
import sys
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw
try:
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Предупреждение: mutagen не установлен. MP3 файлы не поддерживаются.")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Предупреждение: pydub не установлен. MP3 файлы будут загружаться с ограничениями.")

# Светлая тема с современными акцентами как на скриншоте
LIGHT_BG = "#F5F5F7"  # Основной фон серо-голубой
LIGHT_PANE = "#FFFFFF"  # Белый панелей
LIGHT_ACCENT = "#007AFF"  # Синий акцент как на скриншоте
LIGHT_ACCENT_HOVER = "#0051D5"
LIGHT_SUCCESS = "#34C759"  # Зелёный
LIGHT_SUCCESS_HOVER = "#28A745"
LIGHT_DANGER = "#FF3B30"   # Красный
LIGHT_DANGER_HOVER = "#D32F2F"
LIGHT_TEXT = "#1D1D1F"     # Тёмно-серый текст
LIGHT_TEXT_SECONDARY = "#8E8E93"  # Серый вторичный
LIGHT_BORDER = "#E5E5E7"
LIGHT_SHADOW = "#00000005"
BLACK = "#000000"

class EchoBox:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 EchoBox - Библиотека звуков")
        self.root.geometry("900x800")  # Сделал длину немного меньше (800 вместо 900)
        self.root.configure(bg=LIGHT_BG)
        self.root.minsize(800, 650)  # Сделал минимальную высоту тоже меньше
        
        # Получаем путь к папке приложения
        if getattr(sys, 'frozen', False):
            # Если запущено как EXE
            self.app_dir = os.path.dirname(sys.executable)
        else:
            # Если запущено как Python скрипт
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Аудио переменные
        self.current_audio_data = None
        self.current_sample_rate = None
        self.is_playing = False
        self.is_paused = False
        self.current_playback_obj = None
        self.sample_rate = 44100
        self.current_position = 0  # Текущая позиция в сэмплах
        self.total_samples = 0     # Общее количество сэмплов
        self.current_sound_id = None  # ID текущего звука
        
        # Библиотека звуков (в папке приложения)
        self.library_file = os.path.join(self.app_dir, "sound_library.json")
        self.sounds_folder = os.path.join(self.app_dir, "sounds")
        self.sound_library = {}
        
        # Плейлисты
        self.playlists_file = os.path.join(self.app_dir, "playlists.json")
        self.playlists = {}
        self.current_playlist = None  # Текущий выбранный плейлист
        self.playlist_mode = False  # Режим воспроизведения плейлиста
        
        # Настройки биндов для цифр (в папке приложения)
        self.bindings_file = os.path.join(self.app_dir, "key_bindings.json")
        self.number_bindings = {
            '1': '<Key-1>',
            '2': '<Key-2>', 
            '3': '<Key-3>',
            '4': '<Key-4>',
            '5': '<Key-5>',
            '6': '<Key-6>',
            '7': '<Key-7>',
            '8': '<Key-8>',
            '9': '<Key-9>'
        }
        
        # Создание интерфейса (сначала без фона)
        self.create_widgets()
        
        # Создаем фон после небольшой задержки
        self.root.after(500, self.create_background)
        
        # Настройка аудио потока
        self.setup_audio_stream()
        
        # Горячие клавиши
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus_set())
        self.root.bind('<Control-F>', lambda e: self.search_entry.focus_set())
        self.root.bind('<Escape>', lambda e: self.clear_search())
    
    def create_gradient_image(self, width, height, color1, color2, direction="vertical"):
        """Создает градиентное изображение"""
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Конвертируем hex цвета в RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        
        if direction == "vertical":
            for y in range(height):
                ratio = y / height
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        else:  # horizontal
            for x in range(width):
                ratio = x / width
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))
        
        return ImageTk.PhotoImage(image)
    
    def create_background(self):
        """Создает фоновое изображение"""
        try:
            # Создаем изображение похожее на скриншот
            width = 1200
            height = 800
            
            # Создаем изображение с градиентом и узором
            image = Image.new('RGB', (width, height))
            pixels = image.load()
            
            # Основной градиент от серо-голубого к более светлому
            for y in range(height):
                for x in range(width):
                    # Градиент
                    ratio_y = y / height
                    ratio_x = x / width
                    
                    # Основной цвет - серо-голубой
                    r = int(232 + (245 - 232) * ratio_y * 0.3)
                    g = int(232 + (245 - 232) * ratio_y * 0.3) 
                    b = int(237 + (250 - 237) * ratio_y * 0.3)
                    
                    # Добавляем легкий узор
                    pattern = int((x + y) % 50)
                    if pattern < 5:
                        r = min(255, r + 10)
                        g = min(255, g + 10)
                        b = min(255, b + 15)
                    
                    pixels[x, y] = (r, g, b)
            
            # Добавляем декоративные элементы
            for i in range(8):
                x = (i * 150) % width
                y = (i * 100) % height
                size = 80 + i * 15
                
                # Создаем круги с полупрозрачностью
                for dy in range(size):
                    for dx in range(size):
                        if dx*dx + dy*dy <= size*size:
                            px = x + dx - size//2
                            py = y + dy - size//2
                            if 0 <= px < width and 0 <= py < height:
                                pixel = pixels[px, py]
                                pixels[px, py] = (
                                    min(255, pixel[0] + 5),
                                    min(255, pixel[1] + 5), 
                                    min(255, pixel[2] + 10)
                                )
            
            # Сохраняем изображение в папке приложения
            background_path = os.path.join(self.app_dir, "background.png")
            image.save(background_path)
            
            # Загружаем как фон
            self.root.update()
            win_width = self.root.winfo_width()
            win_height = self.root.winfo_height()
            
            if win_width <= 1:
                win_width = 1000
            if win_height <= 1:
                win_height = 700
                
            # Масштабируем изображение
            resized_image = image.resize((win_width, win_height), Image.Resampling.LANCZOS)
            self.background_image = ImageTk.PhotoImage(resized_image)
            
            # Создаем Label с фоном
            self.background_label = tk.Label(self.root, image=self.background_image)
            self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.background_label.lower()
            
            # Привязываем изменение размера
            self.root.bind('<Configure>', self.on_window_resize)
            
        except Exception as e:
            print(f"Ошибка создания фона: {e}")
            self.root.configure(bg="#E8E8ED")
    
    def on_window_resize(self, event):
        """Обрабатывает изменение размера окна"""
        if hasattr(self, 'background_label'):
            background_path = os.path.join(self.app_dir, "background.png")
            if os.path.exists(background_path):
                try:
                    # Перезагружаем изображение с новым размером
                    image = Image.open(background_path)
                    image = image.resize((event.width, event.height), Image.Resampling.LANCZOS)
                    self.background_image = ImageTk.PhotoImage(image)
                    self.background_label.configure(image=self.background_image)
                except Exception as e:
                    print(f"Ошибка обновления фона: {e}")
    
    def create_widgets(self):
        # Основной контейнер с современным дизайном (прозрачный)
        main_container = tk.Frame(self.root, bg="")
        main_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
        
        # Заголовочная панель с градиентом
        header_frame = tk.Frame(main_container, bg=LIGHT_ACCENT, relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        header_inner = tk.Frame(header_frame, bg=LIGHT_ACCENT)
        header_inner.pack(fill=tk.X, padx=32, pady=24)
        
        # Заголовок
        title_label = tk.Label(header_inner, text="🎵 EchoBox", 
                              font=("Segoe UI Emoji", 28, "bold"), 
                              fg="WHITE", bg=LIGHT_ACCENT)
        title_label.pack(pady=(0, 8), anchor=tk.W)
        
        # Подзаголовок
        subtitle_label = tk.Label(header_inner, text="Управляйте своей коллекцией звуков", 
                                 font=("Segoe UI Emoji", 14), 
                                 fg="#E0E7FF", bg=LIGHT_ACCENT)
        subtitle_label.pack(anchor=tk.W)
        
        # Панель инструментов с кнопками как на скриншоте - ВОЗВРАЩАЕМ НАВЕРХ
        toolbar_frame = tk.Frame(main_container, bg="#FFFFFF", relief=tk.FLAT, bd=0)
        toolbar_frame.pack(fill=tk.X, pady=(0, 20))
        
        toolbar_inner = tk.Frame(toolbar_frame, bg=LIGHT_PANE)
        toolbar_inner.pack(fill=tk.X, padx=32, pady=20)
        
        # Левая группа кнопок
        left_buttons = tk.Frame(toolbar_inner, bg=LIGHT_PANE, relief=tk.RAISED, bd=1)
        left_buttons.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Создаем кастомные кнопки с фоном через Frame
        
        # Кнопка добавления звука
        add_button_frame = tk.Frame(left_buttons, bg="#4169E1", relief=tk.FLAT, bd=0)
        add_button_frame.pack(side=tk.LEFT, padx=(0, 4))
        self.add_button = tk.Button(add_button_frame, text="➕", 
                                   command=self.add_sound_to_library,
                                   font=("Segoe UI Emoji", 16, "bold"),
                                   bg="#4169E1", fg="WHITE",
                                   activebackground="#2E4BC7",
                                   relief=tk.SOLID, bd=1,
                                   padx=18, pady=10,
                                   cursor="hand2")
        self.add_button.pack(padx=3, pady=3)
        
        # Кнопка воспроизведения
        play_button_frame = tk.Frame(left_buttons, bg="#28A745", relief=tk.FLAT, bd=0)
        play_button_frame.pack(side=tk.LEFT, padx=4)
        self.play_button = tk.Button(play_button_frame, text="▶️", 
                                    command=self.play_selected_sound,
                                    font=("Segoe UI Emoji", 16, "bold"),
                                    bg="#28A745", fg="WHITE",
                                    activebackground="#1E7E34",
                                    relief=tk.SOLID, bd=1,
                                    padx=18, pady=10,
                                    state=tk.DISABLED,
                                    cursor="hand2")
        self.play_button.pack(padx=3, pady=3)
        
        # Кнопка стопа
        stop_button_frame = tk.Frame(left_buttons, bg="#DC3545", relief=tk.FLAT, bd=0)
        stop_button_frame.pack(side=tk.LEFT, padx=4)
        self.stop_button = tk.Button(stop_button_frame, text="⏹️", 
                                   command=self.stop_playback,
                                   font=("Segoe UI Emoji", 16, "bold"),
                                   bg="#DC3545", fg="WHITE",
                                   activebackground="#C82333",
                                   relief=tk.SOLID, bd=1,
                                   padx=18, pady=10,
                                   state=tk.DISABLED,
                                   cursor="hand2")
        self.stop_button.pack(padx=3, pady=3)
        
        # Кнопка закончить
        finish_button_frame = tk.Frame(left_buttons, bg="#6C757D", relief=tk.FLAT, bd=0)
        finish_button_frame.pack(side=tk.LEFT, padx=4)
        self.finish_button = tk.Button(finish_button_frame, text="🛑", 
                                     command=self.finish_playback,
                                     font=("Segoe UI Emoji", 16, "bold"),
                                     bg="#6C757D", fg="WHITE",
                                     activebackground="#545B62",
                                     relief=tk.SOLID, bd=1,
                                     padx=18, pady=10,
                                     state=tk.DISABLED,
                                     cursor="hand2")
        self.finish_button.pack(padx=3, pady=3)
        
        # Информационная метка рядом с кнопками
        self.status_label = tk.Label(left_buttons, text="Выберите звук для воспроизведения", 
                                  font=("Segoe UI", 11), 
                                  fg=LIGHT_TEXT_SECONDARY, bg=LIGHT_PANE)
        self.status_label.pack(side=tk.LEFT, padx=(16, 0))
        
        # Правая группа кнопок (пустая, так как бинды отключены)
        right_buttons = tk.Frame(toolbar_inner, bg=LIGHT_PANE, relief=tk.RAISED, bd=1)
        right_buttons.pack(side=tk.RIGHT)
        
        # Панель списка звуков с карточным дизайном - ПОСЛЕ КНОПОК
        list_container = tk.Frame(main_container, bg=LIGHT_PANE, relief=tk.FLAT, bd=1)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        list_inner = tk.Frame(list_container, bg=LIGHT_PANE)
        list_inner.pack(fill=tk.BOTH, expand=True, padx=32, pady=24)
        
        # Заголовок списка
        list_title = tk.Label(list_inner, text="📂 Ваша библиотека", 
                              font=("Segoe UI Emoji", 18, "bold"), 
                              fg=LIGHT_TEXT, bg=LIGHT_PANE)
        list_title.pack(pady=(0, 16), anchor=tk.W)
        
        # Панель плейлистов
        playlist_frame = tk.Frame(list_inner, bg=LIGHT_PANE, relief=tk.FLAT, bd=1)
        playlist_frame.pack(fill=tk.X, pady=(0, 16))
        
        playlist_inner = tk.Frame(playlist_frame, bg=LIGHT_PANE)
        playlist_inner.pack(fill=tk.X, padx=12, pady=8)
        
        # Заголовок плейлистов
        playlist_header = tk.Frame(playlist_inner, bg=LIGHT_PANE)
        playlist_header.pack(fill=tk.X, pady=(0, 8))
        
        playlist_label = tk.Label(playlist_header, text="🎵 Плейлисты:", 
                                  font=("Segoe UI Emoji", 12, "bold"), 
                                  fg=LIGHT_TEXT, bg=LIGHT_PANE)
        playlist_label.pack(side=tk.LEFT)
        
        # Кнопки управления плейлистами
        playlist_btn_frame = tk.Frame(playlist_header, bg=LIGHT_PANE)
        playlist_btn_frame.pack(side=tk.RIGHT)
        
        self.new_playlist_btn = tk.Button(playlist_btn_frame, text="➕ Новый", 
                                        font=("Segoe UI", 9, "bold"),
                                        bg=LIGHT_SUCCESS, fg="white",
                                        relief=tk.FLAT, bd=0, padx=8, pady=4,
                                        command=self.show_create_playlist_dialog)
        self.new_playlist_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        self.playlist_mode_btn = tk.Button(playlist_btn_frame, text="🔂 Режим плейлиста", 
                                           font=("Segoe UI", 9, "bold"),
                                           bg=LIGHT_BORDER, fg=LIGHT_TEXT_SECONDARY,
                                           relief=tk.FLAT, bd=0, padx=8, pady=4,
                                           command=self.toggle_playlist_mode)
        self.playlist_mode_btn.pack(side=tk.LEFT)
        
        # Список плейлистов
        self.playlist_frame_inner = tk.Frame(playlist_inner, bg=LIGHT_PANE)
        self.playlist_frame_inner.pack(fill=tk.X)
        
        self.refresh_playlist_list()
        
        # Поле поиска
        search_frame = tk.Frame(list_inner, bg=LIGHT_PANE)
        search_frame.pack(fill=tk.X, pady=(0, 16))
        
        search_label = tk.Label(search_frame, text="🔍 Поиск:", 
                               font=("Segoe UI Emoji", 12), 
                               fg=LIGHT_TEXT_SECONDARY, bg=LIGHT_PANE)
        search_label.pack(side=tk.LEFT, padx=(0, 8))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_sounds)
        
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("Segoe UI", 11), bg=LIGHT_PANE, 
                                     fg=LIGHT_TEXT, relief=tk.FLAT, bd=1)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        # Кнопка очистки поиска
        self.clear_search_btn = tk.Button(search_frame, text="✕", 
                                         font=("Segoe UI", 10, "bold"),
                                         bg=LIGHT_BORDER, fg=LIGHT_TEXT_SECONDARY,
                                         relief=tk.FLAT, bd=0, padx=8, pady=4,
                                         command=self.clear_search)
        self.clear_search_btn.pack(side=tk.RIGHT)
        
        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Light.Treeview", 
                        background=LIGHT_PANE,
                        foreground=LIGHT_TEXT,
                        fieldbackground=LIGHT_PANE,
                        borderwidth=0,
                        relief=tk.FLAT)
        style.configure("Light.Treeview.Heading", 
                        background=LIGHT_PANE,
                        foreground=LIGHT_TEXT,
                        borderwidth=0,
                        relief=tk.FLAT)
        
        tree_frame = tk.Frame(list_inner, bg=LIGHT_PANE)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.sound_tree = ttk.Treeview(tree_frame, columns=("name", "duration", "format"), 
                                     show="headings", style="Light.Treeview",
                                     height=15)  # Уменьшил высоту до 15 строк
        
        # Настройка колонок
        self.sound_tree.heading("name", text="Название")
        self.sound_tree.heading("duration", text="Длительность")
        self.sound_tree.heading("format", text="Формат")
        
        self.sound_tree.column("name", width=200, anchor="w")  # Уменьшил ширину названия
        self.sound_tree.column("duration", width=100, anchor="center")  # Вернул длительность
        self.sound_tree.column("format", width=80, anchor="center")  # Вернул формат
        
        # Добавляем прокрутку
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.sound_tree.yview)
        self.sound_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sound_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для правого клика
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Переименовать", command=self.rename_sound)
        self.context_menu.add_separator()
        
        # Подменю для добавления в плейлист
        self.playlist_submenu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Добавить в плейлист", menu=self.playlist_submenu)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_sound_from_library)
        
        # Привязываем правый клик
        self.sound_tree.bind("<Button-3>", self.show_context_menu)
        
        # Привязка выбора
        self.sound_tree.bind("<<TreeviewSelect>>", self.on_sound_select)
        
        # Загрузка данных
        self.load_library()
        
        # Создаем фон после небольшой задержки
        self.root.after(500, self.create_background)
        
        # Настройка аудио потока
        self.setup_audio_stream()
        
        # Горячие клавиши
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus_set())
        self.root.bind('<Control-F>', lambda e: self.search_entry.focus_set())
        self.root.bind('<Escape>', lambda e: self.clear_search())
    
    def load_number_bindings(self):
        """Загрузка настроек биндов для цифр"""
        try:
            if os.path.exists(self.bindings_file):
                with open(self.bindings_file, 'r', encoding='utf-8') as f:
                    loaded_bindings = json.load(f)
                    print(f"Загружены бинды: {loaded_bindings}")
                    # Преобразуем старый формат в новый
                    for key, value in loaded_bindings.items():
                        if key.startswith('numpad_'):
                            num = key.replace('numpad_', '')
                            if num in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                                self.number_bindings[num] = value
                                print(f"Установлен бинд для цифры {num}: {value}")
        except Exception as e:
            print(f"Ошибка загрузки биндов: {e}")
    
    def save_number_bindings(self):
        """Сохранение настроек биндов для цифр"""
        try:
            print(f"Сохранение в файл {self.bindings_file}: {self.number_bindings}")
            with open(self.bindings_file, 'w', encoding='utf-8') as f:
                json.dump(self.number_bindings, f, ensure_ascii=False, indent=2)
            print("Настройки успешно сохранены в файл")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def apply_number_bindings(self):
        """Применение биндов для цифр"""
        print("Бинды отключены")
        # Удаляем все бинды
        for num in range(1, 10):
            try:
                self.root.unbind(f'<Key-{num}>')
                self.root.unbind(f'<KP_{num}>')
            except:
                pass
        
        # Удаляем бинд на Enter
        try:
            self.root.unbind('<Return>')
        except:
            pass
    
    def play_sound_by_index(self, index):
        """Воспроизведение звука по индексу"""
        if 0 <= index < len(self.sound_library):
            sound_ids = list(self.sound_library.keys())
            if index < len(sound_ids):
                sound_id = sound_ids[index]
                sound_info = self.sound_library[sound_id]
                filepath = os.path.join(self.sounds_folder, sound_info["filename"])
                
                # Выбираем звук в дереве
                children = self.sound_tree.get_children()
                if index < len(children):
                    self.sound_tree.selection_set(children[index])
                    self.sound_tree.see(children[index])
                
                # Воспроизводим сразу
                self.play_selected_sound()
    
    def open_number_bindings(self):
        """Открытие окна настроек биндов для цифр"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки биндов цифр")
        settings_window.geometry("600x550")
        settings_window.configure(bg=LIGHT_BG)
        settings_window.resizable(True, True)
        
        # Заголовок
        title_label = tk.Label(settings_window, text="🔢 Настройки биндов цифр",
                              font=("Segoe UI", 16, "bold"),
                              fg=LIGHT_TEXT, bg=LIGHT_BG)
        title_label.pack(pady=20)
        
        # Инструкция
        info_label = tk.Label(settings_window, 
                             text="Введите комбинации клавиш для цифр 1-9",
                             font=("Segoe UI", 10),
                             fg=LIGHT_TEXT_SECONDARY, bg=LIGHT_BG)
        info_label.pack(pady=(0, 10))
        
        # Фрейм для настроек со скроллбаром
        main_frame = tk.Frame(settings_window, bg=LIGHT_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Создаем canvas и scrollbar
        canvas = tk.Canvas(main_frame, bg=LIGHT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        # Настройка canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = tk.Frame(canvas, bg=LIGHT_PANE)
        
        # Пакуем виджеты
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Добавляем frame в canvas
        canvas_window = canvas.create_window((0, 0), window=canvas_frame, anchor="nw")
        
        # Обновление размеров при изменении
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        canvas_frame.bind("<Configure>", configure_scroll_region)
        
        # Прокрутка мышью
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Поля для настройки биндов
        binding_vars = {}
        
        for i in range(1, 10):
            row_frame = tk.Frame(canvas_frame, bg=LIGHT_PANE)
            row_frame.pack(fill=tk.X, pady=3, padx=10)
            
            tk.Label(row_frame, text=f"Цифра {i} (звук {i}):",
                    font=("Segoe UI", 10),
                    fg=LIGHT_TEXT, bg=LIGHT_PANE,
                    width=15, anchor=tk.W).pack(side=tk.LEFT)
            
            var = tk.StringVar(value=self.number_bindings.get(str(i), f'<Key-{i}>'))
            binding_vars[str(i)] = var
            
            entry = tk.Entry(row_frame, textvariable=var,
                           font=("Segoe UI", 10),
                           bg=LIGHT_PANE, fg=LIGHT_TEXT,
                           relief=tk.SOLID, bd=1,
                           width=25,
                           state="normal",
                           insertbackground=LIGHT_TEXT)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            
            # Фокус на первом поле
            if i == 1:
                entry.focus_set()
        
        # Кнопки управления
        button_frame = tk.Frame(settings_window, bg=LIGHT_BG)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def save_settings():
            print("Сохранение настроек биндов...")
            for num, var in binding_vars.items():
                new_binding = var.get().strip()
                print(f"Цифра {num}: '{new_binding}'")
                if new_binding:
                    self.number_bindings[num] = new_binding
            
            print(f"Все бинды: {self.number_bindings}")
            self.save_number_bindings()
            self.apply_number_bindings()
            messagebox.showinfo("Успех", "Настройки сохранены!")
            settings_window.destroy()
        
        def reset_defaults():
            for i in range(1, 10):
                binding_vars[str(i)].set(f'<Key-{i}>')
        
        # Создаем кнопки с фоном через Frame
        save_frame = tk.Frame(button_frame, bg="#48bb78", relief=tk.FLAT, bd=0)
        save_frame.pack(side=tk.LEFT, padx=(0, 15))
        save_button = tk.Button(save_frame, text="💾 Сохранить",
                              command=save_settings,
                              font=("Segoe UI", 12, "bold"),
                              bg="#48bb78", fg="WHITE",
                              relief=tk.SOLID, bd=1,
                              padx=40, pady=15,
                              cursor="hand2")
        save_button.pack(padx=3, pady=3)
        
        reset_frame = tk.Frame(button_frame, bg="#fbb6ce", relief=tk.FLAT, bd=0)
        reset_frame.pack(side=tk.LEFT, padx=10)
        reset_button = tk.Button(reset_frame, text="🔄 Сброс",
                               command=reset_defaults,
                               font=("Segoe UI", 12, "bold"),
                               bg="#fbb6ce", fg="WHITE",
                               relief=tk.SOLID, bd=1,
                               padx=40, pady=15,
                               cursor="hand2")
        reset_button.pack(padx=3, pady=3)
        
        cancel_frame = tk.Frame(button_frame, bg="#fc8181", relief=tk.FLAT, bd=0)
        cancel_frame.pack(side=tk.RIGHT)
        cancel_button = tk.Button(cancel_frame, text="❌ Отмена",
                                command=settings_window.destroy,
                                font=("Segoe UI", 12, "bold"),
                                bg="#fc8181", fg="WHITE",
                                relief=tk.SOLID, bd=1,
                                padx=40, pady=15,
                                cursor="hand2")
        cancel_button.pack(padx=3, pady=3)
    
    def load_library(self):
        """Загрузка библиотеки из JSON файла"""
        try:
            if os.path.exists(self.library_file):
                with open(self.library_file, 'r', encoding='utf-8') as f:
                    self.sound_library = json.load(f)
        except Exception as e:
            self.sound_library = {}
        
        # Загрузка плейлистов
        self.load_playlists()
    
    def save_library(self):
        """Сохранение библиотеки в JSON файл"""
        try:
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(self.sound_library, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить библиотеку: {str(e)}")
    
    def load_playlists(self):
        """Загрузка плейлистов из JSON файла"""
        try:
            if os.path.exists(self.playlists_file):
                with open(self.playlists_file, 'r', encoding='utf-8') as f:
                    self.playlists = json.load(f)
        except Exception as e:
            self.playlists = {}
    
    def save_playlists(self):
        """Сохранение плейлистов в JSON файл"""
        try:
            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить плейлисты: {str(e)}")
    
    def create_playlist(self, name):
        """Создание нового плейлиста"""
        if not name.strip():
            messagebox.showerror("Ошибка", "Введите название плейлиста")
            return
        
        if name in self.playlists:
            messagebox.showerror("Ошибка", "Плейлист с таким названием уже существует")
            return
        
        self.playlists[name] = []
        self.save_playlists()
        self.refresh_playlist_list()
        # Автоматически выбираем созданный плейлист
        self.select_playlist(name)
        messagebox.showinfo("Успех", f"Плейлист '{name}' создан")
    
    def add_to_playlist(self, playlist_name, sound_id):
        """Добавление звука в плейлист"""
        if playlist_name in self.playlists:
            if sound_id not in self.playlists[playlist_name]:
                self.playlists[playlist_name].append(sound_id)
                self.save_playlists()
                return True
        return False
    
    def remove_from_playlist(self, playlist_name, sound_id):
        """Удаление звука из плейлиста"""
        if playlist_name in self.playlists:
            if sound_id in self.playlists[playlist_name]:
                self.playlists[playlist_name].remove(sound_id)
                self.save_playlists()
                return True
        return False
    
    def delete_playlist(self, name):
        """Удаление плейлиста"""
        if name in self.playlists:
            if messagebox.askyesno("Удаление", f"Удалить плейлист '{name}'?"):
                del self.playlists[name]
                self.save_playlists()
                if self.current_playlist == name:
                    self.current_playlist = None
                    self.playlist_mode = False
                self.refresh_playlist_list()
                messagebox.showinfo("Успех", f"Плейлист '{name}' удален")
    
    def refresh_sound_list(self):
        """Обновление списка звуков"""
        # Вызываем фильтрацию (она обновит список с учетом поиска)
        self.filter_sounds()
    
    def add_sound_to_library(self):
        """Добавление звука в библиотеку"""
        file_path = filedialog.askopenfilename(
            title="Выберите аудиофайл",
            filetypes=[
                ("Аудиофайлы", "*.wav;*.mp3"),
                ("WAV файлы", "*.wav"),
                ("MP3 файлы", "*.mp3"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            print(f"Выбран файл: {file_path}")
            self.process_and_add_sound(file_path)
    
    def process_and_add_sound(self, file_path):
        """Обработка и добавление звука"""
        try:
            print(f"Обработка файла: {file_path}")
            
            # Создание папки для звуков
            if not os.path.exists(self.sounds_folder):
                os.makedirs(self.sounds_folder)
            
            # Получение информации о файле
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            print(f"Имя: {name}, расширение: {ext}")
            
            # Генерация уникального ID
            sound_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Копирование файла в папку звуков
            new_filename = f"{sound_id}{ext}"
            new_filepath = os.path.join(self.sounds_folder, new_filename)
            shutil.copy2(file_path, new_filepath)
            print(f"Файл скопирован: {new_filepath}")
            
            # Определение формата
            format_name = ext.upper().replace('.', '')
            print(f"Формат: {format_name}")
            
            # Определение длительности
            duration = "N/A"
            try:
                if ext.lower() == '.mp3':
                    # Определяем длительность MP3
                    if MUTAGEN_AVAILABLE:
                        try:
                            audio_file = MP3(file_path)
                            duration_sec = audio_file.info.length
                            minutes = int(duration_sec // 60)
                            seconds = int(duration_sec % 60)
                            duration = f"{minutes}:{seconds:02d}"
                            print(f"MP3 длительность через mutagen: {duration}")
                        except Exception as e:
                            print(f"Не удалось определить длительность MP3: {e}")
                            duration = "MP3"
                    else:
                        duration = "MP3"
                elif ext.lower() == '.wav':
                    with wave.open(file_path, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        framerate = wav_file.getframerate()
                        duration_sec = frames / framerate
                        minutes = int(duration_sec // 60)
                        seconds = int(duration_sec % 60)
                        duration = f"{minutes}:{seconds:02d}"
                        print(f"WAV файл, длительность: {duration}")
            except Exception as e:
                print(f"Не удалось определить длительность: {e}")
                duration = ext.upper().replace('.', '')
            
            # Добавление в библиотеку
            self.sound_library[sound_id] = {
                "name": name,
                "filename": new_filename,
                "format": format_name,
                "duration": duration
            }
            print(f"Добавлено в библиотеку: {self.sound_library[sound_id]}")
            
            # Сохранение и обновление
            self.save_library()
            self.refresh_sound_list()
            
            # Если в режиме плейлиста, добавляем в текущий плейлист
            if self.playlist_mode and self.current_playlist:
                if self.add_to_playlist(self.current_playlist, sound_id):
                    self.refresh_playlist_list()  # Обновляем счетчик в плейлисте
                    messagebox.showinfo("Успех", f"Звук '{name}' ({format_name}, {duration}) добавлен в плейлист '{self.current_playlist}'!")
                else:
                    messagebox.showinfo("Успех", f"Звук '{name}' ({format_name}, {duration}) добавлен в библиотеку!")
            else:
                messagebox.showinfo("Успех", f"Звук '{name}' ({format_name}, {duration}) добавлен в библиотеку!")
            
        except Exception as e:
            print(f"Ошибка при добавлении файла: {e}")
            messagebox.showerror("Ошибка", f"Не удалось добавить звук: {str(e)}")
    
    def delete_sound_from_library(self):
        """Удаление звука из библиотеки"""
        selection = self.sound_tree.selection()
        if not selection:
            return
        
        item = self.sound_tree.item(selection[0])
        sound_name = item['values'][0]
        
        # Поиск ID звука
        sound_id = None
        for sid, info in self.sound_library.items():
            if info["name"] == sound_name:
                sound_id = sid
                break
        
        if sound_id and messagebox.askyesno("Подтверждение", f"Удалить звук '{sound_name}'?"):
            try:
                # Удаление файла
                filepath = os.path.join(self.sounds_folder, self.sound_library[sound_id]["filename"])
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Удаление из библиотеки
                del self.sound_library[sound_id]
                
                # Сохранение и обновление
                self.save_library()
                self.refresh_sound_list()
                
                # Отключение кнопок
                self.delete_button.config(state=tk.DISABLED)
                self.play_button.config(state=tk.DISABLED)
                
                messagebox.showinfo("Успех", f"Звук '{sound_name}' удален из библиотеки!")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить звук: {str(e)}")
    
    def on_sound_select(self, event):
        """Обработка выбора звука"""
        selection = self.sound_tree.selection()
        if selection:
            self.play_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.finish_button.config(state=tk.DISABLED)
            
            item = self.sound_tree.item(selection[0])
            sound_name = item['values'][0]
            self.status_label.config(text=f"Выбран: {sound_name}")
        else:
            self.play_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.finish_button.config(state=tk.DISABLED)
            self.status_label.config(text="Выберите звук для воспроизведения")
    
    def stop_playback(self):
        """Остановка воспроизведения с сохранением позиции"""
        if self.is_playing:
            # Позиция сохраняется автоматически в цикле воспроизведения
            self.is_playing = False  # Это остановит цикл и сохранит текущую позицию
            self.status_label.config(text=f"⏸️ Остановлено на {self.current_position//self.sample_rate} сек")
    
    def finish_playback(self):
        """Полное завершение воспроизведения"""
        if self.is_playing:
            self.stop_all()
            # Сбрасываем позицию в начало
            self.current_position = 0
            self.status_label.config(text="✅ Воспроизведение завершено")
    
    def show_context_menu(self, event):
        """Показывает контекстное меню по правому клику"""
        # Выбираем элемент под курсором
        item = self.sound_tree.identify_row(event.y)
        if item:
            self.sound_tree.selection_set(item)
            
            # Обновляем подменю плейлистов
            self.update_playlist_submenu()
            
            self.context_menu.post(event.x_root, event.y_root)
    
    def update_playlist_submenu(self):
        """Обновление подменю плейлистов в контекстном меню"""
        # Очистка подменю
        self.playlist_submenu.delete(0, tk.END)
        
        if not self.playlists:
            self.playlist_submenu.add_command(label="Нет плейлистов", state=tk.DISABLED)
        else:
            # Получаем ID выбранного звука
            selection = self.sound_tree.selection()
            if selection:
                item = self.sound_tree.item(selection[0])
                sound_name = item['values'][0]
                
                # Находим ID звука
                sound_id = None
                for sid, info in self.sound_library.items():
                    if info["name"] == sound_name:
                        sound_id = sid
                        break
                
                if sound_id:
                    # Добавляем плейлисты в подменю
                    for playlist_name in self.playlists.keys():
                        # Проверяем, есть ли уже звук в плейлисте
                        is_in_playlist = sound_id in self.playlists[playlist_name]
                        
                        if is_in_playlist:
                            # Если звук уже в плейлисте, показываем это
                            self.playlist_submenu.add_command(
                                label=f"✓ {playlist_name}", 
                                state=tk.DISABLED
                            )
                        else:
                            # Если звука нет в плейлисте, добавляем команду для добавления
                            self.playlist_submenu.add_command(
                                label=playlist_name,
                                command=lambda name=playlist_name, sid=sound_id: self.add_sound_to_playlist_context(name, sid)
                            )
    
    def rename_sound(self):
        """Переименовывает выбранный звук"""
        selection = self.sound_tree.selection()
        if not selection:
            return
        
        item = self.sound_tree.item(selection[0])
        old_name = item['values'][0]
        
        # Создаем диалоговое окно для ввода нового имени
        dialog = tk.Toplevel(self.root)
        dialog.title("Переименование звука")
        dialog.geometry("300x120")
        dialog.configure(bg=LIGHT_PANE)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрирование окна
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Поле ввода
        tk.Label(dialog, text="Новое название:", font=("Segoe UI", 11), 
                fg=LIGHT_TEXT, bg=LIGHT_PANE).pack(pady=(20, 5))
        
        entry = tk.Entry(dialog, font=("Segoe UI", 11), bg=LIGHT_PANE, fg=LIGHT_TEXT)
        entry.pack(padx=20, fill=tk.X)
        entry.insert(0, old_name)
        entry.select_range(0, tk.END)
        entry.focus_set()
        
        # Кнопки
        btn_frame = tk.Frame(dialog, bg=LIGHT_PANE)
        btn_frame.pack(pady=20)
        
        def save_rename():
            new_name = entry.get().strip()
            if new_name and new_name != old_name:
                # Поиск ID звука
                for sound_id, info in self.sound_library.items():
                    if info["name"] == old_name:
                        info["name"] = new_name
                        self.save_library()
                        self.refresh_sound_list()
                        break
            
            dialog.destroy()
        
        def cancel_rename():
            dialog.destroy()
        
        save_button = tk.Button(btn_frame, text="Сохранить", font=("Segoe UI", 10, "bold"),
                               bg=LIGHT_SUCCESS, fg="white", relief=tk.FLAT, bd=0, padx=15, pady=5,
                               command=save_rename)
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = tk.Button(btn_frame, text="Отмена", font=("Segoe UI", 10),
                                bg=LIGHT_BORDER, fg=LIGHT_TEXT, relief=tk.FLAT, bd=0, padx=15, pady=5,
                                command=cancel_rename)
        cancel_button.pack(side=tk.LEFT)
        
        entry.bind('<Return>', lambda e: save_rename())
        entry.bind('<Escape>', lambda e: cancel_rename())
        
        # Позиционирование курсора
        cursor = "hand2"
        save_button.config(cursor=cursor)
        cancel_button.config(cursor=cursor)
    
    def add_sound_to_playlist_context(self, playlist_name, sound_id):
        """Добавление звука в плейлист через контекстное меню"""
        if self.add_to_playlist(playlist_name, sound_id):
            sound_name = self.sound_library[sound_id]["name"]
            messagebox.showinfo("Успех", f"'{sound_name}' добавлен в плейлист '{playlist_name}'")
            self.refresh_playlist_list()
            # Если мы в режиме плейлиста, обновляем список звуков
            if self.playlist_mode and self.current_playlist == playlist_name:
                self.filter_sounds()
    
    def play_selected_sound(self):
        """Воспроизведение выбранного звука"""
        selection = self.sound_tree.selection()
        if not selection:
            return
        
        item = self.sound_tree.item(selection[0])
        sound_name = item['values'][0]
        
        # Поиск ID звука
        sound_id = None
        for sid, info in self.sound_library.items():
            if info["name"] == sound_name:
                sound_id = sid
                break
        
        if sound_id:
            # Сбрасываем позицию только при выборе другого звука
            if self.current_sound_id != sound_id:
                self.current_position = 0
                print(f"Выбран новый звук, позиция сброшена в 0")
            else:
                print(f"Выбран тот же звук, позиция сохранена: {self.current_position}")
            
            self.current_sound_id = sound_id
            filepath = os.path.join(self.sounds_folder, self.sound_library[sound_id]["filename"])
            self.load_file(filepath)
            if self.current_audio_data is not None:
                self.play_audio()
    
    def load_file(self, file_path):
        """Загрузка аудиофайла"""
        try:
            self.current_file = file_path
            
            # Определение формата файла
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.wav':
                # Загрузка WAV файла
                with wave.open(file_path, 'rb') as wav_file:
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    framerate = wav_file.getframerate()
                    frames = wav_file.readframes(-1)
                    
                    print(f"WAV info: каналы={channels}, бит={sample_width*8}, частота={framerate}, фреймы={len(frames)//(channels*sample_width)}")
                    
                    # Конвертация в numpy array
                    dtype = np.int16 if sample_width == 2 else np.int8
                    audio_data = np.frombuffer(frames, dtype=dtype)
                    
                    if channels == 2:
                        audio_data = audio_data.reshape(-1, 2)
                    
                    self.current_audio_data = audio_data.astype(np.float32) / 32768.0
                    self.sample_rate = framerate
                    self.total_samples = len(audio_data)  # Сохраняем общее количество сэмплов
                    
                    duration = len(frames) / (framerate * channels * sample_width)
                    print(f"Загружено {len(audio_data)} сэмплов, длительность {duration:.2f} сек")
                    
            elif ext == '.mp3':
                # Загрузка MP3 файла
                try:
                    if PYDUB_AVAILABLE:
                        # Используем pydub для загрузки MP3
                        audio = AudioSegment.from_mp3(file_path)
                        
                        # Конвертируем в numpy array
                        samples = np.array(audio.get_array_of_samples())
                        
                        if audio.channels == 2:
                            samples = samples.reshape(-1, 2)
                        
                        self.current_audio_data = samples.astype(np.float32) / 32768.0
                        self.sample_rate = audio.frame_rate
                        self.total_samples = len(samples)
                        
                        duration = len(audio) / 1000.0  # pydub работает с миллисекундами
                        print(f"MP3 загружен через pydub: каналы={audio.channels}, частота={audio.frame_rate}, длительность={duration:.2f} сек")
                        
                    elif MUTAGEN_AVAILABLE:
                        # Используем mutagen для получения информации
                        mp3_file = MP3(file_path)
                        duration_sec = mp3_file.info.length
                        
                        # Простая загрузка через audiofile (если доступен)
                        try:
                            import audiofile
                            af = audiofile.AudioFile(file_path)
                            samples = af.read()
                            if af.channels == 2:
                                samples = samples.T
                            
                            self.current_audio_data = samples.astype(np.float32) / 32768.0
                            self.sample_rate = af.samplerate
                            self.total_samples = len(samples)
                            
                            print(f"MP3 загружен через audiofile: каналы={af.channels}, частота={af.samplerate}, длительность={duration_sec:.2f} сек")
                        except ImportError:
                            # Если audiofile недоступен, показываем ошибку
                            messagebox.showerror("Ошибка", "Для загрузки MP3 файлов требуется pydub или audiofile.\nУстановите: pip install pydub")
                            return
                    else:
                        messagebox.showerror("Ошибка", "Для загрузки MP3 файлов требуется mutagen.\nУстановите: pip install mutagen")
                        return
                        
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить MP3 файл: {str(e)}")
                    return
            
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат файла")
                return
            
            # Обновление информации
            filename = os.path.basename(file_path)
            # self.info_label.config(text=f"Загружен: {filename}")  # Убрали так как info_label больше нет
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
            self.current_audio_data = None
    
    def play_audio(self):
        """Воспроизведение аудио"""
        if self.current_audio_data is None:
            return
        
        try:
            # Остановка предыдущего воспроизведения
            self.stop_all()
            
            self.is_playing = True
            self.start_time = time.time()  # Запоминаем время начала
            
            # Воспроизведение в отдельном потоке
            self.playback_thread = threading.Thread(target=self.play_audio_simple, daemon=True)
            self.playback_thread.start()
            
            # Обновление интерфейса
            self.play_button.config(state=tk.DISABLED)  # Отключаем воспроизведение
            self.stop_button.config(state=tk.NORMAL)   # Активируем стоп
            self.finish_button.config(state=tk.NORMAL)  # Активируем закончить
            
            if self.current_position > 0:
                self.status_label.config(text=f"Воспроизведение с позиции {self.current_position//self.sample_rate} сек...")
            else:
                self.status_label.config(text="Воспроизведение...")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось начать воспроизведение: {str(e)}")
            self.is_playing = False
    
    def play_audio_simple(self):
        """Простое воспроизведение аудио"""
        try:
            # Воспроизводим с текущей позиции
            start_pos = self.current_position
            remaining_samples = self.total_samples - start_pos
            
            if remaining_samples <= 0:
                # Если дошли до конца, начинаем с начала
                start_pos = 0
                self.current_position = 0
                remaining_samples = self.total_samples
            
            print(f"Начинаем воспроизведение с позиции {start_pos} ({start_pos//self.sample_rate} сек)")
            
            # Берем сэмплы с текущей позиции
            audio_to_play = self.current_audio_data[start_pos:]
            
            # Запоминаем точное время начала воспроизведения
            actual_start_time = time.time()
            
            # Воспроизведение через sounddevice
            sd.play(audio_to_play, self.sample_rate)
            
            # Ожидание завершения или остановки
            natural_finish = True  # Флаг естественного завершения
            
            while self.is_playing:
                time.sleep(0.1)
                if not sd.get_stream().active:
                    break
                
                # Обновляем текущую позицию для точного стопа
                elapsed = time.time() - actual_start_time
                self.current_position = start_pos + int(elapsed * self.sample_rate)
                
                # Ограничиваем позицию чтобы не выйти за пределы
                if self.current_position >= self.total_samples:
                    self.current_position = self.total_samples
                    break
            
            if not self.is_playing:
                sd.stop()
                natural_finish = False  # Ручная остановка
                print(f"Ручная остановка на позиции {self.current_position} ({self.current_position//self.sample_rate} сек)")
                # Не вызываем playback_finished() для ручной остановки
                self.root.after(0, self.update_buttons_after_stop)
            else:
                # Если воспроизведение завершилось естественным образом
                self.current_position = 0  # Сбрасываем позицию
                natural_finish = True
                print("Естественное завершение воспроизведения")
            
            # Вызываем playback_finished() только при естественном завершении
            if natural_finish:
                self.root.after(0, self.playback_finished)
            
        except Exception as e:
            print(f"Ошибка в play_audio_simple: {e}")
            self.root.after(0, lambda: messagebox.showerror("Ошибка воспроизведения", str(e)))
            self.is_playing = False
            self.root.after(0, lambda: self.play_button.config(state=tk.NORMAL))  # Включаем воспроизведение
    
    def update_buttons_after_stop(self):
        """Обновление кнопок после ручной остановки"""
        self.play_button.config(state=tk.NORMAL)   # Включаем воспроизведение
        self.stop_button.config(state=tk.DISABLED)  # Отключаем стоп
        self.finish_button.config(state=tk.DISABLED)  # Отключаем закончить
    
    def playback_finished(self):
        """Завершение воспроизведения"""
        if not self.is_playing:
            self.play_button.config(state=tk.NORMAL)   # Включаем воспроизведение
            self.stop_button.config(state=tk.DISABLED)  # Отключаем стоп
            self.finish_button.config(state=tk.DISABLED)  # Отключаем закончить
            self.status_label.config(text="✅ Воспроизведение завершено")
    
    def stop_all(self):
        """Остановка всего воспроизведения"""
        try:
            # Остановка simpleaudio
            if self.current_playback_obj:
                self.current_playback_obj.stop()
                self.current_playback_obj = None
            
            # Остановка sounddevice
            sd.stop()
            
        except Exception as e:
            pass
        
        # Сброс состояний
        self.is_playing = False
        self.is_paused = False
        
        # Обновление интерфейса
        self.play_button.config(state=tk.NORMAL)   # Включаем воспроизведение
        self.stop_button.config(state=tk.DISABLED)  # Отключаем стоп
        self.finish_button.config(state=tk.DISABLED)  # Отключаем закончить
    
    def setup_audio_stream(self):
        """Настройка аудио потока"""
        try:
            devices = sd.query_devices()
            print(f"Доступные аудиоустройства: {len(devices)}")
        except Exception as e:
            print(f"Ошибка настройки аудио: {e}")
    
    def filter_sounds(self, *args):
        """Фильтрация звуков по поисковому запросу"""
        search_term = self.search_var.get().lower().strip()
        
        # Очистка дерева
        for item in self.sound_tree.get_children():
            self.sound_tree.delete(item)
        
        # Определение источника звуков (библиотека или плейлист)
        if self.playlist_mode and self.current_playlist:
            # Режим плейлиста - показываем только звуки из плейлиста
            if self.current_playlist in self.playlists:
                playlist_sound_ids = self.playlists[self.current_playlist]
                filtered_count = 0
                
                for sound_id in playlist_sound_ids:
                    if sound_id in self.sound_library:
                        info = self.sound_library[sound_id]
                        sound_name = info["name"].lower()
                        sound_format = info.get("format", "").lower()
                        
                        # Проверка совпадения по названию или формату
                        if not search_term or search_term in sound_name or search_term in sound_format:
                            self.sound_tree.insert("", tk.END, values=(
                                info["name"],
                                info.get("duration", "N/A"),
                                info.get("format", "N/A")
                            ))
                            filtered_count += 1
                
                # Обновление статуса
                if search_term:
                    self.status_label.config(text=f"🔍 Плейлист '{self.current_playlist}': {filtered_count} звуков")
                else:
                    self.status_label.config(text=f"🎵 Плейлист: {self.current_playlist}")
        else:
            # Режим библиотеки - показываем все звуки
            filtered_count = 0
            for sound_id, info in self.sound_library.items():
                sound_name = info["name"].lower()
                sound_format = info.get("format", "").lower()
                
                # Проверка совпадения по названию или формату
                if not search_term or search_term in sound_name or search_term in sound_format:
                    self.sound_tree.insert("", tk.END, values=(
                        info["name"],
                        info.get("duration", "N/A"),
                        info.get("format", "N/A")
                    ))
                    filtered_count += 1
            
            # Обновление статуса
            if search_term:
                self.status_label.config(text=f"🔍 Найдено: {filtered_count} звуков")
            else:
                self.status_label.config(text="📂 Ваша библиотека")
    
    def clear_search(self):
        """Очистка поля поиска"""
        self.search_var.set("")
        self.search_entry.focus_set()
    
    def refresh_playlist_list(self):
        """Обновление списка плейлистов"""
        # Очистка текущих виджетов
        for widget in self.playlist_frame_inner.winfo_children():
            widget.destroy()
        
        if not self.playlists:
            no_playlist_label = tk.Label(self.playlist_frame_inner, 
                                        text="Нет плейлистов. Создайте новый плейлист.",
                                        font=("Segoe UI", 10),
                                        fg=LIGHT_TEXT_SECONDARY, bg=LIGHT_PANE)
            no_playlist_label.pack(pady=4)
            return
        
        # Создание кнопок для каждого плейлиста
        for playlist_name in self.playlists.keys():
            playlist_item_frame = tk.Frame(self.playlist_frame_inner, bg=LIGHT_PANE)
            playlist_item_frame.pack(fill=tk.X, pady=2)
            
            # Кнопка плейлиста
            playlist_btn = tk.Button(playlist_item_frame, 
                                   text=f"🎵 {playlist_name} ({len(self.playlists[playlist_name])})",
                                   font=("Segoe UI", 10),
                                   bg=LIGHT_ACCENT if self.current_playlist == playlist_name else LIGHT_BORDER,
                                   fg="white" if self.current_playlist == playlist_name else LIGHT_TEXT,
                                   relief=tk.FLAT, bd=0,
                                   anchor=tk.W,
                                   command=lambda name=playlist_name: self.select_playlist(name))
            playlist_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
            
            # Кнопка удаления
            delete_btn = tk.Button(playlist_item_frame, text="🗑️",
                                  font=("Segoe UI", 8),
                                  bg=LIGHT_DANGER, fg="white",
                                  relief=tk.FLAT, bd=0, padx=6, pady=2,
                                  command=lambda name=playlist_name: self.delete_playlist(name))
            delete_btn.pack(side=tk.RIGHT)
    
    def select_playlist(self, name):
        """Выбор плейлиста"""
        self.current_playlist = name
        self.playlist_mode = True
        # Обновляем кнопку режима плейлиста
        self.playlist_mode_btn.config(bg=LIGHT_ACCENT, fg="white", text="🔂 В плейлисте")
        self.refresh_playlist_list()
        self.filter_sounds()  # Обновить список звуков
        self.status_label.config(text=f"🎵 Плейлист: {name}")
    
    def toggle_playlist_mode(self):
        """Переключение режима плейлиста"""
        if self.playlist_mode:
            self.playlist_mode = False
            self.current_playlist = None
            self.playlist_mode_btn.config(bg=LIGHT_BORDER, fg=LIGHT_TEXT_SECONDARY, text="🔂 Режим плейлиста")
            self.status_label.config(text="📂 Ваша библиотека")
        else:
            if self.playlists:
                # Если есть плейлисты, выбираем первый
                first_playlist = list(self.playlists.keys())[0]
                self.select_playlist(first_playlist)
            else:
                messagebox.showinfo("Информация", "Сначала создайте плейлист")
                return
        
        self.refresh_playlist_list()
        self.filter_sounds()
    
    def show_create_playlist_dialog(self):
        """Показать диалог создания плейлиста"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый плейлист")
        dialog.geometry("450x180")  # Сделал окно выше по высоте (180 вместо 150)
        dialog.configure(bg=LIGHT_PANE)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрирование окна
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Поле ввода названия
        tk.Label(dialog, text="Название плейлиста:", 
                font=("Segoe UI", 12), fg=LIGHT_TEXT, bg=LIGHT_PANE).pack(pady=(30, 10))
        
        name_entry = tk.Entry(dialog, font=("Segoe UI", 12), bg=LIGHT_PANE, fg=LIGHT_TEXT)
        name_entry.pack(padx=30, fill=tk.X)
        name_entry.focus_set()
        
        # Кнопки
        btn_frame = tk.Frame(dialog, bg=LIGHT_PANE)
        btn_frame.pack(pady=30)
        
        def create():
            name = name_entry.get().strip()
            if name:
                self.create_playlist(name)
                dialog.destroy()
        
        tk.Button(btn_frame, text="Создать", font=("Segoe UI", 11, "bold"),
                 bg=LIGHT_SUCCESS, fg="white", relief=tk.FLAT, bd=0, padx=20, pady=8,
                 command=create).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(btn_frame, text="Отмена", font=("Segoe UI", 11),
                 bg=LIGHT_BORDER, fg=LIGHT_TEXT, relief=tk.FLAT, bd=0, padx=20, pady=8,
                 command=dialog.destroy).pack(side=tk.LEFT)
        
        name_entry.bind('<Return>', lambda e: create())

if __name__ == "__main__":
    root = tk.Tk()
    app = EchoBox(root)
    root.mainloop()
