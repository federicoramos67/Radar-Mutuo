"""Verificación cruzada de fuentes.

Esta parte la decide el código, no el modelo de lenguaje, a propósito:
un modelo puede sonar seguro sin tener razón. Las reglas son pocas y se leen
en voz alta:

  1. Si la propia empresa o laboratorio lo publicó, está verificada (fuente primaria).
  2. Si lo cuentan dos medios de dominios distintos, está verificada (corroborada).
  3. Si lo cuenta un solo medio, o solo un agregador, queda SIN CONFIRMAR:
     se muestra en el brief, pero marcada y fuera de lo publicable.
"""

from .limpieza import dominio


def verificar(grupo):
    items = grupo["items"]
    oficiales = [i for i in items if i["tipo"] == "oficial"]
    medios = {dominio(i["link"]) for i in items if i["tipo"] == "medio"}

    if oficiales:
        estado, motivo = "verificada", f"Fuente primaria: {oficiales[0]['fuente']}."
    elif len(medios) >= 2:
        estado, motivo = "verificada", f"Corroborada por {len(medios)} medios independientes."
    else:
        unica = items[0]["fuente"]
        estado = "sin_confirmar"
        if items[0]["tipo"] == "comunidad":
            motivo = f"Solo aparece en {unica}, que es un agregador. Falta un medio o la fuente original."
        else:
            motivo = f"Solo lo publicó {unica}. Falta una segunda fuente independiente o el anuncio oficial."
    fuentes = []
    vistos = set()
    for i in items:
        if i["fuente"] in vistos:
            continue
        vistos.add(i["fuente"])
        fuentes.append({"nombre": i["fuente"], "link": i["link"], "tipo": i["tipo"]})
    return {"estado": estado, "motivo": motivo, "fuentes": fuentes}
