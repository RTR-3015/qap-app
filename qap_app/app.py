"""
Aplicación web Flask para resolver el Problema de Asignación Cuadrática (QAP)
mediante heurísticos de construcción (Fase 1) y mejora (Fase 2).

Flujo de navegación:
    /            -> Dashboard: elegir Fase 1 o Fase 2
    /fase1       -> Captura de datos + método de construcción
    /fase2       -> Selección de método de mejora (usa la última solución
                    inicial guardada en sesión, si existe)
"""
import time
import numpy as np
import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    send_file, flash, jsonify
)

from qap.utils import validar_matrices, validar_reglas_qap
from qap.construccion import (
    metodo_greedy_costo,
    asignacion_mayores_flujos,
    asignacion_menores_costos,
    construccion_aleatorizada,
    construccion_semi_greedy,
)
from qap.mejora import (
    swap_primera_mejora,
    busqueda_local_con_perturbacion,
    descenso_maxima_pendiente,
    mejora_recocido_simulado,
    busqueda_tabu,
)

app = Flask(__name__)
app.secret_key = "cambia-esta-clave-en-produccion"  # TODO: usar variable de entorno


# ---------------------------------------------------------------------------
# Dashboard principal
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/borrar_datos", methods=["GET"])
def borrar_datos():
    """
    Borra todos los datos de la sesión (matrices, resultados de ambas fases)
    desde el dashboard principal. A diferencia de fase1_reiniciar, esta
    limpieza es total: se usa cuando el usuario quiere empezar un problema
    completamente nuevo.
    """
    session.clear()
    flash("Se borraron todos los datos. Puedes empezar un nuevo problema.", "success")
    return redirect(url_for("index"))


# ===========================================================================
# FASE 1 — Heurístico de construcción
# ===========================================================================
@app.route("/fase1", methods=["GET"])
def fase1():
    """
    Pantalla única de Fase 1: si no hay datos cargados, muestra las opciones
    de captura/importación. Si ya hay datos, muestra el formulario de método
    de construcción y, si ya se ejecutó, el resultado.
    """
    tiene_datos = "flujo" in session
    return render_template(
        "fase1.html",
        tiene_datos=tiene_datos,
        n=session.get("n"),
        resultado=session.get("resultado_fase1"),
    )


@app.route("/fase1/generar_matrices", methods=["POST"])
def fase1_generar_matrices():
    """
    Recibe el tamaño n y muestra el formulario de captura manual.
    Reutilizamos la misma plantilla fase1.html generando una tabla dinámica
    vía un parámetro de consulta para no crear una pantalla nueva.
    """
    try:
        n = int(request.form.get("n", 0))
    except ValueError:
        n = 0

    if n < 2 or n > 30:
        flash("El número de departamentos debe estar entre 2 y 30.", "error")
        return redirect(url_for("fase1"))

    return render_template("captura_matrices.html", n=n)


@app.route("/fase1/guardar_matrices", methods=["POST"])
def fase1_guardar_matrices():
    n = int(request.form.get("n"))

    try:
        flujo = _leer_matriz_formulario(request.form, "flujo", n)
        distancia = _leer_matriz_formulario(request.form, "distancia", n)
        flujo, distancia = validar_matrices(flujo, distancia)

        reporte = validar_reglas_qap(flujo, distancia)
        if not reporte["valido"]:
            for error in reporte["errores"]:
                flash(error, "error")
            flash(
                "No se guardaron las matrices: corrige los errores señalados.",
                "error",
            )
            return redirect(url_for("fase1_generar_matrices_get", n=n))
    except Exception as e:
        flash(f"Error en los datos capturados: {e}", "error")
        return redirect(url_for("fase1"))

    _guardar_datos_en_sesion(flujo, distancia)
    flash("Matrices guardadas correctamente.", "success")
    return redirect(url_for("fase1"))


@app.route("/fase1/generar_matrices", methods=["GET"])
def fase1_generar_matrices_get():
    """
    Reabre la pantalla de captura manual con el mismo tamaño n, usada cuando
    la validación falla y necesitamos regresar al usuario a corregir datos
    (GET en vez de POST porque no estamos recibiendo un formulario nuevo).
    """
    try:
        n = int(request.args.get("n", 0))
    except ValueError:
        n = 0
    if n < 2 or n > 30:
        return redirect(url_for("fase1"))
    return render_template("captura_matrices.html", n=n)


