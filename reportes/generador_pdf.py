"""
Generación de reportes en formato PDF para los resultados del QAP.
"""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)


def generar_reporte_pdf(resultado):
    """
    Genera un archivo PDF en memoria (BytesIO) con el resumen de resultados
    del QAP: método utilizado, costos, tiempos, mejora porcentual y
    asignaciones inicial y final.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "Titulo", parent=styles["Title"], fontSize=16, spaceAfter=12
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo", parent=styles["Heading2"], fontSize=12,
        textColor=colors.HexColor("#2F5496"), spaceAfter=6, spaceBefore=12
    )

    elementos = []
    elementos.append(Paragraph(
        "Reporte de Resultados &mdash; Problema de Asignación Cuadrática (QAP)",
        titulo_style
    ))
    elementos.append(Paragraph(
        f"Número de departamentos/ubicaciones: <b>{resultado['n']}</b>",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    # --- Fase 1 ---
    elementos.append(Paragraph("Fase 1 — Heurístico de construcción", subtitulo_style))
    datos_f1 = [
        ["Método", resultado["metodo_construccion"]],
        ["Costo inicial (Z)", str(resultado["costo_inicial"])],
        ["Tiempo de ejecución (s)", str(resultado["tiempo_construccion"])],
    ]
    elementos.append(_tabla_simple(datos_f1))

    # --- Fase 2 ---
    elementos.append(Paragraph("Fase 2 — Heurístico de mejora", subtitulo_style))
    datos_f2 = [
        ["Método", resultado["metodo_mejora"]],
        ["Costo final (Z)", str(resultado["costo_final"])],
        ["Tiempo de ejecución (s)", str(resultado["tiempo_mejora"])],
        ["Porcentaje de mejora", f"{resultado['porcentaje_mejora']}%"],
        ["Tiempo total de ejecución (s)", str(resultado["tiempo_total"])],
    ]
    elementos.append(_tabla_simple(datos_f2))

    # --- Asignaciones ---
    elementos.append(Paragraph("Asignación de departamentos a ubicaciones", subtitulo_style))
    n = resultado["n"]
    encabezados = ["Departamento"] + [f"D{i+1}" for i in range(n)]
    fila_inicial = ["Inicial"] + [f"U{u+1}" for u in resultado["asignacion_inicial"]]
    fila_final = ["Final"] + [f"U{u+1}" for u in resultado["asignacion_final"]]

    tabla_asig = Table([encabezados, fila_inicial, fila_final], hAlign="LEFT")
    tabla_asig.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5496")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    elementos.append(tabla_asig)

    doc.build(elementos)
    buffer.seek(0)
    return buffer


def _tabla_simple(datos):
    tabla = Table(datos, colWidths=[200, 250], hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF1FB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tabla
