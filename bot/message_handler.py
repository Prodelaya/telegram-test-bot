
import logging
from typing import Dict, List, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from telegram.error import BadRequest  # Importación específica del error

from config import (
    EMOJI_CORRECTO, EMOJI_INCORRECTO, EMOJI_PREGUNTA, EMOJI_EXPLICACION,
    EMOJI_SIGUIENTE, EMOJI_HISTORIAL, EMOJI_TEST, EMOJI_MENU,
    OPCION_TEST_ASIGNATURA, OPCION_TEST_GLOBAL, OPCION_HISTORIAL, OPCION_AYUDA,
    MENSAJE_BIENVENIDA, ASIGNATURAS, OPCIONES_CANTIDAD_PREGUNTAS,
    MENU_PRINCIPAL, SELECCION_ASIGNATURA, SELECCION_CANTIDAD, REALIZANDO_TEST, VER_HISTORIAL
)
from utils import (
    cargar_preguntas, filtrar_preguntas_por_asignatura, seleccionar_preguntas_aleatorias,
    obtener_todas_asignaturas, guardar_resultado_test,
    obtener_historial_usuario, obtener_estadisticas_usuario, registrar_usuario,
    contar_preguntas_por_asignatura
)
from test_handler import (
    inicializar_test, obtener_pregunta_actual, verificar_respuesta as verificar_respuesta_test,
    avanzar_pregunta, test_completado, calcular_resultados
)

logger = logging.getLogger(__name__)


def enviar_mensaje_bienvenida(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    registrar_usuario(
        user_id=user.id,
        nombre=user.first_name,
        apellido=user.last_name,
        nombre_usuario=user.username
    )
    teclado = crear_teclado_menu_principal()
    update.message.reply_text(
        MENSAJE_BIENVENIDA,
        reply_markup=teclado,
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Usuario {user.id} iniciando bot. Estado: MENU_PRINCIPAL")
    return MENU_PRINCIPAL


# Cambiado a InlineKeyboardMarkup para mejor control y depuración
def crear_teclado_menu_principal() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(OPCION_TEST_ASIGNATURA, callback_data="menu_asignatura")],
        [InlineKeyboardButton(OPCION_TEST_GLOBAL, callback_data="menu_global")],
        [InlineKeyboardButton(OPCION_HISTORIAL, callback_data="menu_historial")],
        [InlineKeyboardButton(OPCION_AYUDA, callback_data="menu_ayuda")]
    ]
    return InlineKeyboardMarkup(keyboard)


def crear_teclado_asignaturas(asignaturas: Dict[str, str], conteo: Dict[str, int]) -> InlineKeyboardMarkup:
    keyboard = []
    for codigo, nombre in asignaturas.items():
        nombre_truncado = nombre if len(nombre) < 30 else nombre[:27] + "..."
        num_preguntas = conteo.get(codigo, 0)
        texto_boton = f"{nombre_truncado} ({num_preguntas} preguntas)"
        keyboard.append([InlineKeyboardButton(texto_boton, callback_data=f"asig_{codigo}")])
    keyboard.append([InlineKeyboardButton(f"{EMOJI_MENU} Volver al menú", callback_data="volver_menu")])
    return InlineKeyboardMarkup(keyboard)


def enviar_seleccion_cantidad_preguntas(update: Update, context: CallbackContext, tipo_test: str) -> None:
    context.user_data['tipo_test'] = tipo_test
    conteo = contar_preguntas_por_asignatura()
    max_preguntas = conteo.get(tipo_test, 0)

    keyboard = []
    for cantidad in OPCIONES_CANTIDAD_PREGUNTAS:
        if cantidad <= max_preguntas:
            keyboard.append([InlineKeyboardButton(
                f"{cantidad} preguntas",
                callback_data=f"cant_{cantidad}"
            )])

    if tipo_test == "global":
        keyboard.append([InlineKeyboardButton(f"{EMOJI_MENU} Volver al menú", callback_data="volver_menu")])
    else:
        keyboard.append([InlineKeyboardButton("⬅️ Volver a asignaturas", callback_data="volver_asignaturas")])

    mensaje = "¿Cuántas preguntas quieres en tu test?"
    if tipo_test != "global":
        asignatura = ASIGNATURAS.get(tipo_test, tipo_test)
        mensaje = f"Has seleccionado: *{asignatura}*\n\nDisponibles: {max_preguntas} preguntas\n\n{mensaje}"
    else:
        mensaje = f"*Test global*\n\nDisponibles: {max_preguntas} preguntas\n\n{mensaje}"

    if update.callback_query:
        update.callback_query.edit_message_text(
            text=mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.message.reply_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )


