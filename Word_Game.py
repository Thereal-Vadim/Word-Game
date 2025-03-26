import json
import random
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.clock import Clock
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Регистрация шрифта SF-Pro
LabelBase.register(name='SFPro', fn_regular='SF-Pro.ttf')

# Установка начального фона (будет меняться в зависимости от темы)
Window.clearcolor = (1, 1, 1, 1)  # Белый фон по умолчанию (светлая тема)

# Установка разрешения iPhone 14 Pro
Window.size = (390, 844)

# Загрузка базы слов
try:
    with open("words.json", "r", encoding="utf-8") as f:
        WORD_DATABASE = json.load(f)
    logger.info("База слов успешно загружена")
except FileNotFoundError:
    logger.error("Файл words.json не найден. Создайте его с корректной структурой.")
    exit(1)
except json.JSONDecodeError:
    logger.error("Ошибка в структуре words.json. Проверьте синтаксис.")
    exit(1)

# Путь для сохранения прогресса и настроек
PROGRESS_FILE = "progress.json"
DIFFICULT_WORDS_FILE = "difficult_words.json"
SETTINGS_FILE = "settings.json"


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация MainMenuScreen")
        self.layout = BoxLayout(orientation="vertical", padding=50, spacing=20)

        self.layout.add_widget(Button(text="Играть", font_size=24, font_name='SFPro',
                                      size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                      on_press=self.go_to_map))
        self.layout.add_widget(Button(text="Словарь", font_size=24, font_name='SFPro',
                                      size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                      on_press=self.go_to_dictionary))
        self.layout.add_widget(Button(text="Настройки", font_size=24, font_name='SFPro',
                                      size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                      on_press=self.go_to_settings))
        self.add_widget(self.layout)
        self.apply_theme()
        logger.debug("MainMenuScreen полностью инициализирован")

    def apply_theme(self):
        settings = self.load_settings()
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Тёмный фон
            for child in self.layout.children:
                if isinstance(child, Button):
                    child.color = (1, 1, 1, 1)  # Белый текст для кнопок
        else:
            Window.clearcolor = (1, 1, 1, 1)  # Светлый фон
            for child in self.layout.children:
                if isinstance(child, Button):
                    child.color = (0, 0, 0, 1)  # Чёрный текст для кнопок

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Файл settings.json не найден, создаём новый")
        return {"timer_duration": 30, "language": "ru", "sound_enabled": True, "theme": "light"}

    def go_to_map(self, *args):
        logger.debug("Переход на экран карты")
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "map"

    def go_to_dictionary(self, *args):
        logger.debug("Переход на экран словаря")
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "dictionary"

    def go_to_settings(self, *args):
        logger.debug("Переход на экран настроек")
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "settings"


class MapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация MapScreen")
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        self.current_cefr_level = "A1"
        self.completed_sub_levels = self.load_progress().get("completed_sub_levels", {})

        self.title_label = Label(text="Карта уровней", font_size=32, font_name='SFPro', color=(0, 0, 0, 1))
        self.layout.add_widget(self.title_label)
        self.map_layout = GridLayout(cols=5, spacing=10, size_hint=(1, 0.8))

        for sub_level in range(1, 11):
            stars = self.completed_sub_levels.get(self.current_cefr_level, {}).get(str(sub_level), 0)
            btn_text = f"{sub_level}\n{'★' * stars}{'☆' * (3 - stars)}" if stars > 0 else str(sub_level)
            is_locked = not self.is_sub_level_unlocked(sub_level)
            btn = Button(text=btn_text, font_size=20, font_name='SFPro',
                         disabled=is_locked,
                         on_press=lambda x, sl=sub_level: self.start_game(sl))
            self.map_layout.add_widget(btn)

        self.layout.add_widget(self.map_layout)

        self.back_button = Button(text="Назад", font_size=20, font_name='SFPro',
                                  size_hint=(1, 0.1), on_press=self.go_back)
        self.layout.add_widget(self.back_button)
        self.add_widget(self.layout)
        self.apply_theme()
        self.update_map()
        logger.debug("MapScreen полностью инициализирован")

    def load_progress(self):
        try:
            if os.path.exists(PROGRESS_FILE):
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info("Прогресс успешно загружен")
                    return data
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Ошибка загрузки прогресса, используется стандартный")
        return {"current_cefr_level": "A1", "completed_sub_levels": {}}

    def save_progress(self):
        try:
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "current_cefr_level": self.current_cefr_level,
                    "completed_sub_levels": self.completed_sub_levels
                }, f, ensure_ascii=False, indent=4)
            logger.info("Прогресс сохранён")
        except Exception as e:
            logger.error(f"Ошибка сохранения прогресса: {e}")

    def apply_theme(self):
        settings = self.load_settings()
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Тёмный фон
            self.title_label.color = (1, 1, 1, 1)  # Белый текст для заголовка
            self.back_button.color = (1, 1, 1, 1)  # Белый текст для кнопки
            for btn in self.map_layout.children:
                btn.color = (1, 1, 1, 1)  # Белый текст для кнопок подуровней
        else:
            Window.clearcolor = (1, 1, 1, 1)  # Светлый фон
            self.title_label.color = (0, 0, 0, 1)  # Чёрный текст для заголовка
            self.back_button.color = (0, 0, 0, 1)  # Чёрный текст для кнопки
            for btn in self.map_layout.children:
                btn.color = (0, 0, 0, 1)  # Чёрный текст для кнопок подуровней

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Файл settings.json не найден, создаём новый")
        return {"timer_duration": 30, "language": "ru", "sound_enabled": True, "theme": "light"}

    def update_map(self):
        self.map_layout.clear_widgets()
        for sub_level in range(1, 11):
            try:
                stars = self.completed_sub_levels.get(self.current_cefr_level, {}).get(str(sub_level), 0)
                btn_text = f"{sub_level}\n{'★' * stars}{'☆' * (3 - stars)}" if stars > 0 else str(sub_level)
                is_locked = not self.is_sub_level_unlocked(sub_level)
                btn = Button(text=btn_text, font_size=20, font_name='SFPro',
                             disabled=is_locked,
                             on_press=lambda x, sl=sub_level: self.start_game(sl))
                self.map_layout.add_widget(btn)
            except Exception as e:
                logger.error(f"Ошибка при обновлении карты для подуровня {sub_level}: {e}")
        self.apply_theme()  # Применяем тему после обновления карты

    def is_sub_level_unlocked(self, sub_level):
        if sub_level == 1:
            return True
        prev_sub_level = sub_level - 1
        return str(prev_sub_level) in self.completed_sub_levels.get(self.current_cefr_level, {})

    def start_game(self, sub_level):
        logger.debug(f"Запуск игры для подуровня {sub_level}")
        game_screen = self.manager.get_screen("game")
        game_screen.setup_game(self.current_cefr_level, sub_level)  # Вызываем setup_game
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "game"

    def go_back(self, *args):
        logger.debug("Возврат на главное меню")
        logger.debug(f"[Текущий экран] {self.manager.current}")
        logger.debug(f"[Все экраны] {list(self.manager.screen_names)}")
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "main_menu"
        logger.debug(f"[Новый текущий экран] {self.manager.current}")


class DictionaryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация DictionaryScreen")
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        self.title_label = Label(text="Словарь", font_size=32, font_name='SFPro', color=(0, 0, 0, 1))
        self.layout.add_widget(self.title_label)

        # Панель фильтров
        self.filter_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.sub_level_spinner = Spinner(
            text="Все подуровни",
            values=["Все подуровни"] + [f"Подуровень {i}" for i in range(1, 11)],
            size_hint=(0.5, 1),
            font_name='SFPro'
        )
        self.sub_level_spinner.bind(text=self.update_word_list)
        self.difficult_only_checkbox = CheckBox(size_hint=(0.1, 1))
        self.difficult_only_checkbox.bind(active=self.update_word_list)
        self.filter_label = Label(text="Только сложные", font_size=16, font_name='SFPro', color=(0, 0, 0, 1))
        self.filter_layout.add_widget(self.sub_level_spinner)
        self.filter_layout.add_widget(self.filter_label)
        self.filter_layout.add_widget(self.difficult_only_checkbox)
        self.layout.add_widget(self.filter_layout)

        # Создаём ScrollView для списка слов
        self.scroll_view = ScrollView(size_hint=(1, 0.7))
        self.word_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.word_list.bind(minimum_height=self.word_list.setter('height'))
        self.scroll_view.add_widget(self.word_list)
        self.layout.add_widget(self.scroll_view)

        self.back_button = Button(text="Назад", font_size=20, font_name='SFPro',
                                  size_hint=(1, 0.1), on_press=self.go_back)
        self.layout.add_widget(self.back_button)

        self.add_widget(self.layout)

        self.difficult_words = self.load_difficult_words()
        self.load_words()
        self.apply_theme()
        logger.debug("DictionaryScreen полностью инициализирован")

    def load_difficult_words(self):
        try:
            if os.path.exists(DIFFICULT_WORDS_FILE):
                with open(DIFFICULT_WORDS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Файл difficult_words.json не найден, создаём новый")
        return {}

    def save_difficult_words(self):
        try:
            with open(DIFFICULT_WORDS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.difficult_words, f, ensure_ascii=False, indent=4)
            logger.info("Список сложных слов сохранён")
        except Exception as e:
            logger.error(f"Ошибка сохранения сложных слов: {e}")

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Файл settings.json не найден, создаём новый")
        return {"timer_duration": 30, "language": "ru", "sound_enabled": True, "theme": "light"}

    def apply_theme(self):
        settings = self.load_settings()
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Тёмный фон
            self.title_label.color = (1, 1, 1, 1)  # Белый текст для заголовка
            self.filter_label.color = (1, 1, 1, 1)  # Белый текст для метки фильтра
            self.sub_level_spinner.color = (1, 1, 1, 1)  # Белый текст для спиннера
            self.back_button.color = (1, 1, 1, 1)  # Белый текст для кнопки
            for child in self.word_list.children:
                for widget in child.children:
                    if isinstance(widget, Label):
                        widget.color = (1, 1, 1, 1)  # Белый текст для слов
        else:
            Window.clearcolor = (1, 1, 1, 1)  # Светлый фон
            self.title_label.color = (0, 0, 0, 1)  # Чёрный текст для заголовка
            self.filter_label.color = (0, 0, 0, 1)  # Чёрный текст для метки фильтра
            self.sub_level_spinner.color = (0, 0, 0, 1)  # Чёрный текст для спиннера
            self.back_button.color = (0, 0, 0, 1)  # Чёрный текст для кнопки
            for child in self.word_list.children:
                for widget in child.children:
                    if isinstance(widget, Label):
                        widget.color = (0, 0, 0, 1)  # Чёрный текст для слов

    def load_words(self):
        # Загружаем прогресс, чтобы узнать, какие подуровни пройдены
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                progress = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            progress = {"current_cefr_level": "A1", "completed_sub_levels": {}}

        self.completed_sub_levels = progress.get("completed_sub_levels", {}).get("A1", {})
        self.update_word_list()

    def update_word_list(self, *args):
        self.word_list.clear_widgets()
        if not self.completed_sub_levels:
            self.word_list.add_widget(
                Label(text="Вы ещё не прошли ни одного подуровня!", font_size=20, font_name='SFPro', color=(0, 0, 0, 1),
                      size_hint_y=None, height=40))
            self.apply_theme()  # Применяем тему после добавления текста
            return

        selected_sub_level = self.sub_level_spinner.text
        show_difficult_only = self.difficult_only_checkbox.active

        # Определяем, какие подуровни отображать
        sub_levels_to_show = self.completed_sub_levels.keys()
        if selected_sub_level != "Все подуровни":
            sub_level_num = selected_sub_level.split()[-1]
            sub_levels_to_show = [sub_level_num] if sub_level_num in self.completed_sub_levels else []

        # Загружаем слова
        settings = self.load_settings()
        language = settings.get("language", "ru")
        for sub_level in sub_levels_to_show:
            try:
                words = WORD_DATABASE["A1"][sub_level]["words"]
                for word_data in words:
                    word_key = f"A1_{sub_level}_{word_data['translations']['ru']}"
                    if show_difficult_only and word_key not in self.difficult_words:
                        continue

                    # Создаём строку для слова
                    word_row = BoxLayout(size_hint_y=None, height=40, spacing=10)
                    word_label = Label(
                        text=f"{word_data['translations'][language]} - {word_data['definitions'][language]}",
                        font_size=18, font_name='SFPro', color=(0, 0, 0, 1),
                        halign="left", text_size=(300, None)
                    )
                    difficult_checkbox = CheckBox(active=word_key in self.difficult_words)
                    difficult_checkbox.bind(active=lambda cb, value, wk=word_key: self.toggle_difficult_word(wk, value))
                    word_row.add_widget(word_label)
                    word_row.add_widget(difficult_checkbox)
                    self.word_list.add_widget(word_row)
            except KeyError as e:
                logger.error(f"Ошибка при загрузке слов для подуровня {sub_level}: {e}")
        self.apply_theme()  # Применяем тему после обновления списка слов

    def toggle_difficult_word(self, word_key, value):
        if value:
            self.difficult_words[word_key] = True
        else:
            self.difficult_words.pop(word_key, None)
        self.save_difficult_words()
        logger.debug(f"[Слово {word_key} помечено как сложное] {value}")

    def go_back(self, *args):
        logger.debug("Возврат на главное меню")
        logger.debug(f"[Текущий экран] {self.manager.current}")
        logger.debug(f"[Все экраны] {list(self.manager.screen_names)}")
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "main_menu"
        logger.debug(f"[Новый текущий экран] {self.manager.current}")


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация SettingsScreen")
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        self.title_label = Label(text="Настройки", font_size=32, font_name='SFPro', color=(0, 0, 0, 1))
        self.layout.add_widget(self.title_label)

        # Загружаем настройки
        self.settings = self.load_settings()

        # Настройка времени таймера
        self.timer_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.timer_label = Label(text="Время на слово (сек):", font_size=20, font_name='SFPro', color=(0, 0, 0, 1))
        self.timer_spinner = Spinner(
            text=str(self.settings.get("timer_duration", 30)),
            values=["15", "30", "45"],
            size_hint=(0.3, 1),
            font_name='SFPro'
        )
        self.timer_spinner.bind(text=self.update_timer_setting)
        self.timer_layout.add_widget(self.timer_label)
        self.timer_layout.add_widget(self.timer_spinner)
        self.layout.add_widget(self.timer_layout)

        # Настройка языка
        self.language_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.language_label = Label(text="Язык:", font_size=20, font_name='SFPro', color=(0, 0, 0, 1))
        self.language_spinner = Spinner(
            text=self.settings.get("language", "ru"),
            values=["ru", "en"],
            size_hint=(0.3, 1),
            font_name='SFPro'
        )
        self.language_spinner.bind(text=self.update_language_setting)
        self.language_layout.add_widget(self.language_label)
        self.language_layout.add_widget(self.language_spinner)
        self.layout.add_widget(self.language_layout)

        # Настройка звука
        self.sound_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.sound_label = Label(text="Звук:", font_size=20, font_name='SFPro', color=(0, 0, 0, 1))
        self.sound_checkbox = CheckBox(active=self.settings.get("sound_enabled", True))
        self.sound_checkbox.bind(active=self.update_sound_setting)
        self.sound_layout.add_widget(self.sound_label)
        self.sound_layout.add_widget(self.sound_checkbox)
        self.layout.add_widget(self.sound_layout)

        # Настройка темы
        self.theme_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.theme_label = Label(text="Тема:", font_size=20, font_name='SFPro', color=(0, 0, 0, 1))
        self.theme_spinner = Spinner(
            text=self.settings.get("theme", "light"),
            values=["light", "dark"],
            size_hint=(0.3, 1),
            font_name='SFPro'
        )
        self.theme_spinner.bind(text=self.update_theme_setting)
        self.theme_layout.add_widget(self.theme_label)
        self.theme_layout.add_widget(self.theme_spinner)
        self.layout.add_widget(self.theme_layout)

        self.back_button = Button(text="Назад", font_size=20, font_name='SFPro',
                                  size_hint=(1, 0.1), on_press=self.go_back)
        self.layout.add_widget(self.back_button)
        self.add_widget(self.layout)
        self.apply_theme()
        logger.debug("SettingsScreen полностью инициализирован")

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Файл settings.json не найден, создаём новый")
        return {"timer_duration": 30, "language": "ru", "sound_enabled": True, "theme": "light"}

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            logger.info("Настройки сохранены")
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")

    def apply_theme(self):
        theme = self.settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Тёмный фон
            self.title_label.color = (1, 1, 1, 1)  # Белый текст для заголовка
            self.timer_label.color = (1, 1, 1, 1)  # Белый текст для метки таймера
            self.timer_spinner.color = (1, 1, 1, 1)  # Белый текст для спиннера таймера
            self.language_label.color = (1, 1, 1, 1)  # Белый текст для метки языка
            self.language_spinner.color = (1, 1, 1, 1)  # Белый текст для спиннера языка
            self.sound_label.color = (1, 1, 1, 1)  # Белый текст для метки звука
            self.theme_label.color = (1, 1, 1, 1)  # Белый текст для метки темы
            self.theme_spinner.color = (1, 1, 1, 1)  # Белый текст для спиннера темы
            self.back_button.color = (1, 1, 1, 1)  # Белый текст для кнопки
        else:
            Window.clearcolor = (1, 1, 1, 1)  # Светлый фон
            self.title_label.color = (0, 0, 0, 1)  # Чёрный текст для заголовка
            self.timer_label.color = (0, 0, 0, 1)  # Чёрный текст для метки таймера
            self.timer_spinner.color = (0, 0, 0, 1)  # Чёрный текст для спиннера таймера
            self.language_label.color = (0, 0, 0, 1)  # Чёрный текст для метки языка
            self.language_spinner.color = (0, 0, 0, 1)  # Чёрный текст для спиннера языка
            self.sound_label.color = (0, 0, 0, 1)  # Чёрный текст для метки звука
            self.theme_label.color = (0, 0, 0, 1)  # Чёрный текст для метки темы
            self.theme_spinner.color = (0, 0, 0, 1)  # Чёрный текст для спиннера темы
            self.back_button.color = (0, 0, 0, 1)  # Чёрный текст для кнопки

    def update_timer_setting(self, spinner, text):
        self.settings["timer_duration"] = int(text)
        self.save_settings()
        logger.debug(f"Время таймера обновлено: {text} секунд")

    def update_language_setting(self, spinner, text):
        self.settings["language"] = text
        self.save_settings()
        logger.debug(f"Язык обновлён: {text}")
        # Обновляем другие экраны
        self.manager.get_screen("dictionary").update_word_list()
        self.manager.get_screen("game").update_language()

    def update_sound_setting(self, checkbox, value):
        self.settings["sound_enabled"] = value
        self.save_settings()
        logger.debug(f"Звук {'включён' if value else 'выключен'}")

    def update_theme_setting(self, spinner, text):
        self.settings["theme"] = text
        self.save_settings()
        logger.debug(f"Тема обновлена: {text}")
        # Применяем тему ко всем экранам
        self.apply_theme()
        self.manager.get_screen("main_menu").apply_theme()
        self.manager.get_screen("map").apply_theme()
        self.manager.get_screen("dictionary").apply_theme()
        self.manager.get_screen("game").apply_theme()

    def go_back(self, *args):
        logger.debug("Возврат на главное меню")
        logger.debug(f"[Текущий экран] {self.manager.current}")
        logger.debug(f"[Все экраны] {list(self.manager.screen_names)}")
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "main_menu"
        logger.debug(f"[Новый текущий экран] {self.manager.current}")


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация GameScreen")
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        # Верхняя панель: прогресс-бар, очки, прогресс и таймер
        self.progress_bar = ProgressBar(max=100, value=0, size_hint=(1, 0.1))
        self.layout.add_widget(self.progress_bar)

        self.top_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        self.score_label = Label(text="Очки: 0", font_size=20, font_name='SFPro', color=(0, 0, 0, 1))
        self.progress_label = Label(text="Слово 0/0", font_size=20, font_name='SFPro', color=(0, 0, 0, 1))
        self.timer_label = Label(text="30", font_size=20, font_name='SFPro', color=(0, 0, 0, 1))
        self.top_layout.add_widget(self.score_label)
        self.top_layout.add_widget(self.progress_label)
        self.top_layout.add_widget(self.timer_label)
        self.layout.add_widget(self.top_layout)

        self.definition_label = Label(text="", font_size=32, font_name='SFPro', color=(0, 0, 0, 1), halign="center",
                                      text_size=(350, None))
        self.layout.add_widget(self.definition_label)

        # Панель с вводом и кнопками
        self.input_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        self.answer_input = TextInput(hint_text="Введи слово", font_size=20, font_name='SFPro', multiline=False)
        self.hint_button = Button(text="Подсказка", font_size=20, font_name='SFPro', on_press=self.show_hint)
        self.check_button = Button(text="Проверить", font_size=20, font_name='SFPro', on_press=self.check_answer)
        self.input_layout.add_widget(self.answer_input)
        self.input_layout.add_widget(self.hint_button)
        self.input_layout.add_widget(self.check_button)
        self.layout.add_widget(self.input_layout)

        self.feedback_label = Label(text="", font_size=24, font_name='SFPro', color=(0, 0, 0, 1))
        self.layout.add_widget(self.feedback_label)

        self.add_widget(self.layout)

        self.current_cefr_level = "A1"
        self.current_sub_level = 1
        self.words = []
        self.current_word_index = 0
        self.correct_answers = 0
        self.score = 0
        self.hint_used = False
        self.target_lang = "ru"
        self.time_left = 30
        self.timer_event = None
        self.initial_time = 30  # Сохраняем начальное время
        self.load_settings()
        self.apply_theme()
        logger.debug("GameScreen полностью инициализирован")

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.initial_time = settings.get("timer_duration", 30)
                    self.time_left = self.initial_time  # Устанавливаем начальное время
                    self.target_lang = settings.get("language", "ru")
                    return settings
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Файл settings.json не найден, используется стандартное время 30 секунд")
            self.initial_time = 30
            self.time_left = 30
            self.target_lang = "ru"
        return {"timer_duration": 30, "language": "ru", "sound_enabled": True, "theme": "light"}

    def apply_theme(self):
        settings = self.load_settings()
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Тёмный фон
            self.score_label.color = (1, 1, 1, 1)  # Белый текст
            self.progress_label.color = (1, 1, 1, 1)  # Белый текст
            self.timer_label.color = (1, 1, 1, 1)  # Белый текст
            self.definition_label.color = (1, 1, 1, 1)  # Белый текст
            self.answer_input.foreground_color = (1, 1, 1, 1)  # Белый текст в поле ввода
            self.hint_button.color = (1, 1, 1, 1)  # Белый текст
            self.check_button.color = (1, 1, 1, 1)  # Белый текст
            self.feedback_label.color = (1, 1, 1, 1)  # Белый текст
            # Применяем тему к экрану результатов, если он активен
            if hasattr(self, 'result_label'):
                self.result_label.color = (1, 1, 1, 1)
            if hasattr(self, 'return_button'):
                self.return_button.color = (1, 1, 1, 1)
        else:
            Window.clearcolor = (1, 1, 1, 1)  # Светлый фон
            self.score_label.color = (0, 0, 0, 1)  # Чёрный текст
            self.progress_label.color = (0, 0, 0, 1)  # Чёрный текст
            self.timer_label.color = (0, 0, 0, 1)  # Чёрный текст
            self.definition_label.color = (0, 0, 0, 1)  # Чёрный текст
            self.answer_input.foreground_color = (0, 0, 0, 1)  # Чёрный текст в поле ввода
            self.hint_button.color = (0, 0, 0, 1)  # Чёрный текст
            self.check_button.color = (0, 0, 0, 1)  # Чёрный текст
            self.feedback_label.color = (0, 0, 0, 1)  # Чёрный текст
            # Применяем тему к экрану результатов, если он активен
            if hasattr(self, 'result_label'):
                self.result_label.color = (0, 0, 0, 1)
            if hasattr(self, 'return_button'):
                self.return_button.color = (0, 0, 0, 1)

    def update_language(self):
        self.load_settings()
        if self.current_word_index < len(self.words):
            word_data = self.words[self.current_word_index]
            self.definition_label.text = word_data["definitions"][self.target_lang]
            if self.feedback_label.text.startswith("Ответ:"):
                correct_answer = self.words[self.current_word_index]["translations"][self.target_lang]
                self.feedback_label.text = f"Ответ: {correct_answer}"

    def setup_game(self, cefr_level, sub_level):
        logger.debug(f"Настройка игры для уровня {cefr_level}, подуровня {sub_level}")
        try:
            self.current_cefr_level = cefr_level
            self.current_sub_level = sub_level
            self.words = WORD_DATABASE[cefr_level][str(sub_level)]["words"]
            random.shuffle(self.words)
            self.current_word_index = 0
            self.correct_answers = 0
            self.score = 0
            self.score_label.text = "Очки: 0"
            self.load_settings()  # Загружаем настройки перед началом игры
            self.progress_bar.max = len(self.words)
            self.progress_bar.value = 0
            # Восстанавливаем исходный layout, если он был изменён (например, после show_results)
            self.layout.clear_widgets()
            self.layout.add_widget(self.progress_bar)
            self.layout.add_widget(self.top_layout)
            self.layout.add_widget(self.definition_label)
            self.layout.add_widget(self.input_layout)
            self.layout.add_widget(self.feedback_label)
            self.show_next_word()
            logger.info(f"Игра настроена для {cefr_level}, подуровень {sub_level}")
        except KeyError as e:
            logger.error(f"Ошибка в структуре базы данных: {e}")
            self.definition_label.text = "Ошибка: уровень или подуровень не найден"
            self.input_layout.clear_widgets()

    def show_next_word(self):
        logger.debug(f"Показ следующего слова, индекс: {self.current_word_index}, всего слов: {len(self.words)}")
        if self.current_word_index < len(self.words):
            word_data = self.words[self.current_word_index]
            self.progress_label.text = f"Слово {self.current_word_index + 1}/{len(self.words)}"
            self.progress_bar.value = self.current_word_index + 1
            self.definition_label.text = word_data["definitions"][self.target_lang]
            self.answer_input.text = ""
            self.feedback_label.text = ""
            self.feedback_label.color = (0, 0, 0, 1) if self.load_settings().get("theme", "light") == "light" else (
            1, 1, 1, 1)
            self.check_button.text = "Проверить"
            self.check_button.on_press = self.check_answer
            self.hint_button.disabled = False
            self.hint_used = False
            # Сбрасываем таймер перед началом нового слова
            self.time_left = self.initial_time
            self.timer_label.text = str(self.time_left)
            if self.timer_event:
                self.timer_event.cancel()
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)
            logger.debug(f"Показ слова {self.current_word_index + 1}: {word_data['definitions'][self.target_lang]}")
        else:
            self.show_results()

    def update_timer(self, dt):
        self.time_left -= 1
        self.timer_label.text = str(self.time_left)
        if self.time_left <= 0:
            self.timer_event.cancel()
            self.feedback_label.text = f"Время вышло! Ответ: {self.words[self.current_word_index]['translations'][self.target_lang]}"
            self.feedback_label.color = (1, 0, 0, 1)
            self.score -= 5  # Штраф за истечение времени
            if self.score < 0:
                self.score = 0  # Устанавливаем минимальный порог
            self.score_label.text = f"Очки: {self.score}"
            self.check_button.text = "Дальше"
            self.check_button.on_press = self.next_word
            self.hint_button.disabled = True
            logger.debug("Время вышло для текущего слова")

    def show_hint(self, *args):
        if not self.hint_used and self.current_word_index < len(self.words):
            correct_answer = self.words[self.current_word_index]["translations"][self.target_lang].lower()
            self.answer_input.text = correct_answer[0]  # Показываем первую букву
            self.hint_used = True
            self.hint_button.disabled = True
            self.score -= 5  # Штраф за подсказку
            if self.score < 0:
                self.score = 0  # Устанавливаем минимальный порог
            self.score_label.text = f"Очки: {self.score}"
            logger.debug(f"Подсказка использована: показана первая буква '{correct_answer[0]}'")

    def check_answer(self, *args):
        self.timer_event.cancel()  # Останавливаем таймер
        user_answer = self.answer_input.text.strip().lower()
        correct_answer = self.words[self.current_word_index]["translations"][self.target_lang].lower()

        settings = self.load_settings()
        sound_enabled = settings.get("sound_enabled", True)
        if user_answer == correct_answer:
            self.feedback_label.text = "✓"
            self.feedback_label.color = (0, 1, 0, 1)
            self.correct_answers += 1
            self.score += 10  # Награда за правильный ответ
            if sound_enabled:
                logger.debug("Звук правильного ответа (будет добавлен позже)")
            logger.debug(f"Правильный ответ: {correct_answer}")
        else:
            self.feedback_label.text = f"Ответ: {correct_answer}"
            self.feedback_label.color = (1, 0, 0, 1)
            self.score -= 5  # Штраф за неправильный ответ
            if self.score < 0:
                self.score = 0  # Устанавливаем минимальный порог
            if sound_enabled:
                logger.debug("Звук неправильного ответа (будет добавлен позже)")
            logger.debug(f"[Неправильный ответ] {user_answer}, правильный: {correct_answer}")

        self.score_label.text = f"Очки: {self.score}"
        self.check_button.text = "Дальше"
        self.check_button.on_press = self.next_word

    def next_word(self, *args):
        self.current_word_index += 1
        self.show_next_word()

    def show_results(self):
        if self.timer_event:
            self.timer_event.cancel()
        stars = self.calculate_stars()

        # Очищаем экран
        self.layout.clear_widgets()

        # Создаём новый layout для результатов
        result_layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        # Заголовок
        self.result_label = Label(text=f"Подуровень пройден!\nОчки: {self.score}", font_size=32, font_name='SFPro',
                                  color=(0, 0, 0, 1), halign="center")
        result_layout.add_widget(self.result_label)

        # Layout для звёзд
        stars_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        for i in range(3):
            star_label = Label(text="☆" if i >= stars else "★", font_size=48,
                               color=(1, 1, 0, 1) if i < stars else (0.5, 0.5, 0.5, 1))
            stars_layout.add_widget(star_label)
        result_layout.add_widget(stars_layout)

        # Кнопка "Вернуться к карте" (показываем сразу)
        self.return_button = Button(text="Вернуться к карте", font_size=20, font_name='SFPro',
                                    size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                    on_press=self.go_to_map)
        result_layout.add_widget(self.return_button)

        self.layout.add_widget(result_layout)
        self.apply_theme()  # Применяем тему после создания экрана результатов

        # Сохраняем прогресс
        map_screen = self.manager.get_screen("map")
        if self.current_cefr_level not in map_screen.completed_sub_levels:
            map_screen.completed_sub_levels[self.current_cefr_level] = {}
        map_screen.completed_sub_levels[self.current_cefr_level][str(self.current_sub_level)] = stars
        map_screen.save_progress()
        map_screen.update_map()

        logger.info(f"Результат: {stars} звёзд, очки: {self.score}")

    def calculate_stars(self):
        # Учитываем как процент правильных ответов, так и очки
        percentage = (self.correct_answers / len(self.words)) * 100
        if percentage >= 90 and self.score >= len(self.words) * 10 * 0.9:
            return 3
        elif percentage >= 70 and self.score >= len(self.words) * 10 * 0.7:
            return 2
        elif percentage >= 50 and self.score >= len(self.words) * 10 * 0.5:
            return 1
        return 0

    def go_to_map(self, *args):
        logger.debug("Возврат на карту")
        logger.debug(f"[Текущий экран] {self.manager.current}")
        logger.debug(f"[Все экраны] {list(self.manager.screen_names)}")
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "map"
        logger.debug(f"[Новый текущий экран] {self.manager.current}")


class WordGameApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_closing = False  # Флаг для предотвращения многократных вызовов on_request_close

    def build(self):
        logger.debug("Создание приложения")
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(DictionaryScreen(name="dictionary"))
        sm.add_widget(SettingsScreen(name="settings"))
        logger.debug("Все экраны добавлены в ScreenManager")

        # Устанавливаем текущий экран явно
        sm.current = "main_menu"
        logger.debug(f"Установлен текущий экран: {sm.current}")

        # Привязываем обработчик клавиш
        Window.bind(on_keyboard=self.on_keyboard)

        # Добавляем отладку для проверки, не вызывается ли stop()
        Window.bind(on_request_close=self.on_request_close)

        return sm

    def on_start(self):
        logger.debug("Приложение запущено, основной цикл начинается")

    def on_stop(self):
        logger.debug("Приложение закрывается")
        # Сохраняем прогресс и настройки перед закрытием
        for screen in self.root.screens:
            if hasattr(screen, 'save_progress'):
                screen.save_progress()
            if hasattr(screen, 'save_settings'):
                screen.save_settings()
            if hasattr(screen, 'save_difficult_words'):
                screen.save_difficult_words()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        # Перехватываем нажатие клавиши Esc (код 27)
        if key == 27:  # Esc
            logger.debug("Нажата клавиша Esc")
            current_screen = self.root.current
            if current_screen == "main_menu":
                logger.debug("На главном меню, запрашиваем подтверждение закрытия")
                return True  # True означает, что событие обработано, и приложение не закроется
            else:
                logger.debug(f"На экране {current_screen}, возвращаемся в главное меню")
                self.root.transition = SlideTransition(direction='right')
                self.root.current = "main_menu"
                return True  # Предотвращаем закрытие приложения
        return False  # Позволяем другим клавишам обрабатываться стандартно

    def on_request_close(self, *args):
        if self.is_closing:
            logger.debug("Запрос на закрытие уже обрабатывается, игнорируем повторный вызов")
            return True
        self.is_closing = True
        logger.debug("Получен запрос на закрытие приложения")
        # Здесь можно добавить диалог подтверждения
        return True  # True предотвращает закрытие, False позволяет закрыть приложение


if __name__ == "__main__":
    logger.info("Запуск приложения")
    try:
        WordGameApp().run()
    except KeyboardInterrupt:
        logger.warning("Приложение прервано пользователем (KeyboardInterrupt)")
        # Вызываем on_stop вручную, чтобы сохранить прогресс
        app = App.get_running_app()
        if app:
            app.on_stop()
        exit(0)