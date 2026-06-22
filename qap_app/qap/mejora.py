"""
Fase 2: Heurísticos de mejora para el QAP.

Cada función recibe una asignación inicial y retorna:
    (asignacion_final, costo_final, nombre_metodo)
"""
import math
import random
from .utils import calcular_costo


def delta_swap(asignacion, flujo, distancia, p, q):
    """
    Calcula el cambio en el costo (delta) al intercambiar las ubicaciones
    asignadas a los departamentos p y q, SIN recalcular todo el costo
    desde cero (más eficiente que recalcular Z completo).

    Válida para matrices de flujo y/o distancia ASIMÉTRICAS (f_ij != f_ji).
    Incluye el término cruzado entre p y q, que cambia de valor cuando las
    matrices no son simétricas y que una versión simplificada del cálculo
    podría omitir por error.
    """
    n = len(asignacion)
    a = asignacion
    delta = 0.0

    for k in range(n):
        if k == p or k == q:
            continue
        delta += (
            (flujo[p][k] - flujo[q][k]) * (distancia[a[q]][a[k]] - distancia[a[p]][a[k]])
            + (flujo[k][p] - flujo[k][q]) * (distancia[a[k]][a[q]] - distancia[a[k]][a[p]])
        )

    # Término del par (p, q) entre sí: al intercambiar sus ubicaciones,
    # f[p][q]*d[a[p]][a[q]] pasa a ser f[p][q]*d[a[q]][a[p]] (y simétricamente
    # para f[q][p]). Si las matrices son simétricas este término es 0.
    delta += (
        flujo[p][q] * (distancia[a[q]][a[p]] - distancia[a[p]][a[q]])
        + flujo[q][p] * (distancia[a[p]][a[q]] - distancia[a[q]][a[p]])
    )

    return delta


def descenso_maxima_pendiente(asignacion_inicial, flujo, distancia, max_iter=10000):
    """
    Descenso de máxima pendiente (steepest descent / best-improvement).

    En cada iteración se evalúan TODOS los intercambios de pares posibles y
    se aplica el que más reduce el costo. Se detiene cuando ningún
    intercambio mejora la solución (óptimo local). Es el más exhaustivo de
    los métodos basados en swap, por eso suele dar buena calidad a costa de
    más tiempo de cómputo (evalúa O(n²) pares en cada iteración).
    """
    n = len(asignacion_inicial)
    asignacion = list(asignacion_inicial)
    costo_actual = calcular_costo(asignacion, flujo, distancia)

    iteraciones = 0
    mejora = True

    while mejora and iteraciones < max_iter:
        mejora = False
        mejor_delta = 0
        mejor_par = None

        for p in range(n):
            for q in range(p + 1, n):
                delta = delta_swap(asignacion, flujo, distancia, p, q)
                if delta < mejor_delta:
                    mejor_delta = delta
                    mejor_par = (p, q)

        iteraciones += 1

        if mejor_par is not None:
            p, q = mejor_par
            asignacion[p], asignacion[q] = asignacion[q], asignacion[p]
            costo_actual += mejor_delta
            mejora = True

    return asignacion, costo_actual, "Descenso de máxima pendiente"


def swap_primera_mejora(asignacion_inicial, flujo, distancia, max_iter=10000, seed=None):
    """
    Intercambio por pares (Swap) con estrategia de PRIMERA MEJORA
    (first-improvement).

    A diferencia del descenso de máxima pendiente (que evalúa TODOS los
    pares antes de decidir), aquí se recorren los pares en orden aleatorio
    y se aplica el PRIMER intercambio que reduzca el costo, sin seguir
    evaluando el resto. Esto lo hace más rápido por iteración, aunque puede
    necesitar más iteraciones para llegar a un óptimo local.
    """
    rng = random.Random(seed)
    n = len(asignacion_inicial)
    asignacion = list(asignacion_inicial)
    costo_actual = calcular_costo(asignacion, flujo, distancia)

    iteraciones = 0
    mejora = True

    while mejora and iteraciones < max_iter:
        mejora = False
        pares = [(p, q) for p in range(n) for q in range(p + 1, n)]
        rng.shuffle(pares)

        for p, q in pares:
            delta = delta_swap(asignacion, flujo, distancia, p, q)
            if delta < 0:
                asignacion[p], asignacion[q] = asignacion[q], asignacion[p]
                costo_actual += delta
                mejora = True
                break  # primera mejora encontrada: se aplica y se reinicia

        iteraciones += 1

    return asignacion, costo_actual, "Swap (primera mejora)"