@app.route("/fase1/validar_ajax", methods=["POST"])
def fase1_validar_ajax():
    """
    Valida en tiempo real (sin recargar la página) los valores capturados
    en el formulario de matrices, usando las mismas reglas que se aplican
    al guardar: diagonal en cero y sin valores negativos.
    Retorna JSON: {"valido": bool, "errores": [str, ...]}
    """
    try:
        n = int(request.form.get("n"))
        flujo = _leer_matriz_formulario(request.form, "flujo", n)
        distancia = _leer_matriz_formulario(request.form, "distancia", n)
    except Exception as e:
        return jsonify({"valido": False, "errores": [f"Datos inválidos: {e}"]})

    reporte = validar_reglas_qap(flujo, distancia)
    return jsonify(reporte)


@app.route("/fase1/importar", methods=["POST"])
def fase1_importar():
    archivo_flujo = request.files.get("archivo_flujo")
    archivo_distancia = request.files.get("archivo_distancia")

    if not archivo_flujo or not archivo_distancia:
        flash("Debes subir ambos archivos: flujo y distancia.", "error")
        return redirect(url_for("fase1"))

    try:
        flujo_df = _leer_matriz_archivo(archivo_flujo)
        distancia_df = _leer_matriz_archivo(archivo_distancia)
        flujo, distancia = validar_matrices(flujo_df.values, distancia_df.values)
    except Exception as e:
        flash(f"Error al leer los archivos: {e}", "error")
        return redirect(url_for("fase1"))

    _guardar_datos_en_sesion(flujo, distancia)
    flash("Archivos importados correctamente.", "success")
    return redirect(url_for("fase1"))


@app.route("/fase1/reiniciar", methods=["GET"])
def fase1_reiniciar():
    """Permite al usuario descartar los datos cargados y volver a empezar."""
    for clave in ("flujo", "distancia", "n", "resultado_fase1"):
        session.pop(clave, None)
    return redirect(url_for("fase1"))


@app.route("/fase1/ejecutar", methods=["POST"])
def fase1_ejecutar():
    if "flujo" not in session:
        flash("No hay datos cargados.", "error")
        return redirect(url_for("fase1"))

    flujo = np.array(session["flujo"])
    distancia = np.array(session["distancia"])
    metodo_construccion = request.form.get("metodo_construccion", "greedy_costo")

    t0 = time.perf_counter()
    if metodo_construccion == "greedy_costo":
        asignacion, costo, nombre = metodo_greedy_costo(flujo, distancia)
    elif metodo_construccion == "mayores_flujos":
        asignacion, costo, nombre = asignacion_mayores_flujos(flujo, distancia)
    elif metodo_construccion == "menores_costos":
        asignacion, costo, nombre = asignacion_menores_costos(flujo, distancia)
    elif metodo_construccion == "aleatorizada":
        asignacion, costo, nombre = construccion_aleatorizada(flujo, distancia)
    elif metodo_construccion == "semi_greedy":
        asignacion, costo, nombre = construccion_semi_greedy(flujo, distancia)
    else:
        flash("Método de construcción no válido.", "error")
        return redirect(url_for("fase1"))
    tiempo = time.perf_counter() - t0

    session["resultado_fase1"] = {
        "n": flujo.shape[0],
        "metodo": nombre,
        "asignacion": asignacion,
        "costo": round(costo, 4),
        "tiempo": round(tiempo, 6),
    }

    return redirect(url_for("fase1"))


# ===========================================================================
# FASE 2 — Heurístico de mejora
# ===========================================================================
@app.route("/fase2", methods=["GET"])
def fase2():
    """
    Acceso libre: la Fase 2 es accesible en cualquier momento. Si existe una
    solución inicial (Fase 1) en sesión, se usa como punto de partida; si no
    existe, se invita a generarla primero.
    """
    return render_template(
        "fase2.html",
        resultado_fase1=session.get("resultado_fase1"),
        resultado=session.get("resultado_fase2"),
    )


