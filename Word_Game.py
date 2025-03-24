import json
import random
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.config import Config
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Установка белого фона
Window.clearcolor = (1, 1, 1, 1)

# Установка разрешения iPhone 14 Pro напрямую
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

# Путь для сохранения прогресса
PROGRESS_FILE = "progress.json"


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация MainMenuScreen")
        self.layout = BoxLayout(orientation="vertical", padding=50, spacing=20)
        self.layout.add_widget(Button(text="Играть", font_size=24, background_color=(0.2, 0.6, 1, 1),
                                      color=(1, 1, 1, 1), size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                      on_press=self.go_to_map))
        self.layout.add_widget(Button(text="Словарь", font_size=24, background_color=(0.2, 0.6, 1, 1),
                                      color=(1, 1, 1, 1), size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                      disabled=True))
        self.layout.add_widget(Button(text="Настройки", font_size=24, background_color=(0.2, 0.6, 1, 1),
                                      color=(1, 1, 1, 1), size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                      disabled=True))
        self.add_widget(self.layout)

    def go_to_map(self, *args):
        logger.debug("Переход на экран карты")
        self.manager.current = "map"


class MapScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация MapScreen")
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        self.layout.add_widget(Label(text="Карта уровней", font_size=32, color=(0, 0, 0, 1)))
        self.map_layout = GridLayout(cols=5, spacing=10, size_hint=(1, 0.8))
        self.layout.add_widget(self.map_layout)
        self.layout.add_widget(Button(text="Назад", font_size=20, size_hint=(1, 0.1),
                                      background_color=(0.2, 0.6, 1, 1), color=(1, 1, 1, 1),
                                      on_press=self.go_back))
        self.add_widget(self.layout)
        self.current_cefr_level = "A1"
        self.completed_sub_levels = self.load_progress().get("completed_sub_levels", {})
        self.update_map()

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

    def update_map(self):
        self.map_layout.clear_widgets()
        for sub_level in range(1, 11):
            try:
                stars = self.completed_sub_levels.get(self.current_cefr_level, {}).get(str(sub_level), 0)
                btn_text = f"{sub_level}\n{'★' * stars}{'☆' * (3 - stars)}" if stars > 0 else str(sub_level)
                is_locked = not self.is_sub_level_unlocked(sub_level)
                btn = Button(text=btn_text, font_size=20,
                             background_color=(0.8, 0.8, 0.8, 1) if is_locked else (0.2, 0.6, 1, 1),
                             color=(1, 1, 1, 1), disabled=is_locked,
                             on_press=lambda x, sl=sub_level: self.start_game(sl))
                self.map_layout.add_widget(btn)
            except Exception as e:
                logger.error(f"Ошибка при обновлении карты для подуровня {sub_level}: {e}")

    def is_sub_level_unlocked(self, sub_level):
        if sub_level == 1:
            return True
        prev_sub_level = sub_level - 1
        return str(prev_sub_level) in self.completed_sub_levels.get(self.current_cefr_level, {})

    def start_game(self, sub_level):
        logger.debug(f"Запуск игры для подуровня {sub_level}")
        self.manager.get_screen("game").setup_game(self.current_cefr_level, sub_level)
        self.manager.current = "game"

    def go_back(self, *args):
        logger.debug("Возврат на главное меню")
        self.manager.current = "main_menu"


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug("Инициализация GameScreen")
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        self.progress_label = Label(text="Слово 0/0", font_size=24, color=(0, 0, 0, 1))
        self.layout.add_widget(self.progress_label)

        self.definition_label = Label(text="", font_size=32, color=(0, 0, 0, 1), halign="center",
                                      text_size=(350, None))
        self.layout.add_widget(self.definition_label)

        self.input_layout = BoxLayout(size_hint=(1, 0.2), spacing=10)
        self.answer_input = TextInput(hint_text="Введи слово", font_size=20, multiline=False)
        self.check_button = Button(text="Проверить", font_size=20, background_color=(0.2, 0.6, 1, 1),
                                   color=(1, 1, 1, 1))
        self.input_layout.add_widget(self.answer_input)
        self.input_layout.add_widget(self.check_button)
        self.layout.add_widget(self.input_layout)

        self.feedback_label = Label(text="", font_size=24, color=(0, 0, 0, 1))
        self.layout.add_widget(self.feedback_label)

        self.add_widget(self.layout)

        self.current_cefr_level = "A1"
        self.current_sub_level = 1
        self.words = []
        self.current_word_index = 0
        self.correct_answers = 0
        self.target_lang = "ru"

    def setup_game(self, cefr_level, sub_level):
        try:
            self.current_cefr_level = cefr_level
            self.current_sub_level = sub_level
            self.words = WORD_DATABASE[cefr_level][str(sub_level)]["words"]
            random.shuffle(self.words)
            self.current_word_index = 0
            self.correct_answers = 0
            self.show_next_word()
            logger.info(f"Игра настроена для {cefr_level}, подуровень {sub_level}")
        except KeyError as e:
            logger.error(f"Ошибка в структуре базы данных: {e}")
            self.definition_label.text = "Ошибка: уровень или подуровень не найден"
            self.input_layout.clear_widgets()

    def show_next_word(self):
        if self.current_word_index < len(self.words):
            word_data = self.words[self.current_word_index]
            self.progress_label.text = f"Слово {self.current_word_index + 1}/{len(self.words)}"
            self.definition_label.text = word_data["definitions"][self.target_lang]
            self.answer_input.text = ""
            self.feedback_label.text = ""
            self.feedback_label.color = (0, 0, 0, 1)  # Сброс цвета на чёрный
            self.check_button.text = "Проверить"
            self.check_button.on_press = self.check_answer  # Прямая привязка без bind/unbind
            logger.debug(f"Показ слова {self.current_word_index + 1}")
        else:
            self.show_results()

    def check_answer(self, *args):
        user_answer = self.answer_input.text.strip().lower()
        correct_answer = self.words[self.current_word_index]["translations"][self.target_lang].lower()

        if user_answer == correct_answer:
            self.feedback_label.text = "✓"
            self.feedback_label.color = (0, 1, 0, 1)  # Зелёный
            self.correct_answers += 1
            logger.debug(f"Правильный ответ: {correct_answer}")
        else:
            self.feedback_label.text = f"Ответ: {correct_answer}"
            self.feedback_label.color = (1, 0, 0, 1)  # Красный
            logger.debug(f"Неправильный ответ: {user_answer}, правильный: {correct_answer}")

        self.check_button.text = "Дальше"
        self.check_button.on_press = self.next_word  # Прямая привязка к next_word

    def next_word(self, *args):
        self.current_word_index += 1
        self.show_next_word()

    def show_results(self):
        stars = self.calculate_stars()
        self.definition_label.text = f"Подуровень пройден!\nЗвёзд: {stars}"
        self.input_layout.clear_widgets()
        self.feedback_label.text = ""
        self.progress_label.text = ""

        map_screen = self.manager.get_screen("map")
        if self.current_cefr_level not in map_screen.completed_sub_levels:
            map_screen.completed_sub_levels[self.current_cefr_level] = {}
        map_screen.completed_sub_levels[self.current_cefr_level][str(self.current_sub_level)] = stars
        map_screen.save_progress()
        map_screen.update_map()

        self.layout.add_widget(Button(text="Вернуться к карте", font_size=20,
                                      background_color=(0.2, 0.6, 1, 1), color=(1, 1, 1, 1),
                                      size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5},
                                      on_press=self.go_to_map))
        logger.info(f"Результат: {stars} звёзд")

    def calculate_stars(self):
        percentage = (self.correct_answers / len(self.words)) * 100
        if percentage == 100:
            return 3
        elif percentage >= 80:
            return 2
        elif percentage >= 50:
            return 1
        return 0

    def go_to_map(self, *args):
        logger.debug("Возврат на карту")
        self.manager.current = "map"


class WordGameApp(App):
    def build(self):
        logger.debug("Создание приложения")
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(MapScreen(name="map"))
        sm.add_widget(GameScreen(name="game"))
        return sm


if __name__ == "__main__":
    logger.info("Запуск приложения")
    WordGameApp().run()