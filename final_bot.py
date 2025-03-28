import os
import json
import datetime
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# تنظیمات
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
USER_DATA_FILE = "users.json"
LOG_FILE = "log.txt"
CREATOR_NAME = "سبحان برخورداری"
CREATOR_INFO_FA = (
    f"🧠 **{CREATOR_NAME}** سازنده من است! 🎉\n"
    "او یک برنامه‌نویس خلاق و باهوش است که من را با عشق و دقت طراحی کرده. "
    "سبحان عاشق حل مسائل پیچیده و ساختن ابزارهای مفید مثل من است. "
    "اگر سوالی درباره من دارید، می‌توانید از او بپرسید! 😊"
)
CREATOR_INFO_EN = (
    f"🧠 **{CREATOR_NAME}** is my creator! 🎉\n"
    "He is a creative and intelligent programmer who designed me with love and care. "
    "Sobhan loves solving complex problems and building useful tools like me. "
    "If you have any questions about me, you can ask him! 😊"
)
BOT_USERNAME = "@sbiyar_bot"  # نام کاربری ربات خود را وارد کنید (مثلاً @MyAwesomeBot)

# بررسی متغیرهای محیطی
if not TELEGRAM_TOKEN or not ADMIN_ID:
    raise ValueError("لطفاً متغیرهای محیطی TELEGRAM_TOKEN و ADMIN_ID را تنظیم کنید.")

# تابع برای بارگذاری داده‌های کاربران از فایل users.json
def load_user_data():
    """Load user data from users.json."""
    try:
        if not os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading user data: {e}")
        return {}

# تابع برای ذخیره داده‌های کاربران در فایل users.json
def save_user_data(data):
    """Save user data to users.json."""
    try:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving user data: {e}")

# تابع برای ثبت لاگ در فایل log.txt
def log_message(message):
    """Log a message to log.txt."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Error logging message: {e}")

# تابع برای دریافت زبان کاربر
def get_user_language(user_id, user_data):
    """Get the user's language from user data."""
    return user_data.get(str(user_id), {}).get("language", "fa")  # Default to Persian

# تابع برای دریافت سؤال از Open Trivia API
def get_trivia_question():
    """Fetch a trivia question from Open Trivia API."""
    try:
        response = requests.get("https://opentdb.com/api.php?amount=1&type=multiple")
        data = response.json()
        if data["response_code"] == 0:
            question = data["results"][0]
            return {
                "question": question["question"],
                "correct_answer": question["correct_answer"],
                "incorrect_answers": question["incorrect_answers"]
            }
    except Exception as e:
        log_message(f"Error fetching trivia question: {e}")
    return None

# تابع برای دانلود آهنگ یا ویدیو
def download_media(url, media_type="audio"):
    """Download audio or video from a URL using yt-dlp."""
    try:
        ydl_opts = {
            "format": "bestaudio/best" if media_type == "audio" else "bestvideo+bestaudio/best",
            "outtmpl": "downloaded_media.%(ext)s",
            "merge_output_format": "mp4" if media_type == "video" else None,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }] if media_type == "audio" else [],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return "downloaded_media.mp3" if media_type == "audio" else "downloaded_media.mp4"
    except Exception as e:
        log_message(f"Error downloading media: {e}")
        return None

# تابع برای دریافت رکوردبندی
def get_leaderboard(game_name, user_data):
    """Get leaderboard for a specific game."""
    scores = []
    for user_id, data in user_data.items():
        score = data.get("scores", {}).get(game_name, 0)
        if score > 0:
            scores.append((data["username"], score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:5]  # 5 نفر برتر

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command to welcome the user and ask for language."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    user_data = load_user_data()

    # بررسی اگر کاربر از طریق لینک دعوت وارد شده است
    if context.args and context.args[0].startswith("ref_"):
        referrer_id = context.args[0].split("_")[1]
        if str(user_id) not in user_data and referrer_id in user_data:
            user_data[referrer_id]["coins"] = user_data[referrer_id].get("coins", 0) + 20
            save_user_data(user_data)
            log_message(f"User {referrer_id} earned 20 coins for referring {user_id} (@{username})")
            try:
                lang = get_user_language(referrer_id, user_data)
                if lang == "fa":
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 یک نفر با لینک دعوت شما وارد شد! 20 سکه به شما اضافه شد.\n"
                             f"🪙 سکه‌های شما: {user_data[referrer_id]['coins']}"
                    )
                else:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 Someone joined using your referral link! You earned 20 coins.\n"
                             f"🪙 Your coins: {user_data[referrer_id]['coins']}"
                    )
            except Exception as e:
                log_message(f"Error notifying referrer {referrer_id}: {e}")

    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            "status": "active",
            "username": username,
            "joined_at": datetime.datetime.now().isoformat(),
            "language": "fa",
            "coins": 0,
            "treasure_game": None,
            "word_battle": None,
            "scores": {  # برای ذخیره امتیازات بازی‌های آنلاین
                "2048": 0,
                "chess": 0,
                "puzzle": 0
            }
        }
        save_user_data(user_data)
        log_message(f"New user started: {user_id} (@{username})")

    # دکمه‌های انتخاب زبان
    keyboard = [
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌟 Please choose your language:\n"
        "لطفاً زبان خود را انتخاب کنید:",
        reply_markup=reply_markup
    )

