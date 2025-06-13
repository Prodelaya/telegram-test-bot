# app/test_handler.py

from typing import List, Dict, Any, Optional
import random

def inicializar_test(preguntas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Inicializa un nuevo test con estado inicial.
    
    Args:
        preguntas (List[Dict[str, Any]]): Lista de preguntas seleccionadas.
        
    Returns:
        Dict[str, Any]: Estado inicial del test.
    """
    estado_test = {
        'preguntas': preguntas,         # Lista de preguntas que se van a usar
        'pregunta_actual': 0,            # Índice de la pregunta actual (empieza en 0)
        'correctas': 0                   # Contador de respuestas correctas
    }
    return estado_test

def obtener_pregunta_actual(estado_test: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Devuelve la pregunta actual del test.
    
    Args:
        estado_test (Dict[str, Any]): Estado actual del test.
        
    Returns:
        Optional[Dict[str, Any]]: Pregunta actual o None si no quedan más.
    """
    preguntas = estado_test.get('preguntas', [])
    indice = estado_test.get('pregunta_actual', 0)
    
    if 0 <= indice < len(preguntas):
        return preguntas[indice]
    return None

def verificar_respuesta(estado_test: Dict[str, Any], respuesta_usuario: str) -> bool:
    """
    Verifica si la respuesta del usuario es correcta y actualiza el contador.
    
    Args:
        estado_test (Dict[str, Any]): Estado actual del test.
        respuesta_usuario (str): Letra de la respuesta del usuario (ej: "A", "B", "C", etc.).
        
    Returns:
        bool: True si es correcta, False si es incorrecta.
    """
    pregunta = obtener_pregunta_actual(estado_test)
    if not pregunta:
        return False  # No hay pregunta actual
    
    respuesta_correcta = pregunta.get('respuesta_correcta')
    
    es_correcta = (respuesta_usuario.upper() == respuesta_correcta.upper())
    
    if es_correcta:
        estado_test['correctas'] += 1  # Incrementamos el contador si acierta
    
    return es_correcta

def avanzar_pregunta(estado_test: Dict[str, Any]) -> None:
    """
    Avanza al siguiente índice de pregunta.
    
    Args:
        estado_test (Dict[str, Any]): Estado actual del test.
    """
    estado_test['pregunta_actual'] += 1

def test_completado(estado_test: Dict[str, Any]) -> bool:
    """
    Comprueba si el test ha terminado.
    
    Args:
        estado_test (Dict[str, Any]): Estado actual del test.
        
    Returns:
        bool: True si se han respondido todas las preguntas, False si faltan.
    """
    preguntas = estado_test.get('preguntas', [])
    indice = estado_test.get('pregunta_actual', 0)
    
    return indice >= len(preguntas)

def calcular_resultados(estado_test: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula los resultados finales del test.
    
    Args:
        estado_test (Dict[str, Any]): Estado actual del test.
        
    Returns:
        Dict[str, Any]: Diccionario con correctas, total y porcentaje de acierto.
    """
    total_preguntas = len(estado_test.get('preguntas', []))
    correctas = estado_test.get('correctas', 0)
    porcentaje = (correctas / total_preguntas * 100) if total_preguntas > 0 else 0
    
    return {
        'correctas': correctas,
        'total': total_preguntas,
        'porcentaje': round(porcentaje, 1)
    }
