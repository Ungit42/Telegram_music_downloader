# 🎵 Telegram Music Downloader v.r01

Программа для скачивания аудио и голосовых сообщений из чатов, каналов и групп Telegram.  
Работает через официальный API Telegram с помощью библиотеки [Pyrogram](https://docs.pyrogram.org).

---

## 🚀 Быстрый старт

1. Скачайте файлы `TGmdown.py` и `requirements.txt`.
2. Убедитесь, что у вас установлен **Python 3.10+**. (Windows)
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Запустите программу:
   ```bash
   python TGmdown.py
   ```
5. При первом запуске рядом создаётся файл `auth.txt`.  
   Заполните его:
   ```ini
   API_ID=ваш_API_ID
   API_HASH=ваш_API_HASH
   PHONE_NUMBER=ваш_номер_телефона
   ```
   👉 API ID и Hash можно получить на [my.telegram.org](https://my.telegram.org).

---

## 📖 Подробная инструкция (с нуля)

### 1. Установка Python
- **Windows**:  
  Скачайте [Python 3.10+](https://www.python.org/downloads/) и при установке отметьте галочку **"Add Python to PATH"**.
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip -y
  ```
- **macOS**:
  ```bash
  brew install python3
  ```

Проверьте установку:
```bash
python --version
pip --version
```

---

### 2. Клонирование проекта или загрузка файлов
- Скачайте `TGmdown.py` и `requirements.txt` вручную  
  **или** клонируйте репозиторий:
  ```bash
  git clone https://github.com/username/telegram-music-downloader.git
  cd telegram-music-downloader
  ```

---

### 3. Установка зависимостей
В папке проекта выполните:
```bash
pip install -r requirements.txt
```

---

### 4. Настройка `auth.txt`
При первом запуске создаётся файл `auth.txt`. Заполните его своими данными:
```ini
API_ID=123456
API_HASH=abcdef1234567890abcdef1234567890
PHONE_NUMBER=+79998887766
```

---

### 5. Запуск программы
```bash
python TGmdown.py
```

После запуска откроется окно с интерфейсом:
- Нажмите **Авторизоваться** и введите код, присланный в Telegram.
- Нажмите **Считать группы/каналы**, выберите нужный чат.
- Используйте кнопки:
  - **Сканировать аудио (поток)** — найти все аудио в чате,
  - **Скачать аудио (поток)** — сохранить их в выбранную папку.

---

## 📂 Папка загрузки

По умолчанию файлы сохраняются в:  
- **Windows**: `C:\Users\<Имя>\Music\TelegramMusic`  
- **Linux/macOS**: `~/Music/TelegramMusic`  

Изменить папку можно кнопкой **"Выбрать папку для музыки"**.  

---

## 📌 Основные возможности

- Авторизация через Telegram API  
- Просмотр списка чатов и каналов  
- Выбор папки для загрузки  
- Сканирование аудио и голосовых сообщений  
- Скачивание файлов  
- Автоматическое ведение логов и отчётов  

---

## 👨‍💻 Автор

- Email: `ungit42@gmail.com`  
- Telegram: [@Kelhiury](https://t.me/Kelhiury)