import requests
from bs4 import BeautifulSoup
from googletrans import Translator


def get_english_words():
    url = "https://randomword.com/"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        english_words = soup.find("div", id="random_word").text.strip()
        word_definition = soup.find("div", id="random_word_definition").text.strip()
        return {
            "english_words": english_words,
            "word_definition": word_definition
        }
    except:
        print("Произошла ошибка")


def translate_text(text, target_lang):
    translator = Translator()
    try:
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except:
        return text


def check_answer(user_answer, correct_word, target_lang):
    translator = Translator()
    try:
        translated_answer = translator.translate(user_answer, dest='en').text
        correct_word_translated = translator.translate(correct_word, dest=target_lang).text

        return {
            'is_correct': translated_answer.lower() == correct_word.lower(),
            'translated_word': correct_word_translated
        }
    except:
        return {
            'is_correct': False,
            'translated_word': correct_word
        }


def get_attempts_message(attempts, target_lang):
    if target_lang == "ru":
        return f"Осталось попыток: {attempts}"
    elif target_lang == "de":
        return f"Verbleibende Versuche: {attempts}"
    elif target_lang == "fr":
        return f"Tentatives restantes: {attempts}"
    else:
        return f"Attempts remaining: {attempts}"


def word_game():
    print("Добро пожаловать в игру")

    print("\nВыберите язык игры:")
    print("1. Русский (ru)")
    print("2. English (en)")
    print("3. Deutsch (de)")
    print("4. Français (fr)")

    lang_dict = {
        "1": "ru",
        "2": "en",
        "3": "de",
        "4": "fr"
    }

    while True:
        lang_choice = input("Введите номер языка (1-4): ")
        if lang_choice in lang_dict:
            target_lang = lang_dict[lang_choice]
            break
        print("Пожалуйста, выберите корректный номер")

    while True:
        word_dict = get_english_words()
        word = word_dict.get("english_words")
        word_definition = word_dict.get("word_definition")
        attempts = 3  # Устанавливаем количество попыток

        if target_lang != "en":
            translated_definition = translate_text(word_definition, target_lang)
        else:
            translated_definition = word_definition

        # Игровой цикл для одного слова
        while attempts > 0:
            if target_lang == "ru":
                print(f"\nЗначение слова - {translated_definition}")
                print("Введите слово на русском языке")
            elif target_lang == "de":
                print(f"\nWortdefinition - {translated_definition}")
                print("Geben Sie das Wort auf Deutsch ein")
            elif target_lang == "fr":
                print(f"\nDéfinition du mot - {translated_definition}")
                print("Entrez le mot en français")
            else:
                print(f"\nWord definition - {translated_definition}")
                print("Enter the word in English")

            print(get_attempts_message(attempts, target_lang))
            user_answer = input("> ")
            check_result = check_answer(user_answer, word, target_lang)

            if check_result['is_correct']:
                if target_lang == "ru":
                    print(f"Все верно! ({check_result['translated_word']} = {word})")
                elif target_lang == "de":
                    print(f"Richtig! ({check_result['translated_word']} = {word})")
                elif target_lang == "fr":
                    print(f"Correct! ({check_result['translated_word']} = {word})")
                else:
                    print(f"Correct! ({word})")
                break
            else:
                attempts -= 1
                if attempts > 0:
                    if target_lang == "ru":
                        print(f"Неверно. Попробуйте еще раз!")
                    elif target_lang == "de":
                        print(f"Falsch. Versuchen Sie es noch einmal!")
                    elif target_lang == "fr":
                        print(f"Incorrect. Essayez encore!")
                    else:
                        print(f"Incorrect. Try again!")
                else:
                    if target_lang == "ru":
                        print(f"Попытки закончились. Правильный ответ: {check_result['translated_word']} ({word})")
                    elif target_lang == "de":
                        print(f"Keine Versuche mehr. Das richtige Wort war: {check_result['translated_word']} ({word})")
                    elif target_lang == "fr":
                        print(f"Plus de tentatives. Le mot était: {check_result['translated_word']} ({word})")
                    else:
                        print(f"No more attempts. The word was: {word}")

        if target_lang == "ru":
            play_again = input("Хотите сыграть еще раз? д/н: ")
            if play_again.lower() != "д":
                print("Спасибо за игру!")
                break
        elif target_lang == "de":
            play_again = input("Möchten Sie noch einmal spielen? j/n: ")
            if play_again.lower() != "j":
                print("Danke fürs Spielen!")
                break
        elif target_lang == "fr":
            play_again = input("Voulez-vous jouer encore? o/n: ")
            if play_again.lower() != "o":
                print("Merci d'avoir joué!")
                break
        else:
            play_again = input("Would you like to play again? y/n: ")
            if play_again.lower() != "y":
                print("Thanks for playing!")
                break


word_game()