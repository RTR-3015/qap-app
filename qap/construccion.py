"""
Fase 1: Heurísticos de construcción para el QAP.

Cada función retorna una tupla:
    (asignacion, costo, nombre_metodo)

donde asignacion[i] = ubicación asignada al departamento i.
"""
import random
import numpy as np
from .utils import calcular_costo


def asignacion_mayores_flujos(flujo, distancia):
    """
    Asignación basada en mayores flujos.

    Idea: se identifican los departamentos con mayor flujo total y se les
    asignan, en orden, las ubicaciones más "centrales" (menor distancia
    total respecto a las demás). Es determinista.
    """
    n = flujo.shape[0]

    # Suma de flujos por departamento (qué tan "activo" es cada departamento)
    suma_flujo = flujo.sum(axis=1)
    # Suma de distancias por ubicación (qué tan "central" es cada ubicación)
    suma_distancia = distancia.sum(axis=1)

    # Ordenar departamentos de mayor a menor flujo total
    deptos_orden = np.argsort(-suma_flujo)
    # Ordenar ubicaciones de menor a mayor distancia total (más centrales primero)
    ubic_orden = np.argsort(suma_distancia)

    asignacion = [None] * n
    for depto, ubic in zip(deptos_orden, ubic_orden):
        asignacion[depto] = int(ubic)

    costo = calcular_costo(asignacion, flujo, distancia)
    return asignacion, costo, "Asignación basada en mayores flujos"


def metodo_greedy_costo(flujo, distancia):
    """
    Método Greedy por costo combinado.

    A diferencia de 'asignación por mayores flujos' (que solo mira el
    flujo), este método evalúa en cada paso el PAR (departamento, ubicación)
    que produce el menor incremento de costo acumulado, considerando flujo
    y distancia conjuntamente contra lo ya asignado. Es el greedy clásico
    de construcción para QAP.
    """
    n = flujo.shape[0]
    deptos_restantes = list(range(n))
    ubic_restantes = list(range(n))
    asignacion = [None] * n

    while deptos_restantes:
        mejor_incremento = None
        mejor_par = None

        for depto in deptos_restantes:
            for ubic in ubic_restantes:
                # Costo adicional de asignar depto->ubic dado lo ya asignado
                incremento = 0.0
                for d2 in range(n):
                    if asignacion[d2] is None:
                        continue
                    incremento += (
                        flujo[depto][d2] * distancia[ubic][asignacion[d2]]
                        + flujo[d2][depto] * distancia[asignacion[d2]][ubic]
                    )

                if mejor_incremento is None or incremento < mejor_incremento:
                    mejor_incremento = incremento
                    mejor_par = (depto, ubic)

        depto, ubic = mejor_par
        asignacion[depto] = ubic
        deptos_restantes.remove(depto)
        ubic_restantes.remove(ubic)

    costo = calcular_costo(asignacion, flujo, distancia)
    return asignacion, costo, "Método Greedy (costo combinado)"


def asignacion_menores_costos(flujo, distancia):
    """
    Asignación basada en menores costos.

    A diferencia del Greedy (que en cada paso busca el MEJOR par posible
    entre todos los disponibles), este método recorre los departamentos
    en un orden fijo (de mayor a menor flujo total, para priorizar a los
    más relevantes) y, para cada uno, elige la ubicación libre de menor
    costo marginal respecto a lo ya asignado. Es más rápido que el Greedy
    puro porque no reevalúa todos los pares en cada paso.
    """
    n = flujo.shape[0]
    suma_flujo = flujo.sum(axis=1)
    orden_deptos = list(np.argsort(-suma_flujo))

    ubic_restantes = list(range(n))
    asignacion = [None] * n

    for depto in orden_deptos:
        mejor_costo_marginal = None
        mejor_ubic = None

        for ubic in ubic_restantes:
            costo_marginal = 0.0
            for d2 in range(n):
                if asignacion[d2] is None:
                    continue
                costo_marginal += (
                    flujo[depto][d2] * distancia[ubic][asignacion[d2]]
                    + flujo[d2][depto] * distancia[asignacion[d2]][ubic]
                )

            if mejor_costo_marginal is None or costo_marginal < mejor_costo_marginal:
                mejor_costo_marginal = costo_marginal
                mejor_ubic = ubic

        asignacion[depto] = mejor_ubic
        ubic_restantes.remove(mejor_ubic)

    costo = calcular_costo(asignacion, flujo, distancia)
    return asignacion, costo, "Asignación basada en menores costos"


def construccion_aleatorizada(flujo, distancia, seed=None):
    """
    Construcción aleatorizada (semi-greedy).

    Genera una permutación aleatoria como solución inicial.
    Útil como punto de partida diverso para la fase de mejora.
    """
    n = flujo.shape[0]
    rng = random.Random(seed)
    asignacion = list(range(n))
    rng.shuffle(asignacion)

    costo = calcular_costo(asignacion, flujo, distancia)
    return asignacion, costo, "Construcción aleatorizada"


def construccion_semi_greedy(flujo, distancia, alpha=0.3, seed=None):
    """
    Construcción semi-greedy.

    En cada paso, en lugar de elegir siempre la mejor opción (greedy puro),
    se elige aleatoriamente entre las 'alpha' mejores opciones disponibles.
    Esto agrega diversidad mientras conserva buen criterio.

    alpha: proporción (0 < alpha <= 1) de candidatos "buenos" entre los que
           se elige aleatoriamente en cada paso.
    """
    n = flujo.shape[0]
    rng = random.Random(seed)

    deptos_restantes = list(range(n))
    ubic_restantes = list(range(n))
    asignacion = [None] * n

    suma_flujo = flujo.sum(axis=1)

    while deptos_restantes:
        # Ordenar deptos restantes por flujo total descendente
        deptos_restantes.sort(key=lambda d: -suma_flujo[d])
        k = max(1, int(np.ceil(alpha * len(deptos_restantes))))
        candidatos = deptos_restantes[:k]
        depto = rng.choice(candidatos)

        # Para ese departamento, elegir entre las k mejores ubicaciones
        # restantes según menor distancia total
        ubic_restantes.sort(
            key=lambda u: distancia[u][ubic_restantes].sum()
        )
        k_ubic = max(1, int(np.ceil(alpha * len(ubic_restantes))))
        candidatos_ubic = ubic_restantes[:k_ubic]
        ubic = rng.choice(candidatos_ubic)

        asignacion[depto] = ubic
        deptos_restantes.remove(depto)
        ubic_restantes.remove(ubic)

    costo = calcular_costo(asignacion, flujo, distancia)
    return asignacion, costo, "Construcción semi-greedy"


METODOS_CONSTRUCCION = {
    "greedy_costo": metodo_greedy_costo,
    "mayores_flujos": asignacion_mayores_flujos,
    "menores_costos": asignacion_menores_costos,
    "aleatorizada": construccion_aleatorizada,
    "semi_greedy": construccion_semi_greedy,
}
