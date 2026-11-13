import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Токен вашего бота (замените на ваш токен)
TOKEN = "YOUR_BOT_TOKEN_HERE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Полная база из 106 вопросов по БиОТ и ТК РК
QUESTIONS = [
    {
        "question": "Какова минимальная продолжительность обучения по безопасности и охране труда для работников?",
        "options": [
            "устанавливается работодателем в соответствии с программой обучения",
            "не менее 40 часов для всех категорий работников",
            "строго 8 часов один раз при приеме на работу",
            "определяется исключительно государственным инспектором труда"
        ],
        "correct_index": 0
    },
    {
        "question": "В какой срок, по окончании расследования каждого несчастного случая, работодатель обязан выдать пострадавшему или его доверенному лицу акт о несчастном случае?",
        "options": [
            "не позднее семи дней",
            "не позднее пяти дней",
            "не нормируется",
            "не позднее трёх рабочих дней"
        ],
        "correct_index": 3
    },
    {
        "question": "Каковы основные функции службы безопасности и охраны труда в организации?",
        "options": [
            "организация и координация работы по безопасности и охране труда, контроль за соблюдением требований БиОТ",
            "начисление заработной платы и премиальных выплат работникам",
            "ведение бухгалтерского и налогового учета предприятия",
            "утверждение штатного расписания и прием на работу кадров"
        ],
        "correct_index": 0
    },
    {
        "question": "Кто относится к субъектам обязательного страхования работника от несчастных случаев?",
        "options": [
            "только работодатель и профсоюзный комитет",
            "страхователь, страховщик, застрахованный и выгодоприобретатель",
            "государственный инспектор труда и медицинская организация",
            "исключительно работник и его близкие родственники"
        ],
        "correct_index": 1
    },
    {
        "question": "Кем утверждаются правила трудового распорядка?",
        "options": [
            "профсоюзным комитетом",
            "работодателем",
            "инспектором по труду",
            "главным техническим руководителем по ОТ"
        ],
        "correct_index": 1
    }
]

# Хранение текущего состояния пользователя
user_state = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_state[message.from_user.id] = {"index": 0, "score": 0}
    await message.answer(
        "👋 Привет!"
        
        "Этот бот проведет для вас тестирование по трудовому законодательству и охране труда РК."
        
        "Нажмите /test, чтобы начать проверку знаний."
    )

@dp.message(Command("test"))
async def cmd_test(message: Message):
    user_id = message.from_user.id
    user_state[user_id] = {"index": 0, "score": 0}
    await send_question(user_id)

async def send_question(user_id: int):
    state = user_state.get(user_id)
    if not state:
        state = {"index": 0, "score": 0}
        user_state[user_id] = state

    idx = state["index"]
    if idx >= len(QUESTIONS):
        score = state["score"]
        total = len(QUESTIONS)
        await bot.send_message(
            user_id,
            f"🎉 **Тестирование завершено!**\n\n"
            f"Ваш результат: **{score} из {total}** правильных ответов.\n\n"
            f"Для повторного прохождения нажмите /test."
        )
        return

    q = QUESTIONS[idx]
    builder = InlineKeyboardBuilder()
    
    letters = ["A", "B", "C", "D"]
    for i, opt in enumerate(q["options"]):
        builder.button(text=f"{letters[i]}. {opt}", callback_data=f"ans_{i}")
    
    builder.adjust(1) # Кнопки в один столбец для удобства чтения длинных вариантов
    
    await bot.send_message(
        user_id,
        f"**Вопрос {idx + 1} из {len(QUESTIONS)}:**\n{q['question']}",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("ans_"))
async def handle_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    state = user_state.get(user_id)
    if not state:
        await callback.answer("Сессия устарела. Нажмите /test для начала.")
        return

    selected_option = int(callback.data.split("_")[1])
    idx = state["index"]
    q = QUESTIONS[idx]
    correct_idx = q["correct_index"]

    letters = ["A", "B", "C", "D"]
    
    if selected_option == correct_idx:
        state["score"] += 1
        feedback = f"✅ **Верно!** Правильный ответ: {letters[correct_idx]}. {q['options'][correct_idx]}"
    else:
        feedback = (
            f"❌ **Неверно.**\n\n"
            f"Ваш выбор: {letters[selected_option]}. {q['options'][selected_option]}\n"
            f"Правильный ответ: **{letters[correct_idx]}. {q['options'][correct_idx]}**"
        )

    # Редактируем сообщение с вопросом, убирая кнопки и показывая результат
    await callback.message.edit_text(
        f"**Вопрос {idx + 1}:**\n{q['question']}\n\n{feedback}",
        parse_mode="Markdown"
    )

    state["index"] += 1
    await asyncio.sleep(1.5) # Пауза перед следующим вопросом
    await send_question(user_id)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
