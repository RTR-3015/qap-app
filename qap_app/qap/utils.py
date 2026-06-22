"""
Utilidades generales para el Problema de Asignación Cuadrática (QAP).
"""
import numpy as np


def calcular_costo(asignacion, flujo, distancia):
    """
    Calcula el valor de la función objetivo Z para una asignación dada.

    Z = sum_i sum_j f[i][j] * d[asignacion[i]][asignacion[j]]

    Parámetros
    ----------
    asignacion : list[int]
        asignacion[i] = ubicación asignada al departamento i
    flujo : np.ndarray (n x n)
    distancia : np.ndarray (n x n)

    Retorna
    -------
    float : costo total
    """
    n = len(asignacion)
    costo = 0.0
    for i in range(n):
        for j in range(n):
            costo += flujo[i][j] * distancia[asignacion[i]][asignacion[j]]
    return costo


def validar_matrices(flujo, distancia):
    """
    Valida que las matrices sean cuadradas y de igual tamaño.
    Lanza ValueError si algo no es correcto.
    """
    flujo = np.array(flujo, dtype=float)
    distancia = np.array(distancia, dtype=float)

    if flujo.shape[0] != flujo.shape[1]:
        raise ValueError("La matriz de flujo debe ser cuadrada.")
    if distancia.shape[0] != distancia.shape[1]:
        raise ValueError("La matriz de distancia debe ser cuadrada.")
    if flujo.shape != distancia.shape:
        raise ValueError(
            "Las matrices de flujo y distancia deben tener el mismo tamaño "
            f"(flujo: {flujo.shape}, distancia: {distancia.shape})."
        )
    if flujo.shape[0] < 2:
        raise ValueError("Se requieren al menos 2 departamentos/ubicaciones.")

    return flujo, distancia


def validar_reglas_qap(flujo, distancia):
    """
    Valida las reglas de negocio del QAP sobre matrices ya cuadradas y del
    mismo tamaño (no repite esas validaciones estructurales, que ya cubre
    validar_matrices). Reglas verificadas:

        1. Diagonal principal en cero (f_ii = 0, d_ii = 0).
        2. No hay valores negativos en ninguna de las dos matrices.

    No exige simetría: f_ij puede ser distinto de f_ji.

    Retorna un diccionario:
        {
            "valido": bool,
            "errores": [str, ...]   # lista vacía si valido es True
        }
    Cada error describe el problema y, cuando aplica, las celdas exactas
    afectadas (fila, columna) para que el usuario pueda corregirlas.
    """
    flujo = np.array(flujo, dtype=float)
    distancia = np.array(distancia, dtype=float)
    n = flujo.shape[0]
    errores = []

    # --- Regla 1: diagonal principal en cero ---
    diag_flujo_mal = [i for i in range(n) if flujo[i][i] != 0]
    if diag_flujo_mal:
        celdas = ", ".join(f"f[{i+1}][{i+1}]={flujo[i][i]:g}" for i in diag_flujo_mal)
        errores.append(
            f"La diagonal de la matriz de FLUJO debe ser 0. Celdas con error: {celdas}."
        )

    diag_dist_mal = [i for i in range(n) if distancia[i][i] != 0]
    if diag_dist_mal:
        celdas = ", ".join(f"d[{i+1}][{i+1}]={distancia[i][i]:g}" for i in diag_dist_mal)
        errores.append(
            f"La diagonal de la matriz de DISTANCIA debe ser 0. Celdas con error: {celdas}."
        )

    # --- Regla 2: sin valores negativos ---
    neg_flujo = np.argwhere(flujo < 0)
    if neg_flujo.size > 0:
        celdas = ", ".join(f"f[{i+1}][{j+1}]={flujo[i][j]:g}" for i, j in neg_flujo)
        errores.append(
            f"La matriz de FLUJO no debe tener valores negativos. Celdas con error: {celdas}."
        )

    neg_dist = np.argwhere(distancia < 0)
    if neg_dist.size > 0:
        celdas = ", ".join(f"d[{i+1}][{j+1}]={distancia[i][j]:g}" for i, j in neg_dist)
        errores.append(
            f"La matriz de DISTANCIA no debe tener valores negativos. Celdas con error: {celdas}."
        )

    return {"valido": len(errores) == 0, "errores": errores}


def generar_matrices_aleatorias_validas(n, min_valor, max_valor, seed=None):
    """
    Genera un par de matrices (flujo, distancia) aleatorias de tamaño n x n
    que cumplen automáticamente las reglas del QAP:
        - Diagonal principal en cero.
        - Sin valores negativos (min_valor se fuerza a >= 0).
        - Sin restricción de simetría.

    Parámetros
    ----------
    n : int
        Número de departamentos/ubicaciones.
    min_valor, max_valor : int
        Rango (inclusive) para los valores fuera de la diagonal.
    seed : int, opcional
        Semilla para reproducibilidad.

    Retorna
    -------
    (flujo, distancia) : tupla de np.ndarray (n x n)
    """
    min_valor = max(0, int(min_valor))
    max_valor = int(max_valor)
    if max_valor < min_valor:
        max_valor = min_valor

    rng = np.random.default_rng(seed)

    flujo = rng.integers(min_valor, max_valor + 1, size=(n, n)).astype(float)
    distancia = rng.integers(min_valor, max_valor + 1, size=(n, n)).astype(float)

    np.fill_diagonal(flujo, 0)
    np.fill_diagonal(distancia, 0)

    return flujo, distancia


def matriz_aleatoria(n, max_valor=20, simetrica=True, diagonal_cero=True, seed=None):
    """
    Genera una matriz aleatoria de tamaño n x n, útil para pruebas rápidas.
    """
    rng = np.random.default_rng(seed)
    m = rng.integers(0, max_valor + 1, size=(n, n)).astype(float)
    if simetrica:
        m = (m + m.T) / 2
    if diagonal_cero:
        np.fill_diagonal(m, 0)
    return m
