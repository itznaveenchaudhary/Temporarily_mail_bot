import os
import telebot
import requests

BOT_TOKEN = os.getenv("TOKEN")  # ← Environment variable se token le

if not BOT_TOKEN:
    raise ValueError("Token not found! Check Render environment variable.")

bot = telebot.TeleBot(BOT_TOKEN)

bot.remove_webhook()
# Store user emails in memory
user_emails = {}

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "📬 *Welcome to TempMail Bot!* 🔥\n\n"
        "🛠️ Instantly generate temporary email addresses\n"
        "📥 Receive OTPs, login codes, and messages in real-time\n"
        "♻️ Auto-refresh inbox every few seconds\n"
        "⏳ *Note: Each email stays active for 60 minutes only!*\n\n"
        "🔐 100% Safe, Secure & Fast\n"
        "✨ Created with ❤️ by [@Itz_naveen_chaudhary](https://t.me/Itz_naveen_chaudhary)\n\n"
        "🚀 Use wisely — emails auto-delete after expiry."
    )
    bot.send_message(
    message.chat.id,
    welcome_text,
    parse_mode="Markdown",
    reply_markup=main_menu()
)

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📧 Generate Email", "🔁 Refresh Inbox")
    markup.row("🗑️ Delete Mail")
    return markup

@bot.message_handler(func=lambda message: message.text == "📧 Generate Email")
def generate_email(message):
    response = requests.get("https://api.mail.tm/domains")
    if response.status_code != 200:
        bot.send_message(message.chat.id, "❌ Failed to connect to temp mail server.")
        return

    domain = response.json()["hydra:member"][0]["domain"]
    username = f"user{message.from_user.id}"
    email = f"{username}@{domain}"
    password = "123456"

    # Register the account
    register = requests.post("https://api.mail.tm/accounts", json={
        "address": email,
        "password": password
    })

    if register.status_code == 422:  # Already exists
        token_req = requests.post("https://api.mail.tm/token", json={
            "address": email,
            "password": password
        })
    else:
        token_req = requests.post("https://api.mail.tm/token", json={
            "address": email,
            "password": password
        })

    if token_req.status_code != 200:
        bot.send_message(message.chat.id, "❌ Failed to generate email. Try again.")
        return

    token = token_req.json()["token"]
    user_emails[message.chat.id] = {
        "email": email,
        "password": password,
        "token": token
    }

    bot.send_message(message.chat.id, f"✅ Your Temp Email:\n`{email}`\n\n⏱️ Valid for 60 minutes.\n\nUse 🔁 *Refresh Inbox* to see incoming mails.", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔁 Refresh Inbox")
def refresh_inbox(message):
    user_data = user_emails.get(message.chat.id)
    if not user_data:
        bot.send_message(message.chat.id, "⚠️ First generate a temp email using 📧 button.")
        return

    headers = {"Authorization": f"Bearer {user_data['token']}"}
    inbox = requests.get("https://api.mail.tm/messages", headers=headers)

    if inbox.status_code != 200:
        bot.send_message(message.chat.id, "⚠️ Error reading inbox.")
        return

    messages = inbox.json()["hydra:member"]
    if not messages:
        bot.send_message(message.chat.id, "📭 Inbox is empty.")
        return

    for mail in messages:
        msg = f"📨 *From:* {mail['from']['address']}\n*Subject:* {mail['subject']}\n\n{mail['intro']}"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🗑️ Delete Mail")
def delete_mail(message):
    if message.chat.id in user_emails:
        del user_emails[message.chat.id]
        bot.send_message(message.chat.id, "🗑️ Temp email deleted successfully.")
    else:
        bot.send_message(message.chat.id, "⚠️ You haven't generated any email yet.")

# Start polling
bot.infinity_polling()