@app.route("/fase2/ejecutar", methods=["POST"])
def fase2_ejecutar():
    resultado_fase1 = session.get("resultado_fase1")
    if not resultado_fase1 or "flujo" not in session:
        flash("Primero genera una solución inicial en la Fase 1.", "error")
        return redirect(url_for("fase2"))

    flujo = np.array(session["flujo"])
    distancia = np.array(session["distancia"])
    asignacion_inicial = resultado_fase1["asignacion"]
    costo_inicial = resultado_fase1["costo"]

    metodo_mejora = request.form.get("metodo_mejora", "descenso_maxima_pendiente")

    t0 = time.perf_counter()
    if metodo_mejora == "swap_primera_mejora":
        asignacion_final, costo_final, nombre = swap_primera_mejora(
            asignacion_inicial, flujo, distancia
        )
    elif metodo_mejora == "busqueda_local_perturbacion":
        asignacion_final, costo_final, nombre = busqueda_local_con_perturbacion(
            asignacion_inicial, flujo, distancia
        )
    elif metodo_mejora == "descenso_maxima_pendiente":
        asignacion_final, costo_final, nombre = descenso_maxima_pendiente(
            asignacion_inicial, flujo, distancia
        )
    elif metodo_mejora == "recocido_simulado":
        asignacion_final, costo_final, nombre = mejora_recocido_simulado(
            asignacion_inicial, flujo, distancia
        )
    elif metodo_mejora == "busqueda_tabu":
        asignacion_final, costo_final, nombre = busqueda_tabu(
            asignacion_inicial, flujo, distancia
        )
    else:
        flash("Método de mejora no válido.", "error")
        return redirect(url_for("fase2"))
    tiempo = time.perf_counter() - t0

    porcentaje_mejora = 0.0
    if costo_inicial > 0:
        porcentaje_mejora = (costo_inicial - costo_final) / costo_inicial * 100

    tiempo_construccion = resultado_fase1.get("tiempo", 0.0)
    tiempo_total = tiempo_construccion + tiempo

    resultado_completo = {
        "n": flujo.shape[0],
        "metodo_construccion": resultado_fase1["metodo"],
        "asignacion_inicial": asignacion_inicial,
        "costo_inicial": costo_inicial,
        "tiempo_construccion": round(tiempo_construccion, 6),
        "metodo_mejora": nombre,
        "asignacion_final": asignacion_final,
        "costo_final": round(costo_final, 4),
        "tiempo_mejora": round(tiempo, 6),
        "tiempo_total": round(tiempo_total, 6),
        "porcentaje_mejora": round(porcentaje_mejora, 2),
        "flujo": flujo.tolist(),
        "distancia": distancia.tolist(),
    }

    session["resultado_fase2"] = {
        "n": flujo.shape[0],
        "metodo": nombre,
        "asignacion": asignacion_final,
        "costo": round(costo_final, 4),
        "tiempo": round(tiempo, 6),
        "porcentaje_mejora": round(porcentaje_mejora, 2),
    }
    # Resultado completo para exportar reportes (incluye matrices y ambas fases)
    session["resultado_export"] = resultado_completo

    return redirect(url_for("fase2"))


# ---------------------------------------------------------------------------
# Helpers de lectura/validación de datos
# ---------------------------------------------------------------------------
def _guardar_datos_en_sesion(flujo, distancia):
    """Guarda las matrices y limpia resultados previos (datos nuevos = empezar de cero)."""
    session["flujo"] = flujo.tolist()
    session["distancia"] = distancia.tolist()
    session["n"] = flujo.shape[0]
    session.pop("resultado_fase1", None)
    session.pop("resultado_fase2", None)
    session.pop("resultado_export", None)


def _leer_matriz_archivo(file_storage):
    """Lee un archivo CSV o Excel subido y retorna un DataFrame numérico."""
    filename = file_storage.filename.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(file_storage, header=None)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_storage, header=None)
    else:
        raise ValueError("Formato no soportado. Usa CSV o Excel (.xlsx/.xls).")
    return df.apply(pd.to_numeric, errors="coerce")


def _leer_matriz_formulario(form, prefijo, n):
    matriz = []
    for i in range(n):
        fila = []
        for j in range(n):
            valor = form.get(f"{prefijo}_{i}_{j}", "0")
            fila.append(float(valor))
        matriz.append(fila)
    return matriz


# ---------------------------------------------------------------------------
# Exportación de reportes (usa el último resultado completo de Fase 2)
# ---------------------------------------------------------------------------
@app.route("/exportar/excel")
def exportar_excel():
    from reportes.generador_excel import generar_reporte_excel

    resultado = session.get("resultado_export")
    if not resultado:
        flash("No hay resultados de Fase 2 para exportar.", "error")
        return redirect(url_for("fase2"))

    buffer = generar_reporte_excel(resultado)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_qap.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/exportar/pdf")
def exportar_pdf():
    from reportes.generador_pdf import generar_reporte_pdf

    resultado = session.get("resultado_export")
    if not resultado:
        flash("No hay resultados de Fase 2 para exportar.", "error")
        return redirect(url_for("fase2"))

    buffer = generar_reporte_pdf(resultado)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_qap.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