def manejar_seleccion_menu_principal(update: Update, context: CallbackContext) -> int:
    logger.info("Entrando a manejar_seleccion_menu_principal")
    
    # Detectar si viene de mensaje normal o de callback query
    if update.message:
        seleccion = update.message.text
        logger.info(f"Selección del menú (mensaje): {seleccion}")
    elif update.callback_query:
        query = update.callback_query
        query.answer()
        seleccion = query.data
        logger.info(f"Selección del menú (callback): {seleccion}")
    else:
        logger.warning("Tipo de update no reconocido")
        return MENU_PRINCIPAL

    # Para el nuevo enfoque de InlineKeyboardMarkup
    if seleccion == "menu_asignatura" or seleccion == OPCION_TEST_ASIGNATURA:
        logger.info("Opción seleccionada: Test por asignatura")
        preguntas = cargar_preguntas()
        asignaturas = obtener_todas_asignaturas(preguntas)
        conteo = contar_preguntas_por_asignatura()

        if update.message:
            update.message.reply_text(
                "Selecciona la asignatura para el test:",
                reply_markup=crear_teclado_asignaturas(asignaturas, conteo)
            )
        else:
            update.callback_query.edit_message_text(
                "Selecciona la asignatura para el test:",
                reply_markup=crear_teclado_asignaturas(asignaturas, conteo)
            )
        return SELECCION_ASIGNATURA

    elif seleccion == "menu_global" or seleccion == OPCION_TEST_GLOBAL:
        logger.info("Opción seleccionada: Test global")
        enviar_seleccion_cantidad_preguntas(update, context, "global")
        return SELECCION_CANTIDAD

    elif seleccion == "menu_historial" or seleccion == OPCION_HISTORIAL:
        logger.info("Opción seleccionada: Historial")
        mostrar_historial(update, context)
        return VER_HISTORIAL

    elif seleccion == "menu_ayuda" or seleccion == OPCION_AYUDA:
        logger.info("Opción seleccionada: Ayuda")
        mensaje_ayuda = (
            "Este bot te permite realizar tests educativos de diferentes asignaturas.\n\n"
            "Puedes elegir entre realizar un test de una asignatura específica o "
            "un test global con preguntas de todas las asignaturas.\n\n"
            "También puedes consultar tu historial de tests realizados y tus estadísticas.\n\n"
            "Para comenzar, selecciona una opción del menú."
        )
        
        if update.message:
            update.message.reply_text(
                mensaje_ayuda,
                reply_markup=crear_teclado_menu_principal()
            )
        else:
            update.callback_query.edit_message_text(
                mensaje_ayuda,
                reply_markup=crear_teclado_menu_principal()
            )
        return MENU_PRINCIPAL
    
    elif seleccion == "volver_menu":
        logger.info("Opción seleccionada: Volver al menú")
        if update.callback_query:
            try:
                update.callback_query.edit_message_text(
                    "Selecciona una opción del menú:",
                    reply_markup=crear_teclado_menu_principal()
                )
            except BadRequest as e:
                # Si el mensaje es idéntico, enviamos uno nuevo
                if "Message is not modified" in str(e):
                    logger.info("Mensaje no modificado, enviando uno nuevo")
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Selecciona una opción del menú:",
                        reply_markup=crear_teclado_menu_principal()
                    )
        return MENU_PRINCIPAL
    else:
        # Opción desconocida
        logger.warning(f"Opción desconocida: {seleccion}")
        if update.message:
            update.message.reply_text(
                "Opción no reconocida. Por favor, selecciona una opción del menú.",
                reply_markup=crear_teclado_menu_principal()
            )
        return MENU_PRINCIPAL

