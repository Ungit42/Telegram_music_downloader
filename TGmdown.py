#!/usr/bin/env python3
# coding: utf-8

import os
import re
import json
import threading
import mimetypes
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import asyncio
import logging
from datetime import datetime
from pyrogram import Client
import webbrowser  # для открытия ссылок

# ====== Константы ======
CONFIG_FILE = "config.json"
AUTH_FILE = "auth.txt"
LOG_DIR = "logs"

# ====== Окно "О программе" ======
def make_about_window(parent):
    win = tk.Toplevel(parent)
    win.title("О программе")
    win.geometry("520x120")
    win.resizable(False, False)

    frame = tk.Frame(win, padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    txt = tk.Text(frame, wrap="word", height=6, width=64)
    txt.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(frame, command=txt.yview)
    scrollbar.pack(side="right", fill="y")
    txt.config(yscrollcommand=scrollbar.set)
    txt.insert("end", "Telegram Music Downloader v.r01\n\n")
    txt.tag_add("title", "1.0", "1.end")
    txt.tag_config("title", foreground="darkblue", font=("Helvetica", 14, "underline"))
    
    # Email
    txt.insert("end", "Email: ")
    start = txt.index("end-1c")
    txt.insert("end", "ungit42@gmail.com\n")
    txt.tag_add("email", start, "end-1c")

    # Telegram
    txt.insert("end", "Telegram: ")
    start = txt.index("end-1c")
    txt.insert("end", "@Kelhiury")
    endpos = txt.index("end-1c")
    txt.insert("end", " (https://t.me/Kelhiury)\n")
    txt.tag_add("telegram_handle", start, endpos)
    txt.tag_add("telegram_url", f"{endpos} + 2 chars", "end-1c")

    # Github
    txt.insert("end", "Github: ")
    start = txt.index("end-1c")
    txt.insert("end", "https://github.com/Ungit42/Telegram_music_downloader\n")
    txt.tag_add("github", start, "end-1c")

    # Стили + события
    def link_tag(tag, action):
        txt.tag_config(tag, foreground="blue", underline=1)
        txt.tag_bind(tag, "<Button-1>", lambda e: action())
        txt.tag_bind(tag, "<Enter>", lambda e: txt.config(cursor="hand2"))
        txt.tag_bind(tag, "<Leave>", lambda e: txt.config(cursor=""))

    link_tag("email", lambda: webbrowser.open("mailto:ungit42@gmail.com"))
    link_tag("telegram_handle", lambda: webbrowser.open("https://t.me/Kelhiury"))
    link_tag("telegram_url", lambda: webbrowser.open("https://t.me/Kelhiury"))
    link_tag("github", lambda: webbrowser.open("https://github.com/Ungit42/Telegram_music_downloader"))

    # Запрет редактирования, но разрешить копирование
    txt.bind("<Key>", lambda e: "break")
    def copy_selection(event=None):
        try:
            sel = txt.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return "break"
        win.clipboard_clear()
        win.clipboard_append(sel)
        return "break"
    txt.bind("<Control-c>", copy_selection)
    txt.bind("<Control-C>", copy_selection)
    txt.config(insertwidth=0)

    txt.focus_set()
    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)

# ====== Логирование ======
os.makedirs(LOG_DIR, exist_ok=True)
logfile = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)
logger.info("Запуск приложения")

# ====== Утилиты ======
def sanitize_filename(name: str) -> str:
    name = name or ""
    name = re.sub(r'[\\/:\*\?"<>\|]', "_", name)
    name = name.strip()
    if not name:
        name = "file"
    return name

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки config.json: {e}")
            return {}
    return {}

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)
    logger.info("Настройки сохранены в config.json")

def create_auth_template(path=AUTH_FILE):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Заполните параметры и сохраните файл\nAPI_ID=\nAPI_HASH=\nPHONE_NUMBER=\n")

def parse_auth_file(path=AUTH_FILE):
    res = {"api_id": "", "api_hash": "", "phone_number": ""}
    if not os.path.exists(path):
        return res
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
            elif ":" in line:
                k, v = line.split(":", 1)
            else:
                continue
            k = k.strip().lower()
            v = v.strip()
            if k in ("api_id", "api id", "id"):
                res["api_id"] = v
            elif k in ("api_hash", "apihash", "hash"):
                res["api_hash"] = v
            elif k in ("phone", "phone_number", "phone number", "phone-number"):
                res["phone_number"] = v
    return res

