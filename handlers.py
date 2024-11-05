from aiogram import types, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart, StateFilter, CommandObject, CREATOR
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from service import generate_options_keyboard, get_question, new_quiz, get_quiz_index, update_quiz_index, get_current_score, get_quiz_length, get_correct_answer

router = Router()

@router.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    await callback.message.answer("Верно!")
    current_question_index = await get_quiz_index(callback.from_user.id)
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index, 1)
    
    total_questions = await get_quiz_length()

    if current_question_index < total_questions:
        await get_question(callback.message, callback.from_user.id)
    else:
        score = await get_current_score(callback.from_user.id)
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваши очки: {score}.")

  
@router.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_answer = await get_correct_answer(current_question_index)

    await callback.message.answer(f"Неправильно. Правильный ответ: {correct_answer}")
    
    current_question_index += 1
    
    await update_quiz_index(callback.from_user.id, current_question_index, 0)

    total_questions = await get_quiz_length()

    if current_question_index < total_questions:
        await get_question(callback.message, callback.from_user.id)
    else:
        score = await get_current_score(callback.from_user.id)
        await callback.message.answer(f"Это был последний вопрос. Квиз завершен! Ваши очки: {score}.")


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    image_url="https://storage.yandexcloud.net/quiz-bot-1111/logistic-1.png"
    await message.answer_photo(photo=image_url, caption="Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text=="Начать игру")
@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)
    


