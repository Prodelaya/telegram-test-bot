
# 📚 Bot de Telegram para practicar tests de FP (DAM/DAW)

Este bot permite practicar preguntas tipo test desde Telegram, ideal para preparar exámenes de ciclos formativos como DAM/DAW. Carga preguntas desde archivos JSON estructurados y registra estadísticas de aciertos y errores.

---

## ✅ Estado del proyecto

💡 **Bot en activo**, alojado en un servidor propio con Ubuntu Server 24/7.  
📱 Usado diariamente por el autor y sus compañeros de clase para preparar los exámenes del primer curso de DAM/DAW.

---

## 👨‍🎓 Sobre el autor

Este proyecto ha sido realizado por **Pablo Laya**, estudiante de 1º de DAM/DAW en Madrid.  
Ha sido desarrollado como parte de su aprendizaje personal, con el objetivo de:

- Entender cómo funciona un bot de Telegram desde cero.
- Aprender sobre estructuras de datos, bases de datos y automatización de procesos.
- Aplicar Python en un proyecto real y útil.

🔍 Se ha contado con el apoyo de herramientas de Inteligencia Artificial como ChatGPT y Claude, para aprender del proceso, resolver dudas, comprender cada parte del código y mejorar el proyecto paso a paso.

---

## 🚀 Características

- Compatible con múltiples asignaturas.
- Estadísticas por usuario.
- Explicaciones y referencias por cada pregunta.
- Integración con SQLite para registrar resultados.
- Extrae preguntas automáticamente desde `.docx` si tienen el formato adecuado.

---

## 🛠️ Instalación y configuración

### 1. Clona este repositorio

```bash
git clone https://github.com/tu-usuario/telegram_test_bot.git
cd telegram_test_bot
```

### 2. Instala dependencias

Asegúrate de tener Python 3 instalado y ejecuta:

```bash
pip install -r requirements.txt
```

### 3. Configura el archivo `.env`

El bot necesita un token de API de Telegram para funcionar.  
Debes crear un archivo `.env` en la raíz del proyecto con esta estructura:

```
TELEGRAM_TOKEN=tu_token_aquí
```

> Puedes conseguir tu token hablando con [@BotFather](https://t.me/BotFather) en Telegram.

También puedes encontrar un ejemplo de este archivo en `env_example.txt`.

---

## 📦 Estructura de las preguntas (JSON)

```json
{
  "enunciado": "¿Qué significa JVM?",
  "opciones": {
    "a": "Java Virtual Machine",
    "b": "Java Variable Method",
    "c": "Java Version Manager"
  },
  "respuesta_correcta": "a",
  "explicacion": "La JVM es el motor que ejecuta el código bytecode de Java.",
  "referencia": "UT3, pág. 21",
  "origen": "Test Jobie",
  "asignatura": "Entornos de Desarrollo"
}
```

---

## ✍️ ¿Cómo cargar nuevas preguntas?

Puedes:
- Crear los archivos `.json` a mano (ver ejemplo en `data/preguntas.json`).
- O usar el extractor incluido en la carpeta `/extractor/` para generar automáticamente el JSON desde archivos `.docx`.

### ⚙️ Usar el extractor

1. Coloca tus archivos `.docx` en la carpeta `docs/docx/` (debe existir en la raíz del proyecto).
2. Ejecuta el extractor:

```bash
python extractor/extractor.py
```

3. Se generará un archivo `preguntas.json` compatible, que puedes usar con el bot.

> ⚠️ **Importante**: los `.docx` deben seguir un formato específico para que el extractor funcione correctamente (ver ejemplo en `dcos/docx/Bases de Datos_Simulacro Elam.docx`).

---

## 📡 ¿Cómo ejecutar el bot?

Una vez configurado todo, puedes lanzar el bot con:

```bash
python bot/bot.py
```

Si todo está correcto, el bot se conectará a Telegram y responderá a los comandos en el chat.

---

## 🧪 Vista previa del bot

### Pantalla de bienvenida
![Bot Telegram - Inicio](images/main_menu.png)

### Selección de asignatura
![Bot Telegram - Asignaturas](images/subject_options.png)

### Ejemplo de pregunta
![Bot Telegram - Pregunta](images/question_example.png)

### Feedback al responder
![Bot Telegram - Feedback](images/mistake_correction.png)

### Estadísticas de usuario
![Bot Telegram - Estadísticas](images/tests_statistics.png)

---

## 🗃️ Base de datos de ejemplo

El proyecto incluye una base de datos `resultados.db` con datos ficticios para poder ver cómo funciona el registro de estadísticas sin necesidad de usarlo con usuarios reales.

---

## 🤖 Tecnologías utilizadas

- Python 3
- python-telegram-bot
- SQLite
- python-docx
- dotenv

---

## 👨‍💻 Autor

**Pablo Laya** — estudiante de 1º de DAM/DAW en Madrid  
🖥️ Apasionado por la automatización, los bots de telegram y el aprendizaje continuo.
