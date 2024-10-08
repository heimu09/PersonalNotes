import logging
import httpx
import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.state import State

API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

router = Router()

user_tokens = {}

logging.basicConfig(level=logging.INFO)

class NoteCreation(StatesGroup):
    title = State()
    content = State()
    tags = State()

class NoteSearch(StatesGroup):
    tags = State()

@router.message(Command(commands=['start', 'auth']))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Отправь свой API-токен для авторизации.")
    user_tokens[message.from_user.id] = None

@router.message(lambda message: message.from_user.id in user_tokens and user_tokens[message.from_user.id] is None)
async def handle_token(message: types.Message):
    user_tokens[message.from_user.id] = message.text
    await message.answer("Вы успешно авторизованы!")

@router.message(Command(commands=['new_note']))
async def new_note_start(message: types.Message, state: FSMContext):
    api_token = user_tokens.get(message.from_user.id)
    if not api_token:
        await message.answer("Сначала авторизуйтесь через /auth и предоставьте ваш API токен.")
        return

    await state.set_state(NoteCreation.title)
    await message.answer("Введите заголовок заметки:")
    current_state = await state.get_state()
    logging.info(f"Текущее состояние: {current_state}")

@router.message(NoteCreation.title)
async def process_note_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    logging.info(f"Заголовок получен: {message.text}")
    await state.set_state(NoteCreation.content)
    await message.answer("Введите содержимое заметки:")
    current_state = await state.get_state()
    logging.info(f"Текущее состояние: {current_state}")

@router.message(NoteCreation.content)
async def process_note_content(message: types.Message, state: FSMContext):
    await state.update_data(content=message.text)
    logging.info(f"Содержимое получено: {message.text}")
    await state.set_state(NoteCreation.tags)
    await message.answer("Введите теги для заметки (через запятую):")
    current_state = await state.get_state()
    logging.info(f"Текущее состояние: {current_state}")

@router.message(NoteCreation.tags)
async def process_note_tags(message: types.Message, state: FSMContext):
    api_token = user_tokens.get(message.from_user.id)
    if not api_token:
        await message.answer("Сначала авторизуйтесь через /auth и предоставьте ваш API токен.")
        return

    user_data = await state.get_data()
    title = user_data.get('title')
    content = user_data.get('content')
    tags = message.text.split(',')

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/notes/",
                json={"title": title, "content": content, "tags": tags},
                headers={'Authorization': f'Bearer {api_token}'}
            )

        if response.status_code == 200:
            await message.answer("Заметка успешно создана!")

        else:
            logging.info(response.text)
            await message.answer("Ошибка при создании заметки.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

    await state.clear()
    logging.info("Состояние завершено.")

@router.message(Command(commands=['search_notes']))
async def search_notes_start(message: types.Message, state: FSMContext):
    api_token = user_tokens.get(message.from_user.id)
    if not api_token:
        await message.answer("Сначала авторизуйтесь через /auth и предоставьте ваш API токен.")
        return

    await state.set_state(NoteSearch.tags)
    await message.answer("Введите теги для поиска (через запятую):")

@router.message(NoteSearch.tags)
async def process_note_search(message: types.Message, state: FSMContext):
    api_token = user_tokens.get(message.from_user.id)
    if not api_token:
        await message.answer("Сначала авторизуйтесь через /auth и предоставьте ваш API токен.")
        return

    tags = message.text
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/notes/search/",
                params={"tags": tags},
                headers={'Authorization': f'Bearer {api_token}'}
            )

        if response.status_code == 200:
            notes = response.json()
            if not notes:
                await message.answer("Заметки с указанными тегами не найдены.")
            else:
                for note in notes:
                    await message.answer(f"<b>Заметка</b>: {note['title']}\n<b>Содержимое</b>: {note['content']}\n<b>Теги</b>: {', '.join(note['tags'])}", parse_mode=ParseMode.HTML)
        else:
            await message.answer("Ошибка при поиске заметок.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)

    dp.include_router(router)

    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