def busqueda_local_con_perturbacion(
    asignacion_inicial, flujo, distancia, max_iter=10000,
    num_perturbaciones=15, seed=None,
):
    """
    Búsqueda local general con reinicios por perturbación.

    Aplica primera-mejora (first-improvement) hasta llegar a un óptimo
    local; al estancarse, aplica una pequeña perturbación aleatoria
    (un swap al azar que no necesariamente mejora) para salir de ese óptimo
    y continúa buscando. Se repite un número fijo de veces y se conserva
    siempre la mejor solución encontrada. Esto la distingue tanto del Swap
    de primera mejora puro como del descenso de máxima pendiente, ya que
    combina explotación (local search) con diversificación (perturbación).
    """
    rng = random.Random(seed)
    n = len(asignacion_inicial)

    asignacion = list(asignacion_inicial)
    costo_actual = calcular_costo(asignacion, flujo, distancia)

    mejor_asignacion = list(asignacion)
    mejor_costo = costo_actual

    def optimizar_local(asign, costo):
        mejora = True
        iteraciones = 0
        while mejora and iteraciones < max_iter:
            mejora = False
            pares = [(p, q) for p in range(n) for q in range(p + 1, n)]
            rng.shuffle(pares)
            for p, q in pares:
                delta = delta_swap(asign, flujo, distancia, p, q)
                if delta < 0:
                    asign[p], asign[q] = asign[q], asign[p]
                    costo += delta
                    mejora = True
                    break
            iteraciones += 1
        return asign, costo

    asignacion, costo_actual = optimizar_local(asignacion, costo_actual)
    if costo_actual < mejor_costo:
        mejor_costo = costo_actual
        mejor_asignacion = list(asignacion)

    for _ in range(num_perturbaciones):
        # Perturbación: un swap aleatorio, mejore o no
        p, q = rng.sample(range(n), 2)
        delta = delta_swap(asignacion, flujo, distancia, p, q)
        asignacion[p], asignacion[q] = asignacion[q], asignacion[p]
        costo_actual += delta

        asignacion, costo_actual = optimizar_local(asignacion, costo_actual)

        if costo_actual < mejor_costo:
            mejor_costo = costo_actual
            mejor_asignacion = list(asignacion)
        else:
            # Si no mejoró, regresamos a la mejor solución conocida antes
            # de seguir perturbando (evita degradar indefinidamente)
            asignacion = list(mejor_asignacion)
            costo_actual = mejor_costo

    return mejor_asignacion, mejor_costo, "Búsqueda local con perturbación"


def mejora_recocido_simulado(
    asignacion_inicial,
    flujo,
    distancia,
    temp_inicial=1000.0,
    temp_final=1.0,
    alpha=0.95,
    iter_por_temp=100,
    seed=None,
):
    """
    Recocido simulado (Simulated Annealing).

    En cada iteración se selecciona un intercambio aleatorio; si mejora la
    solución se acepta siempre, si la empeora se acepta con una probabilidad
    que depende de la temperatura actual (permite escapar de óptimos locales).
    """
    rng = random.Random(seed)
    n = len(asignacion_inicial)
    asignacion = list(asignacion_inicial)
    costo_actual = calcular_costo(asignacion, flujo, distancia)

    mejor_asignacion = list(asignacion)
    mejor_costo = costo_actual

    temp = temp_inicial
    while temp > temp_final:
        for _ in range(iter_por_temp):
            p, q = rng.sample(range(n), 2)
            delta = delta_swap(asignacion, flujo, distancia, p, q)

            if delta < 0 or rng.random() < math.exp(-delta / temp):
                asignacion[p], asignacion[q] = asignacion[q], asignacion[p]
                costo_actual += delta

                if costo_actual < mejor_costo:
                    mejor_costo = costo_actual
                    mejor_asignacion = list(asignacion)

        temp *= alpha

    return mejor_asignacion, mejor_costo, "Recocido simulado"


def busqueda_tabu(
    asignacion_inicial, flujo, distancia,
    max_iter=500, tam_lista_tabu=10, seed=None,
):
    """
    Búsqueda tabú (Tabu Search).

    En cada iteración se evalúa el mejor intercambio disponible ENTRE LOS
    NO PROHIBIDOS por la lista tabú (movimientos recientes), incluso si ese
    intercambio empeora momentáneamente la solución — esto le permite
    escapar de óptimos locales sin ciclos infinitos, a diferencia del
    descenso de máxima pendiente que se detiene apenas no hay mejora.
    El par (p, q) recién intercambiado se marca como tabú durante un número
    fijo de iteraciones, evitando revertirlo de inmediato.
    """
    rng = random.Random(seed)
    n = len(asignacion_inicial)
    asignacion = list(asignacion_inicial)
    costo_actual = calcular_costo(asignacion, flujo, distancia)

    mejor_asignacion = list(asignacion)
    mejor_costo = costo_actual

    lista_tabu = {}  # (p, q) -> iteración en la que deja de ser tabú

    for iteracion in range(max_iter):
        mejor_delta = None
        mejor_par = None

        pares = [(p, q) for p in range(n) for q in range(p + 1, n)]
        rng.shuffle(pares)

        for p, q in pares:
            es_tabu = lista_tabu.get((p, q), -1) > iteracion
            delta = delta_swap(asignacion, flujo, distancia, p, q)
            candidato_costo = costo_actual + delta

            # Criterio de aspiración: si el movimiento tabú produce una
            # solución mejor que la mejor conocida, se permite igualmente.
            if es_tabu and candidato_costo >= mejor_costo:
                continue

            if mejor_delta is None or delta < mejor_delta:
                mejor_delta = delta
                mejor_par = (p, q)

        if mejor_par is None:
            break  # no hay movimientos disponibles (caso extremo)

        p, q = mejor_par
        asignacion[p], asignacion[q] = asignacion[q], asignacion[p]
        costo_actual += mejor_delta
        lista_tabu[(p, q)] = iteracion + tam_lista_tabu

        if costo_actual < mejor_costo:
            mejor_costo = costo_actual
            mejor_asignacion = list(asignacion)

    return mejor_asignacion, mejor_costo, "Búsqueda tabú"


METODOS_MEJORA = {
    "swap_primera_mejora": swap_primera_mejora,
    "busqueda_local_perturbacion": busqueda_local_con_perturbacion,
    "descenso_maxima_pendiente": descenso_maxima_pendiente,
    "recocido_simulado": mejora_recocido_simulado,
    "busqueda_tabu": busqueda_tabu,
}
