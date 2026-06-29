import asyncio
import subprocess
import sqlite3
import re
import os
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "141542593"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "AP1int")

PACKET_TEST = os.getenv("PACKET_TEST", "1024")
PACKET_VIP = os.getenv("PACKET_VIP", "2048")
PACKET_VIP_PREMIUM = os.getenv("PACKET_VIP_PREMIUM", "100")

TOPUP_AMOUNT = os.getenv("TOPUP_AMOUNT", "0.04")
RATE_PER_HOUR = os.getenv("RATE_PER_HOUR", "0.02")
BILLING_URL = os.getenv("BILLING_URL", "https://b.1lot.tv")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

script_semaphore = asyncio.Semaphore(1)
admin_msg_target = {}

_ = {
    "ru": {
        "lang_name": "Русский",
        "lang_btn": "🇷🇺 Русский",
        "choose_lang": "Выберите язык:",
        "lang_changed": "Язык изменён.",
        "test_btn": "🔓 120 минут полного доступа",
        "check_balance_btn": "💰 Проверить баланс",
        "contact_admin": "💬 Связаться с администратором",
        "contact_admin_text": "Свяжитесь с администратором для продления.",
        "back_btn": "◀️ Назад",
        "buy_package": "💳 Подключить полный пакет",
        "renew_btn": "🔄 Продлить пакет",
        "change_lang": "🌐 Язык",
        "start_text": "Доступен полный плейлист (поминуто) или безлимитный пакет (VIP/VIP+XXX).",
        "already_activated": "⚠️ Полный доступ уже был активирован ранее.",
        "playlist_label": "📺 Ваш плейлист:",
        "playlist_not_found": "📺 Ссылка на плейлист будет отправлена администратором.",
        "instruction": "📌 Инструкция:\nСкопируйте ссылку на плейлист в буфер обмена (нажмите на нее) и вставьте в один из IPTV плееров:",
        "android": "📱 Android — <a href=\"https://play.google.com/store/apps/details?id=es.ottplayer.tv\">OTTPlayer</a>",
        "iphone": "📱 iPhone — <a href=\"https://apps.apple.com/us/app/ottplayertv/id1672208961\">OTTPlayer</a>\n📺 <a href=\"https://youtube.com/shorts/ovE0JF-j_do\">Видеоинструкция для iPhone</a>",
        "tv": "📺 Телевизор — любой IPTV плеер",
        "buy_prompt": "💳 Для подключения полного пакета нажмите кнопку ниже.",
        "creating": "⏳ Создаю пользователя...",
        "timeout": "❌ Таймаут. Попробуйте позже.",
        "error": "❌ Ошибка: {e}",
        "create_failed": "❌ Не удалось создать пользователя. Напишите @{admin}.",
        "topup_start": "✅ Пользователь создан. Пополняю баланс...",
        "topup_timeout": "❌ Таймаут при пополнении.",
        "topup_error": "❌ Ошибка пополнения: {e}",
        "activating": "✅ Баланс пополнен. Активирую повременную тарификацию...",
        "activate_failed": "✅ Пользователь создан, но активация не удалась. Обратитесь к @{admin}.",
        "getting_link": "✅ Доступ активирован. Получаю ссылку плейлиста...",
        "success": "✅ 120 минут полного доступа активированы!",
        "balance_label": "💰 Осталось: ~{minutes} мин (~{hd_minutes} мин в HD)",
        "rate_label": "🕐 1 час просмотра = $0.02",
        "prolong_text": "Продлите%20доступ.%20ID%3A%20{tg_id}",
        "buy_text": "Хочу%20подключить%20платный%20пакет.%20ID%3A%20{tg_id}",
        "greeting_text": "Здравствуйте!%20Хочу%20подключить%20платный%20пакет%20IPTV.",
    },
    "en": {
        "lang_name": "English",
        "lang_btn": "🇬🇧 English",
        "choose_lang": "Choose language:",
        "lang_changed": "Language changed.",
        "test_btn": "🔓 120 minutes full access",
        "check_balance_btn": "💰 Check balance",
        "contact_admin": "💬 Contact administrator",
        "contact_admin_text": "Contact the administrator for renewal.",
        "back_btn": "◀️ Back",
        "buy_package": "💳 Subscribe to full package",
        "renew_btn": "🔄 Renew package",
        "change_lang": "🌐 Language",
        "start_text": "Full playlist (per-minute) or unlimited package (VIP/VIP+XXX) available.",
        "already_activated": "⚠️ Full access has already been activated.",
        "playlist_label": "📺 Your playlist:",
        "playlist_not_found": "📺 Playlist link will be sent by the administrator.",
        "instruction": "📌 Instruction:\nCopy the playlist link to clipboard (tap on it) and paste into one of the IPTV players:",
        "android": "📱 Android — <a href=\"https://play.google.com/store/apps/details?id=es.ottplayer.tv\">OTTPlayer</a>",
        "iphone": "📱 iPhone — <a href=\"https://apps.apple.com/us/app/ottplayertv/id1672208961\">OTTPlayer</a>\n📺 <a href=\"https://youtube.com/shorts/ovE0JF-j_do\">Video guide for iPhone</a>",
        "tv": "📺 TV — any IPTV player",
        "buy_prompt": "💳 Click the button below to subscribe to the full package.",
        "creating": "⏳ Creating user...",
        "timeout": "❌ Timeout. Try again later.",
        "error": "❌ Error: {e}",
        "create_failed": "❌ Failed to create user. Contact @{admin}.",
        "topup_start": "✅ User created. Topping up balance...",
        "topup_timeout": "❌ Topup timeout.",
        "topup_error": "❌ Topup error: {e}",
        "activating": "✅ Balance topped up. Activating time-based billing...",
        "activate_failed": "✅ User created, but activation failed. Contact @{admin}.",
        "getting_link": "✅ Access activated. Getting playlist link...",
        "success": "✅ 120 minutes full access activated!",
        "balance_label": "💰 Remaining: ~{minutes} min (~{hd_minutes} min in HD)",
        "rate_label": "🕐 1 hour of viewing = $0.02",
        "prolong_text": "Please%20renew%20my%20access.%20ID%3A%20{tg_id}",
        "buy_text": "I%20want%20to%20subscribe%20to%20a%20paid%20package.%20ID%3A%20{tg_id}",
        "greeting_text": "Hello!%20I%20want%20to%20subscribe%20to%20a%20paid%20IPTV%20package.",
    },
}