# هندلر برای دکمه‌ها
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks for language, games, and downloads."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "Unknown"
    user_data = load_user_data()
    lang = get_user_language(user_id, user_data)

    if query.data.startswith("lang_"):
        # انتخاب زبان
        new_lang = query.data.split("_")[1]
        user_data[str(user_id)]["language"] = new_lang
        save_user_data(user_data)
        log_message(f"User {user_id} (@{username}) selected language: {new_lang}")

        if new_lang == "fa":
            welcome_text = (
                "🎉 **خوش آمدید به ربات!**\n"
                f"من توسط {CREATOR_NAME} ساخته شده‌ام.\n"
                "برای دیدن دستورات، /help را بزنید یا دکمه‌های زیر را امتحان کنید!"
            )
        else:
            welcome_text = (
                "🎉 **Welcome to the Bot!**\n"
                f"I was created by {CREATOR_NAME}.\n"
                "To see the commands, use /help or try the buttons below!"
            )

        # دکمه‌های منوی اصلی
        keyboard = [
            [
                InlineKeyboardButton("🗺️ معمای گنج" if new_lang == "fa" else "🗺️ Treasure Riddle",
                                     callback_data="start_treasure_game"),
                InlineKeyboardButton("⚔️ نبرد کلمات (دو نفره)" if new_lang == "fa" else "⚔️ Word Battle (2 Players)",
                                     callback_data="start_word_battle")
            ],
            [
                InlineKeyboardButton("🎲 بازی 2048" if new_lang == "fa" else "🎲 Play 2048",
                                     callback_data="play_2048"),
                InlineKeyboardButton("♟️ شطرنج آنلاین" if new_lang == "fa" else "♟️ Online Chess",
                                     callback_data="play_chess")
            ],
            [
                InlineKeyboardButton("🧩 پازل آنلاین" if new_lang == "fa" else "🧩 Online Puzzle",
                                     callback_data="play_puzzle"),
                InlineKeyboardButton("🏆 رکوردها" if new_lang == "fa" else "🏆 Leaderboard",
                                     callback_data="show_leaderboard")
            ],
            [
                InlineKeyboardButton("🎵 دانلود آهنگ" if new_lang == "fa" else "🎵 Download Music",
                                     callback_data="download_music"),
                InlineKeyboardButton("🎥 دانلود فیلم" if new_lang == "fa" else "🎥 Download Video",
                                     callback_data="download_video")
            ],
            [
                InlineKeyboardButton("💬 چت با مدیر" if new_lang == "fa" else "💬 Chat with Admin",
                                     callback_data="chat_admin"),
                InlineKeyboardButton("ℹ️ درباره سازنده" if new_lang == "fa" else "ℹ️ About Creator",
                                     callback_data="about_me")
            ],
            [
                InlineKeyboardButton("📎 لینک دعوت من" if new_lang == "fa" else "📎 My Referral Link",
                                     callback_data="get_referral_link")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(welcome_text, reply_markup=reply_markup)

    elif query.data == "start_treasure_game":
        # شروع بازی معمای گنج
        trivia = get_trivia_question()
        if not trivia:
            if lang == "fa":
                await query.message.reply_text("❌ خطا در دریافت معما. لطفاً دوباره امتحان کنید.")
            else:
                await query.message.reply_text("❌ Error fetching riddle. Please try again.")
            return

        options = trivia["incorrect_answers"] + [trivia["correct_answer"]]
        random.shuffle(options)
        user_data[str(user_id)]["treasure_game"] = {
            "question": trivia["question"],
            "correct_answer": trivia["correct_answer"],
            "options": options,
            "level": 1,
            "max_levels": 5
        }
        save_user_data(user_data)
        log_message(f"User {user_id} (@{username}) started treasure game")

        keyboard = [[InlineKeyboardButton(opt, callback_data=f"treasure_answer_{i}")]
                    for i, opt in enumerate(options)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if lang == "fa":
            await query.message.reply_text(
                f"🗺️ **معمای گنج - سطح {user_data[str(user_id)]['treasure_game']['level']}**\n"
                f"سؤال: {trivia['question']}\n"
                "یکی از گزینه‌ها را انتخاب کنید:",
                reply_markup=reply_markup
            )
        else:
            await query.message.reply_text(
                f"🗺️ **Treasure Riddle - Level {user_data[str(user_id)]['treasure_game']['level']}**\n"
                f"Question: {trivia['question']}\n"
                "Choose one option:",
                reply_markup=reply_markup
            )

    elif query.data.startswith("treasure_answer_"):
        # پاسخ به معمای گنج
        answer_index = int(query.data.split("_")[2])
        treasure_game = user_data[str(user_id)]["treasure_game"]
        selected_answer = treasure_game["options"][answer_index]

        if selected_answer == treasure_game["correct_answer"]:
            treasure_game["level"] += 1
            if treasure_game["level"] > treasure_game["max_levels"]:
                user_data[str(user_id)]["coins"] += 10
                user_data[str(user_id)]["treasure_game"] = None
                save_user_data(user_data)
                if lang == "fa":
                    win_text = (
                        f"🎉 **تبریک می‌گم!**\n"
                        "شما گنج را پیدا کردید و 10 سکه برنده شدید!\n"
                        f"🪙 سکه‌های شما: {user_data[str(user_id)]['coins']}"
                    )
                else:
                    win_text = (
                        f"🎉 **Congratulations!**\n"
                        "You found the treasure and won 10 coins!\n"
                        f"🪙 Your coins: {user_data[str(user_id)]['coins']}"
                    )
                await query.message.reply_text(win_text)
                return

            # سؤال بعدی
            trivia = get_trivia_question()
            if not trivia:
                if lang == "fa":
                    await query.message.reply_text("❌ خطا در دریافت معما. لطفاً دوباره امتحان کنید.")
                else:
                    await query.message.reply_text("❌ Error fetching riddle. Please try again.")
                return

            options = trivia["incorrect_answers"] + [trivia["correct_answer"]]
            random.shuffle(options)
            user_data[str(user_id)]["treasure_game"] = {
                "question": trivia["question"],
                "correct_answer": trivia["correct_answer"],
                "options": options,
                "level": treasure_game["level"],
                "max_levels": treasure_game["max_levels"]
            }
            save_user_data(user_data)

            keyboard = [[InlineKeyboardButton(opt, callback_data=f"treasure_answer_{i}")]
                        for i, opt in enumerate(options)]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if lang == "fa":
                await query.message.reply_text(
                    f"✅ پاسخ درست بود! به سطح بعدی می‌روید.\n"
                    f"🗺️ **معمای گنج - سطح {treasure_game['level']}**\n"
                    f"سؤال: {trivia['question']}\n"
                    "یکی از گزینه‌ها را انتخاب کنید:",
                    reply_markup=reply_markup
                )
            else:
                await query.message.reply_text(
                    f"✅ Correct answer! Moving to the next level.\n"
                    f"🗺️ **Treasure Riddle - Level {treasure_game['level']}**\n"
                    f"Question: {trivia['question']}\n"
                    "Choose one option:",
                    reply_markup=reply_markup
                )
        else:
            user_data[str(user_id)]["treasure_game"] = None
            save_user_data(user_data)
            if lang == "fa":
                await query.message.reply_text(
                    f"❌ پاسخ اشتباه بود! جواب درست: {treasure_game['correct_answer']}\n"
                    "بازی تمام شد. دوباره امتحان کنید!"
                )
            else:
                await query.message.reply_text(
                    f"❌ Wrong answer! Correct answer: {treasure_game['correct_answer']}\n"
                    "Game over. Try again!"
                )

    elif query.data == "start_word_battle":
        # شروع بازی دو نفره (نبرد کلمات) - رایگان
        # پیدا کردن حریف
        opponent_id = None
        for uid, data in user_data.items():
            if uid != str(user_id) and data.get("status") == "active" and not data.get("word_battle"):
                opponent_id = uid
                break

        if not opponent_id:
            if lang == "fa":
                await query.message.reply_text("⏳ در حال حاضر حریفی پیدا نشد. لطفاً کمی صبر کنید و دوباره امتحان کنید.")
            else:
                await query.message.reply_text("⏳ No opponent found at the moment. Please wait and try again.")
            return

        # شروع بازی
        user_data[str(user_id)]["word_battle"] = {
            "opponent": opponent_id,
            "score": 0,
            "opponent_score": 0,
            "round": 1,
            "max_rounds": 3,
            "current_word": random.choice(["apple", "book", "cat", "dog", "elephant", "fish", "girl", "house", "ice", "jump"])
        }
        user_data[opponent_id]["word_battle"] = {
            "opponent": str(user_id),
            "score": 0,
            "opponent_score": 0,
            "round": 1,
            "max_rounds": 3,
            "current_word": user_data[str(user_id)]["word_battle"]["current_word"]
        }
        save_user_data(user_data)
        log_message(f"Word battle started between {user_id} (@{username}) and {opponent_id}")

        if lang == "fa":
            await query.message.reply_text(
                f"⚔️ **نبرد کلمات شروع شد!**\n"
                f"حریف شما: @{user_data[opponent_id]['username']}\n"
                f"کلمه دور اول: {user_data[str(user_id)]['word_battle']['current_word']}\n"
                "یک جمله با این کلمه بسازید (مثلاً: The cat is on the mat):"
            )
        else:
            await query.message.reply_text(
                f"⚔️ **Word Battle Started!**\n"
                f"Opponent: @{user_data[opponent_id]['username']}\n"
                f"First round word: {user_data[str(user_id)]['word_battle']['current_word']}\n"
                "Make a sentence with this word (e.g., The cat is on the mat):"
            )

        opponent_lang = get_user_language(opponent_id, user_data)
        if opponent_lang == "fa":
            await context.bot.send_message(
                chat_id=opponent_id,
                text=f"⚔️ **نبرد کلمات شروع شد!**\n"
                     f"حریف شما: @{username}\n"
                     f"کلمه دور اول: {user_data[opponent_id]['word_battle']['current_word']}\n"
                     "یک جمله با این کلمه بسازید (مثلاً: The cat is on the mat):"
            )
        else:
            await context.bot.send_message(
                chat_id=opponent_id,
                text=f"⚔️ **Word Battle Started!**\n"
                     f"Opponent: @{username}\n"
                     f"First round word: {user_data[opponent_id]['word_battle']['current_word']}\n"
                     "Make a sentence with this word (e.g., The cat is on the mat):"
            )

    elif query.data == "play_2048":
        # بازی 2048
        if lang == "fa":
            await query.message.reply_text(
                "🎲 **بازی 2048**\n"
                "برای بازی، روی لینک زیر کلیک کنید:\n"
                "https://play2048.co/\n"
                "بعد از اتمام بازی، امتیاز خود را بنویسید (مثلاً 5000):"
            )
        else:
            await query.message.reply_text(
                "🎲 **Play 2048**\n"
                "Click the link below to play:\n"
                "https://play2048.co/\n"
                "After finishing the game, send your score (e.g., 5000):"
            )
        user_data[str(user_id)]["waiting_for_score"] = "2048"
        save_user_data(user_data)

    elif query.data == "play_chess":
        # بازی شطرنج آنلاین
        if lang == "fa":
            await query.message.reply_text(
                "♟️ **شطرنج آنلاین**\n"
                "برای بازی، روی لینک زیر کلیک کنید:\n"
                "https://www.chess.com/play/computer\n"
                "بعد از اتمام بازی، تعداد حرکات تا پیروزی را بنویسید (مثلاً 30):"
            )
        else:
            await query.message.reply_text(
                "♟️ **Online Chess**\n"
                "Click the link below to play:\n"
                "https://www.chess.com/play/computer\n"
                "After finishing the game, send the number of moves to win (e.g., 30):"
            )
        user_data[str(user_id)]["waiting_for_score"] = "chess"
        save_user_data(user_data)

    elif query.data == "play_puzzle":
        # بازی پازل آنلاین
        if lang == "fa":
            await query.message.reply_text(
                "🧩 **پازل آنلاین**\n"
                "برای بازی، روی لینک زیر کلیک کنید:\n"
                "https://www.jigsawplanet.com/\n"
                "بعد از اتمام بازی، زمان خود را به ثانیه بنویسید (مثلاً 120):"
            )
        else:
            await query.message.reply_text(
                "🧩 **Online Puzzle**\n"
                "Click the link below to play:\n"
                "https://www.jigsawplanet.com/\n"
                "After finishing the game, send your time in seconds (e.g., 120):"
            )
        user_data[str(user_id)]["waiting_for_score"] = "puzzle"
        save_user_data(user_data)

    elif query.data == "show_leaderboard":
        # نمایش رکوردها
        leaderboard_2048 = get_leaderboard("2048", user_data)
        leaderboard_chess = get_leaderboard("chess", user_data)
        leaderboard_puzzle = get_leaderboard("puzzle", user_data)

        if lang == "fa":
            leaderboard_text = (
                "🏆 **رکوردها**\n\n"
                "🎲 **بازی 2048**\n" +
                "\n".join([f"{i+1}. @{user} - {score}" for i, (user, score) in enumerate(leaderboard_2048)]) +
                "\n\n♟️ **شطرنج آنلاین**\n" +
                "\n".join([f"{i+1}. @{user} - {score} حرکت" for i, (user, score) in enumerate(leaderboard_chess)]) +
                "\n\n🧩 **پازل آنلاین**\n" +
                "\n".join([f"{i+1}. @{user} - {score} ثانیه" for i, (user, score) in enumerate(leaderboard_puzzle)])
            )
        else:
            leaderboard_text = (
                "🏆 **Leaderboard**\n\n"
                "🎲 **2048 Game**\n" +
                "\n".join([f"{i+1}. @{user} - {score}" for i, (user, score) in enumerate(leaderboard_2048)]) +
                "\n\n♟️ **Online Chess**\n" +
                "\n".join([f"{i+1}. @{user} - {score} moves" for i, (user, score) in enumerate(leaderboard_chess)]) +
                "\n\n🧩 **Online Puzzle**\n" +
                "\n".join([f"{i+1}. @{user} - {score} seconds" for i, (user, score) in enumerate(leaderboard_puzzle)])
            )

        await query.message.reply_text(leaderboard_text or "🏆 **Leaderboard**\nNo records yet!")

    elif query.data == "download_music":
        # دانلود آهنگ
        if lang == "fa":
            await query.message.reply_text("🎵 لطفاً لینک آهنگ (مثلاً از یوتیوب یا اینستاگرام) را بفرستید:")
        else:
            await query.message.reply_text("🎵 Please send the music link (e.g., from YouTube or Instagram):")
        user_data[str(user_id)]["waiting_for_music_link"] = True
        save_user_data(user_data)

    elif query.data == "download_video":
        # دانلود ویدیو
        if lang == "fa":
            await query.message.reply_text("🎥 لطفاً لینک ویدیو (مثلاً از یوتیوب یا اینستاگرام) را بفرستید:")
        else:
            await query.message.reply_text("🎥 Please send the video link (e.g., from YouTube or Instagram):")
        user_data[str(user_id)]["waiting_for_video_link"] = True
        save_user_data(user_data)

    elif query.data == "chat_admin":
        # چت با مدیر
        if lang == "fa":
            await query.message.reply_text(
                "💬 لطفاً پیام خود را برای مدیر بنویسید:\n"
                "مثال: سلام، من یک مشکل دارم!"
            )
        else:
            await query.message.reply_text(
                "💬 Please write your message for the admin:\n"
                "Example: Hi, I have a problem!"
            )

    elif query.data == "about_me":
        # درباره سازنده
        if lang == "fa":
            await query.message.reply_text(CREATOR_INFO_FA)
        else:
            await query.message.reply_text(CREATOR_INFO_EN)

    elif query.data == "get_referral_link":
        # دریافت لینک دعوت
        referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
        if lang == "fa":
            await query.message.reply_text(
                f"📎 **لینک دعوت شما:**\n"
                f"{referral_link}\n"
                "این لینک را با دوستان خود به اشتراک کنید. به ازای هر نفر که با لینک شما وارد شود، 20 سکه دریافت می‌کنید!"
            )
        else:
            await query.message.reply_text(
                f"📎 **Your Referral Link:**\n"
                f"{referral_link}\n"
                "Share this link with your friends. You’ll get 20 coins for each person who joins using your link!"
            )

# دستور /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the help message."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    user_data = load_user_data()
    lang = get_user_language(user_id, user_data)
    log_message(f"Command /help executed by {user_id} (@{username})")

    if lang == "fa":
        help_text = (
            "📋 **لیست دستورات ربات:**\n"
            "/start - شروع کار با ربات و انتخاب زبان\n"
            "/help - نمایش این راهنما\n"
            "/aboutme - اطلاعات درباره سازنده من\n"
            "/chatadmin <پیام> - ارسال پیام به مدیر\n"
            "🎮 برای بازی‌ها و دانلود، از دکمه‌های منوی اصلی استفاده کنید!\n"
            "دستورات ادمین:\n"
            "/stats - نمایش آمار کاربران\n"
            "/getlogs - دریافت فایل لاگ‌ها\n"
            "/users - نمایش لیست کاربران\n"
            "/givecoins <user_id> <amount> - دادن سکه به کاربر\n"
            "/broadcast <پیام> - ارسال پیام به همه کاربران\n"
            "💬 برای پاسخ به پیام کاربران، روی پیام آن‌ها Reply کنید."
        )
    else:
        help_text = (
            "📋 **List of Bot Commands:**\n"
            "/start - Start the bot and choose your language\n"
            "/help - Show this help message\n"
            "/aboutme - Information about my creator\n"
            "/chatadmin <message> - Send a message to the admin\n"
            "🎮 Use the main menu buttons for games and downloads!\n"
            "Admin Commands:\n"
            "/stats - Show user statistics\n"
            "/getlogs - Get the log file\n"
            "/users - Show list of users\n"
            "/givecoins <user_id> <amount> - Give coins to a user\n"
            "/broadcast <message> - Send a message to all users\n"
            "💬 To reply to users, use Reply on their message."
        )

    await update.message.reply_text(help_text)

# دستور /aboutme
async def about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display information about the creator."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    user_data = load_user_data()
    lang = get_user_language(user_id, user_data)
    log_message(f"Command /aboutme executed by {user_id} (@{username})")

    if lang == "fa":
        await update.message.reply_text(CREATOR_INFO_FA)
    else:
        await update.message.reply_text(CREATOR_INFO_EN)

# دستور /chatadmin (ارسال پیام به مدیر)
async def chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message to the admin."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    user_data = load_user_data()
    lang = get_user_language(user_id, user_data)

    if not context.args:
        if lang == "fa":
            await update.message.reply_text(
                "💬 لطفاً پیام خود را برای مدیر بنویسید:\n"
                "مثال: سلام، من یک مشکل دارم!"
            )
        else:
            await update.message.reply_text(
                "💬 Please write your message for the admin:\n"
                "Example: Hi, I have a problem!"
            )
        return

    message = " ".join(context.args)
    log_message(f"Message to admin from {user_id} (@{username}): {message}")

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💬 **Message from user {user_id} (@{username}):**\n{message}",
            reply_markup={"force_reply": True}
        )
        if lang == "fa":
            await update.message.reply_text("✅ پیام شما به مدیر ارسال شد. منتظر پاسخ باشید!")
        else:
            await update.message.reply_text("✅ Your message has been sent to the admin. Please wait for a reply!")
    except Exception as e:
        log_message(f"Error sending message to admin from {user_id}: {e}")
        if lang == "fa":
            await update.message.reply_text("❌ خطا در ارسال پیام به مدیر. لطفاً دوباره امتحان کنید.")
        else:
            await update.message.reply_text("❌ Error sending message to admin. Please try again.")

# دستور /stats (فقط برای ادمین)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics (admin only)."""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ You don’t have access to this command!")
        return

    user_data = load_user_data()
    total_users = len(user_data)
    active_users = sum(1 for user in user_data.values() if user.get("status") == "active")
    total_coins = sum(user.get("coins", 0) for user in user_data.values())

    stats_text = (
        f"📊 **Bot Statistics:**\n"
        f"Total Users: {total_users}\n"
        f"Active Users: {active_users}\n"
        f"Total Coins in Circulation: {total_coins}"
    )
    log_message(f"Command /stats executed by admin ({user_id})")
    await update.message.reply_text(stats_text)

# دستور /users (فقط برای ادمین)
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of users (admin only)."""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ You don’t have access to this command!")
        return

    user_data = load_user_data()
    users_list = []
    for uid, data in user_data.items():
        users_list.append(
            f"User ID: {uid}\n"
            f"Username: @{data['username']}\n"
            f"Coins: {data.get('coins', 0)}\n"
            f"Referral Link: https://t.me/{BOT_USERNAME}?start=ref_{uid}\n"
            "-------------------"
        )

    users_text = "\n".join(users_list) or "No users found."
    log_message(f"Command /users executed by admin ({user_id})")
    await update.message.reply_text(f"👥 **List of Users:**\n{users_text}")

# دستور /givecoins (فقط برای ادمین)
async def give_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give coins to a user (admin only)."""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ You don’t have access to this command!")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /givecoins <user_id> <amount>\nExample: /givecoins 123456 50")
        return

    target_user_id = context.args[0]
    try:
        amount = int(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please enter a valid positive number for the amount.")
        return

    user_data = load_user_data()
    if target_user_id not in user_data:
        await update.message.reply_text("User not found!")
        return

    user_data[target_user_id]["coins"] = user_data[target_user_id].get("coins", 0) + amount
    save_user_data(user_data)
    log_message(f"Admin ({user_id}) gave {amount} coins to user {target_user_id}")

    await update.message.reply_text(f"✅ {amount} coins given to user {target_user_id}.")
    try:
        target_lang = get_user_language(target_user_id, user_data)
        if target_lang == "fa":
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎁 ادمین به شما {amount} سکه هدیه داد!\n"
                     f"🪙 سکه‌های شما: {user_data[target_user_id]['coins']}"
            )
        else:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎁 The admin gave you {amount} coins!\n"
                     f"🪙 Your coins: {user_data[target_user_id]['coins']}"
            )
    except Exception as e:
        log_message(f"Error notifying user {target_user_id} about coins: {e}")

