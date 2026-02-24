import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

conn = sqlite3.connect("budget.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    name TEXT PRIMARY KEY,
    type TEXT,
    balance REAL,
    debt REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT,
    amount REAL,
    category TEXT
)
""")

conn.commit()

# Başlangıç hesapları (ilk çalışmada eklenir)
def init_accounts():
    accounts = [
        ("gb", "credit_card", 0, 0),
        ("gfb", "credit_card", 0, 0),
        ("iskk", "credit_card", 0, 0),
        ("akkk", "credit_card", 0, 0),
        ("enkk", "credit_card", 0, 0),
        ("gar", "bank", 0, 0),
        ("isb", "bank", 0, 0),
        ("akb", "bank", 0, 0),
        ("enp", "bank", 0, 0)
    ]
    for acc in accounts:
        cursor.execute("INSERT OR IGNORE INTO accounts VALUES (?, ?, ?, ?)", acc)
    conn.commit()

init_accounts()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().split()

    if len(text) < 2:
        await update.message.reply_text("Format: gb 300 market")
        return

    account = text[0]
    amount = float(text[1])
    category = text[2] if len(text) > 2 else "other"

    cursor.execute("SELECT type, balance, debt FROM accounts WHERE name=?", (account,))
    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("Hesap bulunamadı.")
        return

    acc_type, balance, debt = row

    if acc_type == "credit_card":
        debt += amount
        cursor.execute("UPDATE accounts SET debt=? WHERE name=?", (debt, account))
        message = f"{account} yeni borç: {debt:.2f}"
    else:
        balance -= amount
        cursor.execute("UPDATE accounts SET balance=? WHERE name=?", (balance, account))
        message = f"{account} yeni bakiye: {balance:.2f}"

    cursor.execute("INSERT INTO transactions (account, amount, category) VALUES (?, ?, ?)",
                   (account, amount, category))

    conn.commit()

    await update.message.reply_text(message)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
