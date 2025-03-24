import json
import random
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


class WordGame(BoxLayout):
    score = NumericProperty(0)
    attempts = NumericProperty(3)
    time_left = NumericProperty(30)
    definition = StringProperty("")
    message = StringProperty("")
    correct_word = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 10
        self.target_lang = "en"
        self.difficulty = "easy"
        self.word = ""
        self.timer_event = None
        self.hint_level = 0

        # Выбор языка и сложности
        top_layout = BoxLayout(size_hint=(1, 0.15), spacing=10)
        self.lang_spinner = Spinner(
            text="Choose Language",
            values=("English (en)", "Русский (ru)", "Deutsch (de)", "Français (fr)"),
            size_hint=(0.5, 1),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.lang_spinner.bind(text=self.start_game_with_lang)
        top_layout.add_widget(self.lang_spinner)

        self.diff_spinner = Spinner(
            text="Difficulty",
            values=("Easy", "Medium", "Hard"),
            size_hint=(0.5, 1),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.diff_spinner.bind(text=self.set_difficulty)
        top_layout.add_widget(self.diff_spinner)
        self.add_widget(top_layout)

        # Определение слова
        self.definition_label = Label(
            text="Definition will appear here",
            size_hint=(1, 0.25),
            halign="center",
            valign="middle",
            text_size=(self.width - 40, None),
            color=(0, 0, 0, 1),
            font_size=20
        )
        self.add_widget(self.definition_label)

        # Поле ввода
        self.answer_input = TextInput(
            hint_text="Enter your answer",
            size_hint=(1, 0.15),
            multiline=False,
            background_color=(0.9, 0.9, 0.9, 1),
            foreground_color=(0, 0, 0, 1)
        )
        self.answer_input.bind(on_text_validate=self.check_answer)
        self.add_widget(self.answer_input)

        # Кнопки
        button_layout = BoxLayout(size_hint=(1, 0.15), spacing=10)
        self.check_button = Button(
            text="Check Answer",
            size_hint=(0.6, 1),
            background_color=(0, 1, 0, 1),
            color=(1, 1, 1, 1)
        )
        self.check_button.bind(on_press=self.check_answer)
        button_layout.add_widget(self.check_button)

        self.hint_button = Button(
            text="Hint",
            size_hint=(0.4, 1),
            background_color=(1, 0.5, 0, 1),
            color=(1, 1, 1, 1)
        )
        self.hint_button.bind(on_press=self.show_hint)
        button_layout.add_widget(self.hint_button)
        self.add_widget(button_layout)

        # Сообщение о результате
        self.message_label = Label(
            text="",
            size_hint=(1, 0.15),
            halign="center",
            valign="middle",
            text_size=(self.width - 40, None),
            color=(0, 0, 1, 1)
        )
        self.add_widget(self.message_label)

        # Счет, попытки и таймер
        self.status_label = Label(
            text="Score: 0 | Attempts: 3 | Time: 30",
            size_hint=(1, 0.1),
            font_size=16
        )
        self.add_widget(self.status_label)

    def get_random_word(self):
        """Получает случайное слово из локальной базы."""
        suitable_words = [w for w in WORD_DATABASE if w["difficulty"] == self.difficulty]
        if not suitable_words:
            return {"word": "error", "definition": "No words for this difficulty!",
                    "translations": {"ru": "ошибка", "de": "Fehler", "fr": "erreur"}}
        return random.choice(suitable_words)

    def start_game_with_lang(self, spinner, text):
        """Начинает игру с выбранным языком."""
        lang_map = {"English (en)": "en", "Русский (ru)": "ru", "Deutsch (de)": "de", "Français (fr)": "fr"}
        self.target_lang = lang_map.get(text, "en")
        self.message_label.color = {
            "ru": (1, 0, 0, 1), "de": (0, 1, 0, 1), "fr": (1, 0.5, 0, 1), "en": (0, 0, 1, 1)
        }.get(self.target_lang, (0, 0, 1, 1))
        self.new_word()

    def set_difficulty(self, spinner, text):
        """Устанавливает уровень сложности."""
        difficulty_map = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}
        self.difficulty = difficulty_map.get(text, "easy")
        self.new_word()

    def new_word(self):
        """Загружает новое слово и запускает таймер."""
        self.attempts = 3
        self.time_left = 30
        self.hint_level = 0
        word_data = self.get_random_word()
        self.word = word_data["word"]
        self.correct_word = word_data["translations"].get(self.target_lang,
                                                          self.word) if self.target_lang != "en" else self.word
        self.definition = word_data["definition"] if self.target_lang == "en" else self.translate_definition(
            word_data["definition"])
        self.definition_label.text = self.definition
        self.message_label.text = ""
        self.answer_input.text = ""
        self.check_button.text = "Check Answer"
        self.check_button.bind(on_press=self.check_answer)
        self.hint_button.disabled = False
        self.update_status()
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def translate_definition(self, definition):
        """Переводит определение (заглушка, так как переводы уже в базе)."""
        # Если нужно больше языков, можно добавить перевод через внешний сервис позже
        return definition  # Пока оставляем на английском, так как база небольшая

    def update_timer(self, dt):
        """Обновляет таймер."""
        self.time_left -= 1
        if self.time_left <= 0:
            self.attempts = 0
            self.message_label.text = f"Time's up! Word was: {self.correct_word} ({self.word})"
            self.check_button.text = "Next Word"
            self.check_button.bind(on_press=lambda x: self.new_word())
            self.hint_button.disabled = True
            self.timer_event.cancel()
        self.update_status()

    def show_hint(self, instance):
        """Показывает подсказку."""
        if self.attempts <= 0 or self.hint_level >= 2:
            return
        self.hint_level += 1
        if self.hint_level == 1:
            self.message_label.text = f"Hint 1: Word starts with '{self.correct_word[0]}'"
        elif self.hint_level == 2:
            self.message_label.text = f"Hint 2: Word has {len(self.correct_word)} letters"
        if self.hint_level == 2:
            self.hint_button.disabled = True

    def check_answer(self, *args):
        """Проверяет ответ пользователя."""
        if not self.word:
            return

        user_answer = self.answer_input.text.strip().lower()
        prompts = {
            "ru": {
                "correct": f"Верно! ({self.correct_word} = {self.word})",
                "incorrect": "Неверно. Попробуйте еще раз!",
                "no_attempts": f"Попытки закончились. Слово: {self.correct_word} ({self.word})"
            },
            "en": {
                "correct": f"Correct! ({self.word})",
                "incorrect": "Incorrect. Try again!",
                "no_attempts": f"No more attempts. The word was: {self.word}"
            },
            "de": {
                "correct": f"Richtig! ({self.correct_word} = {self.word})",
                "incorrect": "Falsch. Versuchen Sie es nochmal!",
                "no_attempts": f"Keine Versuche mehr. Das Wort war: {self.correct_word} ({self.word})"
            },
            "fr": {
                "correct": f"Correct! ({self.correct_word} = {self.word})",
                "incorrect": "Incorrect. Essayez encore!",
                "no_attempts": f"Plus de tentatives. Le mot était: {self.correct_word} ({self.word})"
            }
        }.get(self.target_lang, {"correct": "", "incorrect": "", "no_attempts": ""})

        if user_answer == self.correct_word.lower():
            score_increment = 1 if self.hint_level == 0 else (0.75 if self.hint_level == 1 else 0.5)
            self.score += score_increment
            self.message_label.text = prompts["correct"]
            self.check_button.text = "Next Word"
            self.check_button.bind(on_press=lambda x: self.new_word())
            self.hint_button.disabled = True
            self.timer_event.cancel()
        else:
            self.attempts -= 1
            if self.attempts > 0:
                self.message_label.text = prompts["incorrect"]
            else:
                self.message_label.text = prompts["no_attempts"]
                self.check_button.text = "Next Word"
                self.check_button.bind(on_press=lambda x: self.new_word())
                self.hint_button.disabled = True
                self.timer_event.cancel()

        self.update_status()

    def update_status(self):
        """Обновляет счет, попытки и таймер на экране."""
        self.status_label.text = f"Score: {self.score} | Attempts: {self.attempts} | Time: {self.time_left}"


class WordGameApp(App):
    def build(self):
        return WordGame()


if __name__ == "__main__":
    WordGameApp().run()