# دستور /getlogs (فقط برای ادمین)
async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send log.txt file to admin."""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ You don’t have access to this command!")
        return

    try:
        with open(LOG_FILE, "rb") as f:
            await update.message.reply_document(document=f, filename="log.txt")
        log_message(f"Log file sent to admin ({user_id})")
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending logs: {e}")
        log_message(f"Error sending logs to admin ({user_id}): {e}")

# دستور /broadcast (فقط برای ادمین)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast a message to all users (admin only)."""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ You don’t have access to this command!")
        return

    if not context.args:
        await update.message.reply_text("📢 Please enter your message after the command.\nExample: /broadcast Hello everyone!")
        return

    message = " ".join(context.args)
    user_data = load_user_data()
    success_count = 0
    failed_count = 0

    for target_user_id in user_data.keys():
        try:
            lang = get_user_language(target_user_id, user_data)
            if lang == "fa":
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📢 **پیام از ادمین:**\n{message}"
                )
            else:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📢 **Message from Admin:**\n{message}"
                )
            success_count += 1
        except Exception as e:
            failed_count += 1
            log_message(f"Error sending broadcast to {target_user_id}: {e}")

    log_message(f"Command /broadcast executed by admin ({user_id}): {message}")
    await update.message.reply_text(
        f"📢 **Broadcast Result:**\n"
        f"Successful: {success_count}\n"
        f"Failed: {failed_count}"
    )

