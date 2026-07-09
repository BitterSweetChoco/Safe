## English🟥

### 🔐 Secure Safe – Telegram Password Manager

Secure Safe is a Telegram bot that securely stores your passwords. All passwords are encrypted using a master password that you provide on the fly – it is never stored anywhere. The bot also requires a secret key for initial access, adding an extra layer of protection.

#### ✨ Features
- Secure encryption – each password is encrypted with Fernet (symmetric encryption) using a master password derived with PBKDF2.
- Master password never saved – you enter it each time you add or retrieve a password.
- Secret key authorization – only users who know the secret key can access the bot (useful for private deployment).
- Simple commands – add, get, list, and delete service credentials.
- Lightweight – uses SQLite for local storage, no external database required.

#### 🛠 Installation & Setup
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Replace the hardcoded credentials in bot.py with environment variables (recommended):
   - BOT_TOKEN – your Telegram Bot Token from @BotFather.
   - SECRET_KEY – a secret key that users must enter to authorize.
   - SALT – a fixed 16‑byte salt for key derivation (you can generate your own).
3. Run the bot:
   ```bash
   python bot.py
   ```

#### 📋 Usage
Once started, every new user must send the secret key to gain access. Then the following commands are available:

| Command | Description |
|---------|-------------|
| /add service login password | Store a new password (you will be prompted for your master password) |
| /get service               | Retrieve the password for a service (master password required) |
| /list                      | Show all stored services and logins |
| /del service               | Delete a service entry |

#### ⚠️ Security Notes
- The master password is transmitted in plain text to the bot (Telegram messages are encrypted in transit, but the bot sees them). Do not use a master password that you use elsewhere.
- The secret key provides basic access control; change it regularly.
- For production, use environment variables instead of hardcoding secrets.

---

## Русский🟩

### 🔐 Надёжный Сейф – менеджер паролей в Telegram

Надежный Сейф — это Telegram-бот для безопасного хранения паролей. Все пароли шифруются с помощью мастер-пароля, который вы вводите при каждой операции – он нигде не сохраняется. Для первоначального доступа требуется секретный ключ, что добавляет дополнительный уровень защиты.

#### ✨ Возможности
- Надёжное шифрование – каждый пароль шифруется алгоритмом Fernet (симметричное шифрование) с использованием мастер-пароля, преобразованного через PBKDF2.
- Мастер-пароль не хранится – вы вводите его каждый раз при добавлении или получении пароля.
- Авторизация по секретному ключу – только знающие ключ пользователи могут получить доступ к боту (удобно для личного использования).
- Простые команды – добавление, получение, список и удаление записей.
- Лёгкость – использует SQLite для локального хранения, не требует внешней базы данных.

#### 🛠 Установка и настройка
1. Клонируйте репозиторий и установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Замените жёстко заданные данные в bot.py на переменные окружения (рекомендуется):
   - BOT_TOKEN – токен вашего бота от @BotFather.
   - SECRET_KEY – секретный ключ, который пользователи должны ввести для доступа.
   - SALT – фиксированная 16‑байтовая соль для генерации ключа (можно сгенерировать свою).
3. Запустите бота:
   ```bash
   python bot.py
   ```

#### 📋 Использование
После запуска каждый новый пользователь должен отправить секретный ключ для получения доступа. Затем доступны команды:

| Команда | Описание |
|---------|----------|
| /add сервис логин пароль | Сохранить новый пароль (будет запрошен мастер-пароль) |
| /get сервис               | Получить пароль для сервиса (требуется мастер-пароль) |
| /list                     | Показать все сохранённые сервисы и логины |
| /del сервис               | Удалить запись о сервисе |
#### ⚠️ Замечания по безопасности
- Мастер-пароль передаётся в открытом виде в бот (сообщения Telegram шифруются при передаче, но бот их видит). Не используйте мастер-пароль, который вы применяете где-либо ещё.
- Секретный ключ обеспечивает базовый контроль доступа; меняйте его периодически.
- В производственном окружении используйте переменные окружения, а не жёстко заданные секреты в коде.
