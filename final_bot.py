#!/bin/bash

# نصب پیش‌نیازها
echo "🤖 در حال نصب کتابخونه‌ها..."
pip3 install --user python-telegram-bot requests

# ساخت فایل users.json اگه وجود نداشته باشه
if [ ! -f "/home/sbiorg/users.json" ]; then
    echo "ساخت فایل users.json..."
    echo "{}" > /home/sbiorg/users.json
    chmod 666 /home/sbiorg/users.json
fi

# ساخت فایل log.txt اگه وجود نداشته باشه
if [ ! -f "/home/sbiorg/log.txt" ]; then
    echo "ساخت فایل log.txt..."
    touch /home/sbiorg/log.txt
    chmod 666 /home/sbiorg/log.txt
fi

# تنظیمات ربات
TELEGRAM_TOKEN="7779706057:AAFh_88PzgML5rUZ0JfcB-SfcIvzAmUBUng"
ADMIN_ID="90133620"

# ساخت فایل ربات
echo "🔥 ساخت فایل ربات..."
cat << 'EOF' > /home/sbiorg/final_bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import json
import random
import os
from datetime import datetime, timedelta
import requests

# تنظیمات
TELEGRAM_TOKEN = "7779706057:AAFh_88PzgML5rUZ0JfcB-SfcIvzAmUBUng"
ADMIN_ID = "90133620"
DEEPSEEK_API_URL = "https://www.chatstream.org/api/deepseek"  # سرویس آنلاین رایگان
USER_DATA_FILE = "/home/sbiorg/users.json"
LOG_FILE = "/home/sbiorg/log.txt"

# سؤال‌های بازی
GAME_QUESTIONS = {
    "medium": [
        {"question": "2 + 2 × 3 = ?", "answer": "8"},
        {"question": "پایتخت ایران کجاست؟", "answer": "تهران"},
        {"question": "5 - 3 × 2 = ?", "answer": "-1"},
        {"question": "بزرگ‌ترین سیاره منظومه شمسی چیه؟", "answer": "مشتری"},
        {"question": "عدد اول بعد از 7 چیه؟", "answer": "11"}
    ],
    "hard": [
        {"question": "یه روز اومدم به یکی pm بدم، ولی چون ساعت از 12 گذشته بود چی شد؟", "answer": "دیگه am شد"},
        {"question": "اگر x + 2 = 5، مقدار x چیه؟", "answer": "3"},
        {"question": "پدر علم فیزیک کیه؟", "answer": "نیوتن"},
        {"question": "یه عدد 3 رقمی که مجموع ارقامش 15 باشه و رقم اولش 5 باشه چیه؟", "answer": "573"},
        {"question": "درخت بدون سایه، پرنده بدون آواز، و مرد بدون راز چی می‌تونه باشه؟", "answer": "خدا"}
    ]
}

# درباره ربات
ABOUT_TEXT = {
    "fa": """
🌟 **درباره ربات:**
من دستیار هوشمند و سرگرم‌کننده‌ای هستم که با DeepSeek کار می‌کنم! 😎  
با من می‌تونی سؤال بپرسی، بازی کنی، فیلم از اینستا دانلود کنی، آهنگ پیدا کنی، و کلی چیز دیگه!  
فقط یادت باشه، هر روز 3 سؤال رایگان داری، و اگه بیشتر بخوای، باید سکه خرج کنی.  
ولی نگران نباش، با بازی کردن می‌تونی سکه ببری! 🎮  
دانلود فیلم و پیدا کردن آهنگ برای همه رایگانه! 🎵📹
""",
    "en": """
🌟 **About the Bot:**
I’m a smart and fun assistant powered by DeepSeek! 😎  
With me, you can ask questions, play games, download videos from Instagram, find songs, and more!  
Remember, you have 3 free questions per day, and if you want more, you’ll need to spend coins.  
But don’t worry, you can win coins by playing games! 🎮  
Downloading videos and finding songs are free for everyone! 🎵📹
""",
    "ar": """
🌟 **عن البوت:**
أنا مساعد ذكي ومسلي يعمل بـ DeepSeek! 😎  
معي، يمكنك طرح الأسئلة، ولعب الألعاب، وتنزيل مقاطع فيديو من إنستجرام، والعثور على الأغاني، وأكثر!  
تذكر، لديك 3 أسئلة مجانية يوميًا، وإذا أردت المزيد، ستحتاج إلى إنفاق العملات.  
لكن لا تقلق، يمكنك الفوز بالعملات من خلال لعب الألعاب! 🎮  
تنزيل الفيديوهات والعثور على الأغاني مجاني للجميع! 🎵📹
"""
}