def L(lang, key, **kwargs):
    s = _[lang].get(key, key) if lang in _ else _["ru"].get(key, key)
    if kwargs:
        s = s.format(**kwargs)
    return s

def get_db():
    conn = sqlite3.connect(os.path.join(SCRIPT_DIR, "bot.db"))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            billing_user_id TEXT,
            billing_username TEXT,
            playlist_url TEXT,
            current_package TEXT DEFAULT 'Free',
            expires_at TEXT,
            lang TEXT DEFAULT 'ru',
            comment TEXT,
            balance TEXT
        )
    """)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN comment TEXT")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN balance TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()

init_db()

def run_script_blocking(*args, timeout=120):
    result = subprocess.run(
        args, capture_output=True, text=True,
        cwd=SCRIPT_DIR, timeout=timeout
    )
    return result.stdout + result.stderr

async def run_script(*args, timeout=120):
    async with script_semaphore:
        loop = asyncio.get_running_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(None, lambda: run_script_blocking(*args)),
            timeout=timeout
        )

def parse_output(output):
    user_id = None
    playlist = None
    m = re.search(r'USER_ID=(\d+)', output)
    if m:
        user_id = m.group(1)
    m = re.search(r'PLAYLIST=(https?://\S+)', output)
    if m:
        playlist = m.group(1).strip()
    return user_id, playlist, output

def get_user_lang(tg_id):
    conn = get_db()
    row = conn.execute("SELECT lang FROM users WHERE telegram_id = ?", (tg_id,)).fetchone()
    conn.close()
    return row["lang"] if row else "ru"

def set_user_lang(tg_id, lang):
    conn = get_db()
    conn.execute("""
        INSERT INTO users (telegram_id, lang) VALUES (?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET lang=excluded.lang
    """, (tg_id, lang))
    conn.commit()
    conn.close()

def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_["ru"]["lang_btn"], callback_data="setlang_ru")],
        [InlineKeyboardButton(text=_["en"]["lang_btn"], callback_data="setlang_en")],
    ])

def start_kb(is_existing, tg_id=None, lang="ru"):
    buttons = []
    if is_existing:
        buttons.append([InlineKeyboardButton(
            text=L(lang, "check_balance_btn"), callback_data="test_equip"
        )])
        buttons.append([InlineKeyboardButton(
            text=L(lang, "renew_btn"),
            url=f"tg://resolve?domain={ADMIN_USERNAME}&text={L(lang, 'prolong_text', tg_id=tg_id)}"
        )])
        buttons.append([InlineKeyboardButton(
            text=L(lang, "contact_admin"),
            url=f"tg://resolve?domain={ADMIN_USERNAME}&text={L(lang, 'prolong_text', tg_id=tg_id)}"
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text=L(lang, "test_btn"), callback_data="test_equip"
        )])
        buttons.append([InlineKeyboardButton(
            text=L(lang, "buy_package"),
            url=f"tg://resolve?domain={ADMIN_USERNAME}&text={L(lang, 'greeting_text')}"
        )])
    buttons.append([InlineKeyboardButton(
        text=L(lang, "change_lang"), callback_data="change_lang"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Панель администратора", callback_data="admin_back")],
        [InlineKeyboardButton(text="🔓 Полный доступ на 1 час", callback_data="test_equip")],
    ])

def reply_markup_for(tg_id, is_admin=False):
    if is_admin:
        return admin_start_kb()
    lang = get_user_lang(tg_id)
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,)).fetchone()
    conn.close()
    return start_kb(bool(row), tg_id, lang)

def admin_main_kb(count=0):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Список пользователей ({count})", callback_data="admin_list")],
        [InlineKeyboardButton(text="✏️ Ввести Telegram ID", callback_data="admin_enter_id")],
        [InlineKeyboardButton(text="🔄 Sync users", callback_data="admin_sync")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_to_start")],
    ])

def admin_user_card_kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Выдать пакет", callback_data=f"admin_give:{uid}")],
        [InlineKeyboardButton(text="🔄 Продлить", callback_data=f"admin_extend:{uid}")],
        [InlineKeyboardButton(text="✉️ Написать", callback_data=f"admin_msg:{uid}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"admin_delete:{uid}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
    ])

def package_select_kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Тест (2 дня)", callback_data=f"pkg:test:2:{uid}")],
        [InlineKeyboardButton(text="🛠 Тест (7 дней)", callback_data=f"pkg:test:7:{uid}")],
        [InlineKeyboardButton(text="⭐ VIP (30 дней)", callback_data=f"pkg:vip:30:{uid}")],
        [InlineKeyboardButton(text="⭐ VIP (90 дней)", callback_data=f"pkg:vip:90:{uid}")],
        [InlineKeyboardButton(text="💎 VIP Global (30 дней)", callback_data=f"pkg:vip_premium:30:{uid}")],
        [InlineKeyboardButton(text="💎 VIP Global (90 дней)", callback_data=f"pkg:vip_premium:90:{uid}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
    ])

def confirm_delete_kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data=f"admin_delete_do:{uid}")],
        [InlineKeyboardButton(text="❌ Нет", callback_data=f"admin_card:{uid}")],
    ])

def get_packet_id(pkg_type):
    return {"test": PACKET_TEST, "vip": PACKET_VIP, "vip_premium": PACKET_VIP_PREMIUM}.get(pkg_type, PACKET_TEST)

def get_packet_name(pkg_type):
    return {"test": "Тест", "vip": "VIP", "vip_premium": "VIP Global"}.get(pkg_type, pkg_type)

# ====== Handlers ======

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id
    if tg_id == ADMIN_ID:
        await message.answer("👑 Панель администратора", reply_markup=admin_start_kb())
        return
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,)).fetchone()
    conn.close()
    if row and row["lang"]:
        lang = row["lang"]
        text = L(lang, "start_text")
        if row["playlist_url"]:
            text += f"\n\n{L(lang, 'playlist_label')} <code>{row['playlist_url']}</code>"
        await message.answer(text, parse_mode="HTML", reply_markup=start_kb(bool(row), tg_id, lang))
    else:
        await message.answer(L("ru", "choose_lang"), reply_markup=lang_kb())

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang(cq: CallbackQuery):
    await cq.answer()
    lang = "en" if cq.data == "setlang_en" else "ru"
    tg_id = cq.from_user.id
    set_user_lang(tg_id, lang)
    text = L(lang, "start_text")
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=start_kb(False, tg_id, lang))

@dp.callback_query(F.data == "change_lang")
async def change_lang(cq: CallbackQuery):
    await cq.answer()
    await cq.message.edit_text(L("ru", "choose_lang"), reply_markup=lang_kb())

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(cq: CallbackQuery):
    await cq.answer()
    tg_id = cq.from_user.id
    lang = get_user_lang(tg_id)
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,)).fetchone()
    conn.close()
    text = L(lang, "start_text")
    if row and row["playlist_url"]:
        text += f"\n\n{L(lang, 'playlist_label')} <code>{row['playlist_url']}</code>"
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=start_kb(bool(row), tg_id, lang))

@dp.callback_query(F.data == "test_equip")
async def test_equip(cq: CallbackQuery):
    await cq.answer()
    tg_id = cq.from_user.id
    username = f"u{tg_id}"
    tg_username = cq.from_user.username or ""
    lang = get_user_lang(tg_id)

    conn = get_db()
    existing = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,)).fetchone()
    conn.close()

    if existing and existing["billing_user_id"]:
        url = existing["playlist_url"]
        text = f"{L(lang, 'already_activated')}\n\n"
        try:
            page = await asyncio.wait_for(run_script(
                os.path.join(SCRIPT_DIR, "get_page.sh"),
                f"{BILLING_URL}/dealer_iptv.php?action=adminUser&userId={existing['billing_user_id']}"
            ), timeout=30)
            bm = re.search(r'баланс\s*<font[^>]*>([\d.]+)</font>\s*\$', page)
            if bm:
                bal = float(bm.group(1))
                mins = int(bal / float(RATE_PER_HOUR) * 60)
                hd = mins // 2
                text += f"{L(lang, 'balance_label', minutes=mins, hd_minutes=hd)}\n\n"
        except Exception:
            pass
        if url:
            text += f"{L(lang, 'playlist_label')} <code>{url}</code>\n\n"
        else:
            text += f"{L(lang, 'playlist_not_found')}\n\n"
        text += f"{L(lang, 'instruction')}\n{L(lang, 'android')}\n{L(lang, 'iphone')}\n{L(lang, 'tv')}\n\n"
        text += L(lang, "contact_admin_text")
        await cq.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=L(lang, "contact_admin"),
                    url=f"tg://resolve?domain={ADMIN_USERNAME}&text={L(lang, 'prolong_text', tg_id=tg_id)}")],
                [InlineKeyboardButton(text=L(lang, "back_btn"), callback_data="back_to_menu")],
            ])
        )
        return

    msg = await cq.message.edit_text(L(lang, "creating"))

    try:
        output = await asyncio.wait_for(
            run_script(os.path.join(SCRIPT_DIR, "create_user.sh"), username, "pass", tg_username),
            timeout=60
        )
    except asyncio.TimeoutError:
        await msg.edit_text(L(lang, "timeout"))
        return
    except Exception as e:
        logger.exception("create_user failed")
        await msg.edit_text(L(lang, "error", e=e))
        return

    billing_id, _, raw = parse_output(output)
    logger.info(f"create_user output:\n{raw}")

    if not billing_id:
        await msg.edit_text(L(lang, "create_failed", admin=ADMIN_USERNAME))
        return

    await msg.edit_text(L(lang, "topup_start"))

    try:
        topup_out = await asyncio.wait_for(
            run_script(os.path.join(SCRIPT_DIR, "topup_user.sh"), username, TOPUP_AMOUNT),
            timeout=30
        )
        logger.info(f"topup output:\n{topup_out}")
    except asyncio.TimeoutError:
        await msg.edit_text(L(lang, "topup_timeout"))
        return
    except Exception as e:
        logger.exception("topup failed")
        await msg.edit_text(L(lang, "topup_error", e=e))
        return

    await msg.edit_text(L(lang, "activating"))

    try:
        await asyncio.wait_for(
            run_script(os.path.join(SCRIPT_DIR, "activate_user.sh"), billing_id),
            timeout=30
        )
    except Exception as e:
        logger.exception("activate failed")
        await msg.edit_text(L(lang, "activate_failed", admin=ADMIN_USERNAME))
        return

    await msg.edit_text(L(lang, "getting_link"))

    await asyncio.sleep(2)

    playlist = None
    balance = None
    try:
        page = await asyncio.wait_for(run_script(
            os.path.join(SCRIPT_DIR, "get_page.sh"),
            f"{BILLING_URL}/dealer_iptv.php?action=adminUser&userId={billing_id}"
        ), timeout=30)
        logger.info(f"playlist page fetched ({len(page)} chars)")
        m = re.search(r'https://[^"\']+\.m3u8', page)
        if m:
            playlist = m.group(0)
        bm = re.search(r'баланс\s*<font[^>]*>([\d.]+)</font>\s*\$', page)
        if bm:
            balance = float(bm.group(1))
    except asyncio.TimeoutError:
        logger.warning("playlist fetch timed out")
    except Exception as e:
        logger.exception(f"playlist fetch error: {e}")

    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO users
        (telegram_id, billing_user_id, billing_username, playlist_url, current_package, expires_at, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tg_id, billing_id, username, playlist or "", "Free", None, tg_username))
    conn.commit()
    conn.close()

    try:
        name = cq.from_user.full_name
        mention = f"<a href=\"tg://user?id={tg_id}\">{name}</a>"
        notif = f"\U0001f195 <b>\u041d\u043e\u0432\u044b\u0439 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c</b>\n\n"
        notif += f"ID: <code>{tg_id}</code>\n"
        notif += f"Username: @{tg_username}\n" if tg_username else ""
        notif += f"\u0418\u043c\u044f: {mention}\n"
        notif += f"\u041b\u043e\u0433\u0438\u043d: <code>{username}</code>\n"
        notif += f"Billing ID: <code>{billing_id}</code>\n"
        if playlist:
            notif += f"\u0421\u0441\u044b\u043b\u043a\u0430: <code>{playlist[:60]}...</code>\n"
        await bot.send_message(ADMIN_ID, notif, parse_mode="HTML")
    except Exception as e:
        logger.exception(f"admin notification failed: {e}")

    text = f"{L(lang, 'success')}\n\n"
    if balance is not None:
        minutes = int(balance / float(RATE_PER_HOUR) * 60)
        hd_minutes = minutes // 2
        text += f"{L(lang, 'balance_label', minutes=minutes, hd_minutes=hd_minutes)}\n\n"
    if playlist:
        text += f"{L(lang, 'playlist_label')} <code>{playlist}</code>\n\n"
    else:
        text += f"{L(lang, 'playlist_not_found')}\n\n"
    text += f"{L(lang, 'instruction')}\n{L(lang, 'android')}\n{L(lang, 'iphone')}\n{L(lang, 'tv')}\n\n"
    text += L(lang, "buy_prompt")

    await msg.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=L(lang, "buy_package"),
                url=f"tg://resolve?domain={ADMIN_USERNAME}&text={L(lang, 'buy_text', tg_id=tg_id)}")],
        ])
    )

@dp.callback_query(F.data.startswith("pkg:"))
async def admin_give_package(cq: CallbackQuery):
    await cq.answer()
    parts = cq.data.split(":")
    if len(parts) < 4:
        return
    _, pkg_type, days_str, uid = parts
    days = int(days_str)
    date_to = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    packet_id = get_packet_id(pkg_type)
    pkg_name = get_packet_name(pkg_type)

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (uid,)).fetchone()

    if not row:
        # Try to find user in billing by login u{id}
        billing_user = f"u{uid}"
        try:
            page = await asyncio.wait_for(run_script(
                os.path.join(SCRIPT_DIR, "get_page.sh"),
                f"{BILLING_URL}/dealer_iptv.php?action=adminUsers"
            ), timeout=30)
            import re as _re
            pat = r"userId=(\d+)\">" + re.escape(billing_user) + r"</a></td>\s*<td[^>]*>([^<]*)</td>"
            billing_match = _re.search(pat, page)
            if billing_match:
                billing_id = billing_match.group(1)
                comment = billing_match.group(2).strip()
                conn.execute(
                    "INSERT OR REPLACE INTO users (telegram_id, billing_user_id, billing_username, comment, lang) VALUES (?, ?, ?, ?, 'ru')",
                    (uid, billing_id, billing_user, comment)
                )
                conn.commit()
                row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (uid,)).fetchone()
        except Exception:
            pass

    if not row:
        conn.close()
        await cq.message.edit_text("❌ Пользователь не найден в БД.")
        return

    billing_id = row["billing_user_id"]
    billing_user = row["billing_username"]
    needs_create = not billing_id

    msg = await cq.message.edit_text(f"⏳ Выдаю пакет {pkg_name}...")

    try:
        if needs_create:
            output = await asyncio.wait_for(run_script(
                os.path.join(SCRIPT_DIR, "create_and_buy.sh"),
                billing_user or f"u{uid}", "pass", f"tg_{uid}",
                packet_id, date_to, "1"
            ), timeout=120)
        else:
            output = await asyncio.wait_for(run_script(
                os.path.join(SCRIPT_DIR, "extend_sub.sh"),
                billing_id, packet_id, date_to, "1"
            ), timeout=120)
    except asyncio.TimeoutError:
        await msg.edit_text("❌ Таймаут. Попробуйте позже.")
        return
    except Exception as e:
        logger.exception("give_package failed")
        await msg.edit_text(f"❌ Ошибка: {e}")
        return

    new_billing_id, playlist, raw = parse_output(output)
    logger.info(f"give output:\n{raw}")

    if not new_billing_id and not billing_id:
        await msg.edit_text(f"❌ Ошибка:\n<code>{raw[:500]}</code>", parse_mode="HTML")
        return

    final_id = new_billing_id or billing_id
    final_playlist = playlist or row["playlist_url"]
    final_user = (billing_user or f"u{uid}") if needs_create else row["billing_username"]

    conn.execute("""
        UPDATE users SET billing_user_id=?, billing_username=?, playlist_url=?,
                         current_package=?, expires_at=?
        WHERE telegram_id=?
    """, (final_id, final_user, final_playlist, pkg_name, date_to, uid))
    conn.commit()
    conn.close()

    await msg.edit_text(
        f"✅ Пакет «{pkg_name}» выдан.\n"
        f"Пользователь: {uid}\n"
        f"Действует до: {date_to}",
        reply_markup=admin_user_card_kb(uid)
    )

# ====== Admin handlers ======

def is_admin(user_id):
    return user_id == ADMIN_ID

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY telegram_id").fetchall()
    conn.close()
    await message.answer(
        f"👑 Панель администратора\nПользователей в БД: {len(rows)}",
        reply_markup=admin_main_kb(len(rows))
    )

@dp.callback_query(F.data.startswith("admin_"))
async def admin_callback(cq: CallbackQuery):
    await cq.answer()
    if not is_admin(cq.from_user.id):
        await cq.message.edit_text("⛔ Доступ запрещен.")
        return

    data = cq.data

    if data == "admin_to_start":
        await cq.message.edit_text("👑 Панель администратора", reply_markup=admin_start_kb())

    elif data == "admin_back":
        conn = get_db()
        rows = conn.execute("SELECT * FROM users ORDER BY telegram_id").fetchall()
        conn.close()
        await cq.message.edit_text(
            f"👑 Панель администратора\nПользователей в БД: {len(rows)}",
            reply_markup=admin_main_kb(len(rows))
        )

    elif data == "admin_enter_id":
        await cq.message.edit_text(
            "Введите Telegram ID пользователя (только цифры):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
            ])
        )

    elif data == "admin_list":
        conn = get_db()
        rows = conn.execute("SELECT * FROM users ORDER BY telegram_id").fetchall()
        conn.close()
        if not rows:
            await cq.message.edit_text("📭 Нет пользователей.", reply_markup=admin_main_kb(0))
            return
        buttons = []
        for r in rows:
            display = (r['comment'] or str(r['telegram_id']))[:20]
            label = f"{display} | {r['current_package']} | {r['expires_at'] or '∞'}"
            buttons.append([InlineKeyboardButton(text=label, callback_data=f"admin_card:{r['telegram_id']}")])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")])
        await cq.message.edit_text("📋 Выберите пользователя:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    elif data.startswith("admin_card:"):
        uid = data.split(":", 1)[1]
        await show_user_card(cq, uid)

    elif data.startswith("admin_give:"):
        uid = data.split(":", 1)[1]
        await cq.message.edit_text("Выберите пакет:", reply_markup=package_select_kb(uid))

    elif data.startswith("admin_extend:"):
        uid = data.split(":", 1)[1]
        await extend_user(cq, uid)

    elif data.startswith("admin_delete:"):
        uid = data.split(":", 1)[1]
        await cq.message.edit_text("⚠️ Удалить пользователя из бота?", reply_markup=confirm_delete_kb(uid))

    elif data.startswith("admin_msg:"):
        uid = data.split(":", 1)[1]
        admin_msg_target[cq.from_user.id] = uid
        await cq.message.edit_text(
            f"✉️ Напишите сообщение для пользователя {uid}.\n"
            f"Оно будет отправлено от имени бота.\n"
            f"Отправьте /cancel чтобы отменить.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_back")]
            ])
        )

    elif data == "admin_sync":
        msg = await cq.message.edit_text("🔄 Синхронизация...")
        try:
            phpsessid = open(os.path.join(SCRIPT_DIR, ".phpsessid")).read().strip()
            import subprocess
            page = subprocess.run(
                ["curl", "-s", "-b", f"PHPSESSID={phpsessid}",
                 f"{BILLING_URL}/dealer_iptv.php?action=adminUsers"],
                capture_output=True, text=True, timeout=30
            ).stdout
            conn = get_db()
            added = 0
            import re as _re
            rows_html = _re.findall(r"<tr[^>]*>.*?</tr>", page, re.DOTALL)
            for row_html in rows_html:
                if "userId=" not in row_html:
                    continue
                tds = _re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
                if len(tds) < 7:
                    continue
                login_td = tds[1] if len(tds) > 1 else ""
                comment_td = tds[2] if len(tds) > 2 else ""
                packet_td = tds[4] if len(tds) > 4 else ""
                expires_td = tds[5] if len(tds) > 5 else ""

                login_match = _re.search(r"userId=(\d+)\">([^<]+)</a>", login_td)
                if not login_match:
                    continue
                uid_billing = login_match.group(1)
                login = login_match.group(2)
                comment = _re.sub(r"<.*?>", "", comment_td).strip()
                packet = _re.sub(r"<.*?>", "", packet_td).strip()
                expires_raw = _re.sub(r"<.*?>", "", expires_td).strip()
                expires = expires_raw.strip("()")

                tg_match = _re.match(r"u(\d+)", login)
                if tg_match:
                    tg_id = int(tg_match.group(1))
                    existing = conn.execute(
                        "SELECT * FROM users WHERE telegram_id = ?", (tg_id,)
                    ).fetchone()
                    if not existing:
                        conn.execute(
                            "INSERT INTO users (telegram_id, billing_user_id, billing_username, current_package, expires_at, comment, lang) VALUES (?, ?, ?, ?, ?, ?, 'ru')",
                            (tg_id, uid_billing, login, packet, expires, comment)
                        )
                        added += 1
                    else:
                        conn.execute(
                            "UPDATE users SET billing_user_id=?, billing_username=?, current_package=?, expires_at=?, comment=? WHERE telegram_id=?",
                            (uid_billing, login, packet, expires, comment, tg_id)
                        )
                        if existing["billing_user_id"] != uid_billing or existing["current_package"] != packet:
                            added += 1
            conn.commit()
            conn.close()
            await msg.edit_text(f"✅ Синхронизация завершена. Добавлено/обновлено: {added}")
        except Exception as e:
            logger.exception("sync failed")
            await msg.edit_text(f"❌ Ошибка: {e}")
    elif data.startswith("admin_delete_do:"):
        uid = data.split(":", 1)[1]
        conn = get_db()
        conn.execute("DELETE FROM users WHERE telegram_id = ?", (uid,))
        conn.commit()
        conn.close()
        await cq.message.edit_text(f"✅ Пользователь {uid} удалён.")

@dp.message(Command("cancel"))
async def admin_cancel(message: types.Message):
    if is_admin(message.from_user.id):
        admin_msg_target.pop(message.from_user.id, None)
        await message.answer("Отменено.")

@dp.message(F.text, ~F.text.regexp(r'^\d+$'))
async def admin_send_msg(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    if message.from_user.id not in admin_msg_target:
        return
    uid = admin_msg_target.pop(message.from_user.id)
    try:
        await bot.send_message(int(uid), f"✉️ Сообщение от администратора:\n\n{message.text}")
        await message.answer(f"✅ Сообщение отправлено пользователю {uid}.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(F.text.regexp(r'^\d+$'))
async def admin_search_by_id(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    uid = message.text.strip()
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (uid,)).fetchone()
    conn.close()
    if not row:
        await message.answer(f"❌ Пользователь {uid} не найден.")
        return
    text = (
        f"👤 Карточка пользователя\n"
        f"├ Telegram ID: {row['telegram_id']}\n"
        f"├ Username: {row['billing_username'] or '—'}\n"
        f"├ Комментарий: {row['comment'] or '—'}\n"
        f"├ ID биллинга: {row['billing_user_id'] or '—'}\n"
        f"├ Пакет: {row['current_package']}\n"
        f"├ Действует до: {row['expires_at'] or '—'}\n"
        f"├ Баланс: {row['balance'] or '0'}\n"
        f"├ Язык: {row['lang'] or 'ru'}\n"
        f"└ Плейлист: <code>{row['playlist_url'] or '—'}</code>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=admin_user_card_kb(uid))

async def show_user_card(cq: CallbackQuery, uid):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (uid,)).fetchone()
    conn.close()
    if not row:
        await cq.message.edit_text(f"❌ Пользователь {uid} не найден.", reply_markup=admin_main_kb())
        return
    text = (
        f"👤 Карточка пользователя\n"
        f"├ Telegram ID: {row['telegram_id']}\n"
        f"├ Username: {row['billing_username'] or '—'}\n"
        f"├ Комментарий: {row['comment'] or '—'}\n"
        f"├ ID биллинга: {row['billing_user_id'] or '—'}\n"
        f"├ Пакет: {row['current_package']}\n"
        f"├ Действует до: {row['expires_at'] or '—'}\n"
        f"├ Баланс: {row['balance'] or '0'}\n"
        f"├ Язык: {row['lang'] or 'ru'}\n"
        f"└ Плейлист: <code>{row['playlist_url'] or '—'}</code>"
    )
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=admin_user_card_kb(uid))

async def extend_user(cq: CallbackQuery, uid):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (uid,)).fetchone()
    conn.close()
    if not row or not row["billing_user_id"]:
        await cq.message.edit_text("❌ Невозможно продлить: нет ID биллинга.")
        return

    if row["expires_at"]:
        try:
            base = datetime.strptime(row["expires_at"], "%Y-%m-%d")
        except (ValueError, TypeError):
            base = datetime.now()
    else:
        base = datetime.now()
    date_to = (base + timedelta(days=30)).strftime("%Y-%m-%d")

    pkg_type = "test"
    if row["current_package"]:
        if "VIP Premium" in row["current_package"]:
            pkg_type = "vip_premium"
        elif "VIP" in row["current_package"]:
            pkg_type = "vip"
    packet_id = get_packet_id(pkg_type)

    msg = await cq.message.edit_text("⏳ Продлеваю...")

    try:
        output = await asyncio.wait_for(run_script(
            os.path.join(SCRIPT_DIR, "extend_sub.sh"),
            row["billing_user_id"], packet_id, date_to, "1"
        ), timeout=60)
    except asyncio.TimeoutError:
        await msg.edit_text("❌ Таймаут.")
        return
    except Exception as e:
        logger.exception("extend failed")
        await msg.edit_text(f"❌ Ошибка: {e}")
        return

    _, playlist, raw = parse_output(output)
    logger.info(f"extend output:\n{raw}")

    final_playlist = playlist or row["playlist_url"]
    conn = get_db()
    conn.execute("UPDATE users SET playlist_url=?, expires_at=? WHERE telegram_id=?",
                 (final_playlist, date_to, uid))
    conn.commit()
    conn.close()

    await msg.edit_text(f"✅ Продлено до {date_to}.", reply_markup=admin_user_card_kb(uid))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
