# AnonymousX888
# Note if you are trying to deploy on vps then directly fill values in ("")

from os import getenv
from dotenv import load_dotenv
load_dotenv(".env")

API_ID = int(getenv("API_ID", "26544005"))
API_HASH = getenv("API_HASH", "66f6221e5ce9109827b50eaf3d105025")
BOT_TOKEN = getenv("BOT_TOKEN", "7564999456:AAGGcrLBHHxrI6Mcmc2Rh_620zKfFuCU0Zg")
OWNER_ID = int(getenv("OWNER_ID", "5870285414"))
MONGODB_CONNECTION_STRING = getenv("MONGO_DB", "mongodb+srv://naura:ahahahahaha@naura.al4xuyo.mongodb.net/?retryWrites=true&w=majority&appName=naura")
LOG_GROUP = int(getenv("LOG_GROUP", "-1002554488354"))
FORCESUB = getenv("FORCESUB", "-1002818541265")
