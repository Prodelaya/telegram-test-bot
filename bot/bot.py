# app/bot.py

import logging
import os
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, CallbackQueryHandler,
    Filters, ConversationHandler, TypeHandler
)
from telegram import Update
from config import (
    BOT_TOKEN, LOGS_DIR,
    MENU_PRINCIPAL, SELECCION_ASIGNATURA, SELECCION_CANTIDAD,
    REALIZANDO_TEST, VER_HISTORIAL
)
from utils import inicializar_base_datos

from message_handler import (
    enviar_mensaje_bienvenida,
    manejar_seleccion_menu_principal,
    manejar_seleccion_asignatura,
    manejar_seleccion_cantidad,
    manejar_respuesta,
    mostrar_historial
)

# Asegurar que existe el directorio de logs
os.makedirs(LOGS_DIR, exist_ok=True)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Cambiar a DEBUG para ver más información
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "bot.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_all_updates(update: Update, context) -> None:
    """Registra todos los updates recibidos para depuración."""
    if update.message:
        logger.debug(f"[DEPURACIÓN] Mensaje recibido: '{update.message.text}' de {update.effective_user.id}")
    elif update.callback_query:
        logger.debug(f"[DEPURACIÓN] Callback recibido: '{update.callback_query.data}' de {update.effective_user.id}")
    else:
        logger.debug(f"[DEPURACIÓN] Update recibido de tipo desconocido: {update}")

def main() -> None:
    """Función principal que inicia el bot."""
    # Inicializar base de datos
    inicializar_base_datos()

    # Crear el Updater y pasarle el token de tu bot
    updater = Updater(BOT_TOKEN)

    # Obtener el Dispatcher para registrar los handlers
    dp = updater.dispatcher
    
    # Añadir handler para registrar todos los updates
    dp.add_handler(TypeHandler(Update, log_all_updates), group=-1)

    # Crear el ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', enviar_mensaje_bienvenida)],
        states={
            MENU_PRINCIPAL: [
                # Manejar callbacks para los botones inline
                CallbackQueryHandler(manejar_seleccion_menu_principal),
                # Mantener soporte para mensajes de texto por compatibilidad
                MessageHandler(Filters.text & ~Filters.command, manejar_seleccion_menu_principal),
            ],
            SELECCION_ASIGNATURA: [
                CallbackQueryHandler(manejar_seleccion_asignatura)
            ],
            SELECCION_CANTIDAD: [
                CallbackQueryHandler(manejar_seleccion_cantidad)
            ],
            REALIZANDO_TEST: [
                CallbackQueryHandler(manejar_respuesta)
            ],
            VER_HISTORIAL: [
                # Específicamente manejar callbacks en el estado VER_HISTORIAL
                CallbackQueryHandler(mostrar_historial)
            ]
        },
        fallbacks=[
            CommandHandler('start', enviar_mensaje_bienvenida),
            MessageHandler(Filters.all, lambda update, context: MENU_PRINCIPAL)  # Fallback para mensajes no esperados
        ],
        allow_reentry=True,
        per_message=False  # Mantenemos esto por ahora, lo cambiaremos después
    )

    # Añadir ConversationHandler al Dispatcher
    dp.add_handler(conv_handler)
    
    # Manejador para comandos desconocidos
    dp.add_handler(MessageHandler(Filters.command, lambda update, context: update.message.reply_text(
        "Comando no reconocido. Usa /start para reiniciar el bot."
    )))

    # Iniciar el bot
    updater.start_polling()
    logger.info("Bot iniciado correctamente. Esperando mensajes...")
    updater.idle()


if __name__ == '__main__':
    main()