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
        "Por favor, elija un banco (BNA, PROVINCIA, CIUDAD, BBVA) o escriba 'TODOS' para obtener todas las cotizaciones."
    )


async def process_bank(update: Update, context):
    bank = update.message.text.upper()

    csv_path = os.path.join("data", "exchange_rates_v2.csv")
    logging.info(f"Buscando cotización para el banco: {bank}...")

    if bank == "" or bank == "START":
        await start(update, context)
        return ConversationHandler.END

    if not os.path.exists(csv_path):
        await update.message.reply_text(
            "Error: No se encontró el archivo de cotizaciones... Verifique proceso 'run_exchange_rates.py'..."
        )
        return ConversationHandler.END

    df = pd.read_csv(csv_path)

    if bank != "TODOS":
        df = df[df["source"].str.upper().str.contains(bank)]

        if df.empty:
            await update.message.reply_text(
                f"No se encontraron cotizaciones para {bank}...\n\n"
                "Por favor, elija un banco (BNA, PROVINCIA, CIUDAD, BBVA) o escriba 'TODOS'."
            )
            return ConversationHandler.END

        last_row = df.tail(1).iloc[0]
        banco = last_row["source"]
        compra = last_row["buy_rate"]
        venta = last_row["sell_rate"]
        fecha = last_row["exchange_date"]
        hora = last_row["collection_time"].split()[1]

        mensaje = (
            f"📅 Cotización del {banco} al {fecha} {hora}:\n"
            f"🔸 Compra: ${compra}\n"
            f"🔹 Venta: ${venta}"
        )

    else:
        # Agrupar por banco y tomar la última cotización de cada uno
        df["collection_time"] = pd.to_datetime(df["collection_time"])
        ultimas = df.sort_values("collection_time").groupby("source").tail(1)

        mensajes = []
        for _, row in ultimas.iterrows():
            banco = row["source"]
            compra = row["buy_rate"]
            venta = row["sell_rate"]
            fecha = row["exchange_date"]
            hora = row["collection_time"].strftime("%H:%M:%S")

            mensajes.append(
                f"🏦 {banco} ({fecha} {hora})\n"
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
