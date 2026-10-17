"""El trabajo editorial: puntuar con la rúbrica, elegir y redactar las piezas."""

import json

from . import config
from .modelo import SinModelo

FORMATOS = {"reel", "carrusel", "post", "hilo", "agenda", "streaming"}


def _rubrica_texto():
    return "\n".join(f"- {clave} (0 a 5): {pregunta}" for clave, _, pregunta in config.EJES)


SISTEMA_PUNTAJE = (
    config.VOZ_MUTUO
    + """
Tu tarea ahora es de editor de research: leer historias de IA del día y puntuarlas con esta rúbrica.
"""
    + _rubrica_texto()
    + """
Sé exigente. La mayoría de las historias tiene que quedar por debajo de 3 en algún eje.
Un anuncio sin datos, una cifra sin estudio o una lista de "10 cosas" tiene antihype 0 o 1.
Respondé SOLO con un objeto JSON con esta forma:
{"historias": [{"id": "...", "senal": 0, "impacto": 0, "conversacion": 0, "antihype": 0,
  "titular": "titular en español, corto, con criterio, máximo 12 palabras",
  "resumen": "1 o 2 frases cortas en español: qué pasó, solo con datos del material",
  "porque_importa": "1 frase: qué le cambia a la gente que crea y trabaja",
  "angulo": "una línea que serviría de gancho para redes",
  "formato": "reel | carrusel | post | hilo | agenda | streaming",
  "descarte": "si alguna nota es baja, por qué en una frase corta; si no, vacío"}]}\nSé breve: cada campo, una o dos líneas como máximo.
"""
)


SISTEMA_PIEZAS = (
    config.VOZ_MUTUO
    + """
Ahora sos guionista y redactor. Con las notas aprobadas del brief armás piezas listas para revisar.
Usá SOLO los datos de cada nota. Si una fecha o cifra no está, no la escribas.
Respondé SOLO con un objeto JSON con esta forma:
{"reel": {"nota": "id", "titulo": "...", "beats": [{"t": "0:00", "texto": "lo que se dice", "pantalla": "lo que se ve"}]},
 "carrusel": {"nota": "id", "titulo": "...", "placas": ["texto placa 1", "... hasta 6"]},
 "post": {"nota": "id", "titulo": "...", "texto": "post de LinkedIn, párrafos cortos separados por línea en blanco"},
 "hilo": {"nota": "id", "titulo": "...", "partes": ["parte 1", "... 4 a 6 partes"]},
 "opencast": {"notas": ["id", "id"], "preguntas": ["3 preguntas incómodas y honestas para el streaming"]}}
El reel dura unos 40 segundos y tiene 5 o 6 beats. Cada pieza sale de una nota distinta cuando se pueda.
"""
)


def _para_modelo(grupo):
    p = grupo["principal"]
    otras = [i["fuente"] for i in grupo["items"][1:]]
    return {
        "id": grupo["id"],
        "titulo": p["titulo"],
        "resumen": p["resumen"][:450],
        "fuente": p["fuente"],
        "tipo_fuente": p["tipo"],
        "tambien_en": otras,
    }


def _acotar(n):
    try:
        return max(0, min(5, int(round(float(n)))))
    except (TypeError, ValueError):
        return 0


def puntuar(grupos, cliente):
    """Agrega a cada grupo sus puntajes y textos editoriales.

    Devuelve True si el modelo trabajó, False si se usó el puntaje de respaldo.
    """
    por_id = {g["id"]: g for g in grupos}
    algun_lote_ok = False
    for inicio in range(0, len(grupos), config.LOTE_PUNTAJE):
        lote = grupos[inicio : inicio + config.LOTE_PUNTAJE]
        pedido = "Historias del día:\n" + json.dumps([_para_modelo(g) for g in lote], ensure_ascii=False, indent=1)
        try:
            datos = cliente.pedir_json(SISTEMA_PUNTAJE, pedido, max_tokens=3500)
        except SinModelo:
            continue
        for h in datos.get("historias", []) if isinstance(datos, dict) else []:
            g = por_id.get(str(h.get("id", "")))
            if not g:
                continue
            g["puntos"] = {clave: _acotar(h.get(clave)) for clave, _, _ in config.EJES}
            g["titular"] = (h.get("titular") or "").strip()
            g["resumen"] = (h.get("resumen") or "").strip()
            g["porque_importa"] = (h.get("porque_importa") or "").strip()
            g["angulo"] = (h.get("angulo") or "").strip()
            fmt = (h.get("formato") or "post").strip().lower()
            g["formato"] = fmt if fmt in FORMATOS else "post"
            g["descarte"] = (h.get("descarte") or "").strip()
            algun_lote_ok = True
    for g in grupos:
        if "puntos" not in g:
            _puntaje_respaldo(g)
        g["total"] = sum(g["puntos"].values())
    return algun_lote_ok


def _puntaje_respaldo(g):
    """Sin modelo: un puntaje simple y honesto, marcado como tal en la página."""
    n_fuentes = len({i["fuente"] for i in g["items"]})
    oficial = any(i["tipo"] == "oficial" for i in g["items"])
    g["puntos"] = {
        "senal": 3 if oficial else 2,
        "impacto": 2,
        "conversacion": min(5, 1 + n_fuentes),
        "antihype": 3 if (oficial or n_fuentes > 1) else 1,
    }
    g["titular"] = g["principal"]["titulo"]
    g["resumen"] = g["principal"]["resumen"]
    g["porque_importa"] = ""
    g["angulo"] = ""
    g["formato"] = "post"
    g["descarte"] = ""
    g["respaldo"] = True


def seleccionar(grupos):
    orden = sorted(grupos, key=lambda g: (g["total"], g["puntos"]["antihype"]), reverse=True)
    # Sin modelo el puntaje es grueso: se baja el umbral y manda la verificación.
    umbral = config.UMBRAL_PUBLICABLE if any(not g.get("respaldo") for g in grupos) else 8
    publicables = [g for g in orden if g["verificacion"]["estado"] == "verificada" and g["total"] >= umbral]
    publicables = publicables[: config.MAX_PUBLICABLES]
    # Lo sin confirmar que más interés despierta: se muestra para no esconderlo.
    sin_confirmar = [g for g in orden if g["verificacion"]["estado"] == "sin_confirmar" and g["total"] >= umbral - 2]
    sin_confirmar = sin_confirmar[: config.MAX_SIN_VERIFICAR]
    elegidos = {g["id"] for g in publicables + sin_confirmar}
    # Descartados: los que más ruido hacían (más fuentes o más conversación) y no pasaron.
    resto = [g for g in grupos if g["id"] not in elegidos and not g.get("respaldo")]
    resto.sort(key=lambda g: (g["puntos"]["conversacion"], -g["puntos"]["antihype"]), reverse=True)
    descartados = [g for g in resto if g.get("descarte")][: config.MAX_DESCARTADOS]
    return publicables, sin_confirmar, descartados


def redactar_piezas(publicables, cliente):
    if not publicables:
        return None
    notas = [
        {
            "id": g["id"],
            "titular": g["titular"],
            "resumen": g["resumen"],
            "porque_importa": g["porque_importa"],
            "angulo": g["angulo"],
            "formato_sugerido": g["formato"],
        }
        for g in publicables[:5]
    ]
    pedido = "Notas aprobadas del brief de hoy:\n" + json.dumps(notas, ensure_ascii=False, indent=1)
    try:
        datos = cliente.pedir_json(SISTEMA_PIEZAS, pedido, max_tokens=3500)
    except SinModelo:
        return None
    return datos if isinstance(datos, dict) else None