# درباره سازنده
CREATOR_TEXT = {
    "fa": """
🌟 **درباره سازنده:**
من سبحانم! یه برنامه‌نویس ساده که همه فکر می‌کنن هکرم! 😈  
میگن با یه خط کد کل دارک‌وب رو به هم ریختم و سیستم‌ها رو قفل می‌کنم! 💥  
اگه یه روز سیستمت خود به خود خاموش شد، بدون کار منه! 😏  
میگن شب‌ها توی دارک‌وب پرسه می‌زنم و با یه "print('boom')" همه چی رو نابود می‌کنم! 👾  
خطرناکم، بترسید... ولی فقط یه کم! 😜  
این ربات رو ساختم که بتونم بهت کمک کنم، ولی حواست باشه، شاید یه روز رباتم هکت کنه! 😅
""",
    "en": """
🌟 **About the Creator:**
I’m Sobhan! Just a simple coder, but they say I’m a hacker! 😈  
Rumor has it I crashed the whole dark web with one line of code! 💥  
If your system shuts down out of nowhere, you know it’s me! 😏  
They say I roam the dark web at night and destroy everything with a "print('boom')"! 👾  
I’m dangerous, be scared… but just a little! 😜  
I made this bot to help you, but watch out, it might hack you one day! 😅
""",
    "ar": """
🌟 **عن المبدع:**
أنا سبحان! مبرمج بسيط، لكن يقولون إنني هاكر! 😈  
يشاع أنني خربت الدارك ويب كله بسطر واحد من الكود! 💥  
إذا أغلق نظامك فجأة، فاعلم أنني من فعل ذلك! 😏  
يقولون إنني أتجول في الدارك ويب ليلاً وأدمر كل شيء بـ "print('boom')"! 👾  
أنا خطير، خافوا مني… لكن قليلاً فقط! 😜  
صنعت هذا البوت لمساعدتك، لكن احذر، قد يخترقك يوماً ما! 😅
"""
}

# زبان‌ها
LANGUAGES = {"fa": "فارسی", "en": "English", "ar": "العربية"}

