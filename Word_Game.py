import json
import random
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.properties import NumericProperty, StringProperty
from kivy.clock import Clock

# Загрузка базы слов
with open("words.json", "r", encoding="utf-8") as f:
    WORD_DATABASE = json.load(f)

# Путь для сохранения прогресса
PROGRESS_FILE = "progress.json"

class WordGame(BoxLayout):
    score = NumericProperty(0)
    attempts = NumericProperty(3)
    time_left = NumericProperty(30)
    definition = StringProperty("")
    message = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 10
        self.target_lang = "en"
        self.current_cefr_level = "A1"
        self.current_sub_level = 1
        self.timer_duration = 30
        self.word = ""
        self.correct_word = ""
        self.current_theme = "Not set yet"  # Начальное значение темы
        self.timer_event = None
        self.completed_words = {}  # {cefr_level: {sub_level: [word1, word2, ...]}}

        # Верхняя панель
        top_layout = BoxLayout(size_hint=(1, 0.15), spacing=10)
        self.lang_spinner = Spinner(
            text="Language",
            values=("English (en)", "Русский (ru)", "Deutsch (de)", "Français (fr)"),
            size_hint=(0.3, 1)
        )
        self.lang_spinner.bind(text=self.start_game_with_lang)
        top_layout.add_widget(self.lang_spinner)

        self.cefr_spinner = Spinner(
            text="CEFR Level",
            values=("A1", "A2", "B1", "B2", "C1"),
            size_hint=(0.3, 1)
        )
        self.cefr_spinner.bind(text=self.set_cefr_level)
        top_layout.add_widget(self.cefr_spinner)

        self.sub_level_label = Label(
            text=f"Sub-Level: {self.current_sub_level} (Theme: {self.current_theme})",
            size_hint=(0.4, 1)
        )
        top_layout.add_widget(self.sub_level_label)
        self.add_widget(top_layout)

        # Определение слова
        self.definition_label = Label(
            text="Definition will appear here",
            size_hint=(1, 0.3),
            halign="center",
            valign="middle",
            text_size=(self.width - 40, None)
        )
        self.add_widget(self.definition_label)

        # Поле ввода
        self.answer_input = TextInput(
            hint_text="Enter your answer",
            size_hint=(1, 0.15),
            multiline=False
        )
        self.answer_input.bind(on_text_validate=self.check_answer)
        self.add_widget(self.answer_input)

        # Кнопка проверки
        self.check_button = Button(
            text="Check Answer",
            size_hint=(1, 0.15)
        )
        self.check_button.bind(on_press=self.check_answer)
        self.add_widget(self.check_button)

        # Сообщение
        self.message_label = Label(
            text="",
            size_hint=(1, 0.15),
            halign="center",
            valign="middle",
            text_size=(self.width - 40, None)
        )
        self.add_widget(self.message_label)

        # Статус
        self.status_label = Label(
            text=f"Score: {self.score} | Attempts: 3 | Time: 30",
            size_hint=(1, 0.1)
        )
        self.add_widget(self.status_label)

        # Загрузка прогресса и начало игры после создания интерфейса
        self.load_progress()
        self.new_word()

    def load_progress(self):
        """Загружает сохранённый прогресс."""
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.score = data.get("score", 0)
                self.current_cefr_level = data.get("current_cefr_level", "A1")
                self.current_sub_level = data.get("current_sub_level", 1)
                self.completed_words = data.get("completed_words", {})
                self.update_sub_level_label()

    def save_progress(self):
        """Сохраняет прогресс."""
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "score": self.score,
                "current_cefr_level": self.current_cefr_level,
                "current_sub_level": self.current_sub_level,
                "completed_words": self.completed_words
            }, f, ensure_ascii=False, indent=4)

    def get_random_word(self):
        """Получает случайное слово из текущей группы, которое ещё не завершено."""
        cefr_level = self.current_cefr_level
        sub_level = str(self.current_sub_level)
        if cefr_level not in WORD_DATABASE or sub_level not in WORD_DATABASE[cefr_level]:
            return {"word": "error", "definitions": {"en": "No words for this level!", "ru": "Нет слов для этого уровня!", "de": "Keine Wörter für diese Stufe!", "fr": "Pas de mots pour ce niveau!"}, "translations": {"ru": "ошибка", "de": "Fehler", "fr": "erreur"}}

        self.current_theme = WORD_DATABASE[cefr_level][sub_level]["theme"]
        self.update_sub_level_label()
        words = WORD_DATABASE[cefr_level][sub_level]["words"]
        completed = self.completed_words.get(cefr_level, {}).get(sub_level, [])
        available_words = [w for w in words if w["word"] not in completed]

        if not available_words:
            self.move_to_next_sub_level()
            return self.get_random_word()

        return random.choice(available_words)

    def update_sub_level_label(self):
        """Обновляет метку подуровня с темой."""
        self.sub_level_label.text = f"Sub-Level: {self.current_sub_level} (Theme: {self.current_theme})"

    def move_to_next_sub_level(self):
        """Переходит к следующему подуровню."""
        self.current_sub_level += 1
        if self.current_sub_level > 30:  # Полный уровень A1 до 30 подуровней
            self.current_sub_level = 1
            self.current_cefr_level = "A2"  # Пример перехода
            self.cefr_spinner.text = self.current_cefr_level
            self.message_label.text = "Congratulations! You've completed A1 in this example!"
        self.update_sub_level_label()
        self.save_progress()

    def start_game_with_lang(self, spinner, text):
        """Начинает игру с выбранным языком."""
        lang_map = {"English (en)": "en", "Русский (ru)": "ru", "Deutsch (de)": "de", "Français (fr)": "fr"}
        self.target_lang = lang_map.get(text, "en")
        self.new_word()

    def set_cefr_level(self, spinner, text):
        """Устанавливает уровень CEFR."""
        self.current_cefr_level = text
        self.current_sub_level = 1
        self.update_sub_level_label()
        self.new_word()
        self.save_progress()

    def new_word(self):
        """Загружает новое слово и запускает таймер."""
        self.attempts = 3
        self.time_left = self.timer_duration
        word_data = self.get_random_word()
        self.word = word_data["word"]
        self.correct_word = word_data["translations"].get(self.target_lang, self.word) if self.target_lang != "en" else self.word
        self.definition_label.text = word_data["definitions"].get(self.target_lang, "Definition not available")
        self.message_label.text = ""
        self.answer_input.text = ""
        self.check_button.text = "Check Answer"
        self.check_button.bind(on_press=self.check_answer)
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, dt):
        """Обновляет таймер."""
        self.time_left -= 1
        if self.time_left <= 0:
            self.attempts = 0
            self.message_label.text = f"Time's up! Word was: {self.correct_word} ({self.word})"
            self.check_button.text = "Next Word"
            self.check_button.bind(on_press=lambda x: self.new_word())
            self.timer_event.cancel()
        self.update_status()

    def check_answer(self, *args):
        """Проверяет ответ пользователя."""
        user_answer = self.answer_input.text.strip().lower()
        if user_answer == self.correct_word.lower():
            self.score += 1
            self.message_label.text = f"Correct! ({self.correct_word} = {self.word})"
            self.check_button.text = "Next Word"
            self.check_button.bind(on_press=lambda x: self.new_word())
            self.timer_event.cancel()
            # Помечаем слово как завершённое
            cefr_level = self.current_cefr_level
            sub_level = str(self.current_sub_level)
            if cefr_level not in self.completed_words:
                self.completed_words[cefr_level] = {}
            if sub_level not in self.completed_words[cefr_level]:
                self.completed_words[cefr_level][sub_level] = []
            self.completed_words[cefr_level][sub_level].append(self.word)
            self.save_progress()
        else:
            self.attempts -= 1
            if self.attempts > 0:
                self.message_label.text = "Incorrect. Try again!"
            else:
                self.message_label.text = f"No attempts left. Word was: {self.correct_word} ({self.word})"
                self.check_button.text = "Next Word"
                self.check_button.bind(on_press=lambda x: self.new_word())
                self.timer_event.cancel()
        self.update_status()

    def update_status(self):
        """Обновляет статус."""
        self.status_label.text = f"Score: {self.score} | Attempts: {self.attempts} | Time: {self.time_left}"

class WordGameApp(App):
    def build(self):
        return WordGame()

if __name__ == "__main__":
    WordGameApp().run()