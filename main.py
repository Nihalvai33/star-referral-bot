import telebot
from telebot import types
from pymongo import MongoClient

API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

# List of required channel usernames
channels = ['@Star_Bot_02', '@Zealy_02', '@Instanlykop', '@Bachelor_point_Se', '@join_Our_New_Channal']

# Connect to MongoDB
client = MongoClient('YOUR_MONGODB_URI')
db = client['telegram_bot']
users = db['users']

# Add user to database
def add_user(user_id, referrer=None):
    if users.find_one({'user_id': user_id}) is None:
        users.insert_one({
            'user_id': user_id,
            'stars': 0,
            'ref_count': 0,
            'ref_by': referrer,
            'joined_ok': False
        })
        if referrer:
            users.update_one({'user_id': referrer}, {'$inc': {'stars': 2, 'ref_count': 1}})

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    ref = None
    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            pass
    user_id = message.from_user.id
    add_user(user_id, ref)

    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        markup.add(types.InlineKeyboardButton(text=f"Join {ch}", url=f"https://t.me/{ch.strip('@')}"))
    bot.send_message(user_id, "📌 Please join all the channels below, then click ✅ Done.", reply_markup=markup)

# ✅ Button to verify join
@bot.message_handler(func=lambda m: m.text and m.text.strip() == '✅')
def joined(message):
    user_id = message.from_user.id
    missing = []
    for ch in channels:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ['left', 'kicked']:
                missing.append(ch)
        except:
            missing.append(ch)

    if missing:
        bot.send_message(user_id, "❌ You're still missing these channels:\n" + "\n".join(missing))
    else:
        users.update_one({'user_id': user_id}, {'$set': {'joined_ok': True}})
        bot.send_message(
            user_id,
            f"✅ All set! Share your referral link:\n\nhttps://t.me/{bot.get_me().username}?start={user_id}"
        )

# /balance command
@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = message.from_user.id
    u = users.find_one({'user_id': user_id})
    stars = u['stars'] if u else 0
    bot.send_message(user_id, f"⭐ You have {stars} stars.")

# /withdraw command
@bot.message_handler(commands=['withdraw'])
def withdraw(message):
    user_id = message.from_user.id
    u = users.find_one({'user_id': user_id})
    stars = u['stars'] if u else 0
    if stars >= 15:
        bot.send_message(user_id, "🚀 Withdraw request received. Our admin will process it shortly.")
        users.update_one({'user_id': user_id}, {'$inc': {'stars': -15}})
        # Optional: Add log, admin alert, or payment API here
    else:
        bot.send_message(user_id, "❌ You need at least 15 stars to request a withdrawal.")

# Start polling
bot.infinity_polling()