# منوی اصلی دکمه‌ها برای کاربران عادی
def get_main_menu(lang):
    buttons = [
        [KeyboardButton("🎮 بازی"), KeyboardButton("😂 جوک")],
        [KeyboardButton("💻 تولید کد"), KeyboardButton("🌐 جستجو در وب")],
        [KeyboardButton("📹 دانلود از اینستا"), KeyboardButton("🎵 پیدا کردن آهنگ")],
        [KeyboardButton("ℹ️ درباره ربات"), KeyboardButton("👨‍💻 درباره سازنده")],
        [KeyboardButton("📊 سکه‌ها و سؤالم"), KeyboardButton("❓ راهنما")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# منوی ادمین
def get_admin_menu():
    buttons = [
        [KeyboardButton("📢 ارسال پیام همگانی")],
        [KeyboardButton("👥 مدیریت کاربران")],
        [KeyboardButton("📊 آمار ربات")],
        [KeyboardButton("🔴 خاموش کردن ربات"), KeyboardButton("🟢 روشن کردن ربات")],
        [KeyboardButton("⬅️ بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# بارگذاری اطلاعات کاربران
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError):
            with open(USER_DATA_FILE, "w") as f:
                json.dump({}, f)
            return {}
    return {}

# ذخیره اطلاعات کاربران
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# لاگ کردن پیام‌ها
def log_message(user_id, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{timestamp} - User {user_id}: {message}\n")

# ریست روزانه
def reset_daily_limits(user_data):
    today = datetime.now().date()
    for user_id, data in user_data.items():
        last_reset = data.get("last_reset", None)
        if last_reset is None or datetime.strptime(last_reset, "%Y-%m-%d").date() < today:
            data["daily_questions"] = 0
            data["joke_count"] = 0
            data["last_reset"] = today.strftime("%Y-%m-%d")
    save_user_data(user_data)

# گرفتن جواب از سرویس آنلاین DeepSeek
def get_deepseek_response(message, lang):
    try:
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "message": message,
            "language": LANGUAGES.get(lang, "فارسی")
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "نمی‌تونم جواب بدم!")
    except Exception as e:
        return f"خطا: {str(e)}"

# تولید جوک با سرویس آنلاین
def generate_joke(lang):
    try:
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "message": "Tell me a funny joke!",
            "language": LANGUAGES.get(lang, "فارسی")
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "نمی‌تونم جوک بگم!")
    except Exception as e:
        return f"خطا: {str(e)}"

# تولید کد با سرویس آنلاین
async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")

    if not context.args:
        msg = {
            "fa": "لطفاً توضیح بده چه کدی می‌خوای! مثال: بنویس یه تابع برای جمع دو عدد در پایتون",
            "en": "Please explain what code you want! Example: Write a function to add two numbers in Python",
            "ar": "يرجى شرح الكود الذي تريده! مثال: اكتب دالة لجمع عددين في بايثون"
        }
        await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=get_main_menu(lang))
        return

    code_request = " ".join(context.args)
    try:
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "message": f"Generate code: {code_request}",
            "language": LANGUAGES.get(lang, "فارسی")
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        code = result.get("response", "نمی‌تونم کد تولید کنم!")
        await update.message.reply_text(f"```python\n{code}\n```", parse_mode="Markdown", reply_markup=get_main_menu(lang))
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}", reply_markup=get_main_menu(lang))

# جستجوی وب با سرویس آنلاین
async def web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")

    if not context.args:
        msg = {
            "fa": "لطفاً چیزی که می‌خوای جستجو کنی رو بنویس! مثال: پایتخت فرانسه",
            "en": "Please write what you want to search for! Example: Capital of France",
            "ar": "يرجى كتابة ما تريد البحث عنه! مثال: عاصمة فرنسا"
        }
        await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=get_main_menu(lang))
        return

    search_query = " ".join(context.args)
    try:
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "message": f"Search the web for: {search_query}",
            "language": LANGUAGES.get(lang, "فارسی")
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        search_result = result.get("response", "نمی‌تونم جستجو کنم!")
        await update.message.reply_text(search_result, reply_markup=get_main_menu(lang))
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}", reply_markup=get_main_menu(lang))

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    user_data = load_user_data()

    if user_id not in user_data:
        user_data[user_id] = {
            "name": user_name,
            "coins": 15,  # 15 سکه رایگان
            "daily_questions": 0,
            "joke_count": 0,
            "score": 0,
            "language": None,
            "current_game": None,
            "last_reset": datetime.now().date().strftime("%Y-%m-%d"),
            "banned": False  # برای مدیریت بن کردن کاربران
        }
        save_user_data(user_data)
        # ارسال پیام به ادمین برای کاربر جدید
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"کاربر جدید: {user_name} (آیدی: {user_id}) - 15 سکه گرفت.")

    # منوی انتخاب زبان
    keyboard = [
        [InlineKeyboardButton("فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("العربية", callback_data="lang_ar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام! خوش اومدی! 🌟\nلطفاً زبونت رو انتخاب کن:\nHi! Welcome! Please choose your language:\nمرحباً! أهلاً بك! اختر لغتك:",
        reply_markup=reply_markup
    )

# مدیریت انتخاب زبان (اصلاح‌شده)
async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    user_data = load_user_data()

    if user_id in user_data:
        lang = query.data.split("_")[1]
        user_data[user_id]["language"] = lang
        save_user_data(user_data)
        welcome_msg = {
            "fa": (
                "🌟 **سلام! من دستیار هوشمند و سرگرم‌کننده‌ای هستم!** 🌟\n\n"
                "با من می‌تونی سؤال بپرسی، بازی کنی، فیلم از اینستا دانلود کنی، آهنگ پیدا کنی، و کلی چیز دیگه!\n"
                "هر روز 3 سؤال رایگان داری. اگه بیشتر بخوای، هر سؤال 1 سکه کم می‌کنه.\n"
                "با بازی کردن می‌تونی سکه ببری! 🏆\n"
                "درباره سازنده من با دکمه زیر بیشتر بخون، ولی مراقب باش، میگن هکره! 😈\n"
                "برای اطلاعات بیشتر، از منوی زیر استفاده کن."
            ),
            "en": (
                "🌟 **Hi! I’m a smart and fun assistant!** 🌟\n\n"
                "With me, you can ask questions, play games, download Instagram videos, find songs, and more!\n"
                "You have 3 free questions per day. If you want more, each extra question costs 1 coin.\n"
                "Play games to win coins! 🏆\n"
                "Read about my creator with the button below, but be careful, they say he’s a hacker! 😈\n"
                "For more info, use the menu below."
            ),
            "ar": (
                "🌟 **مرحباً! أنا مساعد ذكي ومسلي!** 🌟\n\n"
                "معي، يمكنك طرح الأسئلة، ولعب الألعاب، وتنزيل مقاطع فيديو من إنستجرام، والعثور على الأغاني، وأكثر!\n"
                "لديك 3 أسئلة مجانية يوميًا. إذا أردت المزيد، فكل سؤال إضافي يكلف 1 عملة.\n"
                "العب الألعاب للفوز بالعملات! 🏆\n"
                "اقرأ عن مبدعي مع الزر أدناه، لكن كن حذراً، يقولون إنه هاكر! 😈\n"
                "لمزيد من المعلومات، استخدم القائمة أدناه."
            )
        }
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
        # حذف پیام انتخاب زبان
        await query.delete_message()
        # ارسال پیام جدید با منوی دکمه‌ای
        await context.bot.send_message(
            chat_id=user_id,
            text=welcome_msg.get(lang, welcome_msg["fa"]),
            reply_markup=menu
        )

# دستور /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")
    help_msg = {
        "fa": (
            "دستورات من:\n"
            "🎮 بازی - بازی با سؤال‌های تایم‌دار\n"
            "😂 جوک - شنیدن جوک (حداکثر 3 بار در روز)\n"
            "💻 تولید کد - تولید کد (مثال: بنویس یه تابع برای جمع دو عدد در پایتون)\n"
            "🌐 جستجو در وب - جستجوی وب (مثال: پایتخت فرانسه)\n"
            "📹 دانلود از اینستا - دانلود فیلم از اینستا\n"
            "🎵 پیدا کردن آهنگ - پیدا کردن آهنگ\n"
            "ℹ️ درباره ربات - درباره ربات\n"
            "👨‍💻 درباره سازنده - درباره سازنده (یه کم ترسناکه! 😈)\n"
            "📊 سکه‌ها و سؤالم - سؤال‌ها و سکه‌های باقی‌مونده\n"
            "\n**شرایط بازی:**\n"
            "- هر سؤال 1 دقیقه زمان داره.\n"
            "- سؤال متوسط: 5 سکه جایزه\n"
            "- سؤال سخت: 8 سکه جایزه\n"
            "- هر روز 3 سؤال رایگان داری. برای سؤال‌های بیشتر، سکه خرج کن.\n"
            "- با بازی کردن می‌تونی سکه ببری!"
        ),
        "en": (
            "My commands:\n"
            "🎮 Play - Play with timed questions\n"
            "😂 Joke - Hear a joke (max 3 per day)\n"
            "💻 Generate Code - Generate code (e.g., Write a function to add two numbers in Python)\n"
            "🌐 Web Search - Web search (e.g., Capital of France)\n"
            "📹 Download from Insta - Download Instagram video\n"
            "🎵 Find Song - Find song\n"
            "ℹ️ About Bot - About the bot\n"
            "👨‍💻 About Creator - About the creator (a bit scary! 😈)\n"
            "📊 Coins & Questions - Remaining questions and coins\n"
            "\n**Game Rules:**\n"
            "- Each question has a 1-minute timer.\n"
            "- Medium question: 5 coins reward\n"
            "- Hard question: 8 coins reward\n"
            "- You have 3 free questions per day. Spend coins for more.\n"
            "- Play games to win coins!"
        ),
        "ar": (
            "أوامري:\n"
            "🎮 لعب - لعب بأسئلة مؤقتة\n"
            "😂 نكتة - سماع نكتة (حد أقصى 3 يومياً)\n"
            "💻 إنشاء كود - إنشاء كود (مثال: اكتب دالة لجمع عددين في بايثون)\n"
            "🌐 البحث في الويب - البحث في الويب (مثال: عاصمة فرنسا)\n"
            "📹 تنزيل من إنستا - تنزيل فيديو من إنستجرام\n"
            "🎵 العثور على أغنية - العثور على أغنية\n"
            "ℹ️ عن البوت - عن البوت\n"
            "👨‍💻 عن المبدع - عن المبدع (مخيف قليلاً! 😈)\n"
            "📊 العملات والأسئلة - الأسئلة والعملات المتبقية\n"
            "\n**قواعد اللعبة:**\n"
            "- كل سؤال له مهلة دقيقة واحدة.\n"
            "- سؤال متوسط: 5 عملات مكافأة\n"
            "- سؤال صعب: 8 عملات مكافأة\n"
            "- لديك 3 أسئلة مجانية يوميًا. أنفق العملات للمزيد.\n"
            "- العب الألعاب للفوز بالعملات!"
        )
    }
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(help_msg.get(lang, help_msg["fa"]), reply_markup=menu)

# دستور /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(ABOUT_TEXT.get(lang, ABOUT_TEXT["fa"]), parse_mode="Markdown", reply_markup=menu)

# دستور /creator
async def creator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(CREATOR_TEXT.get(lang, CREATOR_TEXT["fa"]), parse_mode="Markdown", reply_markup=menu)

# دستور /joke
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")

    if user_data[user_id]["banned"]:
        await update.message.reply_text("شما بن شده‌اید و نمی‌توانید از ربات استفاده کنید!", reply_markup=get_main_menu(lang))
        return

    if user_data[user_id]["joke_count"] >= 3:
        limit_msg = {
            "fa": "😂 امروز دیگه جوکات تموم شد! فردا بیا!",
            "en": "😂 You’ve used up your jokes for today! Come back tomorrow!",
            "ar": "😂 لقد نفدت نكاتك لهذا اليوم! عد غداً!"
        }
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
        await update.message.reply_text(limit_msg.get(lang, limit_msg["fa"]), reply_markup=menu)
        return

    user_data[user_id]["joke_count"] += 1
    save_user_data(user_data)
    joke_text = generate_joke(lang)
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(joke_text, reply_markup=menu)

# دستور /game
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")

    if user_data[user_id]["banned"]:
        await update.message.reply_text("شما بن شده‌اید و نمی‌توانید از ربات استفاده کنید!", reply_markup=get_main_menu(lang))
        return

    if user_data[user_id]["language"] is None:
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
        await update.message.reply_text("لطفاً اول /start رو بزن و زبونت رو انتخاب کن!", reply_markup=menu)
        return

    if user_data[user_id]["current_game"]:
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
        await update.message.reply_text("تو الان توی یه بازی هستی! اول به سؤالم جواب بده.", reply_markup=menu)
        return

    # انتخاب تصادفی سطح سؤال (50% متوسط، 50% سخت)
    level = random.choice(["medium", "hard"])
    question_data = random.choice(GAME_QUESTIONS[level])
    user_data[user_id]["current_game"] = {
        "question": question_data["question"],
        "answer": question_data["answer"],
        "level": level,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_user_data(user_data)

    msg = {
        "fa": f"🎮 سؤالم اینه ({'متوسط' if level == 'medium' else 'سخت'}):\n{question_data['question']}\nجوابتو توی 1 دقیقه بنویس!\n(متوسط: 5 سکه، سخت: 8 سکه)",
        "en": f"🎮 Here’s my question ({'medium' if level == 'medium' else 'hard'}):\n{question_data['question']}\nAnswer within 1 minute!\n(Medium: 5 coins, Hard: 8 coins)",
        "ar": f"🎮 سؤالي هو ({'متوسط' if level == 'medium' else 'صعب'}):\n{question_data['question']}\nأجب في غضون دقيقة واحدة!\n(متوسط: 5 عملات، صعب: 8 عملات)"
    }
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)

# دستور /insta
async def insta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")

    if user_data[user_id]["banned"]:
        await update.message.reply_text("شما بن شده‌اید و نمی‌توانید از ربات استفاده کنید!", reply_markup=get_main_menu(lang))
        return

    if not context.args:
        msg = {
            "fa": "لطفاً لینک اینستاگرام رو وارد کن! مثال: /insta [لینک]",
            "en": "Please provide an Instagram link! Example: /insta [link]",
            "ar": "يرجى تقديم رابط إنستجرام! مثال: /insta [رابط]"
        }
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
        await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)
        return

    link = context.args[0]
    msg = {
        "fa": f"در حال دانلود فیلم از لینک: {link}\n(این قابلیت به زودی اضافه می‌شه!)",
        "en": f"Downloading video from link: {link}\n(This feature will be added soon!)",
        "ar": f"جاري تنزيل الفيديو من الرابط: {link}\n(سيتم إضافة هذه الميزة قريبًا!)"
    }
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)