def manejar_seleccion_asignatura(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    callback_data = query.data
    logger.info(f"Recibida selección de asignatura: {callback_data}")

    if callback_data == "volver_menu":
        query.edit_message_text(
            "Selecciona una opción:",
            reply_markup=crear_teclado_menu_principal()
        )
        return MENU_PRINCIPAL

    if callback_data.startswith("asig_"):
        codigo_asignatura = callback_data.split("_")[1]
        enviar_seleccion_cantidad_preguntas(update, context, codigo_asignatura)
        return SELECCION_CANTIDAD

    query.edit_message_text("Opción no válida. Por favor, selecciona nuevamente.")
    return SELECCION_ASIGNATURA


def manejar_seleccion_cantidad(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    callback_data = query.data
    logger.info(f"Recibida selección de cantidad: {callback_data}")

    if callback_data == "volver_menu":
        query.edit_message_text(
            "Selecciona una opción:",
            reply_markup=crear_teclado_menu_principal()
        )
        return MENU_PRINCIPAL

    if callback_data == "volver_asignaturas":
        preguntas = cargar_preguntas()
        asignaturas = obtener_todas_asignaturas(preguntas)
        conteo = contar_preguntas_por_asignatura()

        query.edit_message_text(
            "Selecciona la asignatura para el test:",
            reply_markup=crear_teclado_asignaturas(asignaturas, conteo)
        )
        return SELECCION_ASIGNATURA

    if callback_data.startswith("cant_"):
        cantidad = int(callback_data.split('_')[1])
        tipo_test = context.user_data.get('tipo_test', 'global')
        context.user_data['cantidad_preguntas'] = cantidad

        # Añadir logs para depuración
        logger.info(f"Tipo de test seleccionado: {tipo_test}")
        
        preguntas = cargar_preguntas()
        
        # Añadir logs para depuración
        logger.info(f"Número total de preguntas cargadas: {len(preguntas)}")
        if preguntas:
            logger.info(f"Ejemplo de pregunta cargada: {preguntas[0]}")
            logger.info(f"Campo asignatura: {preguntas[0].get('asignatura')}")
        
        if tipo_test != "global":
            # Añadir logs para depuración
            logger.info(f"Filtrando preguntas por asignatura: {tipo_test}")
            preguntas = filtrar_preguntas_por_asignatura(preguntas, tipo_test)
            logger.info(f"Preguntas filtradas: {len(preguntas)}")
            if preguntas:
                logger.info(f"Ejemplo de pregunta filtrada: {preguntas[0]}")
                logger.info(f"Campo asignatura después de filtrar: {preguntas[0].get('asignatura')}")

        if len(preguntas) < cantidad:
            cantidad = len(preguntas)
            context.user_data['cantidad_preguntas'] = cantidad

        # Añadir logs para depuración
        logger.info(f"Seleccionando {cantidad} preguntas aleatorias")
        preguntas_seleccionadas = seleccionar_preguntas_aleatorias(preguntas, cantidad)
        
        # Añadir logs para depuración
        if preguntas_seleccionadas:
            logger.info(f"Ejemplo de pregunta seleccionada: {preguntas_seleccionadas[0]}")
            logger.info(f"Campo asignatura después de selección: {preguntas_seleccionadas[0].get('asignatura')}")
        
        estado_test = inicializar_test(preguntas_seleccionadas)
        context.user_data['estado_test'] = estado_test
        
        # Añadir logs para depuración
        pregunta_actual = obtener_pregunta_actual(estado_test)
        if pregunta_actual:
            logger.info(f"Primera pregunta del test: {pregunta_actual}")
            logger.info(f"Campo asignatura de primera pregunta: {pregunta_actual.get('asignatura')}")

        enviar_siguiente_pregunta(update, context)
        return REALIZANDO_TEST

    query.edit_message_text("Opción no válida. Por favor, selecciona nuevamente.")
    return SELECCION_CANTIDAD

def enviar_siguiente_pregunta(update: Update, context: CallbackContext) -> None:
    estado_test = context.user_data.get('estado_test')
    if not estado_test:
        if update.callback_query:
            update.callback_query.edit_message_text("No hay un test activo. Usa /start para comenzar.")
        else:
            update.message.reply_text("No hay un test activo. Usa /start para comenzar.")
        return

    if test_completado(estado_test):
        resultados = calcular_resultados(estado_test)
        enviar_resultados_test(update, context, resultados)
        return

    pregunta = obtener_pregunta_actual(estado_test)
    enviar_pregunta(
        update,
        context,
        pregunta,
        estado_test['pregunta_actual'] + 1,
        len(estado_test['preguntas'])
    )


def enviar_pregunta(update: Update, context: CallbackContext, pregunta: Dict[str, Any],
                   num_pregunta: int, total_preguntas: int) -> None:
    logger.info(f"Dentro de enviar_pregunta: {pregunta.get('id')}")
    logger.info(f"Asignatura recibida: {pregunta.get('asignatura')}")
    
    asignatura = pregunta.get("asignatura", "Desconocida")
    logger.info(f"Asignatura después de get: {asignatura}")
    
    origen = pregunta.get("origen", "Desconocido")
    enunciado = pregunta.get("enunciado", "")
    
    # Escapar caracteres especiales en el enunciado
    enunciado = enunciado.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")

    # Construir opciones de texto con escape de caracteres especiales
    opciones_texto = []
    for opcion in pregunta.get("opciones", []):
        texto_opcion = opcion.get('texto', '')
        # Escapar caracteres especiales
        texto_opcion = texto_opcion.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
        opciones_texto.append(f"{opcion.get('letra')}) {texto_opcion}")
    
    # Unir las opciones en un solo texto
    opciones_formateadas = "\n".join(opciones_texto)

    texto_pregunta = (f"{EMOJI_PREGUNTA} Pregunta {num_pregunta}/{total_preguntas}\n"
                      f"Asignatura: {asignatura}\n"
                      f"Origen: {origen}\n\n"
                      f"{enunciado}\n\n"
                      f"{opciones_formateadas}")
    
    logger.info(f"Texto generado para pregunta: {texto_pregunta[:50]}...")

    teclado = [[InlineKeyboardButton(opcion.get('letra'), callback_data=f"resp_{pregunta['id']}_{opcion.get('letra')}")]
               for opcion in pregunta.get("opciones", [])]

    if update.callback_query:
        try:
            update.callback_query.edit_message_text(
                text=texto_pregunta,
                reply_markup=InlineKeyboardMarkup(teclado)
            )
        except Exception as e:
            logger.error(f"Error al editar mensaje: {e}")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=texto_pregunta,
                reply_markup=InlineKeyboardMarkup(teclado)
            )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=texto_pregunta,
            reply_markup=InlineKeyboardMarkup(teclado)
        )


