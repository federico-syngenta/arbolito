import os
import logging
import pandas as pd
import io
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()
bot_token = os.environ.get("TOKEN_TELEGRAM_ARBOLITO")

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
CHOOSING = 0


# Handle the /start command
async def start(update: Update, context):
    await update.message.reply_text(
        "Bienvenido al bot de cotizaciones de bancos. "
        "Por favor, elija un banco (BNA, PROVINCIA, CIUDAD, BBVA) o escriba 'TODOS' para obtener todas las cotizaciones, seguido de la fecha en formato 'yyyy-mm-dd'. Por ejemplo, bna 2025-04-25.\n"
    )


from datetime import datetime


async def process_bank(update: Update, context):
    user_input = update.message.text.strip().upper()
    parts = user_input.split()

    csv_path = os.path.join("data", "exchange_rates_v2.csv")
    logging.info(f"Mensaje recibido: {user_input}")

    if not os.path.exists(csv_path):
        await update.message.reply_text(
            "Error: No se encontró el archivo de cotizaciones... Verifique proceso 'run_exchange_rates.py'..."
        )
        return ConversationHandler.END

    df = pd.read_csv(csv_path)
    df["collection_time"] = pd.to_datetime(df["collection_time"])
    df["exchange_date"] = pd.to_datetime(df["exchange_date"]).dt.date

    # --- Analizar input del usuario ---
    bank = None
    fecha = None

    for part in parts:
        if part in ["BNA", "PROVINCIA", "CIUDAD", "BBVA", "TODOS"]:
            bank = part
        else:
            try:
                fecha = datetime.strptime(part, "%Y-%m-%d").date()
            except ValueError:
                pass

    # Si no hay banco y tampoco fecha, mandar bienvenida
    if not bank and not fecha:
        await start(update, context)
        return ConversationHandler.END

    # Aplicar filtros
    if fecha:
        df = df[df["exchange_date"] == fecha]
    if bank and bank != "TODOS":
        df = df[df["source"].str.upper().str.contains(bank)]

    if df.empty:
        await update.message.reply_text(
            "No se encontraron cotizaciones para ese criterio."
        )
        return ConversationHandler.END

    if bank != "TODOS":
        last_row = df.sort_values("collection_time").tail(1).iloc[0]
        banco = last_row["source"]
        compra = last_row["buy_rate"]
        venta = last_row["sell_rate"]
        fecha_str = last_row["exchange_date"]
        hora = last_row["collection_time"].strftime("%H:%M:%S")

        mensaje = (
            f"📅 Cotización del {banco} al {fecha_str} {hora}:\n"
            f"🔸 Compra: ${compra}\n"
            f"🔹 Venta: ${venta}"
        )
    else:
        ultimas = df.sort_values("collection_time").groupby("source").tail(1)
        mensajes = []
        for _, row in ultimas.iterrows():
            banco = row["source"]
            compra = row["buy_rate"]
            venta = row["sell_rate"]
            fecha_str = row["exchange_date"]
            hora = row["collection_time"].strftime("%H:%M:%S")
            mensajes.append(
                f"🏦 {banco} ({fecha_str} {hora})\n"
                f"🔸 Compra: ${compra}\n"
                f"🔹 Venta: ${venta}"
            )
        mensaje = "\n\n".join(mensajes)

    await update.message.reply_text(mensaje)
    return ConversationHandler.END


def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = Application.builder().token(bot_token).build()

    # Add handler for /start command
    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    # Add handler for message processing
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, process_bank)],
        states={},
        fallbacks=[],
    )
    application.add_handler(conv_handler)

    # Set the event loop policy
    nest_asyncio.apply()

    # Start the Bot, don't use asyncio.run
    application.run_polling()


if __name__ == "__main__":
    main()