# دستور /music
async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")

    if user_data[user_id]["banned"]:
        await update.message.reply_text("شما بن شده‌اید و نمی‌توانید از ربات استفاده کنید!", reply_markup=get_main_menu(lang))
        return

    if not context.args:
        msg = {
            "fa": "لطفاً نام آهنگ رو وارد کن! مثال: /music [نام آهنگ]",
            "en": "Please provide the song name! Example: /music [song name]",
            "ar": "يرجى تقديم اسم الأغنية! مثال: /music [اسم الأغنية]"
        }
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
        await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)
        return

    song_name = " ".join(context.args)
    msg = {
        "fa": f"در حال جستجوی آهنگ: {song_name}\n(این قابلیت به زودی اضافه می‌شه!)",
        "en": f"Searching for song: {song_name}\n(This feature will be added soon!)",
        "ar": f"جاري البحث عن الأغنية: {song_name}\n(سيتم إضافة هذه الميزة قريبًا!)"
    }
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)

# دستور /remaining
async def remaining(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    lang = user_data.get(user_id, {}).get("language", "fa")

    if user_data[user_id]["banned"]:
        await update.message.reply_text("شما بن شده‌اید و نمی‌توانید از ربات استفاده کنید!", reply_markup=get_main_menu(lang))
        return

    coins = user_data[user_id]["coins"]
    questions_left = 3 - user_data[user_id]["daily_questions"]
    msg = {
        "fa": f"تو {questions_left} سؤال رایگان امروز داری و {coins} سکه.\nبرای سؤال‌های بیشتر، سکه خرج کن یا بازی کن!",
        "en": f"You have {questions_left} free questions left today and {coins} coins.\nSpend coins for more questions or play games!",
        "ar": f"لديك {questions_left} أسئلة مجانية متبقية اليوم و{coins} عملات.\nأنفق العملات للمزيد من الأسئلة أو العب الألعاب!"
    }
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)

