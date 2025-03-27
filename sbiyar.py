import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
import asyncio
import whisper
from PIL import Image
import io
import os
import yt_dlp
from gtts import gTTS

# تنظیمات لاگ با جزئیات بیشتر
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# توکن‌ها
TELEGRAM_TOKEN = '7779706057:AAFh_88PzgML5rUZ0JfcB-SfcIvzAmUBUng'
HF_API_TOKEN = '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'
HF_TEXT_URL = "https://api-inference.huggingface.co/models/mixtral-8x7b-instruct-v0.1"
HF_IMAGE_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"

# مدل Whisper برای تشخیص ویس
whisper_model = whisper.load_model("base")

# دیکشنری پیام‌ها به دو زبان
MESSAGES = {
    "fa": {
        "welcome": "سلام! من دستیار سبحان هستم، خیلی خوشحال می‌شم که بتونم بهت کمک کنم! 😊\nلطفاً زبانت رو انتخاب کن:",
        "language_prompt": "لطفاً زبانت رو انتخاب کن:",
        "welcome_after_language": (
            "خیلی خوشحال می‌شم که بتونم بهت کمک کنم! 😊 "
            "من یه ربات خفنم که می‌تونم کلی کار باحال بکنم. هر چی بخوای بگو، باهم حرف می‌زنیم و خوش می‌گذرونیم! "
            "می‌تونی درباره هر موضوعی باهام صحبت کنی، مثلاً:\n"
            "- از عشق و عاشقی بگیم، یا یه خاطره باحال تعریف کنی!\n"
            "- درباره فیلم و سریال مورد علاقه‌ت حرف بزنیم، مثلاً آخرین فیلمی که دیدی چی بود؟\n"
            "- اگه گیمری، بگو چه بازی‌ای رو دوست داری، منم گیمرما! 🎮\n"
            "- یا حتی درباره رویاهات، آرزوهات، یا یه روز رویاهات باهام حرف بزن!\n"
            "من می‌تونم ویس فارسی بفهمم، عکساتو تحلیل کنم، از اینستا و جاهای دیگه ویدیو دانلود کنم، "
            "آهنگ برات پیدا کنم، و جوابامو به‌صورت صوتی بفرستم. بگو /help تا ببینی چه کارای دیگه‌ای می‌تونم بکنم! "
            "حالا بگو، درباره چی دوست داری حرف بزنیم؟ 😄"
        ),
        "help": (
            "اینا کاراییه که می‌تونم بکنم:\n"
            "/start - شروع چت\n"
            "/language - تغییر زبان\n"
            "/help - این پیام\n"
            "/joke - یه جوک بگم\n"
            "/song <اسم آهنگ و خواننده> - آهنگ دانلود کن\n"
            "- ویس بفرست، به فارسی می‌فهمم\n"
            "- عکس بفرست، توضیح می‌دم\n"
            "- لینک اینستا یا جاهای دیگه بفرست، ویدیوشو دانلود می‌کنم\n"
            "- هر سؤالی بپرس، جواب می‌دم (متنی و صوتی)!"
        ),
        "joke": "چرا برنامه‌نویسا تاریکی رو دوست دارن؟ چون نور کدشون رو خراب می‌کنه! 😄",
        "thinking": "یه لحظه صبر کن، دارم فکر می‌کنم...",
        "api_error": "یه مشکلی تو API پیش اومد، یه کم صبر کن!",
        "api_exception": "خطا: {error}. بعداً امتحان کن!",
        "image_analyzing": "دارم عکس رو نگاه می‌کنم...",
        "image_description": "تو عکس دیدم: {description}",
        "image_error": "نمی‌تونم عکس رو تحلیل کنم، یه کم صبر کن!",
        "image_exception": "خطا تو تحلیل عکس: {error}",
        "voice_listening": "دارم به ویست گوش می‌دم...",
        "voice_recognized": "شنیدم که گفتی: {text}",
        "voice_error": "خطا تو تشخیص ویس: {error}",
        "voice_response_error": "خطا تو ارسال جواب صوتی: {error}",
        "invalid_link": "لطفاً یه لینک معتبر بفرست (مثلاً از اینستاگرام، توییتر، تیک‌تاک)!",
        "downloading_video": "دارم ویدیوت رو دانلود می‌کنم، یه کم صبر کن...",
        "video_too_large": "فایل خیلی بزرگه! تلگرام فقط فایلای زیر 50 مگابایت رو قبول می‌کنه.",
        "video_download_error": "خطا تو دانلود ویدیو: {error}",
        "video_ready": "ویدیوت آماده‌ست: {title}",
        "song_query_missing": "لطفاً اسم آهنگ و خواننده رو بعد از /song بنویس (مثلاً: /song ماکان بند یه لحظه نگام کن)",
        "searching_song": "دارم دنبال آهنگ '{query}' می‌گردم، یه کم صبر کن...",
        "song_too_large": "فایل خیلی بزرگه! تلگرام فقط فایلای زیر 50 مگابایت رو قبول می‌کنه.",
        "song_download_error": "خطا تو دانلود آهنگ: {error}",
        "song_ready": "آهنگت آماده‌ست: {title}",
    },
    "en": {
        "welcome": "Hello! I'm Sobhan's assistant, and I'm so happy to help you! 😊\nPlease choose your language:",
        "language_prompt": "Please choose your language:",
        "welcome_after_language": (
            "I'm so happy to help you! 😊 "
            "I'm a cool bot that can do lots of awesome things. Just tell me anything, and we'll chat and have fun together! "
            "You can talk to me about anything, for example:\n"
            "- Let's talk about love or share a cool memory!\n"
            "- We can discuss your favorite movie or series—what's the last one you watched?\n"
            "- If you're a gamer, tell me what game you like, I'm a gamer too! 🎮\n"
            "- Or even talk about your dreams, wishes, or a day in your dream life!\n"
            "I can understand Persian voice messages, analyze your photos, download videos from Instagram and other places, "
            "find songs for you, and send my responses as voice messages. Say /help to see what else I can do! "
            "So, what would you like to talk about? 😄"
        ),
        "help": (
            "Here’s what I can do:\n"
            "/start - Start chatting\n"
            "/language - Change language\n"
            "/help - This message\n"
            "/joke - Tell a joke\n"
            "/song <song name and artist> - Download a song\n"
            "- Send a voice message, I can understand Persian\n"
            "- Send a photo, I’ll describe it\n"
            "- Send a link from Instagram or other platforms, I’ll download the video\n"
            "- Ask any question, I’ll answer (text and voice)!"
        ),
        "joke": "Why do programmers prefer dark mode? Because the light attracts bugs! 😄",
        "thinking": "Just a moment, I'm thinking...",
        "api_error": "There was a problem with the API, please wait a bit!",
        "api_exception": "Error: {error}. Try again later!",
        "image_analyzing": "I'm looking at the photo...",
        "image_description": "I saw in the photo: {description}",
        "image_error": "I can’t analyze the photo, please wait a bit!",
        "image_exception": "Error analyzing the photo: {error}",
        "voice_listening": "I'm listening to your voice message...",
        "voice_recognized": "I heard you say: {text}",
        "voice_error": "Error recognizing the voice: {error}",
        "voice_response_error": "Error sending voice response: {error}",
        "invalid_link": "Please send a valid link (e.g., from Instagram, Twitter, TikTok)!",
        "downloading_video": "I'm downloading your video, please wait a bit...",
        "video_too_large": "The file is too large! Telegram only accepts files under 50 MB.",
        "video_download_error": "Error downloading the video: {error}",
        "video_ready": "Your video is ready: {title}",
        "song_query_missing": "Please write the song name and artist after /song (e.g., /song Macan Band Ye Lahze Negam Kon)",
        "searching_song": "I'm searching for the song '{query}', please wait a bit...",
        "song_too_large": "The file is too large! Telegram only accepts files under 50 MB.",
        "song_download_error": "Error downloading the song: {error}",
        "song_ready": "Your song is ready: {title}",
    }
}