def session_exists(session_name: str) -> bool:
    pattern = session_name + ".session"
    for item in os.listdir("."):
        if item.startswith(session_name) and ("session" in item):
            return True
    if os.path.exists(pattern):
        return True
    return False

def remove_session_files(session_name: str):
    removed = []
    for item in os.listdir("."):
        if item.startswith(session_name) and ("session" in item):
            try:
                path = os.path.join(".", item)
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                removed.append(item)
            except Exception:
                pass
    try:
        if os.path.exists(f"{session_name}.session"):
            os.remove(f"{session_name}.session")
            removed.append(f"{session_name}.session")
    except Exception:
        pass
    return removed
# ====== Основное приложение ======
class TelegramMusicApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Telegram Music Downloader v.r01")
        self.root.geometry("950x900")

        # ====== Конфиг и папка для скачивания ======
        self.config = load_config()
        default_dl = os.path.join(os.path.expanduser("~"), "Music", "TelegramMusic")
        self.download_folder = self.config.get("download_folder", default_dl)
        os.makedirs(self.download_folder, exist_ok=True)

        # ====== Подготовка auth.txt ======
        create_auth_template(AUTH_FILE)
        auth_values = parse_auth_file(AUTH_FILE)

        # ====== 1 блок: Поля ввода данных ======
        input_frame = tk.Frame(root, padx=6, pady=6, relief=tk.RIDGE, bd=2)
        input_frame.pack(fill="x", padx=6, pady=4)
        self.api_id_entry = self._make_labeled_entry_frame(input_frame, "API ID:",
                                                           "Получить можно в my.telegram.org",
                                                           auth_values.get("api_id", self.config.get("api_id", "")),
                                                           hidden=True)
        self.api_hash_entry = self._make_labeled_entry_frame(input_frame, "API Hash:",
                                                             "Получить можно в my.telegram.org",
                                                             auth_values.get("api_hash", self.config.get("api_hash", "")),
                                                             hidden=True)
        self.session_name_entry = self._make_labeled_entry_frame(input_frame, "Имя сессии:",
                                                                 "Имя файла сессии для хранения авторизации",
                                                                 self.config.get("session_name", "telegram_music"))
        self.phone_entry = self._make_labeled_entry_frame(input_frame, "Номер телефона:",
                                                          "Номер Telegram-аккаунта",
                                                          auth_values.get("phone_number", self.config.get("phone_number", "")),
                                                          hidden=True)
        self.chat_id_entry = self._make_labeled_entry_frame(input_frame, "ID выбранного чата:",
                                                            "ID группы/канала/чата",
                                                            self.config.get("chat_id", ""))

        # ====== Кнопка показать/скрыть данные ======
        self.show_passwords = False
        toggle_frame = tk.Frame(root, padx=6, pady=2)
        toggle_frame.pack(fill="x", padx=6, pady=2)
        self.toggle_button = tk.Button(toggle_frame, text="Показать данные", width=22, command=self.toggle_auth_fields)
        self.toggle_button.pack(side="left")

        # ====== 2 блок: Кнопки авторизации ======
        auth_frame = tk.Frame(root, padx=6, pady=4)
        auth_frame.pack(fill="x", padx=6, pady=4)
        self._make_button_with_help_frame(auth_frame, "Авторизоваться", self.login, "Авторизация через API")
        self._make_button_with_help_frame(auth_frame, "Подгрузить auth.txt", self.reload_auth_data, "Подгрузка данных из auth.txt")
        self._make_button_with_help_frame(auth_frame, "Разлогиниться", self.logout, "Выйти из сессии")
        self._make_button_with_help_frame(auth_frame, "Сохранить настройки", self.save_settings, "Сохранение config.json")
        self._make_button_with_help_frame(auth_frame, "Удалить данные авторизации", self.clear_auth_data, "Очистка config.json и auth.txt")

        # ====== 3 блок: Список чатов ======
        list_frame = tk.Frame(root, padx=6, pady=4)
        list_frame.pack(fill="both", expand=True, padx=6, pady=4)
        tk.Label(list_frame, text="Список групп/каналов:").pack(anchor="w")
        self.chat_listbox = tk.Listbox(list_frame, width=110, height=15)
        self.chat_listbox.pack(side="left", fill="both", expand=True, pady=4)
        self.chat_listbox.bind("<<ListboxSelect>>", self.on_chat_select)
        chat_scroll = tk.Scrollbar(list_frame, command=self.chat_listbox.yview)
        chat_scroll.pack(side="right", fill="y")
        self.chat_listbox.config(yscrollcommand=chat_scroll.set)

        # ====== 4 блок: Папка для загрузки ======
        folder_frame = tk.Frame(root, padx=6, pady=4)
        folder_frame.pack(fill="x", padx=6, pady=4)
        self._make_button_with_help_frame(folder_frame, "Выбрать папку для музыки", self.choose_folder, "Папка для загрузки")
        self.folder_label = tk.Label(folder_frame, text=f"📂 Папка: {self.download_folder}", fg="gray", wraplength=900, anchor="w", justify="left")
        self.folder_label.pack(fill="x", pady=4)

        # ====== 5 блок: Кнопки действий ======
        action_frame = tk.Frame(root, padx=6, pady=4)
        action_frame.pack(fill="x", padx=6, pady=4)
        self._make_button_with_help_frame(action_frame, "Считать группы/каналы", self.fetch_chats, "Подгрузка чатов")
        self._make_button_with_help_frame(action_frame, "Сканировать аудио (поток)", self.scan_audio_threaded, "Сканирование аудио")
        self._make_button_with_help_frame(action_frame, "Скачать аудио (поток)", self.download_audio_threaded, "Скачивание аудио")

        # ====== 6 блок: Статус и прогресс ======
        progress_frame = tk.Frame(root, padx=6, pady=4, relief=tk.GROOVE, bd=2)
        progress_frame.pack(fill="x", padx=6, pady=4)
        self.status_label = tk.Label(progress_frame, text="⛔ Не авторизован", fg="red", anchor="w")
        self.status_label.pack(fill="x", pady=2)
        self.stats_label = tk.Label(progress_frame, text="Найдено: 0 | Скачано: 0 | Пропущено: 0 | Повторов: 0", anchor="w")
        self.stats_label.pack(fill="x", pady=2)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, length=480, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=4)
        self.cancel_button = tk.Button(progress_frame, text="❌", command=self.cancel_process)
        self.cancel_button.pack(pady=2, anchor="e")

        # ====== 7 блок: Автор и "О программе" ======
        author_frame = tk.Frame(root, padx=6, pady=4)
        author_frame.pack(fill="x", padx=6, pady=2)
        self.author_label = tk.Label(author_frame, text="Автор: UN | Telegram: @Kelhiury", fg="gray", anchor="w")
        self.author_label.pack(fill="x")

        about_frame = tk.Frame(root, padx=6, pady=4)
        about_frame.pack(fill="x", padx=6, pady=4)
        tk.Button(about_frame, text="О программе", width=22, command=lambda: make_about_window(self.root)).pack()

        # ====== Инициализация ======
        self.chats_all = []
        self.stats = {"found": 0, "downloaded": 0, "skipped": 0, "duplicates": 0}
        self.stop_flag = False

        self.load_auth_if_no_session()
        self.update_status()
        logger.info("UI инициализирован")
    # ====== Методы для кнопки показать/скрыть ======
    def toggle_auth_fields(self):
        self.show_passwords = not self.show_passwords
        show_char = "" if self.show_passwords else "*"
        for entry in [self.api_id_entry, self.api_hash_entry, self.phone_entry]:
            entry.config(show=show_char)
        self.toggle_button.config(text="Скрыть данные" if self.show_passwords else "Показать данные")

    # ====== Вспомогательные методы GUI ======
    def _make_labeled_entry_frame(self, parent, text, hint, default="", hidden=False):
        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=2)
        tk.Label(frame, text=text, width=20, anchor="e").pack(side="left")
        entry = tk.Entry(frame, width=60, show="*" if hidden else "")
        entry.pack(side="left", fill="x", expand=True)
        entry.insert(0, default or "")
        tk.Button(frame, text="❔", command=lambda: messagebox.showinfo(text, hint), width=2).pack(side="left")
        return entry

    def _make_button_with_help_frame(self, parent, text, command, hint=None):
        frame = tk.Frame(parent)
        frame.pack(side="left", padx=4)
        tk.Button(frame, text=text, command=command, width=22).pack(side="left")
        if hint:
            tk.Button(frame, text="❔", command=lambda: messagebox.showinfo(text, hint), width=2).pack(side="left")

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для загрузки", initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_label.config(text=f"📂 Папка: {self.download_folder}")
            self.save_settings()
            logger.info(f"Папка для загрузки изменена: {self.download_folder}")

    def load_auth_if_no_session(self):
        session_name = self.session_name_entry.get().strip()
        if not session_exists(session_name):
            auth = parse_auth_file(AUTH_FILE)
            self.api_id_entry.delete(0, tk.END)
            self.api_id_entry.insert(0, auth.get("api_id",""))
            self.api_hash_entry.delete(0, tk.END)
            self.api_hash_entry.insert(0, auth.get("api_hash",""))
            self.phone_entry.delete(0, tk.END)
            self.phone_entry.insert(0, auth.get("phone_number",""))

    def update_status(self):
        session_name = self.session_name_entry.get().strip()
        if session_exists(session_name):
            self.status_label.config(text="✅ Авторизован", fg="green")
        else:
            self.status_label.config(text="⛔ Не авторизован", fg="red")
        stats_text = (f"Найдено: {self.stats['found']} | "
                      f"Скачано: {self.stats['downloaded']} | "
                      f"Пропущено: {self.stats['skipped']} | "
                      f"Повторов: {self.stats['duplicates']}")
        self.stats_label.config(text=stats_text)

    # ====== Авторизация ======
    def login(self):
        api_id = self.api_id_entry.get().strip()
        api_hash = self.api_hash_entry.get().strip()
        session_name = self.session_name_entry.get().strip()
        if not api_id or not api_hash or not session_name:
            messagebox.showerror("Ошибка", "Заполните API_ID, API_HASH и имя сессии")
            return
        try:
            api_id_int = int(api_id)
        except:
            messagebox.showerror("Ошибка", "API ID должно быть числом")
            return
        try:
            with Client(session_name, api_id=api_id_int, api_hash=api_hash) as app:
                me = app.get_me()
                messagebox.showinfo("Успех", f"Авторизация успешна: {getattr(me, 'first_name', 'user')}")
            self.save_settings()
            logger.info("Авторизация успешна")
            self.update_status()
        except Exception as e:
            logger.exception("Ошибка авторизации")
            messagebox.showerror("Ошибка авторизации", str(e))
            self.update_status()

    def logout(self):
        session_name = self.session_name_entry.get().strip()
        removed = remove_session_files(session_name)
        if removed:
            messagebox.showinfo("Разлогин", f"Удалено: {', '.join(removed)}")
            logger.info(f"Удалены файлы сессии: {removed}")
        else:
            messagebox.showwarning("Разлогин", "Файлы сессии не найдены")
        self.update_status()

    def reload_auth_data(self):
        auth = parse_auth_file(AUTH_FILE)
        self.api_id_entry.delete(0, tk.END)
        self.api_id_entry.insert(0, auth.get("api_id", ""))
        self.api_hash_entry.delete(0, tk.END)
        self.api_hash_entry.insert(0, auth.get("api_hash", ""))
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, auth.get("phone_number", ""))
        messagebox.showinfo("Готово", "Данные из auth.txt подгружены (если были).")
        logger.info("Данные auth.txt подгружены")
        self.update_status()

    def clear_auth_data(self):
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
        if os.path.exists(AUTH_FILE): os.remove(AUTH_FILE)
        create_auth_template(AUTH_FILE)
        for e in [self.api_id_entry, self.api_hash_entry, self.phone_entry, self.session_name_entry, self.chat_id_entry]:
            e.delete(0, tk.END)
        self.session_name_entry.insert(0, "telegram_music")
        self.chat_listbox.delete(0, tk.END)
        self.chats_all = []
        self.update_status()
        messagebox.showinfo("Готово", "Данные авторизации удалены, auth.txt пересоздан.")
        logger.info("Данные авторизации очищены и auth.txt пересоздан")

    def save_settings(self):
        cfg = {
            "api_id": self.api_id_entry.get().strip(),
            "api_hash": self.api_hash_entry.get().strip(),
            "session_name": self.session_name_entry.get().strip(),
            "phone_number": self.phone_entry.get().strip(),
            "download_folder": self.download_folder,
            "chat_id": self.chat_id_entry.get().strip()
        }
        save_config(cfg)
        messagebox.showinfo("Сохранено", "Настройки сохранены в config.json")
        logger.info("Сохранены настройки пользователя")

    def cancel_process(self):
        if messagebox.askyesno("Подтверждение", "Действительно остановить процесс?"):
            self.stop_flag = True
            logger.info("Процесс отменен пользователем")
    # ====== Работа со списком чатов ======
    def fetch_chats(self):
        try:
            api_id = int(self.api_id_entry.get().strip())
            api_hash = self.api_hash_entry.get().strip()
            session_name = self.session_name_entry.get().strip()
        except Exception as e:
            messagebox.showerror("Ошибка", "Неверные данные авторизации")
            logger.error(f"Ошибка при получении данных авторизации: {e}")
            return
        try:
            with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
                self.chat_listbox.delete(0, tk.END)
                self.chats_all = []
                for dlg in app.get_dialogs():
                    title = getattr(dlg.chat, "title", None) or getattr(dlg.chat, "first_name", None) or "Чат"
                    cid = dlg.chat.id
                    uname = getattr(dlg.chat, "username", "") or ""
                    label = f"{title} ({cid})" + (f" [@{uname}]" if uname else "")
                    self.chats_all.append((label, cid, uname))
                    self.chat_listbox.insert(tk.END, label)
                if not self.chats_all:
                    messagebox.showinfo("Результат", "Чаты не найдены")
                logger.info(f"Подгружено чатов: {len(self.chats_all)}")
        except Exception as e:
            logger.exception("Ошибка при получении списка чатов")
            messagebox.showerror("Ошибка", str(e))

    def on_chat_select(self, event):
        sel = event.widget.curselection()
        if not sel: return
        idx = sel[0]
        _, cid, _ = self.chats_all[idx]
        self.chat_id_entry.delete(0, tk.END)
        self.chat_id_entry.insert(0, str(cid))

    async def get_chat_label(self, app, chat_id):
        try:
            chat = await app.get_chat(chat_id)
            title = getattr(chat, "title", None) or getattr(chat, "first_name", None) or f"chat_{chat_id}"
            uname = getattr(chat, "username", "") or ""
            return f"{title} ({chat_id})" + (f" [@{uname}]" if uname else "")
        except Exception:
            return f"chat_{chat_id}"

    # ====== Потоковое сканирование аудио ======
    def scan_audio_threaded(self):
        self.stop_flag = False
        threading.Thread(target=self._scan_worker_thread, daemon=True).start()

    def _scan_worker_thread(self):
        self.stats.update({"found":0,"downloaded":0,"skipped":0,"duplicates":0})
        self.progress_var.set(0)
        self.update_status()

        chat_id = self.chat_id_entry.get().strip()
        if not chat_id:
            messagebox.showerror("Ошибка", "Выберите чат")
            return
        try:
            api_id = int(self.api_id_entry.get().strip())
            api_hash = self.api_hash_entry.get().strip()
            session_name = self.session_name_entry.get().strip()
        except Exception:
            messagebox.showerror("Ошибка", "Неверные данные авторизации")
            return

        timestamp = datetime.now().strftime("%Y.%m.%d - %H_%M")
        report_file = None
        error_file = None
        chat_label = f"chat_{chat_id}"

        async def scan_async():
            nonlocal report_file, error_file, chat_label
            audio_list = []
            errors = []
            try:
                async with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
                    chat_label = next(
                        ((label) for label, cid, _ in getattr(self,"chats_all",[]) if str(cid)==chat_id),
                        None
                    )
                    if not chat_label:
                        chat_label = await self.get_chat_label(app, chat_id)
                    safe_label = sanitize_filename(chat_label)
                    report_file = os.path.join(self.download_folder, f"{timestamp}_scan_report_{safe_label}.txt")
                    error_file = os.path.join(self.download_folder, f"{timestamp}_scan_errors_{safe_label}.txt")

                    total = 0
                    async for _ in app.get_chat_history(chat_id):
                        total +=1

                    processed = 0
                    async for msg in app.get_chat_history(chat_id):
                        if self.stop_flag:
                            errors.append("Сканирование остановлено пользователем")
                            break
                        try:
                            if getattr(msg, "audio", None) or getattr(msg, "voice", None):
                                audio_list.append(msg)
                                self.stats["found"] +=1
                                self.update_status()
                        except Exception as e:
                            errors.append(f"Ошибка msg_id {getattr(msg,'id','N/A')}: {e}")
                        processed += 1
                        self.root.after(0, lambda v=processed/total*100: self.progress_var.set(v))
            except Exception as e:
                logger.exception("Критическая ошибка во время сканирования")
                errors.append(f"Critical: {e}")
            return audio_list, errors

        try:
            audio_list, errors = asyncio.run(scan_async())
            # Запись отчета
            try:
                with open(report_file,"w",encoding="utf-8") as rf:
                    header = [
                        "=== Отчёт о сканировании ===",
                        f"Чат: {chat_label}",
                        f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        f"Всего найдено: {len(audio_list)}",
                        f"Скачано: {self.stats['downloaded']}",
                        f"Пропущено: {self.stats['skipped']}",
                        f"Повторов: {self.stats['duplicates']}",
                        "="*30
                    ]
                    rf.write("\n".join(header)+"\n")
                    for msg in audio_list:
                        try:
                            if getattr(msg,"audio",None):
                                ext = mimetypes.guess_extension(msg.audio.mime_type) or ".mp3"
                                fname = msg.audio.file_name or f"audio_{msg.id}{ext}"
                                dur = getattr(msg.audio,"duration",None)
                            elif getattr(msg,"voice",None):
                                fname = f"voice_{msg.id}.ogg"
                                dur = getattr(msg.voice,"duration",None)
                            else:
                                continue
                            date_str = getattr(msg,"date",None)
                            date_formatted = date_str.strftime('%Y-%m-%d %H:%M:%S') if date_str else "N/A"
                            rf.write(f"{fname} | message_id: {msg.id} | duration: {dur}s | date: {date_formatted}\n")
                        except Exception as e:
                            logger.exception(f"Ошибка записи строки отчёта msg {getattr(msg,'id','N/A')}: {e}")
            except Exception as e:
                logger.exception(f"Не удалось записать файл отчёта: {e}")

            if errors:
                try:
                    with open(error_file,"w",encoding="utf-8") as ef:
                        for err in errors:
                            ef.write(err+"\n")
                except Exception:
                    logger.exception("Не удалось записать файл ошибок")
            messagebox.showinfo("Готово", f"Сканирование завершено. Найдено: {len(audio_list)}")
            self.progress_var.set(0)
            self.update_status()
        except Exception as e:
            logger.exception("Неожиданная ошибка в сканере")
            messagebox.showerror("Ошибка", str(e))
            self.progress_var.set(0)
            self.update_status()
    # ====== Потоковое скачивание аудио ======
    def download_audio_threaded(self):
        self.stop_flag = False
        threading.Thread(target=self._download_worker_thread, daemon=True).start()

    def _download_worker_thread(self):
        self.stats.update({"found":0,"downloaded":0,"skipped":0,"duplicates":0})
        self.progress_var.set(0)
        self.update_status()

        chat_id = self.chat_id_entry.get().strip()
        if not chat_id:
            messagebox.showerror("Ошибка","Выберите чат")
            return
        try:
            api_id = int(self.api_id_entry.get().strip())
            api_hash = self.api_hash_entry.get().strip()
            session_name = self.session_name_entry.get().strip()
        except Exception:
            messagebox.showerror("Ошибка","Неверные данные авторизации")
            return

        timestamp = datetime.now().strftime("%Y.%m.%d - %H_%M")
        report_file = None
        error_file = None
        chat_label = f"chat_{chat_id}"

        async def download_async():
            nonlocal report_file, error_file, chat_label
            errors = []
            to_download=[]
            try:
                async with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
                    chat_label = next(
                        ((label) for label, cid, _ in getattr(self,"chats_all",[]) if str(cid)==chat_id),
                        None
                    )
                    if not chat_label:
                        chat_label = await self.get_chat_label(app, chat_id)
                    safe_label = sanitize_filename(chat_label)
                    chat_folder = os.path.join(self.download_folder, safe_label)
                    os.makedirs(chat_folder, exist_ok=True)
                    report_file = os.path.join(chat_folder, f"{timestamp}_downloaded_{safe_label}.txt")
                    error_file = os.path.join(chat_folder, f"{timestamp}_download_errors_{safe_label}.txt")

                    async for msg in app.get_chat_history(chat_id):
                        if self.stop_flag:
                            errors.append("Скачивание остановлено пользователем")
                            break
                        if getattr(msg,"audio",None) or getattr(msg,"voice",None):
                            to_download.append(msg)

                    total = len(to_download)
                    self.stats["found"]=total

                    for idx,msg in enumerate(to_download):
                        if self.stop_flag: break
                        try:
                            if getattr(msg,"audio",None):
                                ext = mimetypes.guess_extension(msg.audio.mime_type) or ".mp3"
                                fname = msg.audio.file_name or f"audio_{msg.id}{ext}"
                            else:
                                fname = f"voice_{msg.id}.ogg"
                            safe_name = sanitize_filename(fname)
                            out_path = os.path.join(chat_folder,safe_name)
                            if os.path.exists(out_path) and os.path.getsize(out_path)>0:
                                self.stats["duplicates"] += 1
                                logger.info(f"Пропущен (duplicate): {out_path}")
                            else:
                                await msg.download(file_name=out_path)
                                self.stats["downloaded"] += 1
                                logger.info(f"Скачано: {out_path}")
                        except Exception as e:
                            self.stats["skipped"] +=1
                            errtxt = f"Ошибка msg_id {getattr(msg,'id','N/A')}: {e}"
                            errors.append(errtxt)
                            logger.exception(errtxt)
                        self.root.after(0, lambda v=(idx+1)/total*100: self.progress_var.set(v))
                        self.update_status()
            except Exception as e:
                logger.exception("Критическая ошибка во время скачивания")
                errors.append(f"Critical: {e}")
            return len(to_download), errors

        try:
            count, errors = asyncio.run(download_async())
            try:
                with open(report_file,"w",encoding="utf-8") as rf:
                    header = [
                        "=== Отчёт о скачивании ===",
                        f"Чат: {chat_label} ({chat_id})",
                        f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        f"Всего найдено: {self.stats['found']}",
                        f"Скачано: {self.stats['downloaded']}",
                        f"Пропущено: {self.stats['skipped']}",
                        f"Повторов: {self.stats['duplicates']}",
                        "="*30
                    ]
                    rf.write("\n".join(header))
            except Exception:
                logger.exception("Не удалось записать файл отчёта скачивания")

            if errors:
                try:
                    with open(error_file,"w",encoding="utf-8") as ef:
                        for err in errors:
                            ef.write(err+"\n")
                except Exception:
                    logger.exception("Не удалось записать файл ошибок скачивания")

            messagebox.showinfo("Готово", f"Скачивание завершено. Найдено: {self.stats['found']} Скачано: {self.stats['downloaded']}")
            self.progress_var.set(0)
            self.update_status()
        except Exception as e:
            logger.exception("Неожиданная ошибка в загрузчике")
            if error_file:
                with open(error_file,"a",encoding="utf-8") as ef:
                    ef.write(f"Critical error: {e}\n")
            messagebox.showerror("Ошибка", str(e))
            self.progress_var.set(0)
            self.update_status()


# ====== Запуск приложения ======
if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramMusicApp(root)
    root.mainloop()
