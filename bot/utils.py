# app/utils.py

import json
import logging
import random
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple

from config import (
    PREGUNTAS_JSON, ASIGNATURAS, DATA_DIR, DB_PATH, 
    TABLA_RESULTADOS, TABLA_USUARIOS
)

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def cargar_preguntas() -> List[Dict[str, Any]]:
    """
    Carga las preguntas desde el archivo JSON.
    
    Returns:
        List[Dict[str, Any]]: Lista de preguntas con toda su información.
    """
    try:
        with open(PREGUNTAS_JSON, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get("preguntas", [])
    except Exception as e:
        logger.error(f"Error al cargar el archivo de preguntas: {e}")
        return []

def filtrar_preguntas_por_asignatura(preguntas: List[Dict[str, Any]], codigo_asignatura: str) -> List[Dict[str, Any]]:
    """
    Filtra las preguntas por asignatura.
    
    Args:
        preguntas (List[Dict[str, Any]]): Lista completa de preguntas.
        codigo_asignatura (str): Código de la asignatura (ej: "BDD", "EDD").
        
    Returns:
        List[Dict[str, Any]]: Lista de preguntas filtradas por asignatura.
    """
    return [p for p in preguntas if p.get("asignatura") == codigo_asignatura]

def seleccionar_preguntas_aleatorias(preguntas: List[Dict[str, Any]], cantidad: int) -> List[Dict[str, Any]]:
    """
    Selecciona un número determinado de preguntas aleatorias.
    
    Args:
        preguntas (List[Dict[str, Any]]): Lista de preguntas disponibles.
        cantidad (int): Cantidad de preguntas a seleccionar.
        
    Returns:
        List[Dict[str, Any]]: Lista de preguntas seleccionadas aleatoriamente.
    """
    if not preguntas:
        return []
    
    # Asegurarse de que la cantidad no exceda el número de preguntas disponibles
    cantidad = min(cantidad, len(preguntas))
    
    # Seleccionar preguntas aleatorias sin repetición
    return random.sample(preguntas, cantidad)

def verificar_respuesta(pregunta: Dict[str, Any], respuesta_usuario: str) -> bool:
    """
    Verifica si la respuesta del usuario es correcta.
    
    Args:
        pregunta (Dict[str, Any]): Pregunta con la respuesta correcta.
        respuesta_usuario (str): Respuesta proporcionada por el usuario.
        
    Returns:
        bool: True si la respuesta es correcta, False en caso contrario.
    """
    respuesta_correcta = pregunta.get("respuesta_correcta", "")
    return respuesta_usuario == respuesta_correcta

def obtener_todas_asignaturas(preguntas: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Obtiene todas las asignaturas disponibles en las preguntas.
    
    Args:
        preguntas (List[Dict[str, Any]]): Lista completa de preguntas.
        
    Returns:
        Dict[str, str]: Diccionario con los códigos y nombres de las asignaturas.
    """
    asignaturas_disponibles = {}
    for pregunta in preguntas:
        codigo = pregunta.get("asignatura")
        if codigo and codigo not in asignaturas_disponibles:
            asignaturas_disponibles[codigo] = ASIGNATURAS.get(codigo, codigo)
    
    return asignaturas_disponibles

def inicializar_base_datos() -> None:
    """
    Inicializa la base de datos si no existe.
    Crea las tablas necesarias.
    """
    try:
        # Asegurar que el directorio de datos existe
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # Conectar a la base de datos
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Crear tablas si no existen
        cursor.execute(TABLA_RESULTADOS)
        cursor.execute(TABLA_USUARIOS)
        
        # Guardar cambios y cerrar conexión
        conn.commit()
        conn.close()
        
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")

def registrar_usuario(user_id: int, nombre: str = None, apellido: str = None, nombre_usuario: str = None) -> None:
    """
    Registra o actualiza un usuario en la base de datos.
    
    Args:
        user_id (int): ID del usuario de Telegram.
        nombre (str, optional): Nombre del usuario.
        apellido (str, optional): Apellido del usuario.
        nombre_usuario (str, optional): Nombre de usuario en Telegram.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT user_id FROM usuarios WHERE user_id = ?", (user_id,))
        usuario_existente = cursor.fetchone()
        
        # Obtener la fecha y hora actuales
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if usuario_existente:
            # Actualizar información del usuario
            cursor.execute(
                "UPDATE usuarios SET ultimo_acceso = ?, nombre = COALESCE(?, nombre), "
                "apellido = COALESCE(?, apellido), nombre_usuario = COALESCE(?, nombre_usuario) "
                "WHERE user_id = ?",
                (ahora, nombre, apellido, nombre_usuario, user_id)
            )
        else:
            # Insertar nuevo usuario
            cursor.execute(
                "INSERT INTO usuarios (user_id, nombre, apellido, nombre_usuario, fecha_registro, ultimo_acceso) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, nombre, apellido, nombre_usuario, ahora, ahora)
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error al registrar usuario: {e}")

def guardar_resultado_test(user_id: int, user_name: str, tipo_test: str, correctas: int, total: int) -> None:
    """
    Guarda el resultado de un test en la base de datos.
    
    Args:
        user_id (int): ID del usuario de Telegram.
        user_name (str): Nombre de usuario de Telegram.
        tipo_test (str): Tipo de test realizado ('global' o código de asignatura).
        correctas (int): Número de respuestas correctas.
        total (int): Total de preguntas en el test.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calcular el porcentaje de acierto
        porcentaje = (correctas / total) * 100 if total > 0 else 0
        
        # Determinar la asignatura si no es un test global
        asignatura = None
        if tipo_test != 'global':
            asignatura = ASIGNATURAS.get(tipo_test, tipo_test)
        
        # Insertar resultado
        cursor.execute(
            "INSERT INTO resultados (user_id, user_name, tipo_test, asignatura, correctas, total, porcentaje) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, user_name, tipo_test, asignatura, correctas, total, porcentaje)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Resultado guardado: Usuario {user_id}, Test {tipo_test}, Resultado {correctas}/{total}")
    except Exception as e:
        logger.error(f"Error al guardar resultado: {e}")

def obtener_historial_usuario(user_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el historial de resultados de un usuario.
    
    Args:
        user_id (int): ID del usuario de Telegram.
        
    Returns:
        List[Dict[str, Any]]: Lista con los resultados de los tests.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
        cursor = conn.cursor()
        
        # Obtener todos los resultados del usuario ordenados por fecha
        cursor.execute(
            "SELECT id, fecha, tipo_test, asignatura, correctas, total, porcentaje "
            "FROM resultados WHERE user_id = ? ORDER BY fecha DESC",
            (user_id,)
        )
        
        # Convertir los resultados a diccionarios
        resultados = [dict(resultado) for resultado in cursor.fetchall()]
        
        conn.close()
        return resultados
    except Exception as e:
        logger.error(f"Error al obtener historial: {e}")
        return []

def obtener_estadisticas_usuario(user_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas globales del usuario.
    
    Args:
        user_id (int): ID del usuario de Telegram.
        
    Returns:
        Dict[str, Any]: Diccionario con las estadísticas.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Obtener estadísticas globales
        cursor.execute(
            "SELECT COUNT(*) as total_tests, "
            "AVG(porcentaje) as promedio_porcentaje, "
            "SUM(correctas) as total_correctas, "
            "SUM(total) as total_preguntas "
            "FROM resultados WHERE user_id = ?",
            (user_id,)
        )
        
        resultado = cursor.fetchone()
        
        # Obtener estadísticas por asignatura
        cursor.execute(
            "SELECT asignatura, COUNT(*) as total_tests, AVG(porcentaje) as promedio "
            "FROM resultados WHERE user_id = ? AND asignatura IS NOT NULL "
            "GROUP BY asignatura",
            (user_id,)
        )
        
        por_asignatura = {}
        for row in cursor.fetchall():
            por_asignatura[row[0]] = {
                'total_tests': row[1],
                'promedio': row[2]
            }
        
        conn.close()
        
        if resultado:
            return {
                'total_tests': resultado[0],
                'promedio_porcentaje': resultado[1] if resultado[1] is not None else 0,
                'total_correctas': resultado[2] if resultado[2] is not None else 0,
                'total_preguntas': resultado[3] if resultado[3] is not None else 0,
                'por_asignatura': por_asignatura
            }
        
        return {
            'total_tests': 0,
            'promedio_porcentaje': 0,
            'total_correctas': 0,
            'total_preguntas': 0,
            'por_asignatura': {}
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        return {
            'total_tests': 0,
            'promedio_porcentaje': 0,
            'total_correctas': 0,
            'total_preguntas': 0,
            'por_asignatura': {}
        }

def contar_preguntas_por_asignatura() -> Dict[str, int]:
    """
    Cuenta el número de preguntas disponibles por asignatura.
    
    Returns:
        Dict[str, int]: Diccionario con el conteo por asignatura.
    """
    try:
        preguntas = cargar_preguntas()
        conteo = {}
        
        for pregunta in preguntas:
            asignatura = pregunta.get("asignatura")
            if asignatura:
                conteo[asignatura] = conteo.get(asignatura, 0) + 1
        
        conteo["global"] = len(preguntas)  # Total global
        
        return conteo
    except Exception as e:
        logger.error(f"Error al contar preguntas: {e}")
        return {"global": 0}

def verificar_base_datos() -> bool:
    """
    Verifica que la base de datos existe y tiene las tablas necesarias.
    
    Returns:
        bool: True si la base de datos está correctamente configurada, False en caso contrario.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar existencia de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        tablas = [t[0] for t in tablas]
        
        necesarias = ['resultados', 'usuarios']
        todas_existen = all(tabla in tablas for tabla in necesarias)
        
        conn.close()
        return todas_existen
    except Exception as e:
        logger.error(f"Error al verificar la base de datos: {e}")
        return False