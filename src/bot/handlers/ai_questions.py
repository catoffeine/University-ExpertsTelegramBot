import json
from ast import literal_eval

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from bot.definitions import GIGACHAT_KEY
from bot.handlers.permission_handlers import permission_check
from bot.sql.users import get_user_setting, get_all_users, set_user_setting, get_user_table_setting

router = Router()


class ExpertAskStates(StatesGroup):
    choose_expert = State()
    ask_expert = State()


def cut_history(history, max_symbols=1000):
    if len(history) == 0:
        return history
    sym_count = sum([len(x[1]) for x in history])

    if sym_count > max_symbols:
        history = history[1:]
        cut_history(history, max_symbols)

    return history


@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def ask_bot(message: Message, state: FSMContext, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot):
        return

    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.SYSTEM,
                content="Ты бот, который вежливо отвечает на любой вопрос студента."
            )
        ],
        temperature=0.7,
        max_tokens=1000,
    )

    history = literal_eval(str(await get_user_setting(message.from_user.id, "history")))


    for item in history:
        if item[0] == "user":
            payload.messages.append(Messages(role=MessagesRole.USER, content=item[1]))
            # print("user:", item[1])
        else:
            # print("system:", item[1])
            payload.messages.append(Messages(role=MessagesRole.ASSISTANT, content=item[1]))

    # print("__________________")
    with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
        payload.messages.append(Messages(role=MessagesRole.USER, content=message.text))
        history.append(("user", message.text))
        try:
            response = giga.chat(payload)
        except BaseException as exc:
            await message.answer("Неизвестная ошибка, пожалуйста свяжитесь с разработчиком - @iamacoffee")
            print(repr(exc))
            return

        res = response.choices[0].message.content
        history.append(("system", res))

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Задать вопрос эксперту", callback_data="choose_expert")
                ]
            ]
        )

    history = cut_history(history)
    await set_user_setting(message.from_user.id, "history", history)
    await state.update_data(last_question=message.text, user_id=message.from_user.id)

    first_name = await get_user_setting(message.from_user.id, "name")
    last_name = await get_user_setting(message.from_user.id, "surname")
    username = await get_user_table_setting(message.from_user.id, "username")

    await state.update_data(
        last_question=message.text,
        user_id=message.from_user.id,
        first_name=first_name,
        last_name=last_name,
        username=username
    )
    await message.answer(res, reply_markup=keyboard)


@router.message(Command("clear"))
async def cmd_clear_history(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot):
        return

    await set_user_setting(message.from_user.id, "history", [])
    await message.answer("История сообщений отчищена!")

@router.callback_query(F.data == "choose_expert")
async def ask_expert(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ExpertAskStates.ask_expert)

    all_people = await get_all_users()

    list_experts = []
    text = "Список экспертов, которым можно задать вопрос: \n\n"
    for i, person in enumerate(all_people):
        user_id = person["user_id"]
        is_expert = await get_user_setting(user_id, "is_expert")
        if is_expert:
            first_name = await get_user_setting(user_id, "name")
            last_name = await get_user_setting(user_id, "surname")
            username = await get_user_table_setting(user_id, "username")
            text += f"{i + 1}: {first_name} {last_name}"
            if username != "no_user_name":
                text += f" (@{username})"
            text += "\n"
            list_experts.append(user_id)

    if len(list_experts) == 0:
        await state.clear()
        text += "Нет экспертов на текущий момент"

    builder = InlineKeyboardBuilder()
    for i, expert in enumerate(list_experts):
        builder.add(InlineKeyboardButton(text=str(i + 1), callback_data=f"expert_{expert}"))
        builder.adjust(3)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(ExpertAskStates.ask_expert)
async def ask_expert(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    question = data["last_question"]
    if "expert" not in callback.data:
        return
    expert_id = int(callback.data.lstrip("expert_"))
    expert_chat_id = await get_user_table_setting(expert_id, "chat_id")

    text = question
    if data["username"] != "no_user_name":
        text = f"Новый вопрос от пользователя ({data['first_name']} {data['last_name']} - @{data['username']}):\n\n{text}"
    else:
        text = f"Новый вопрос от пользователя ({data['first_name']} {data['last_name']}):\n\n{text}"

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Ответить", callback_data=f"answeruser_{data['user_id']}"),
        ]]
    )
    await bot.send_message(expert_chat_id, text=text, reply_markup=inline_keyboard)
    await callback.message.edit_text("Вопрос отправлен эксперту,\nкогда он ответит, мы отправим вам ответ на ваш вопрос.")
    await state.clear()

class AnswerUserStates(StatesGroup):
    answer_message = State()

@router.callback_query(F.data.regexp(r"^answeruser_.*"))
async def answer_user(callback: CallbackQuery, state: FSMContext):
    if "answeruser" not in callback.data:
        return
    from_user = int(callback.data.lstrip("answeruser_"))

    await state.set_state(AnswerUserStates.answer_message)
    await state.update_data(from_user=from_user)

    await callback.message.answer(text="Введите ответ: ")

@router.message(AnswerUserStates.answer_message)
async def answer_user(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    from_user = int(data["from_user"])
    from_user_chat_id = await get_user_table_setting(from_user, "chat_id")
    answer_text = f"Ответ от эксперта: \n\n{message.text}"
    await bot.send_message(from_user_chat_id, answer_text)
    await message.answer("Ответ успешно отправлен пользователю.")
    await state.clear()