# دکمه‌های انتخاب زبان
def get_language_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("فارسی 🇮🇷", callback_data="lang_fa"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# تابع برای گرفتن زبان کاربر
def get_user_language(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("language", "fa")  # پیش‌فرض فارسی

# تابع برای تنظیم زبان
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]  # lang_fa -> fa, lang_en -> en
    context.user_data["language"] = lang
    lang_messages = MESSAGES[lang]

    await query.edit_message_text(
        text=lang_messages["welcome_after_language"],
        reply_markup=None
    )
    logger.info(f"زبان کاربر {update.effective_user.id} به {lang} تغییر کرد")

# تابع شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"دریافت دستور /start از کاربر: {update.effective_user.id}")
    # اگه زبان قبلاً انتخاب شده، مستقیم به پیام خوش‌آمدگویی برو
    if "language" in context.user_data:
        lang = get_user_language(context)
        await update.message.reply_text(MESSAGES[lang]["welcome_after_language"])
        logger.info(f"پیام خوش‌آمدگویی برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد")
    else:
        # اگه زبان انتخاب نشده، از کاربر بخواه زبانش رو انتخاب کنه
        await update.message.reply_text(
            MESSAGES["fa"]["welcome"],
            reply_markup=get_language_keyboard()
        )
        logger.info(f"درخواست انتخاب زبان برای کاربر {update.effective_user.id} ارسال شد")

# تابع تغییر زبان
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"دریافت دستور /language از کاربر: {update.effective_user.id}")
    lang = get_user_language(context)
    await update.message.reply_text(
        MESSAGES[lang]["language_prompt"],
        reply_markup=get_language_keyboard()
    )
    logger.info(f"درخواست تغییر زبان برای کاربر {update.effective_user.id} ارسال شد")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"دریافت دستور /help از کاربر: {update.effective_user.id}")
    lang = get_user_language(context)
    await update.message.reply_text(MESSAGES[lang]["help"])
    logger.info(f"پیام کمک برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد")

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"دریافت دستور /joke از کاربر: {update.effective_user.id}")
    lang = get_user_language(context)
    await update.message.reply_text(MESSAGES[lang]["joke"])
    logger.info(f"جوک برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد")