# دستورات ادمین
# ارسال پیام همگانی
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return

    user_data = load_user_data()
    if not context.args:
        await update.message.reply_text("لطفاً پیام خود را وارد کنید! مثال: /broadcast سلام به همه!", reply_markup=get_admin_menu())
        return

    message = " ".join(context.args)
    for uid in user_data.keys():
        if uid != ADMIN_ID and not user_data[uid].get("banned", False):
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 پیام از ادمین:\n{message}")
            except:
                continue
    await update.message.reply_text("پیام همگانی با موفقیت ارسال شد!", reply_markup=get_admin_menu())

# مدیریت کاربران
async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return

    user_data = load_user_data()
    if not context.args:
        users_list = "👥 لیست کاربران:\n"
        for uid, data in user_data.items():
            users_list += f"آیدی: {uid} - نام: {data['name']} - سکه‌ها: {data['coins']} - بن شده: {'بله' if data.get('banned', False) else 'خیر'}\n"
        users_list += "\nبرای مدیریت کاربر، از فرمت زیر استفاده کنید:\n/change_coins [آیدی] [تعداد سکه]\n/ban [آیدی]\n/unban [آیدی]"
        await update.message.reply_text(users_list, reply_markup=get_admin_menu())
        return

    command = context.args[0]
    if command == "change_coins" and len(context.args) == 3:
        target_id = context.args[1]
        coins = int(context.args[2])
        if target_id in user_data:
            user_data[target_id]["coins"] = coins
            save_user_data(user_data)
            await update.message.reply_text(f"سکه‌های کاربر {target_id} به {coins} تغییر کرد!", reply_markup=get_admin_menu())
        else:
            await update.message.reply_text("کاربر یافت نشد!", reply_markup=get_admin_menu())
    elif command == "ban" and len(context.args) == 2:
        target_id = context.args[1]
        if target_id in user_data:
            user_data[target_id]["banned"] = True
            save_user_data(user_data)
            await update.message.reply_text(f"کاربر {target_id} بن شد!", reply_markup=get_admin_menu())
        else:
            await update.message.reply_text("کاربر یافت نشد!", reply_markup=get_admin_menu())
    elif command == "unban" and len(context.args) == 2:
        target_id = context.args[1]
        if target_id in user_data:
            user_data[target_id]["banned"] = False
            save_user_data(user_data)
            await update.message.reply_text(f"کاربر {target_id} از بن خارج شد!", reply_markup=get_admin_menu())
        else:
            await update.message.reply_text("کاربر یافت نشد!", reply_markup=get_admin_menu())
    else:
        await update.message.reply_text("دستور نامعتبر! از فرمت زیر استفاده کنید:\n/change_coins [آیدی] [تعداد سکه]\n/ban [آیدی]\n/unban [آیدی]", reply_markup=get_admin_menu())

