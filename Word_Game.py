import json
import random
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.clock import Clock
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Регистрация шрифта SF-Pro
try:
    LabelBase.register(name='SFPro', fn_regular='SF-Pro.ttf')
except Exception as e:
    logger.error(f"Ошибка загрузки шрифта SF-Pro: {e}")

# Регистрация шрифта SF-Pro-Text-Light
try:
    LabelBase.register(name='SFProTextLight', fn_regular='SF-Pro-Text-Light.ttf')
except Exception as e:
    logger.error(f"Ошибка загрузки шрифта SF-Pro-Text-Light: {e}")

# Регистрация шрифта SF-Pro-Text-Medium
try:
    LabelBase.register(name='SFProTextMedium', fn_regular='SF-Pro-Text-Medium.ttf')
except Exception as e:
    logger.error(f"Ошибка загрузки шрифта SF-Pro-Text-Medium: {e}")

# Определение цветов
ORANGE = (1, 87/255, 0, 1)  # #FF5700
GRAY_BG = (249/255, 249/255, 249/255, 1)  # #F9F9F9
WHITE_BG = (1, 1, 1, 1)  # #FFFFFF
BLACK_TEXT = (0, 0, 0, 1)  # #000000
WHITE_TEXT = (1, 1, 1, 1)  # #FFFFFF

# Установка начального фона (светлая тема по умолчанию)
Window.clearcolor = WHITE_BG

# Установка разрешения iPhone 14 Pro (402x874)
Window.size = (402, 874)

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

# Путь для сохранения прогресса, настроек и данных пользователя
PROGRESS_FILE = "progress.json"
DIFFICULT_WORDS_FILE = "difficult_words.json"
SETTINGS_FILE = "settings.json"
USER_FILE = "user.json"