async def chat_with_ai(message: str, lang: str) -> str:
    logger.debug(f"ارسال درخواست به API برای پیام: {message}")
    prompt = "سوال کاربر: {message}\nجواب بده مثل یه دوست باهوش و مهربون." if lang == "fa" else "User question: {message}\nAnswer like a smart and kind friend."
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": prompt.format(message=message),
        "parameters": {"max_length": 500, "temperature": 0.7}
    }
    try:
        response = requests.post(HF_TEXT_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("پاسخ از API دریافت شد")
            return response.json()['generated_text'].split("جواب:")[-1].strip() if lang == "fa" else response.json()['generated_text'].split("Answer:")[-1].strip()
        else:
            logger.error(f"خطا در API: {response.status_code}")
            return MESSAGES[lang]["api_error"]
    except Exception as e:
        logger.error(f"خطا در ارتباط با API: {str(e)}")
        return MESSAGES[lang]["api_exception"].format(error=str(e))

async def analyze_image(image_path: str, lang: str) -> str:
    logger.debug(f"تحلیل تصویر: {image_path}")
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    try:
        response = requests.post(HF_IMAGE_URL, headers=headers, data=image_data, timeout=30)
        if response.status_code == 200:
            logger.info("تصویر با موفقیت تحلیل شد")
            return response.json()['generated_text']
        else:
            logger.error(f"خطا در تحلیل تصویر: {response.status_code}")
            return MESSAGES[lang]["image_error"]
    except Exception as e:
        logger.error(f"خطا در تحلیل تصویر: {str(e)}")
        return MESSAGES[lang]["image_exception"].format(error=str(e))

# تابع کمکی برای تبدیل متن به صوت
def text_to_speech(text: str, lang: str) -> str:
    logger.debug(f"تبدیل متن به صوت: {text}")
    tts = gTTS(text=text, lang=lang, slow=False)
    voice_path = "response.mp3"
    tts.save(voice_path)
    logger.info(f"فایل صوتی در مسیر {voice_path} ذخیره شد")
    return voice_path

# تابع برای جواب دادن به متن (با جواب صوتی)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = get_user_language(context)
    logger.debug(f"دریافت پیام متنی از کاربر {update.effective_user.id}: {user_message}")
    await update.message.reply_text(MESSAGES[lang]["thinking"])
    ai_response = await asyncio.to_thread(chat_with_ai, user_message, lang)
    
    # ارسال جواب متنی
    await update.message.reply_text(ai_response)
    logger.info(f"جواب متنی برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد")
    
    # تبدیل جواب به صوت و ارسال
    try:
        voice_path = text_to_speech(ai_response, lang)
        await update.message.reply_voice(voice=open(voice_path, 'rb'))
        logger.info(f"جواب صوتی برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد")
        os.remove(voice_path)
    except Exception as e:
        logger.error(f"خطا در ارسال جواب صوتی: {str(e)}")
        await update.message.reply_text(MESSAGES[lang]["voice_response_error"].format(error=str(e)))

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_language(context)
    logger.debug(f"دریافت ویس از کاربر: {update.effective_user.id}")
    voice_file = await update.message.voice.get_file()
    voice_path = "voice.ogg"
    await voice_file.download_to_drive(voice_path)

    # تبدیل ویس به متن
    await update.message.reply_text(MESSAGES[lang]["voice_listening"])
    try:
        audio = whisper.load_audio(voice_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(whisper_model.device)
        options = whisper.DecodingOptions(language="fa")  # زبان فارسی برای تشخیص
        result = whisper.decode(whisper_model, mel, options)
        text = result.text
        await update.message.reply_text(MESSAGES[lang]["voice_recognized"].format(text=text))
        logger.info(f"ویس کاربر {update.effective_user.id} به متن تبدیل شد: {text}")

        # جواب دادن به متن ویس
        ai_response = await asyncio.to_thread(chat_with_ai, text, lang)
        await update.message.reply_text(ai_response)

        # تبدیل جواب به صوت و ارسال
        try:
            voice_path_response = text_to_speech(ai_response, lang)
            await update.message.reply_voice(voice=open(voice_path_response, 'rb'))
            logger.info(f"جواب صوتی برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد")
            os.remove(voice_path_response)
        except Exception as e:
            logger.error(f"خطا در ارسال جواب صوتی: {str(e)}")
            await update.message.reply_text(MESSAGES[lang]["voice_response_error"].format(error=str(e)))
    except Exception as e:
        logger.error(f"خطا در تشخیص ویس: {str(e)}")
        await update.message.reply_text(MESSAGES[lang]["voice_error"].format(error=str(e)))
    finally:
        if os.path.exists(voice_path):
            os.remove(voice_path)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_language(context)
    logger.debug(f"دریافت عکس از کاربر: {update.effective_user.id}")
    photo_file = await update.message.photo[-1].get_file()
    photo_path = "photo.jpg"
    await photo_file.download_to_drive(photo_path)

    # تحلیل عکس
    await update.message.reply_text(MESSAGES[lang]["image_analyzing"])
    description = await asyncio.to_thread(analyze_image, photo_path, lang)
    await update.message.reply_text(MESSAGES[lang]["image_description"].format(description=description))
    logger.info(f"عکس کاربر {update.effective_user.id} تحلیل شد: {description}")

    # جواب دادن درباره عکس
    ai_response = await asyncio.to_thread(chat_with_ai, f"Describe this: {description}" if lang == "en" else f"درباره این توضیح بده: {description}", lang)
    await update.message.reply_text(ai_response)

    # تبدیل جواب به صوت و ارسال
    try:
        voice_path = text_to_speech(ai_response, lang)
        await update.message.reply_voice(voice=open(voice_path, 'rb'))
        logger.info(f"جواب صوتی برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد")
        os.remove(voice_path)
    except Exception as e:
        logger.error(f"خطا در ارسال جواب صوتی: {str(e)}")
        await update.message.reply_text(MESSAGES[lang]["voice_response_error"].format(error=str(e)))

    if os.path.exists(photo_path):
        os.remove(photo_path)

# تابع برای دانلود ویدیو از اینستاگرام و جاهای دیگه
async def handle_download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = get_user_language(context)
    logger.debug(f"دریافت لینک برای دانلود ویدیو از کاربر {update.effective_user.id}: {user_message}")
    if not ("http" in user_message or "https" in user_message):
        await update.message.reply_text(MESSAGES[lang]["invalid_link"])
        logger.warning(f"لینک نامعتبر از کاربر {update.effective_user.id}")
        return

    await update.message.reply_text(MESSAGES[lang]["downloading_video"])
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloaded_video.%(ext)s',
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(user_message, download=True)
            video_path = "downloaded_video.mp4"
            video_title = info.get('title', 'ویدیو' if lang == "fa" else 'Video')

        if os.path.getsize(video_path) > 50 * 1024 * 1024:
            await update.message.reply_text(MESSAGES[lang]["video_too_large"])
            logger.warning(f"فایل ویدیویی برای کاربر {update.effective_user.id} خیلی بزرگ است")
            os.remove(video_path)
            return

        await update.message.reply_video(video=open(video_path, 'rb'), caption=MESSAGES[lang]["video_ready"].format(title=video_title))
        logger.info(f"ویدیو برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد: {video_title}")
        os.remove(video_path)
    except Exception as e:
        logger.error(f"خطا در دانلود ویدیو: {str(e)}")
        await update.message.reply_text(MESSAGES[lang]["video_download_error"].format(error=str(e)))
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)

# تابع برای جستجو و دانلود آهنگ
async def handle_download_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = get_user_language(context)
    logger.debug(f"دریافت دستور دانلود آهنگ از کاربر {update.effective_user.id}: {user_message}")
    if not user_message.startswith("/song"):
        return

    song_query = user_message.replace("/song", "").strip()
    if not song_query:
        await update.message.reply_text(MESSAGES[lang]["song_query_missing"])
        logger.warning(f"دستور /song بدون ورودی از کاربر {update.effective_user.id}")
        return

    await update.message.reply_text(MESSAGES[lang]["searching_song"].format(query=song_query))
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloaded_song.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch:{song_query} official audio"
            info = ydl.extract_info(search_query, download=True)
            song_path = "downloaded_song.mp3"
            song_title = info['entries'][0].get('title', 'آهنگ' if lang == "fa" else 'Song')

        if os.path.getsize(song_path) > 50 * 1024 * 1024:
            await update.message.reply_text(MESSAGES[lang]["song_too_large"])
            logger.warning(f"فایل آهنگ برای کاربر {update.effective_user.id} خیلی بزرگ است")
            os.remove(song_path)
            return

        await update.message.reply_audio(audio=open(song_path, 'rb'), caption=MESSAGES[lang]["song_ready"].format(title=song_title))
        logger.info(f"آهنگ برای کاربر {update.effective_user.id} به زبان {lang} ارسال شد: {song_title}")
        os.remove(song_path)
    except Exception as e:
        logger.error(f"خطا در دانلود آهنگ: {str(e)}")
        await update.message.reply_text(MESSAGES[lang]["song_download_error"].format(error=str(e)))
        if 'song_path' in locals() and os.path.exists(song_path):
            os.remove(song_path)

def main():
    logger.debug("شروع ساخت Application")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    logger.debug("Application با موفقیت ساخته شد")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", language))
    application.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("joke", joke))
    application.add_handler(CommandHandler("song", handle_download_song))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(r'(http|https)'), handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Regex(r'(http|https)'), handle_download_video))

    logger.info("ربات خفن شروع شد!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()