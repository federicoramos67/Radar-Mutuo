"""Verificación cruzada de fuentes.

Esta parte la decide el código, no el modelo de lenguaje, a propósito:
un modelo puede sonar seguro sin tener razón. Las reglas son pocas y se leen
en voz alta:

  1. Si lo cuentan dos medios de dominios distintos, está VERIFICADA (corroborada).
  2. Si lo publicó la propia empresa y además lo cubre al menos un medio, está
     VERIFICADA (fuente primaria + cobertura).
  3. Si lo publicó solo la propia empresa:
       - si es un lanzamiento o una investigación con datos concretos, está
         VERIFICADA como fuente primaria: es cierto que existe;
       - si es un caso de cliente, una opinión, una promoción o no se puede
         saber qué es, es un COMUNICADO: es cierto que la empresa lo dijo, pero
         nadie independiente lo cubrió. Se muestra aparte y no es publicable.
  4. Si lo cuenta un solo medio, o solo un agregador, queda SIN CONFIRMAR.

El modelo informa la "naturaleza" de la nota (lanzamiento, caso de cliente…),
pero la regla que la convierte en estado la aplica este archivo.
"""

import re

from .limpieza import dominio

NATURALEZAS_NOTICIA = {"lanzamiento", "investigacion"}
# Títulos típicos de contenido de marketing en blogs corporativos.
_PATRON_CASO = re.compile(
    r"^(how|cómo|como)\b.*\b(is|are|uses?|using|builds?|building|scales?|scaling|transforms?|"
    r"usa|usan|construye|transforma)\b|customer stor|case stud|caso de (éxito|exito|cliente)|"
    r"\bwith (chatgpt|openai|gemini|copilot|claude)\b|powered by",
    re.I,
)


def _fuentes(items):
    out, vistos = [], set()
    for i in items:
        if i["fuente"] in vistos:
            continue
        vistos.add(i["fuente"])
        out.append({"nombre": i["fuente"], "link": i["link"], "tipo": i["tipo"]})
    return out


def verificar(grupo):
    """Estado según las fuentes. Antes de puntuar: la parte que no depende del modelo."""
    items = grupo["items"]
    oficiales = [i for i in items if i["tipo"] == "oficial"]
    medios = {dominio(i["link"]) for i in items if i["tipo"] == "medio"}
    if len(medios) >= 2:
        estado, motivo = "verificada", f"Corroborada por {len(medios)} medios independientes."
    elif oficiales and medios:
        estado, motivo = "verificada", f"Fuente primaria ({oficiales[0]['fuente']}) con cobertura independiente."
    elif oficiales:
        # Provisorio: se decide entre verificada y comunicado después de puntuar.
        estado, motivo = "solo_oficial", f"Solo lo publicó {oficiales[0]['fuente']}."
    else:
        unica = items[0]["fuente"]
        estado = "sin_confirmar"
        if items[0]["tipo"] == "comunidad":
            motivo = f"Solo aparece en {unica}, que es un agregador. Falta un medio o la fuente original."
        else:
            motivo = f"Solo lo publicó {unica}. Falta una segunda fuente independiente o el anuncio oficial."
    return {"estado": estado, "motivo": motivo, "fuentes": _fuentes(items)}


# Títulos de tono publicitario: celebran en vez de informar.
_PATRON_PROMO = re.compile(r"celebrat|ignites?|\bmagic|game.?changer|revolution|unleash|supercharg|the future of|"
                           r"celebra|revoluciona|potencia tu|descubr[ií]", re.I)


def es_promocion(titulo):
    return bool(_PATRON_PROMO.search(titulo or ""))


def es_caso_de_cliente(titulo):
    return bool(_PATRON_CASO.search(titulo or ""))


def reclasificar(grupo):
    """Después de puntuar: resuelve las notas que solo tienen fuente oficial."""
    v = grupo["verificacion"]
    if v["estado"] != "solo_oficial":
        return v
    empresa = next(i["fuente"] for i in grupo["items"] if i["tipo"] == "oficial")
    naturaleza = grupo.get("naturaleza")
    titulo = grupo["principal"]["titulo"]
    antihype = grupo.get("puntos", {}).get("antihype", 0)
    noticia = (naturaleza in NATURALEZAS_NOTICIA and not es_caso_de_cliente(titulo)
               and not es_promocion(titulo) and antihype >= 3)
    if noticia:
        v["estado"] = "verificada"
        v["motivo"] = f"Fuente primaria: {empresa}. Es un {naturaleza} con datos concretos."
    else:
        v["estado"] = "comunicado"
        if es_caso_de_cliente(titulo) or naturaleza == "caso_cliente":
            tipo = "un caso de cliente"
        elif naturaleza == "promocion" or es_promocion(titulo):
            tipo = "una pieza de promoción"
        elif naturaleza == "opinion":
            tipo = "una pieza de opinión"
        else:
            tipo = "un anuncio sin datos verificables"
        v["motivo"] = f"Lo dijo {empresa} en su propio blog y es {tipo}. Ningún medio independiente lo cubrió todavía."
    return v
