from  database import pool, execute_update_query, execute_select_query
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types
import json


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()

async def get_quiz_data(quiz_index):
    query = """
    DECLARE $id AS Uint64;

    SELECT id, question, options, correct_option FROM quiz_questions
    WHERE id = $id;
    """
    results = execute_select_query(pool, query, id=quiz_index)
    
    if results:
        question_data = results[0]
        options = json.loads(question_data['options'].decode('utf-8'))
        question = question_data['question'].decode('utf-8')
        question_data['question'] = question
        question_data['options'] = options
        return question_data
    return None
  

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)

    question_data = await get_quiz_data(current_question_index)

    if question_data:
        correct_index = question_data['correct_option']
        opts = question_data['options']
        print(f"Options: {opts}, Correct Index: {correct_index}")
        kb = generate_options_keyboard(opts, opts[correct_index])

        await message.answer(f"{question_data['question']}", reply_markup=kb)
    else:
        await message.answer("Вопрос не найден.")
        await message.answer("К сожалению, вопрос не найден.")


async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    score = 0
    await update_quiz_index(user_id, current_question_index, score)
    await get_question(message, user_id)
    await reset_user_score(user_id)


async def get_quiz_index(user_id):
    get_user_index = f"""
        DECLARE $user_id AS Uint64;
        
        SELECT question_index
        FROM `quiz_state`
        WHERE user_id == $user_id;
    """
    results = execute_select_query(pool, get_user_index, user_id=user_id)

    if len(results) == 0:
        return 0
    if results[0]["question_index"] is None:
        return 0
    return results[0]["question_index"]    

async def get_current_score(user_id):
    query = """
    DECLARE $user_id AS Uint64;
    SELECT score 
    FROM quiz_state
    WHERE user_id = $user_id;"""
    result = execute_select_query(pool, query, user_id=user_id)
    return result[0][0] if result else 0    
    

async def update_quiz_index(user_id, question_index, new_score):
    current_score = await get_current_score(user_id)
    updated_score = current_score + new_score

    set_quiz_state = """
        DECLARE $user_id AS Uint64;
        DECLARE $question_index AS Uint64;
        DECLARE $updated_score AS Uint64;

        UPSERT INTO quiz_state (user_id, question_index, score) 
        VALUES ($user_id, $question_index, $updated_score);
    """

    execute_update_query(
        pool,
        set_quiz_state,
        user_id=user_id,
        question_index=question_index,
        updated_score=updated_score
    )
    
async def get_quiz_length():
    query = "SELECT COUNT(*) FROM quiz_questions;"
    
    result = execute_select_query(pool, query)
    if result and result[0]:
        return result[0][0] 
    return 0

async def reset_user_score(user_id):
    query = """
    DECLARE $user_id AS Uint64;

    UPDATE quiz_state SET score = 0
    WHERE user_id = $user_id;"""
    execute_update_query(pool, query,user_id=user_id)

async def get_correct_answer(quiz_index):
    query = """
    DECLARE $id AS Uint64;

    SELECT options, correct_option FROM quiz_questions
    WHERE id = $id;
    """
    results = execute_select_query(pool, query, id=quiz_index)

    if results:
        question_data = results[0]
        options = json.loads(question_data['options'].decode('utf-8'))
        correct_index = question_data['correct_option']
        return options[correct_index]

    return None 