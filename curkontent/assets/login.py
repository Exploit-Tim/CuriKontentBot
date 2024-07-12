import pymongo
import os
from .. import bot as gagan
from .. import Bot as app
from pyrogram import Client, filters
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
import asyncio
from config import API_ID as api_id, API_HASH as api_hash, MONGODB_CONNECTION_STRING, LOG_GROUP 

DB_NAME = "logins"
COLLECTION_NAME = "stringsession"

mongo_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

user_steps = {}
user_data = {}


def delete_session_files(user_id):
    session_file = f"session_{user_id}.session"
    if os.path.exists(session_file):
        os.remove(session_file)
    memory_file = f"session_{user_id}.session-journal"
    if os.path.exists(memory_file):
        os.remove(memory_file)

@app.on_message(filters.command("cleardb"))
async def clear_db(client, message):
    user_id = message.chat.id
    delete_session_files(user_id)
    await message.reply("✅ Data dan file sesi Anda telah dihapus dari memori dan disk.")

async def process_step(client, message):
    user_id = message.chat.id
    step = user_steps.get(user_id, None)

    if step == "phone_number":
        user_data[user_id] = {"phone_number": message.text}
        user_steps[user_id] = "otp"
        omsg = await message.reply("Sending OTP...")
        temp_client = Client(f"session_{user_id}", api_id, api_hash)
        user_data[user_id]["client"] = temp_client
        await temp_client.connect()
        try:
            code = await temp_client.send_code(user_data[user_id]["phone_number"])
            user_data[user_id]["phone_code_hash"] = code.phone_code_hash
            await omsg.delete()
            await message.reply("OTP telah terkirim. Silakan masukkan OTP dengan format: '1 2 3 4 5'.")
        except ApiIdInvalid:
            await message.reply('❌ Kombinasi ID API dan HASH API tidak valid. Silakan mulai ulang sesinya.')
            reset_user(user_id)
        except PhoneNumberInvalid:
            await message.reply('❌ Nomor telepon tidak valid. Silakan mulai ulang sesinya.')
            reset_user(user_id)
    elif step == "otp":
        phone_code = message.text.replace(" ", "")
        temp_client = user_data[user_id]["client"]
        try:
            await temp_client.sign_in(user_data[user_id]["phone_number"], user_data[user_id]["phone_code_hash"], phone_code)
            session_string = await temp_client.export_session_string()
            session_data = {
                "user_id": user_id,
                "session_string": session_string
            }
            collection.update_one(
                {"user_id": user_id},
                {"$set": session_data},
                upsert=True
            )
            await message.reply(f"✅ Login successful!")
            await temp_client.disconnect()
            reset_user(user_id)
        except PhoneCodeInvalid:
            await message.reply('❌ OTP tidak valid. Silakan mulai ulang sesinya.')
            reset_user(user_id)
        except PhoneCodeExpired:
            await message.reply('❌ OTP sudah habis masa berlakunya. Silakan mulai ulang sesinya.')
            reset_user(user_id)
        except SessionPasswordNeeded:
            user_steps[user_id] = "password"
            await message.reply('Akun Anda mengaktifkan verifikasi dua langkah. Silakan masukkan kata sandi Anda.')
    elif step == "password":
        temp_client = user_data[user_id]["client"]
        try:
            password = message.text
            await temp_client.check_password(password=password)
            session_string = await temp_client.export_session_string()
            session_data = {
                "user_id": user_id,
                "session_string": session_string
            }
            collection.update_one(
                {"user_id": user_id},
                {"$set": session_data},
                upsert=True
            )
            await message.reply(f"✅ Login successful!")
            await temp_client.disconnect()
            reset_user(user_id)
        except PasswordHashInvalid:
            await message.reply('❌ Kata sandi salah. Silakan mulai ulang sesinya.')
            reset_user(user_id)
    else:
        await message.reply('Silakan masukkan nomor telepon Anda beserta kode negara. \n\nContoh: +19876543210')
        user_steps[user_id] = "phone_number"

def reset_user(user_id):
    user_steps.pop(user_id, None)
    user_data.pop(user_id, None)

@app.on_message(filters.command("login"))
async def login_command(client, message):
    await process_step(client, message)

@app.on_message(filters.text & filters.private)
async def handle_steps(client, message):
    user_id = message.chat.id
    if user_id in user_steps:
        await process_step(client, message)

def get_session(sender_id):
    user_data = collection.find_one({"user_id": sender_id})
    if user_data:
        return user_data.get("session_string")
    else:
        return None
