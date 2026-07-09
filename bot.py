import asyncio
import sqlite3
import base64
from typing import Callable, Dict, Any, Awaitable

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import BaseMiddleware
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "XXX"
SECRET_KEY = "XXX"
SALT = b"my_salt_16bytes"  # ровно 16 байт
DB_NAME = "passwords.db"

# ========== АВТОРИЗАЦИЯ ПО КЛЮЧУ ==========
authorized_users = {}

class AuthState(StatesGroup):
    waiting_for_key = State()

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        # Команду /start пропускаем всегда
        if event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # Получаем текущее состояние FSM
        state = data.get("state")
        if state is not None:
            current_state = await state.get_state()
            # Если пользователь в процессе ввода ключа — пропускаем
            if current_state == AuthState.waiting_for_key:
                return await handler(event, data)

        # В остальных случаях — только для авторизованных
        if event.from_user.id not in authorized_users:
            await event.answer("⛔️ Доступ запрещён. Напишите /start")
            return
        return await handler(event, data)

# ========== ШИФРОВАНИЕ ==========
def get_key_from_master(master_password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

def encrypt_password(password: str, master_password: str) -> str:
    f = Fernet(get_key_from_master(master_password))
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str, master_password: str) -> str:
    f = Fernet(get_key_from_master(master_password))
    return f.decrypt(encrypted.encode()).decode()

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS passwords
                 (service TEXT PRIMARY KEY, login TEXT, encrypted TEXT)''')
    conn.commit()
    conn.close()

def add_or_update(service: str, login: str, encrypted: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("REPLACE INTO passwords VALUES (?, ?, ?)", (service, login, encrypted))
    conn.commit()
    conn.close()

def find_record(service: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT login, encrypted FROM passwords WHERE service=?", (service,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_services():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT service, login FROM passwords")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_service(service: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM passwords WHERE service=?", (service,))
    conn.commit()
    conn.close()

# ========== FSM ДЛЯ ПАРОЛЕЙ ==========
class PasswordStates(StatesGroup):
    waiting_for_master_for_add = State()
    waiting_for_master_for_get = State()

# ========== СОЗДАНИЕ БОТА И ДИСПЕТЧЕРА ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.message.middleware(AuthMiddleware())
# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ГЛАВНОГО МЕНЮ ==========
async def show_main_menu(message: types.Message):
    await message.answer(
        "🔐 *Надёжный Сейф. Хранит пароли в зашифрованной броне.*\n\n"
        "Все пароли хранятся в зашифрованном виде.\n"
        "Мастер-пароль не сохраняется — вводите его при каждой операции.\n\n"
        "Команды:\n"
        "/add сервис логин пароль — добавить запись\n"
        "/get сервис — получить пароль\n"
        "/list — показать все сервисы и логины\n"
        "/del сервис — удалить запись\n\n"
        "⚠️ Мастер-пароль передаётся в Telegram, но не хранится на сервере.\n"
        "⚠️ Секретный ключ нужен только для первого входа.",
        parse_mode="Markdown"
    )

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in authorized_users:
        await show_main_menu(message)
        return
    await message.answer("🔐 Введите секретный ключ для доступа:")
    await state.set_state(AuthState.waiting_for_key)

@dp.message(AuthState.waiting_for_key)
async def process_key(message: types.Message, state: FSMContext):
    print(f"[DEBUG] Получен ключ: '{message.text}'")  # отладка
    if message.text == SECRET_KEY:
        authorized_users[message.from_user.id] = True
        await message.answer("✅ Ключ верный! Доступ разрешён.")
        await show_main_menu(message)
        await state.clear()
    else:
        await message.answer("❌ Неверный ключ. Доступ запрещён. Попробуйте /start снова.")
        await state.clear()

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    rows = get_all_services()
    if not rows:
        await message.answer("Список пуст.")
        return
    answer = "📋 *Сервисы и логины:*\n"
    for service, login in rows:
        answer += f"• *{service}* — `{login}`\n"
    await message.answer(answer, parse_mode="Markdown")

@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("❌ Формат: /add сервис логин пароль", parse_mode="Markdown")
        return
    service, login, password = parts[1], parts[2], parts[3]
    await state.update_data(add_service=service, add_login=login, add_password=password)
    await message.answer("🔐 Введите мастер-пароль для шифрования и сохранения:")
    await state.set_state(PasswordStates.waiting_for_master_for_add)

@dp.message(PasswordStates.waiting_for_master_for_add)
async def process_master_for_add(message: types.Message, state: FSMContext):
    master = message.text
    data = await state.get_data()
    service = data["add_service"]
    login = data["add_login"]
    password = data["add_password"]
    try:
        encrypted = encrypt_password(password, master)
        add_or_update(service, login, encrypted)
        await message.answer(f"✅ Пароль для '{service}' сохранён (зашифрован).")
    except Exception as e:
        await message.answer(f"❌ Ошибка шифрования. Неверный мастер-пароль? Ошибка: {e}")
    finally:
        await state.clear()

@dp.message(Command("get"))
async def cmd_get(message: types.Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите сервис: /get gmail", parse_mode="Markdown")
        return
    service = parts[1]
    record = find_record(service)
    if not record:
        await message.answer(f"❌ Сервис '{service}' не найден.")
        return
    login, encrypted = record
    await state.update_data(get_service=service, get_login=login, get_encrypted=encrypted)
    await message.answer(f"🔐 Введите мастер-пароль для расшифровки пароля от *{service}*:", parse_mode="Markdown")
    await state.set_state(PasswordStates.waiting_for_master_for_get)
  @dp.message(PasswordStates.waiting_for_master_for_get)
async def process_master_for_get(message: types.Message, state: FSMContext):
    master = message.text
    data = await state.get_data()
    service = data["get_service"]
    login = data["get_login"]
    encrypted = data["get_encrypted"]
    try:
        password = decrypt_password(encrypted, master)
        await message.answer(
            f"🔓 *{service}*\nЛогин: `{login}`\nПароль: `{password}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Неверный мастер-пароль или данные повреждены. Ошибка: {e}")
    finally:
        await state.clear()

@dp.message(Command("del"))
async def cmd_delete(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите сервис: /del gmail", parse_mode="Markdown")
        return
    service = parts[1]
    record = find_record(service)
    if not record:
        await message.answer(f"❌ Сервис '{service}' не найден.")
        return
    delete_service(service)
    await message.answer(f"🗑 Запись для сервиса '{service}' удалена.")

# ========== ЗАПУСК ==========
async def main():
    init_db()
    print("Бот запущен. Пароли шифруются. Требуется секретный ключ при старте.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
