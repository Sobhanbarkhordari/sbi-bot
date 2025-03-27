import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import asyncio
import whisper
from PIL import Image
import io
import os

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)  # اصلاح شده: name به __name_

# توکن‌ها
TELEGRAM_TOKEN = '7779706057:AAFh_88PzgML5rUZ0JfcB-SfcIvzAmUBUng'
HF_API_TOKEN = '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'
HF_TEXT_URL = "https://api-inference.huggingface.co/models/mixtral-8x7b-instruct-v0.1"
HF_IMAGE_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"

# مدل Whisper برای تشخیص ویس
whisper_model = whisper.load_model("base")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام سبحان! من ربات خفنتم! می‌تونم:\n'
                                    '- ویس فارسی بفهمم\n'
                                    '- عکس تحلیل کنم\n'
                                    '- درباره هر چی بخوای حرف بزنم\n'
                                    'بگو /help برای کمک!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('اینا کاراییه که می‌تونم بکنم:\n'
                                    '/start - شروع چت\n'
                                    '/help - این پیام\n'
                                    '/joke - یه جوک بگم\n'
                                    '- ویس بفرست، به فارسی می‌فهمم\n'
                                    '- عکس بفرست، توضیح می‌دم\n'
                                    '- هر سؤالی بپرس، جواب می‌دم!')

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('چرا برنامه‌نویسا تاریکی رو دوست دارن؟ چون نور کدشون رو خراب می‌کنه! 😄')

async def chat_with_ai(message: str) -> str:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {
        "inputs": f"سوال کاربر: {message}\nجواب بده مثل یه دوست باهوش و مهربون.",
        "parameters": {"max_length": 500, "temperature": 0.7}
    }
    try:
        response = requests.post(HF_TEXT_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['generated_text'].split("جواب:")[-1].strip()
        else:
            return "یه مشکلی تو API پیش اومد، یه کم صبر کن!"
    except Exception as e:
        return f"خطا: {str(e)}. بعداً امتحان کن!"

async def analyze_image(image_path: str) -> str:
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    try:
        response = requests.post(HF_IMAGE_URL, headers=headers, data=image_data, timeout=30)
        if response.status_code == 200:
            return response.json()['generated_text']
        else:
            return "نمی‌تونم عکس رو تحلیل کنم، یه کم صبر کن!"
    except Exception as e:
        return f"خطا تو تحلیل عکس: {str(e)}"

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.reply_text("یه لحظه صبر کن، دارم فکر می‌کنم...")
    ai_response = await asyncio.to_thread(chat_with_ai, user_message)
    await update.message.reply_text(ai_response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice_file = await update.message.voice.get_file()
    voice_path = "voice.ogg"
    await voice_file.download_to_drive(voice_path)

    # تبدیل ویس به متن
    await update.message.reply_text("دارم به ویست گوش می‌دم...")
    try:
        audio = whisper.load_audio(voice_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(whisper_model.device)
        options = whisper.DecodingOptions(language="fa")  # زبان فارسی
        result = whisper.decode(whisper_model, mel, options)
        text = result.text
        await update.message.reply_text(f"شنیدم که گفتی: {text}")

        # جواب دادن به متن ویس
        ai_response = await asyncio.to_thread(chat_with_ai, text)
        await update.message.reply_text(ai_response)
    except Exception as e:
        await update.message.reply_text(f"خطا تو تشخیص ویس: {str(e)}")
    finally:
        if os.path.exists(voice_path):
            os.remove(voice_path)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_path = "photo.jpg"
    await photo_file.download_to_drive(photo_path)

    # تحلیل عکس
    await update.message.reply_text("دارم عکس رو نگاه می‌کنم...")
    description = await asyncio.to_thread(analyze_image, photo_path)
    await update.message.reply_text(f"تو عکس دیدم: {description}")

    # اگه بخوای درباره عکس بیشتر حرف بزنه
    ai_response = await asyncio.to_thread(chat_with_ai, f"درباره این توضیح بده: {description}")
    await update.message.reply_text(ai_response)

    if os.path.exists(photo_path):
        os.remove(photo_path)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("joke", joke))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("ربات خفن شروع شد!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()