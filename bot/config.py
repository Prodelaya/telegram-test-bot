# app/config.py

import os
from pathlib import Path
import os
from dotenv import load_dotenv


# Configuración del bot
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN no está configurado en el archivo .env")

# Rutas de archivos
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
PREGUNTAS_JSON = os.path.join(DATA_DIR, "preguntas.json")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "resultados.db")

# Configuración de los tests
PREGUNTAS_POR_TEST_DEFAULT = 10  # Número de preguntas por defecto en cada test
MAX_PREGUNTAS_POR_TEST = 70  # Límite máximo de preguntas que un usuario puede seleccionar
OPCIONES_CANTIDAD_PREGUNTAS = [10, 20, 30, 40, 50, 60, 70]  # Opciones para seleccionar cantidad de preguntas

# Mensajes del bot
MENSAJE_BIENVENIDA = """
¡Bienvenido al Bot de Tests Educativos! 📚✨

Este bot te permite realizar tests de distintas asignaturas para evaluar tus conocimientos.
Están incluidos los Test Finales de Jobie y los Simulacros de Examen de Elam (Gracias profe!).
Espero que os sirva para aprobar a todos. Pablo Laya os desea suerte!

¿Cómo funciona?
- Selecciona el tipo de test que quieres realizar
- Elige la cantidad de preguntas
- Responde a las preguntas seleccionando una opción
- Recibe feedback inmediato sobre tus respuestas
- Consulta tu historial de resultados

¡Comencemos! Usa el comando /start para iniciar.
"""

# Emojis para feedback
EMOJI_CORRECTO = "✅"
EMOJI_INCORRECTO = "❌"
EMOJI_PREGUNTA = "❓"
EMOJI_EXPLICACION = "📝"
EMOJI_SIGUIENTE = "➡️"
EMOJI_HISTORIAL = "📊"
EMOJI_TEST = "📝"
EMOJI_MENU = "🏠"

# Estados de la conversación (para ConversationHandler)
MENU_PRINCIPAL, SELECCION_ASIGNATURA, SELECCION_CANTIDAD, REALIZANDO_TEST, VER_EXPLICACION, VER_HISTORIAL = range(6)

# Opciones del menú principal
OPCION_TEST_ASIGNATURA = "Test por asignatura 📚"
OPCION_TEST_GLOBAL = "Test global 🌍"
OPCION_HISTORIAL = "Mi historial 📊"
OPCION_AYUDA = "Ayuda ❓"

# Nombres de las asignaturas
ASIGNATURAS = {
    "BDD": "Bases de Datos",
    "EDD": "Entornos de Desarrollo",
    "LDMYSDGDLI": "Lenguaje de Marcas y Sistema de Gestión de la Información",
    "P": "Programación"
}

# Configuración de la base de datos
TABLA_RESULTADOS = """
CREATE TABLE IF NOT EXISTS resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    user_name TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_test TEXT NOT NULL,
    asignatura TEXT,
    correctas INTEGER NOT NULL,
    total INTEGER NOT NULL,
    porcentaje REAL NOT NULL
)
"""

TABLA_USUARIOS = """
CREATE TABLE IF NOT EXISTS usuarios (
    user_id INTEGER PRIMARY KEY,
    nombre TEXT,
    apellido TEXT,
    nombre_usuario TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""