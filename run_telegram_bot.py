import os
import logging
import importlib.util
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


async def start(update: Update, context):
    await update.message.reply_text(
        "Bienvenido al bot de cotizaciones de bancos. "
        "Por favor, elija un banco (BNA, PROVINCIA, CIUDAD, BBVA) o escriba 'TODOS' para obtener todas las cotizaciones."
    )
    return CHOOSING


async def process_bank(update: Update, context):
    bank = update.message.text.upper()

    # Path al archivo CSV
    csv_path = os.path.join("data", "exchange_rates_v2.csv")

    logging.info(f"Buscando cotización para el banco: {bank}...")

    # Verificar si el archivo existe
    if not os.path.exists(csv_path):
        await update.message.reply_text(
            f"Error: No se encontró el archivo de cotizaciones... Verifique proceso 'run_exchange_rates.py'..."
        )
        return ConversationHandler.END

    # Leer el archivo CSV
    df = pd.read_csv(csv_path)

    # Filtrar las filas por banco seleccionado
    if bank != "TODOS":
        df = df[df["source"].str.upper() == bank]

    if df.empty:
        await update.message.reply_text(
            f"No se encontraron cotizaciones para {bank}..."
        )
        return ConversationHandler.END

    # Convertir el DataFrame a CSV en formato de texto
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    # Enviar el archivo CSV al usuario
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=io.BytesIO(csv_buffer.getvalue().encode()),
        filename="exchange_rates.csv",
        caption=f"Aquí están las cotizaciones para {bank}.",
    )

    return ConversationHandler.END


def main():
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    application = Application.builder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bank)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    # Set the event loop policy
    nest_asyncio.apply()

    # Start the Bot
    asyncio.run(application.run_polling())


if __name__ == "__main__":
    main()