def manejar_respuesta(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    callback_data = query.data
    logger.info(f"Recibida respuesta: {callback_data}")

    if callback_data == "siguiente":
        avanzar_pregunta(context.user_data['estado_test'])
        enviar_siguiente_pregunta(update, context)
        return REALIZANDO_TEST

    if callback_data == "nuevo_test":
        query.edit_message_text(
            "Selecciona una opción:",
            reply_markup=crear_teclado_menu_principal()
        )
        return MENU_PRINCIPAL

    if callback_data == "ver_historial":
        mostrar_historial(update, context)
        return VER_HISTORIAL

    if callback_data.startswith("resp_"):
        partes = callback_data.split("_")
        pregunta_id = "_".join(partes[1:-1])  # Toma todo excepto 'resp' y la letra de respuesta
        respuesta = partes[-1]  # La última parte es la letra de respuesta

        logger.info(f"ID pregunta: {pregunta_id}, Respuesta: {respuesta}")

        estado_test = context.user_data.get('estado_test')
        if not estado_test:
            query.edit_message_text("No hay un test activo. Usa /start para comenzar.")
            return MENU_PRINCIPAL

        pregunta = obtener_pregunta_actual(estado_test)
        if not pregunta:
            query.edit_message_text("Error al obtener la pregunta actual.")
            return MENU_PRINCIPAL

        # Comparar el ID de la pregunta, independientemente del formato
        pregunta_actual_id = str(pregunta.get("id", ""))
        logger.info(f"ID pregunta actual: {pregunta_actual_id}, ID callback: {pregunta_id}")

        if pregunta_actual_id != pregunta_id:
            query.edit_message_text("Error al procesar la respuesta. Por favor, inicia un nuevo test.")
            return MENU_PRINCIPAL

        es_correcta = verificar_respuesta_test(estado_test, respuesta)

        if es_correcta:
            enviar_respuesta_correcta(update, context, pregunta)
        else:
            enviar_respuesta_incorrecta(update, context, pregunta, respuesta)

        return REALIZANDO_TEST

    if callback_data.startswith("expl_"):
        pregunta_id = callback_data.split("_", 1)[1]  # Toma todo después del primer '_'
        preguntas = context.user_data.get('estado_test', {}).get('preguntas', [])
        
        # Buscar la pregunta por ID, con tolerancia a diferentes formatos
        pregunta = None
        for p in preguntas:
            if str(p.get('id', '')) == pregunta_id:
                pregunta = p
                break
        
        if pregunta:
            enviar_explicacion(update, context, pregunta)
        else:
            query.edit_message_text("No se pudo encontrar la explicación para esta pregunta.")

        return REALIZANDO_TEST

    query.edit_message_text("Opción no válida. Por favor, intenta de nuevo.")
    return REALIZANDO_TEST


def enviar_respuesta_correcta(update: Update, context: CallbackContext, pregunta: Dict[str, Any]) -> None:
    teclado = [
        [InlineKeyboardButton(f"{EMOJI_EXPLICACION} Ver explicación", callback_data=f"expl_{pregunta['id']}")],
        [InlineKeyboardButton(f"{EMOJI_SIGUIENTE} Siguiente pregunta", callback_data="siguiente")]
    ]

    context.bot.answer_callback_query(
        callback_query_id=update.callback_query.id,
        text="¡Respuesta correcta!",
        show_alert=True
    )

    # Eliminar formato Markdown del texto original para evitar errores
    texto_original = update.callback_query.message.text
    
    try:
        update.callback_query.edit_message_text(
            text=f"{texto_original}\n\n{EMOJI_CORRECTO} ¡Correcto!",
            reply_markup=InlineKeyboardMarkup(teclado)
        )
    except Exception as e:
        logger.error(f"Error al editar mensaje: {e}")
        # Intento alternativo sin el texto original
        try:
            update.callback_query.edit_message_text(
                text=f"{EMOJI_CORRECTO} ¡Correcto!",
                reply_markup=InlineKeyboardMarkup(teclado)
            )
        except Exception as e2:
            logger.error(f"Error en segundo intento: {e2}")
            # Último recurso: enviar nuevo mensaje
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{EMOJI_CORRECTO} ¡Correcto!",
                reply_markup=InlineKeyboardMarkup(teclado)
            )


