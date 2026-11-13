import os
import json
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Токен вшит напрямую для стабильной работы на Railway
TOKEN = "9005451655:AAH8wBg6bBrOmHnZGU054qW0vi6xn0X2WL4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранение текущего сеанса пользователя
user_state = {}

def load_questions():
    """Загрузка вопросов из файла questions.json"""
    if os.path.exists("questions.json"):
        with open("questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@dp.message(Command("start"))
async def cmd_start(message: Message):
    questions_pool = load_questions()
    await message.answer(
        "👋 Привет!\n\n"
        "Этот бот проведёт для вас тестирование по трудовому законодательству и охране труда РК.\n\n"
        f"📚 Загружено вопросов в базу: **{len(questions_pool)}**.\n"
        "🎯 В каждом тесте случайным образом выбирается **50 вопросов**.\n"
        "📈 Для успешной сдачи необходимо набрать **не менее 70%** правильных ответов.\n\n"
        "Нажмите /test, чтобы начать проверку знаний."
    )

@dp.message(Command("test"))
async def cmd_test(message: Message):
    user_id = message.from_user.id
    questions_pool = load_questions()
   
    if not questions_pool:
        await message.answer("⚠️ Ошибка: файл `questions.json` не найден или пуст!")
        return
   
    # Случайный выбор 50 вопросов из файла (или всех, если в базе меньше 50)
    test_questions = random.sample(questions_pool, min(50, len(questions_pool)))
   
    user_state[user_id] = {
        "questions": test_questions,
        "index": 0,
        "score": 0
    }
    await send_question(message, user_id)

async def send_question(message_or_callback, user_id):
    state = user_state.get(user_id)
    if not state:
        questions_pool = load_questions()
        test_questions = random.sample(questions_pool, min(50, len(questions_pool)))
        state = {"questions": test_questions, "index": 0, "score": 0}
        user_state[user_id] = state

    index = state["index"]
    questions = state["questions"]
   
    # Если вопросы закончились — подводим итоги
    if index >= len(questions):
        score = state["score"]
        total = len(questions)
        percentage = (score / total) * 100

        if percentage >= 70:
            text = (
                f"🎉 **Поздравляем! Экзамен успешно сдан!** 🏆\n\n"
                f"📊 Ваш результат: **{score} из {total}** ({percentage:.1f}%).\n"
                f"Вы отлично справились с проверкой знаний по БиОТ и ТК РК!"
            )
        else:
            text = (
                f"❌ **Экзамен не сдан.**\n\n"
                f"📊 Ваш результат: **{score} из {total}** ({percentage:.1f}%).\n"
                f"Для успешной сдачи требуется набрать не менее **70%**.\n\n"
                f"🔄 Пожалуйста, отправьте команду /test, чтобы пройти пересдачу."
            )

        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(text, parse_mode="Markdown")
            await message_or_callback.answer()
        else:
            await message_or_callback.answer(text, parse_mode="Markdown")
       
        # Очищаем состояние сеанса
        user_state.pop(user_id, None)
        return

    q = questions[index]
    keyboard_buttons = [
        [InlineKeyboardButton(text=option, callback_data=f"ans_{i}")]
        for i, option in enumerate(q["options"])
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    question_text = f"❓ **Вопрос {index + 1} из {len(questions)}**\n\n{q['question']}"
   
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(question_text, reply_markup=keyboard, parse_mode="Markdown")
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(question_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("ans_"))
async def process_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
   
    state = user_state.get(user_id)
    if not state:
        await callback.answer("Сессия устарела или тест завершен. Начните заново с помощью /test", show_alert=True)
        return

    selected_option = int(callback.data.split("_")[1])
    index = state["index"]
    questions = state["questions"]
    q = questions[index]

    if selected_option == q["correct_index"]:
        state["score"] += 1
        await callback.message.answer("✅ **Верно!**", parse_mode="Markdown")
    else:
        correct_text = q["options"][q["correct_index"]]
        await callback.message.answer(f"❌ **Неверно.**\nПравильный ответ: {correct_text}", parse_mode="Markdown")

    state["index"] += 1
    await send_question(callback, user_id)

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