# هندلر پیام‌های متنی
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    user_data = load_user_data()
    lang = get_user_language(user_id, user_data)
    message = update.message.text.lower()

    # اگر پیام یک Reply از ادمین باشد، به تابع reply_to_user هدایت می‌شود
    if str(user_id) == ADMIN_ID and update.message.reply_to_message:
        await reply_to_user(update, context)
        return

    # بررسی اگر کاربر درباره سازنده پرسید
    if "سبحان" in message or "سازنده" in message or "مغز متفکر" in message or "sobhan" in message or "creator" in message:
        log_message(f"User {user_id} (@{username}) asked about the creator")
        if lang == "fa":
            await update.message.reply_text(CREATOR_INFO_FA)
        else:
            await update.message.reply_text(CREATOR_INFO_EN)
        return

    # بررسی اگر کاربر در حال ارسال لینک برای دانلود است
    if user_data[str(user_id)].get("waiting_for_music_link"):
        user_data[str(user_id)]["waiting_for_music_link"] = False
        save_user_data(user_data)
        if lang == "fa":
            await update.message.reply_text("⏳ در حال دانلود آهنگ... لطفاً صبر کنید.")
        else:
            await update.message.reply_text("⏳ Downloading music... Please wait.")

        file_path = download_media(message, media_type="audio")
        if file_path:
            with open(file_path, "rb") as f:
                await update.message.reply_audio(audio=f)
            os.remove(file_path)
            log_message(f"Music downloaded for user {user_id} (@{username})")
        else:
            if lang == "fa":
                await update.message.reply_text("❌ خطا در دانلود آهنگ. لطفاً لینک معتبر بفرستید.")
            else:
                await update.message.reply_text("❌ Error downloading music. Please send a valid link.")
        return

    if user_data[str(user_id)].get("waiting_for_video_link"):
        user_data[str(user_id)]["waiting_for_video_link"] = False
        save_user_data(user_data)
        if lang == "fa":
            await update.message.reply_text("⏳ در حال دانلود ویدیو... لطفاً صبر کنید.")
        else:
            await update.message.reply_text("⏳ Downloading video... Please wait.")

        file_path = download_media(message, media_type="video")
        if file_path:
            with open(file_path, "rb") as f:
                await update.message.reply_video(video=f)
            os.remove(file_path)
            log_message(f"Video downloaded for user {user_id} (@{username})")
        else:
            if lang == "fa":
                await update.message.reply_text("❌ خطا در دانلود ویدیو. لطفاً لینک معتبر بفرستید.")
            else:
                await update.message.reply_text("❌ Error downloading video. Please send a valid link.")
        return

    # بررسی اگر کاربر در حال ارسال امتیاز بازی آنلاین است
    if user_data[str(user_id)].get("waiting_for_score"):
        game_name = user_data[str(user_id)]["waiting_for_score"]
        user_data[str(user_id)]["waiting_for_score"] = None
        try:
            score = int(message)
            if score < 0:
                raise ValueError
            user_data[str(user_id)]["scores"][game_name] = max(
                user_data[str(user_id)]["scores"].get(game_name, 0), score
            )
            save_user_data(user_data)
            log_message(f"User {user_id} (@{username}) submitted score {score} for {game_name}")

            if lang == "fa":
                await update.message.reply_text(
                    f"✅ امتیاز شما برای {game_name} ثبت شد: {score}\n"
                    "برای دیدن رکوردها، از منوی اصلی گزینه 'رکوردها' را انتخاب کنید."
                )
            else:
                await update.message.reply_text(
                    f"✅ Your score for {game_name} has been recorded: {score}\n"
                    "To see the leaderboard, select 'Leaderboard' from the main menu."
                )
        except ValueError:
            if lang == "fa":
                await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید (مثلاً 5000)!")
            else:
                await update.message.reply_text("❌ Please enter a valid number (e.g., 5000)!")
        return

    # بررسی اگر کاربر در حال بازی نبرد کلمات است
    if str(user_id) in user_data and user_data[str(user_id)].get("word_battle"):
        word_battle = user_data[str(user_id)]["word_battle"]
        opponent_id = word_battle["opponent"]
        current_word = word_battle["current_word"]

        # بررسی اگر کلمه در جمله استفاده شده است
        if current_word.lower() in message.lower():
            word_battle["score"] += len(message.split())  # امتیاز بر اساس تعداد کلمات جمله
            user_data[str(user_id)]["word_battle"] = word_battle
            user_data[opponent_id]["word_battle"]["opponent_score"] = word_battle["score"]
            save_user_data(user_data)

            # بررسی اگر هر دو بازیکن جمله خود را فرستاده‌اند
            if user_data[opponent_id]["word_battle"]["score"] > 0:
                word_battle["round"] += 1
                if word_battle["round"] > word_battle["max_rounds"]:
                    # پایان بازی
                    user_score = word_battle["score"]
                    opponent_score = user_data[opponent_id]["word_battle"]["score"]
                    if user_score > opponent_score:
                        winner = str(user_id)
                        loser = opponent_id
                    elif opponent_score > user_score:
                        winner = opponent_id
                        loser = str(user_id)
                    else:
                        winner = None

                    if winner:
                        if lang == "fa":
                            await update.message.reply_text(
                                f"🏆 **شما برنده شدید!**\n"
                                f"امتیاز شما: {user_score}\n"
                                f"امتیاز حریف: {opponent_score}\n"
                                "این بازی فقط برای سرگرمی بود!"
                            )
                        else:
                            await update.message.reply_text(
                                f"🏆 **You Won!**\n"
                                f"Your score: {user_score}\n"
                                f"Opponent’s score: {opponent_score}\n"
                                "This game was just for fun!"
                            )

                        opponent_lang = get_user_language(opponent_id, user_data)
                        if opponent_lang == "fa":
                            await context.bot.send_message(
                                chat_id=opponent_id,
                                text=f"❌ **شما باختید!**\n"
                                     f"امتیاز شما: {opponent_score}\n"
                                     f"امتیاز حریف: {user_score}\n"
                                     "این بازی فقط برای سرگرمی بود!"
                            )
                        else:
                            await context.bot.send_message(
                                chat_id=opponent_id,
                                text=f"❌ **You Lost!**\n"
                                     f"Your score: {opponent_score}\n"
                                     f"Opponent’s score: {user_score}\n"
                                     "This game was just for fun!"
                            )
                    else:
                        if lang == "fa":
                            await update.message.reply_text(
                                f"🤝 **مساوی!**\n"
                                f"امتیاز شما: {user_score}\n"
                                f"امتیاز حریف: {opponent_score}\n"
                                "این بازی فقط برای سرگرمی بود!"
                            )
                        else:
                            await update.message.reply_text(
                                f"🤝 **It’s a Tie!**\n"
                                f"Your score: {user_score}\n"
                                f"Opponent’s score: {opponent_score}\n"
                                "This game was just for fun!"
                            )

                        opponent_lang = get_user_language(opponent_id, user_data)
                        if opponent_lang == "fa":
                            await context.bot.send_message(
                                chat_id=opponent_id,
                                text=f"🤝 **مساوی!**\n"
                                     f"امتیاز شما: {opponent_score}\n"
                                     f"امتیاز حریف: {user_score}\n"
                                     "این بازی فقط برای سرگرمی بود!"
                            )
                        else:
                            await context.bot.send_message(
                                chat_id=opponent_id,
                                text=f"🤝 **It’s a Tie!**\n"
                                     f"Your score: {opponent_score}\n"
                                     f"Opponent’s score: {user_score}\n"
                                     "This game was just for fun!"
                            )

                    user_data[str(user_id)]["word_battle"] = None
                    user_data[opponent_id]["word_battle"] = None
                    save_user_data(user_data)
                    return

                # دور بعدی
                new_word = random.choice(["apple", "book", "cat", "dog", "elephant", "fish", "girl", "house", "ice", "jump"])
                user_data[str(user_id)]["word_battle"]["current_word"] = new_word
                user_data[str(user_id)]["word_battle"]["round"] = word_battle["round"]
                user_data[opponent_id]["word_battle"]["current_word"] = new_word
                user_data[opponent_id]["word_battle"]["round"] = word_battle["round"]
                user_data[str(user_id)]["word_battle"]["score"] = 0
                user_data[opponent_id]["word_battle"]["score"] = 0
                save_user_data(user_data)

                if lang == "fa":
                    await update.message.reply_text(
                        f"✅ جمله شما ثبت شد! منتظر حریف باشید.\n"
                        f"دور {word_battle['round']}: کلمه جدید: {new_word}\n"
                        "یک جمله با این کلمه بسازید:"
                    )
                else:
                    await update.message.reply_text(
                        f"✅ Your sentence was recorded! Waiting for your opponent.\n"
                        f"Round {word_battle['round']}: New word: {new_word}\n"
                        "Make a sentence with this word:"
                    )

                opponent_lang = get_user_language(opponent_id, user_data)
                if opponent_lang == "fa":
                    await context.bot.send_message(
                        chat_id=opponent_id,
                        text=f"✅ جمله شما ثبت شد! منتظر حریف باشید.\n"
                             f"دور {word_battle['round']}: کلمه جدید: {new_word}\n"
                             "یک جمله با این کلمه بسازید:"
                    )
                else:
                    await context.bot.send_message(
                        chat_id=opponent_id,
                        text=f"✅ Your sentence was recorded! Waiting for your opponent.\n"
                             f"Round {word_battle['round']}: New word: {new_word}\n"
                             "Make a sentence with this word:"
                    )
            else:
                if lang == "fa":
                    await update.message.reply_text("⏳ جمله شما ثبت شد. منتظر جمله حریف باشید...")
                else:
                    await update.message.reply_text("⏳ Your sentence was recorded. Waiting for your opponent’s sentence...")
        else:
            if lang == "fa":
                await update.message.reply_text(f"❌ کلمه '{current_word}' در جمله شما استفاده نشده است! دوباره امتحان کنید.")
            else:
                await update.message.reply_text(f"❌ The word '{current_word}' was not used in your sentence! Try again.")
        return

    # پاسخ به پیام‌های معمولی
    log_message(f"Message from {user_id} (@{username}): {message}")
    if lang == "fa":
        await update.message.reply_text(f"📩 **پیام شما:** {message}\nمن دریافت کردم! 😊")
    else:
        await update.message.reply_text(f"📩 **Your message:** {message}\nI received it! 😊")

# تابع اصلی برای راه‌اندازی ربات
def main():
    """Main function to start the bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("aboutme", about_me))
    app.add_handler(CommandHandler("chatadmin", chat_admin))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("givecoins", give_coins))
    app.add_handler(CommandHandler("getlogs", get_logs))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Bot is running...")
    log_message("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