def enviar_respuesta_incorrecta(update: Update, context: CallbackContext, pregunta: Dict[str, Any], respuesta_usuario: str) -> None:
    respuesta_correcta = pregunta.get("respuesta_correcta", "")
    texto_respuesta_correcta = next((opcion.get('texto') for opcion in pregunta.get("opciones", []) if opcion.get('letra') == respuesta_correcta), "")

    explicacion = pregunta.get("explicacion", "No hay explicación disponible.")
    referencia = pregunta.get("referencia", "")

    # Escapar caracteres especiales en el texto
    texto_respuesta_correcta = texto_respuesta_correcta.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
    explicacion = explicacion.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
    if referencia:
        referencia = referencia.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")

    texto_feedback = (
        f"{EMOJI_INCORRECTO} ¡Incorrecto!\n\n"
        f"La respuesta correcta es: {respuesta_correcta}\n"
        f"{texto_respuesta_correcta}\n\n"
        f"Explicación:\n{explicacion}\n\n"
    )

    if referencia:
        texto_feedback += f"Referencia: {referencia}\n\n"

    teclado = [[InlineKeyboardButton(f"{EMOJI_SIGUIENTE} Siguiente pregunta", callback_data="siguiente")]]

    context.bot.answer_callback_query(
        callback_query_id=update.callback_query.id,
        text="Respuesta incorrecta",
        show_alert=True
    )

    try:
        update.callback_query.edit_message_text(
            text=texto_feedback,
            reply_markup=InlineKeyboardMarkup(teclado)
        )
    except Exception as e:
        logger.error(f"Error al editar mensaje: {e}")
        # Si falla, intentamos enviar un nuevo mensaje
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=texto_feedback,
            reply_markup=InlineKeyboardMarkup(teclado)
        )