# Новый экран: Начальный экран для ввода имени
class WelcomeScreen(Screen):
    def save_name_and_proceed(self, *args):
        name = self.ids.name_input.text.strip()
        if not name:
            self.ids.name_input.hint_text = "Пожалуйста, введите имя!"
            return

        # Сохраняем имя в user.json
        try:
            with open(USER_FILE, "w", encoding="utf-8") as f:
                json.dump({"name": name}, f, ensure_ascii=False, indent=4)
            logger.info(f"Имя пользователя сохранено: {name}")
        except Exception as e:
            logger.error(f"Ошибка сохранения имени: {e}")
            return

        # Переходим на главный экран
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "main_menu"


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация MainMenuScreen")
        self.user_name = self.load_user_name()
        logger.debug("MainMenuScreen полностью инициализирован")

    def on_pre_enter(self):
        self.ids.greeting_label.text = f"Привет, {self.user_name}!"
        self.apply_theme()  # Переносим сюда
        self.show_today()  # По умолчанию показываем "Сегодня"

    def load_user_name(self):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("name", "Пользователь")
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Файл user.json не найден, используется имя по умолчанию")
            return "Пользователь"

    def apply_theme(self):
        settings = self.manager.app_settings
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Тёмный фон
            self.ids.greeting_label.color = WHITE_TEXT
            self.ids.today_button.color = WHITE_TEXT
            self.ids.tasks_button.color = WHITE_TEXT
            for child in self.ids.content_layout.children:
                if isinstance(child, Button):
                    child.color = WHITE_TEXT
                elif isinstance(child, Carousel):
                    for slide in child.slides:
                        slide.color = WHITE_TEXT
            for child in self.ids.menu_layout.children:
                child.color = WHITE_TEXT
        else:
            Window.clearcolor = WHITE_BG
            self.ids.greeting_label.color = BLACK_TEXT
            self.ids.today_button.color = WHITE_TEXT if self.ids.today_button.background_color == ORANGE else BLACK_TEXT
            self.ids.tasks_button.color = WHITE_TEXT if self.ids.tasks_button.background_color == ORANGE else BLACK_TEXT
            for child in self.ids.content_layout.children:
                if isinstance(child, Button):
                    child.color = WHITE_TEXT if child.background_color == ORANGE else BLACK_TEXT
                elif isinstance(child, Carousel):
                    for slide in child.slides:
                        slide.color = BLACK_TEXT
            for child in self.ids.menu_layout.children:
                child.color = BLACK_TEXT

    def show_today(self, *args):
        logger.debug("Показываем вкладку 'Сегодня'")
        self.ids.today_button.background_color = ORANGE
        self.ids.tasks_button.background_color = GRAY_BG
        self.ids.today_button.color = WHITE_TEXT
        self.ids.tasks_button.color = BLACK_TEXT
        self.ids.content_layout.clear_widgets()

        # Кнопка "Разминка"
        warmup_button = Button(
            text="Разминка (10 вопросов)",
            font_size=20,
            font_name='SFPro',
            size_hint=(0.9, 0.25),
            pos_hint={'center_x': 0.5},
            background_color=ORANGE,
            color=WHITE_TEXT,
            background_normal='',
            background_down=''
        )
        warmup_button.bind(on_press=self.start_warmup)
        self.ids.content_layout.add_widget(warmup_button)

        # Блоки тем с горизонтальной прокруткой (Carousel)
        carousel = Carousel(direction='right', size_hint=(1, 0.35), loop=True)
        for i in range(3):
            theme_button = Button(
                text=f"Тема {i + 1}",
                font_size=20,
                font_name='SFPro',
                background_color=GRAY_BG,
                color=BLACK_TEXT,
                size_hint=(0.8, 1),
                pos_hint={'center_x': 0.5},
                background_normal='',
                background_down=''
            )
            theme_button.bind(on_press=self.start_game_with_theme)
            carousel.add_widget(theme_button)
        self.ids.content_layout.add_widget(carousel)

        self.apply_theme()

    def show_tasks(self, *args):
        logger.debug("Показываем вкладку 'Задания'")
        self.ids.today_button.background_color = GRAY_BG
        self.ids.tasks_button.background_color = ORANGE
        self.ids.today_button.color = BLACK_TEXT
        self.ids.tasks_button.color = WHITE_TEXT
        self.ids.content_layout.clear_widgets()

        # Список подуровней
        scroll_view = ScrollView(size_hint=(1, 0.6))
        sublevel_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        sublevel_layout.bind(minimum_height=sublevel_layout.setter('height'))

        for i in range(1, 6):
            is_unlocked = i <= 3  # Пример: первые 3 уровня открыты
            sublevel_button = Button(
                text=f"Подуровень {i}",
                font_size=20,
                font_name='SFPro',
                size_hint_y=None,
                height=60,
                background_color=ORANGE if is_unlocked else GRAY_BG,
                color=WHITE_TEXT if is_unlocked else BLACK_TEXT,
                disabled=not is_unlocked,
                background_normal='',
                background_down=''
            )
            sublevel_button.bind(on_press=lambda x, sl=i: self.start_game(sl))
            sublevel_layout.add_widget(sublevel_button)

        scroll_view.add_widget(sublevel_layout)
        self.ids.content_layout.add_widget(scroll_view)

        self.apply_theme()

    def start_warmup(self, *args):
        logger.debug("Запуск разминки")
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "game"

    def start_game_with_theme(self, *args):
        logger.debug("Запуск игры с выбранной темой")
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "game"

    def start_game(self, sub_level):
        logger.debug(f"Запуск игры для подуровня {sub_level}")
        game_screen = self.manager.get_screen("game")
        game_screen.setup_game("A1", sub_level)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "game"

    def go_to_main(self, *args):
        logger.debug("Переход на главный экран")
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "main_menu"

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
        self.current_cefr_level = "A1"  # Инициализация
        self.completed_sub_levels = {}  # Инициализация

    def on_pre_enter(self):
        self.update_map()
        self.apply_theme()

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
        settings = self.manager.app_settings
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)
            self.ids.title_label.color = WHITE_TEXT
            self.ids.back_button.color = WHITE_TEXT
            for btn in self.ids.map_layout.children:
                btn.color = WHITE_TEXT if btn.background_color == ORANGE else BLACK_TEXT
        else:
            Window.clearcolor = WHITE_BG
            self.ids.title_label.color = BLACK_TEXT
            self.ids.back_button.color = WHITE_TEXT
            for btn in self.ids.map_layout.children:
                btn.color = WHITE_TEXT if btn.background_color == ORANGE else BLACK_TEXT

    def update_map(self):
        self.current_cefr_level = "A1"
        self.completed_sub_levels = self.load_progress().get("completed_sub_levels", {})
        self.ids.map_layout.clear_widgets()
        for sub_level in range(1, 11):
            try:
                stars = self.completed_sub_levels.get(self.current_cefr_level, {}).get(str(sub_level), 0)
                btn_text = f"{sub_level}\n{'★' * stars}{'☆' * (3 - stars)}" if stars > 0 else str(sub_level)
                is_locked = not self.is_sub_level_unlocked(sub_level)
                btn = Button(
                    text=btn_text,
                    font_size=20,
                    font_name='SFPro',
                    background_color=ORANGE if not is_locked else GRAY_BG,
                    color=WHITE_TEXT if not is_locked else BLACK_TEXT,
                    disabled=is_locked,
                    background_normal='',
                    background_down='',
                    on_press=lambda x, sl=sub_level: self.start_game(sl)
                )
                self.ids.map_layout.add_widget(btn)
            except Exception as e:
                logger.error(f"Ошибка при обновлении карты для подуровня {sub_level}: {e}")
        self.apply_theme()

    def is_sub_level_unlocked(self, sub_level):
        if sub_level == 1:
            return True
        prev_sub_level = sub_level - 1
        return str(prev_sub_level) in self.completed_sub_levels.get(self.current_cefr_level, {})

    def start_game(self, sub_level):
        logger.debug(f"Запуск игры для подуровня {sub_level}")
        game_screen = self.manager.get_screen("game")
        game_screen.setup_game(self.current_cefr_level, sub_level)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = "game"

    def go_back(self, *args):
        logger.debug("Возврат на главное меню")
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "main_menu"


class DictionaryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.difficult_words = {}  # Инициализация

    def on_pre_enter(self):
        self.load_words()
        self.apply_theme()

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

    def apply_theme(self):
        settings = self.manager.app_settings
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)
            self.ids.title_label.color = WHITE_TEXT
            self.ids.filter_label.color = WHITE_TEXT
            self.ids.sub_level_spinner.color = WHITE_TEXT
            self.ids.back_button.color = WHITE_TEXT
            for child in self.ids.word_list.children:
                for widget in child.children:
                    if isinstance(widget, Label):
                        widget.color = WHITE_TEXT
        else:
            Window.clearcolor = WHITE_BG
            self.ids.title_label.color = BLACK_TEXT
            self.ids.filter_label.color = BLACK_TEXT
            self.ids.sub_level_spinner.color = BLACK_TEXT
            self.ids.back_button.color = WHITE_TEXT
            for child in self.ids.word_list.children:
                for widget in child.children:
                    if isinstance(widget, Label):
                        widget.color = BLACK_TEXT

    def load_words(self):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                progress = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            progress = {"current_cefr_level": "A1", "completed_sub_levels": {}}

        self.completed_sub_levels = progress.get("completed_sub_levels", {}).get("A1", {})
        self.difficult_words = self.load_difficult_words()
        self.update_word_list()

    def update_word_list(self, *args):
        self.ids.word_list.clear_widgets()
        if not self.completed_sub_levels:
            self.ids.word_list.add_widget(Label(
                text="Вы ещё не прошли ни одного подуровня!",
                font_size=20,
                font_name='SFPro',
                color=BLACK_TEXT,
                size_hint_y=None,
                height=40
            ))
            self.apply_theme()
            return

        selected_sub_level = self.ids.sub_level_spinner.text
        show_difficult_only = self.ids.difficult_only_checkbox.active

        sub_levels_to_show = self.completed_sub_levels.keys()
        if selected_sub_level != "Все подуровни":
            sub_level_num = selected_sub_level.split()[-1]
            sub_levels_to_show = [sub_level_num] if sub_level_num in self.completed_sub_levels else []

        settings = self.manager.app_settings
        language = settings.get("language", "ru")
        for sub_level in sub_levels_to_show:
            try:
                words = WORD_DATABASE["A1"][sub_level]["words"]
                for word_data in words:
                    word_key = f"A1_{sub_level}_{word_data['translations']['ru']}"
                    if show_difficult_only and word_key not in self.difficult_words:
                        continue

                    word_row = BoxLayout(size_hint_y=None, height=40, spacing=10)
                    word_label = Label(
                        text=f"{word_data['translations'][language]} - {word_data['definitions'][language]}",
                        font_size=18,
                        font_name='SFPro',
                        color=BLACK_TEXT,
                        halign="left",
                        text_size=(300, None)
                    )
                    difficult_checkbox = CheckBox(active=word_key in self.difficult_words)
                    difficult_checkbox.bind(active=lambda cb, value, wk=word_key: self.toggle_difficult_word(wk, value))
                    word_row.add_widget(word_label)
                    word_row.add_widget(difficult_checkbox)
                    self.ids.word_list.add_widget(word_row)
            except KeyError as e:
                logger.error(f"Ошибка при загрузке слов для подуровня {sub_level}: {e}")
        self.apply_theme()

    def toggle_difficult_word(self, word_key, value):
        if value:
            self.difficult_words[word_key] = True
        else:
            self.difficult_words.pop(word_key, None)
        self.save_difficult_words()
        logger.debug(f"[Слово {word_key} помечено как сложное] {value}")

    def go_back(self, *args):
        logger.debug("Возврат на главное меню")
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "main_menu"


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = {}  # Инициализация

    def on_pre_enter(self):
        self.settings = self.manager.app_settings
        self.ids.timer_spinner.text = str(self.settings.get("timer_duration", 30))
        self.ids.language_spinner.text = self.settings.get("language", "ru")
        self.ids.sound_checkbox.active = self.settings.get("sound_enabled", True)
        self.ids.theme_spinner.text = self.settings.get("theme", "light")
        self.apply_theme()

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            logger.info("Настройки сохранены")
            self.manager.app_settings = self.settings  # Обновляем кэш в приложении
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")

    def apply_theme(self):
        theme = self.settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)
            self.ids.title_label.color = WHITE_TEXT
            self.ids.timer_label.color = WHITE_TEXT
            self.ids.timer_spinner.color = WHITE_TEXT
            self.ids.language_label.color = WHITE_TEXT
            self.ids.language_spinner.color = WHITE_TEXT
            self.ids.sound_label.color = WHITE_TEXT
            self.ids.theme_label.color = WHITE_TEXT
            self.ids.theme_spinner.color = WHITE_TEXT
            self.ids.back_button.color = WHITE_TEXT
        else:
            Window.clearcolor = WHITE_BG
            self.ids.title_label.color = BLACK_TEXT
            self.ids.timer_label.color = BLACK_TEXT
            self.ids.timer_spinner.color = BLACK_TEXT
            self.ids.language_label.color = BLACK_TEXT
            self.ids.language_spinner.color = BLACK_TEXT
            self.ids.sound_label.color = BLACK_TEXT
            self.ids.theme_label.color = BLACK_TEXT
            self.ids.theme_spinner.color = BLACK_TEXT
            self.ids.back_button.color = WHITE_TEXT

    def update_timer_setting(self, spinner, text):
        self.settings["timer_duration"] = int(text)
        self.save_settings()
        logger.debug(f"Время таймера обновлено: {text} секунд")

    def update_language_setting(self, spinner, text):
        self.settings["language"] = text
        self.save_settings()
        logger.debug(f"Язык обновлён: {text}")
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
        self.apply_theme()
        self.manager.get_screen("main_menu").apply_theme()
        self.manager.get_screen("map").apply_theme()
        self.manager.get_screen("dictionary").apply_theme()
        self.manager.get_screen("game").apply_theme()

    def go_back(self, *args):
        logger.debug("Возврат на главное меню")
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "main_menu"