# آمار ربات
async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return

    user_data = load_user_data()
    total_users = len(user_data)
    banned_users = sum(1 for uid, data in user_data.items() if data.get("banned", False))
    total_coins = sum(data["coins"] for data in user_data.values())
    stats = (
        f"📊 آمار ربات:\n"
        f"تعداد کل کاربران: {total_users}\n"
        f"کاربران بن‌شده: {banned_users}\n"
        f"مجموع سکه‌ها: {total_coins}"
    )
    await update.message.reply_text(stats, reply_markup=get_admin_menu())

# خاموش کردن ربات
async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return

    await update.message.reply_text("ربات خاموش شد! برای روشن کردن دوباره، دکمه 'روشن کردن ربات' را بزنید.", reply_markup=get_admin_menu())
    os._exit(0)

# روشن کردن ربات (فقط اطلاع‌رسانی)
async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return

    await update.message.reply_text("ربات در حال اجرا است!", reply_markup=get_admin_menu())

# مدیریت پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    reset_daily_limits(user_data)  # ریست روزانه

    if user_id not in user_data or user_data[user_id]["language"] is None:
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu("fa")
        await update.message.reply_text("لطفاً اول /start رو بزن و زبونت رو انتخاب کن!", reply_markup=menu)
        return

    if user_data[user_id]["banned"] and user_id != ADMIN_ID:
        await update.message.reply_text("شما بن شده‌اید و نمی‌توانید از ربات استفاده کنید!", reply_markup=get_main_menu("fa"))
        return

    lang = user_data[user_id]["language"]
    message_text = update.message.text

    # مدیریت دکمه‌های ادمین
    if user_id == ADMIN_ID:
        if message_text == "📢 ارسال پیام همگانی":
            await update.message.reply_text("لطفاً پیام خود را وارد کنید! مثال: /broadcast سلام به همه!", reply_markup=get_admin_menu())
            return
        elif message_text == "👥 مدیریت کاربران":
            await manage_users(update, context)
            return
        elif message_text == "📊 آمار ربات":
            await bot_stats(update, context)
            return
        elif message_text == "🔴 خاموش کردن ربات":
            await stop_bot(update, context)
            return
        elif message_text == "🟢 روشن کردن ربات":
            await start_bot(update, context)
            return
        elif message_text == "⬅️ بازگشت به منوی اصلی":
            menu = get_main_menu(lang)
            await update.message.reply_text("به منوی اصلی برگشتید!", reply_markup=menu)
            return

    # مدیریت دکمه‌های کاربران عادی
    if message_text == "🎮 بازی":
        await game(update, context)
        return
    elif message_text == "😂 جوک":
        await joke(update, context)
        return
    elif message_text == "💻 تولید کد":
        await update.message.reply_text("لطفاً توضیح بده چه کدی می‌خوای! مثال: بنویس یه تابع برای جمع دو عدد در پایتون", reply_markup=get_main_menu(lang))
        return
    elif message_text == "🌐 جستجو در وب":
        await update.message.reply_text("لطفاً چیزی که می‌خوای جستجو کنی رو بنویس! مثال: پایتخت فرانسه", reply_markup=get_main_menu(lang))
        return
    elif message_text == "📹 دانلود از اینستا":
        await update.message.reply_text("لطفاً لینک اینستاگرام رو وارد کن! مثال: /insta [لینک]", reply_markup=get_main_menu(lang))
        return
    elif message_text == "🎵 پیدا کردن آهنگ":
        await update.message.reply_text("لطفاً نام آهنگ رو وارد کن! مثال: /music [نام آهنگ]", reply_markup=get_main_menu(lang))
        return
    elif message_text == "ℹ️ درباره ربات":
        await about(update, context)
        return
    elif message_text == "👨‍💻 درباره سازنده":
        await creator(update, context)
        return
    elif message_text == "📊 سکه‌ها و سؤالم":
        await remaining(update, context)
        return
    elif message_text == "❓ راهنما":
        await help_command(update, context)
        return

    # اگه کاربر توی بازی باشه، پیامش رو به عنوان جواب سؤال در نظر می‌گیریم
    if user_data[user_id]["current_game"]:
        correct_answer = user_data[user_id]["current_game"]["answer"]
        start_time = datetime.strptime(user_data[user_id]["current_game"]["start_time"], "%Y-%m-%d %H:%M:%S")
        level = user_data[user_id]["current_game"]["level"]

        if (datetime.now() - start_time).total_seconds() > 60:
            user_data[user_id]["current_game"] = None
            save_user_data(user_data)
            msg = {
                "fa": "⌛ زمانت تموم شد! دوباره بازی کن با /game",
                "en": "⌛ Time’s up! Play again with /game",
                "ar": "⌛ انتهى الوقت! العب مرة أخرى بـ /game"
            }
            menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
            await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)
            return

        user_answer = update.message.text.strip()
        if user_answer.lower() == correct_answer.lower():
            coins_reward = 5 if level == "medium" else 8
            user_data[user_id]["coins"] += coins_reward
            user_data[user_id]["current_game"] = None
            save_user_data(user_data)
            msg = {
                "fa": f"🎉 آفرین! جواب درست بود! {coins_reward} سکه گرفتی! 🏆\nدوباره بازی کن با دکمه زیر",
                "en": f"🎉 Well done! Correct answer! You got {coins_reward} coins! 🏆\nPlay again with the button below",
                "ar": f"🎉 أحسنت! الإجابة صحيحة! حصلت على {coins_reward} عملات! 🏆\nالعب مرة أخرى باستخدام الزر أدناه"
            }
            menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
            await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"کاربر {user_id} به سؤال {'متوسط' if level == 'medium' else 'سخت'} درست جواب داد و {coins_reward} سکه گرفت.")
        else:
            user_data[user_id]["current_game"] = None
            save_user_data(user_data)
            msg = {
                "fa": f"❌ اشتباه بود! جواب درست: {correct_answer}\nدوباره بازی کن با دکمه زیر",
                "en": f"❌ Wrong! The correct answer was: {correct_answer}\nPlay again with the button below",
                "ar": f"❌ خطأ! الإجابة الصحيحة كانت: {correct_answer}\nالعب مرة أخرى باستخدام الزر أدناه"
            }
            menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
            await update.message.reply_text(msg.get(lang, msg["fa"]), reply_markup=menu)
        return

    # اگه توی بازی نباشه، پیامش رو به عنوان سؤال معمولی در نظر می‌گیریم
    if user_data[user_id]["daily_questions"] >= 3 and user_data[user_id]["coins"] <= 0:
        limit_msg = {
            "fa": "اوپس! سؤال‌های رایگان امروزت تموم شد و سکه نداری! 😔\nبا دکمه بازی، سکه ببر.",
            "en": "Oops! You’ve used up your free questions for today and have no coins! 😔\nPlay games to win coins.",
            "ar": "عذراً! لقد استنفدت أسئلتك المجانية اليوم وليس لديك عملات! 😔\nالعب الألعاب للفوز بالعملات."
        }
        menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
        await update.message.reply_text(limit_msg.get(lang, limit_msg["fa"]), reply_markup=menu)
        return

    if user_data[user_id]["daily_questions"] < 3:
        user_data[user_id]["daily_questions"] += 1
        save_user_data(user_data)
    else:
        user_data[user_id]["coins"] -= 1
        save_user_data(user_data)
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"کاربر {user_id} 1 سکه خرج کرد برای سؤال اضافی.")

    log_message(user_id, update.message.text)
    response = get_deepseek_response(update.message.text, lang)
    menu = get_admin_menu() if user_id == ADMIN_ID else get_main_menu(lang)
    await update.message.reply_text(response, reply_markup=menu)

# اجرای ربات
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("creator", creator))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("game", game))
    app.add_handler(CommandHandler("code", generate_code))
    app.add_handler(CommandHandler("search", web_search))
    app.add_handler(CommandHandler("insta", insta))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(CommandHandler("remaining", remaining))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    app.add_handler(CommandHandler("manage_users", manage_users))
    app.add_handler(CommandHandler("stats", bot_stats))
    app.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات در حال اجرا است...")
    app.run_polling()

if __name__ == "__main__":
    main()
EOF

# حذف Webhook و اجرای ربات
echo "حذف Webhook..."
curl -s "https://api.telegram.org/bot$TELEGRAM_TOKEN/deleteWebhook"
echo "🔥 در حال اجرای ربات..."
python3 /home/sbiorg/final_bot.py