def enviar_explicacion(update: Update, context: CallbackContext, pregunta: Dict[str, Any]) -> None:
    respuesta_correcta = pregunta.get("respuesta_correcta", "")
    texto_respuesta_correcta = next((opcion.get('texto') for opcion in pregunta.get("opciones", []) if opcion.get('letra') == respuesta_correcta), "")

    explicacion = pregunta.get("explicacion", "No hay explicación disponible.")
    referencia = pregunta.get("referencia", "")
    
    # Escapar caracteres especiales en el texto
    enunciado = pregunta.get("enunciado", "").replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
    texto_respuesta_correcta = texto_respuesta_correcta.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
    explicacion = explicacion.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
    if referencia:
        referencia = referencia.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")

    texto_explicacion = (
        f"Explicación de la pregunta:\n\n"
        f"{enunciado}\n\n"
        f"Respuesta correcta: {respuesta_correcta}\n"
        f"{texto_respuesta_correcta}\n\n"
        f"Explicación:\n{explicacion}\n\n"
    )

    if referencia:
        texto_explicacion += f"Referencia: {referencia}\n\n"

    teclado = [[InlineKeyboardButton(f"{EMOJI_SIGUIENTE} Siguiente pregunta", callback_data="siguiente")]]

    try:
        update.callback_query.edit_message_text(
            text=texto_explicacion,
            reply_markup=InlineKeyboardMarkup(teclado)
        )
    except Exception as e:
        logger.error(f"Error al editar mensaje: {e}")
        # Si falla, intentamos enviar un nuevo mensaje
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=texto_explicacion,
            reply_markup=InlineKeyboardMarkup(teclado)
        )

def enviar_resultados_test(update: Update, context: CallbackContext, resultados: Dict[str, Any]) -> None:
    porcentaje = resultados["porcentaje"]
    user = update.effective_user
    tipo_test = context.user_data.get('tipo_test', 'global')

    guardar_resultado_test(
        user_id=user.id,
        user_name=user.username or user.first_name,
        tipo_test=tipo_test,
        correctas=resultados["correctas"],
        total=resultados["total"]
    )

    mensaje = (
        f"*¡Test completado!* 🎉\n\n"
        f"Has respondido correctamente {resultados['correctas']} de {resultados['total']} preguntas.\n"
        f"Porcentaje de acierto: {porcentaje:.1f}%\n\n"
    )

    if porcentaje >= 90:
        mensaje += "¡Excelente trabajo! 🌟 Dominas este tema."
    elif porcentaje >= 70:
        mensaje += "¡Muy buen trabajo! 👏 Tienes un buen conocimiento del tema."
    elif porcentaje >= 50:
        mensaje += "Buen esfuerzo. 👍 Sigue practicando para mejorar."
    else:
        mensaje += "No te desanimes. 💪 Con práctica mejorarás tus resultados."

    teclado = [
        [InlineKeyboardButton(f"{EMOJI_TEST} Realizar otro test", callback_data="nuevo_test")],
        [InlineKeyboardButton(f"{EMOJI_HISTORIAL} Ver mi historial", callback_data="ver_historial")]
    ]

    if update.callback_query:
        update.callback_query.edit_message_text(
            text=mensaje,
            reply_markup=InlineKeyboardMarkup(teclado),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=mensaje,
            reply_markup=InlineKeyboardMarkup(teclado),
            parse_mode=ParseMode.MARKDOWN
        )