class GameScreen(Screen):
    def on_pre_enter(self):
        self.load_settings()
        self.apply_theme()

    def load_settings(self):
        settings = self.manager.app_settings
        self.initial_time = settings.get("timer_duration", 30)
        self.time_left = self.initial_time
        self.target_lang = settings.get("language", "ru")
        return settings

    def apply_theme(self):
        settings = self.manager.app_settings
        theme = settings.get("theme", "light")
        if theme == "dark":
            Window.clearcolor = (0.1, 0.1, 0.1, 1)
            self.ids.score_label.color = WHITE_TEXT
            self.ids.progress_label.color = WHITE_TEXT
            self.ids.timer_label.color = WHITE_TEXT
            self.ids.definition_label.color = WHITE_TEXT
            self.ids.answer_input.foreground_color = WHITE_TEXT
            self.ids.hint_button.color = WHITE_TEXT
            self.ids.check_button.color = WHITE_TEXT
            self.ids.feedback_label.color = WHITE_TEXT
            if hasattr(self, 'result_label'):
                self.result_label.color = WHITE_TEXT
            if hasattr(self, 'return_button'):
                self.return_button.color = WHITE_TEXT
        else:
            Window.clearcolor = WHITE_BG
            self.ids.score_label.color = BLACK_TEXT
            self.ids.progress_label.color = BLACK_TEXT
            self.ids.timer_label.color = BLACK_TEXT
            self.ids.definition_label.color = BLACK_TEXT
            self.ids.answer_input.foreground_color = BLACK_TEXT
            self.ids.hint_button.color = WHITE_TEXT
            self.ids.check_button.color = WHITE_TEXT
            self.ids.feedback_label.color = BLACK_TEXT
            if hasattr(self, 'result_label'):
                self.result_label.color = BLACK_TEXT
            if hasattr(self, 'return_button'):
                self.return_button.color = WHITE_TEXT

    def update_language(self):
        self.load_settings()
        if self.current_word_index < len(self.words):
            word_data = self.words[self.current_word_index]
            self.ids.definition_label.text = word_data["definitions"][self.target_lang]
            if self.ids.feedback_label.text.startswith("Ответ:"):
                correct_answer = self.words[self.current_word_index]["translations"][self.target_lang]
                self.ids.feedback_label.text = f"Ответ: {correct_answer}"

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
            self.ids.score_label.text = "Очки: 0"
            self.load_settings()
            self.ids.progress_bar.max = len(self.words)
            self.ids.progress_bar.value = 0
            self.show_next_word()
            logger.info(f"Игра настроена для {cefr_level}, подуровень {sub_level}")
        except KeyError as e:
            logger.error(f"Ошибка в структуре базы данных: {e}")
            self.ids.definition_label.text = "Ошибка: уровень или подуровень не найден"
            self.ids.input_layout.clear_widgets()

    def show_next_word(self):
        logger.debug(f"Показ следующего слова, индекс: {self.current_word_index}, всего слов: {len(self.words)}")
        if self.current_word_index < len(self.words):
            word_data = self.words[self.current_word_index]
            self.ids.progress_label.text = f"Слово {self.current_word_index + 1}/{len(self.words)}"
            self.ids.progress_bar.value = self.current_word_index + 1
            self.ids.definition_label.text = word_data["definitions"][self.target_lang]
            self.ids.answer_input.text = ""
            self.ids.feedback_label.text = ""
            self.ids.feedback_label.color = BLACK_TEXT if self.load_settings().get("theme",
                                                                                   "light") == "light" else WHITE_TEXT
            self.ids.check_button.text = "Проверить"
            self.ids.check_button.on_press = self.check_answer
            self.ids.hint_button.disabled = False
            self.hint_used = False
            self.time_left = self.initial_time
            self.ids.timer_label.text = str(self.time_left)
            if self.timer_event:
                self.timer_event.cancel()
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)
            logger.debug(f"Показ слова {self.current_word_index + 1}: {word_data['definitions'][self.target_lang]}")
        else:
            self.show_results()

    def update_timer(self, dt):
        self.time_left -= 1
        self.ids.timer_label.text = str(self.time_left)
        if self.time_left <= 0:
            self.timer_event.cancel()
            self.ids.feedback_label.text = f"Время вышло! Ответ: {self.words[self.current_word_index]['translations'][self.target_lang]}"
            self.ids.feedback_label.color = (1, 0, 0, 1)
            self.score -= 5
            if self.score < 0:
                self.score = 0
            self.ids.score_label.text = f"Очки: {self.score}"
            self.ids.check_button.text = "Дальше"
            self.ids.check_button.on_press = self.next_word
            self.ids.hint_button.disabled = True
            logger.debug("Время вышло для текущего слова")

    def show_hint(self, *args):
        if not self.hint_used and self.current_word_index < len(self.words):
            correct_answer = self.words[self.current_word_index]["translations"][self.target_lang].lower()
            self.ids.answer_input.text = correct_answer[0]
            self.hint_used = True
            self.ids.hint_button.disabled = True
            self.score -= 5
            if self.score < 0:
                self.score = 0
            self.ids.score_label.text = f"Очки: {self.score}"
            logger.debug(f"Подсказка использована: показана первая буква '{correct_answer[0]}'")

    def check_answer(self, *args):
        self.timer_event.cancel()
        user_answer = self.ids.answer_input.text.strip().lower()
        correct_answer = self.words[self.current_word_index]["translations"][self.target_lang].lower()

        settings = self.load_settings()
        sound_enabled = settings.get("sound_enabled", True)
        if user_answer == correct_answer:
            self.ids.feedback_label.text = "✓"
            self.ids.feedback_label.color = (0, 1, 0, 1)
            self.correct_answers += 1
            self.score += 10
            if sound_enabled:
                logger.debug("Звук правильного ответа (будет добавлен позже)")
            logger.debug(f"Правильный ответ: {correct_answer}")
        else:
            self.ids.feedback_label.text = f"Ответ: {correct_answer}"
            self.ids.feedback_label.color = (1, 0, 0, 1)
            self.score -= 5
            if self.score < 0:
                self.score = 0
            if sound_enabled:
                logger.debug("Звук неправильного ответа (будет добавлен позже)")
            logger.debug(f"[Неправильный ответ] {user_answer}, правильный: {correct_answer}")

        self.ids.score_label.text = f"Очки: {self.score}"
        self.ids.check_button.text = "Дальше"
        self.ids.check_button.on_press = self.next_word

    def next_word(self, *args):
        self.current_word_index += 1
        self.show_next_word()

    def show_results(self):
        if self.timer_event:
            self.timer_event.cancel()
        stars = self.calculate_stars()

        self.ids.layout.clear_widgets()

        result_layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        self.result_label = Label(
            text=f"Подуровень пройден!\nОчки: {self.score}",
            font_size=32,
            font_name='SFPro',
            color=BLACK_TEXT,
            halign="center"
        )
        result_layout.add_widget(self.result_label)

        stars_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        for i in range(3):
            star_label = Label(
                text="☆" if i >= stars else "★",
                font_size=48,
                color=(1, 1, 0, 1) if i < stars else (0.5, 0.5, 0.5, 1)
            )
            stars_layout.add_widget(star_label)
        result_layout.add_widget(stars_layout)

        self.return_button = Button(
            text="Вернуться к карте",
            font_size=20,
            font_name='SFPro',
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5},
            background_color=ORANGE,
            color=WHITE_TEXT,
            background_normal='',
            background_down='',
            on_press=self.go_to_map
        )
        result_layout.add_widget(self.return_button)

        self.ids.layout.add_widget(result_layout)
        self.apply_theme()

        map_screen = self.manager.get_screen("map")
        if self.current_cefr_level not in map_screen.completed_sub_levels:
            map_screen.completed_sub_levels[self.current_cefr_level] = {}
        map_screen.completed_sub_levels[self.current_cefr_level][str(self.current_sub_level)] = stars
        map_screen.save_progress()
        map_screen.update_map()

        logger.info(f"Результат: {stars} звёзд, очки: {self.score}")

    def calculate_stars(self):
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
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = "map"


class WordGameApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_closing = False
        # Кэшируем настройки приложения
        self.app_settings = self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Файл settings.json не найден, создаём новый")
        return {"timer_duration": 30, "language": "ru", "sound_enabled": True, "theme": "light"}

    def build(self):
        logger.debug("Создание приложения")
        sm = ScreenManager()
        sm.app_settings = self.app_settings  # Передаём настройки в ScreenManager
        sm.add_widget(WelcomeScreen(name="welcome"))
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(DictionaryScreen(name="dictionary"))
        sm.add_widget(SettingsScreen(name="settings"))
        logger.debug("Все экраны добавлены в ScreenManager")

        # Всегда открываем WelcomeScreen для тестирования
        sm.current = "welcome"
        logger.debug(f"Установлен текущий экран: {sm.current}")

        Window.bind(on_keyboard=self.on_keyboard)
        Window.bind(on_request_close=self.on_request_close)
        return sm

    def on_start(self):
        logger.debug("Приложение запущено, основной цикл начинается")

    def on_stop(self):
        logger.debug("Приложение закрывается")
        for screen in self.root.screens:
            if hasattr(screen, 'save_progress'):
                screen.save_progress()
            if hasattr(screen, 'save_settings'):
                screen.save_settings()
            if hasattr(screen, 'save_difficult_words'):
                screen.save_difficult_words()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            logger.debug("Нажата клавиша Esc")
            current_screen = self.root.current
            if current_screen == "main_menu":
                logger.debug("На главном меню, запрашиваем подтверждение закрытия")
                return True
            else:
                logger.debug(f"На экране {current_screen}, возвращаемся в главное меню")
                self.root.transition = SlideTransition(direction='right')
                self.root.current = "main_menu"
                return True
        return False

    def on_request_close(self, *args):
        if self.is_closing:
            logger.debug("Запрос на закрытие уже обрабатывается, игнорируем повторный вызов")
            return True
        self.is_closing = True
        logger.debug("Получен запрос на закрытие приложения")
        return True


if __name__ == "__main__":
    logger.info("Запуск приложения")
    try:
        WordGameApp().run()
    except KeyboardInterrupt:
        logger.warning("Приложение прервано пользователем (KeyboardInterrupt)")
        app = App.get_running_app()
        if app:
            app.on_stop()
        exit(0)