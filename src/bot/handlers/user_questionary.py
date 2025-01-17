from aiogram import Router, Bot, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, KeyboardButton, \
    ReplyKeyboardMarkup

from bot.handlers.permission_handlers import permission_check
from bot.sql.users import add_user, set_user_setting, get_user_setting, set_user_table_setting, get_user_table_setting, \
    check_if_user_exists

router = Router()

class UserDataStates(StatesGroup):
    name = State()
    surname = State()
    confirmation = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    profile_button = KeyboardButton(text="Профиль")
    profile_keyboard = ReplyKeyboardMarkup(
        keyboard=[[profile_button]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    if not await permission_check(message.from_user.id, message.chat.id, bot, is_start=True):
        await message.answer("Привет! Ты первый раз в боте, поэтому введи твое имя: ", reply_markup=profile_keyboard)
        await state.update_data(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            username=message.from_user.username
        )
        await state.set_state(UserDataStates.name)
    else:
        current_username = await get_user_table_setting(message.from_user.id, "username")
        if message.from_user.username != current_username:
            await set_user_table_setting(message.from_user.id, "username", message.from_user.username)

        await message.answer("Привет! Этот бот поможет тебе ответить на любой вопрос, если же ответ бота тебя не "
                             "устроит, то ты можешь задать вопрос эксперту из списка", reply_markup=profile_keyboard)


@router.message(Command("profile"))
async def cmd_profile(message: Message, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot):
        return
    user_id = message.from_user.id
    name = await get_user_setting(user_id, "name")
    surname = await get_user_setting(user_id, "surname")
    is_expert = await get_user_setting(user_id, "is_expert")

    text = f"id: `{user_id}`\n\n"
    text += f"Имя: {name}\nФамилия: {surname}\n\n"
    if is_expert:
        text += "Вы являетесь экспертом, поэтому к вам могут поступать вопросы от других пользователей!"

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить данные", callback_data=f"change_data_{message.from_user.id}")],
    ])

    await message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=inline_keyboard)


@router.message(F.text == "Профиль")
async def profile_handler(message: Message, bot: Bot):
    await cmd_profile(message, bot)


@router.message(Command("change_data"))
async def cmd_change_data(message: Message, state: FSMContext, bot: Bot):
    if not await permission_check(message.from_user.id, message.chat.id, bot):
        return

    await state.update_data(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        username=message.from_user.username
    )

    await message.answer("Хорошо, введи свое имя: ")
    await state.set_state(UserDataStates.name)

@router.callback_query(F.data.regexp(r"^change_data_.*"))
async def callback_change_data(callback: CallbackQuery, state: FSMContext):
    message = callback.message
    user_id = int(callback.data.lstrip("change_data_"))
    await state.update_data(
        user_id=user_id,
        chat_id=message.chat.id,
        username=message.from_user.username
    )

    await message.answer("Хорошо, введи свое имя: ")
    await state.set_state(UserDataStates.name)

@router.message(UserDataStates.name)
async def name_handler(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Отлично! Теперь давай введи свою фамилию:")
    await state.set_state(UserDataStates.surname)

@router.message(UserDataStates.surname)
async def surname_handler(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    data = await state.get_data()

    confirmation_text = (
        f"Пожалуйста, подтвердите ваши данные:\n\n"
        f"Имя: {data['name']}\n"
        f"Фамилия: {data['surname']}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить", callback_data="confirm_data"),
                InlineKeyboardButton(text="Изменить", callback_data="change_data"),
            ]
        ]
    )

    await message.answer(confirmation_text, reply_markup=keyboard)
    await state.set_state(UserDataStates.confirmation)

@router.callback_query(UserDataStates.confirmation)
async def confirmation_handler(callback: CallbackQuery, state: FSMContext):
    if callback.data == "confirm_data":
        data = await state.get_data()

        first_time = False

        if not await check_if_user_exists(data["user_id"]):
            first_time = True
            await add_user(
                data["user_id"],
                data["chat_id"],
                data["username"])

        await set_user_setting(data["user_id"], "name", data["name"])
        await set_user_setting(data["user_id"], "surname", data["surname"])

        if first_time:
            await callback.message.edit_text(f"{data['name']}, вы успешно зарегестрированы в боте!")
        else:
            await callback.message.edit_text(f"{data['name']}, данные успешно изменены!")

        await state.clear()
    elif callback.data == "change_data":
        await callback.message.edit_text("Давайте начнем заново! Пожалуйста введите ваше имя:")
        await state.set_state(UserDataStates.name)