def mostrar_historial(update: Update, context: CallbackContext) -> int:
    # Identificar si la llamada proviene de un callback query
    callback_query = update.callback_query
    # Si proviene de un callback específico, verificar si es para volver al menú
    if callback_query and callback_query.data in ["volver_menu", "nuevo_test_desde_historial"]:
        if callback_query.data == "volver_menu":
            logger.info("Volviendo al menú principal desde historial")
            callback_query.edit_message_text(
                "Selecciona una opción:",
                reply_markup=crear_teclado_menu_principal()
            )
            return MENU_PRINCIPAL
        elif callback_query.data == "nuevo_test_desde_historial":
            logger.info("Iniciando nuevo test desde historial")
            preguntas = cargar_preguntas()
            asignaturas = obtener_todas_asignaturas(preguntas)
            conteo = contar_preguntas_por_asignatura()
            
            callback_query.edit_message_text(
                "Selecciona la asignatura para el test:",
                reply_markup=crear_teclado_asignaturas(asignaturas, conteo)
            )
            return SELECCION_ASIGNATURA
    
    # Continuar con la visualización normal del historial
    user_id = update.effective_user.id
    resultados = obtener_historial_usuario(user_id)
    estadisticas = obtener_estadisticas_usuario(user_id)

    if not resultados:
        mensaje = (
            "Aún no has completado ningún test. ¡Realiza tu primer test para "
            "empezar a construir tu historial!"
        )
        teclado = [[InlineKeyboardButton(f"{EMOJI_TEST} Realizar un test", callback_data="volver_menu")]]

        if update.callback_query:
            update.callback_query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(teclado)
            )
        else:
            update.message.reply_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(teclado)
            )
        return VER_HISTORIAL  # Cambiamos a VER_HISTORIAL para manejar el callback

    mensaje = "*Tu historial de tests:*\n\n"

    for i, resultado in enumerate(resultados[:10], 1):
        fecha = resultado.get('fecha', '')[:16]
        tipo_test = resultado.get('tipo_test', '')
        asignatura = resultado.get('asignatura', '')

        if not asignatura and tipo_test != 'global':
            asignatura = ASIGNATURAS.get(tipo_test, tipo_test)

        tipo_nombre = "Test global" if tipo_test == 'global' else asignatura

        correctas = resultado.get('correctas', 0)
        total = resultado.get('total', 0)
        porcentaje = resultado.get('porcentaje', 0)

        mensaje += (f"*{i}. {fecha}*\n"
                    f"📚 Test: {tipo_nombre}\n"
                    f"✅ Resultado: {correctas}/{total} ({porcentaje:.1f}%)\n\n")

    mensaje += "*Estadísticas globales:*\n"
    mensaje += f"📝 Tests completados: {estadisticas.get('total_tests', 0)}\n"
    mensaje += f"📊 Promedio de acierto: {estadisticas.get('promedio_porcentaje', 0):.1f}%\n"

    por_asignatura = estadisticas.get('por_asignatura', {})
    if por_asignatura:
        mensaje += "\n*Resultados por asignatura:*\n"
        for asignatura, datos in por_asignatura.items():
            mensaje += f"• {asignatura}: {datos.get('promedio', 0):.1f}% en {datos.get('total_tests', 0)} tests\n"

    # Cambiar los callbacks para ser más específicos
    teclado = [
        [InlineKeyboardButton(f"{EMOJI_TEST} Realizar otro test", callback_data="nuevo_test_desde_historial")],
        [InlineKeyboardButton(f"{EMOJI_MENU} Volver al menú", callback_data="volver_menu")]
    ]

    if update.callback_query:
        update.callback_query.edit_message_text(
            text=mensaje,
            reply_markup=InlineKeyboardMarkup(teclado),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        update.message.reply_text(
            text=mensaje,
            reply_markup=InlineKeyboardMarkup(teclado),
            parse_mode=ParseMode.MARKDOWN
        )
    
    return VER_HISTORIAL  # Mantenemos en VER_HISTORIAL para procesar callbacks futuros