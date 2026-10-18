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
Un caso de cliente contado por la empresa que vende el producto es marketing: antihype 2 como máximo.
naturaleza: "lanzamiento" = sale un producto, modelo o función nueva con datos concretos;
"investigacion" = paper o estudio con resultados; "caso_cliente" = una empresa cuenta cómo la usa un cliente.
Respondé SOLO con un objeto JSON con esta forma:
{"historias": [{"id": "...", "senal": 0, "impacto": 0, "conversacion": 0, "antihype": 0,
  "titular": "titular en español, corto, con criterio, máximo 12 palabras",
  "resumen": "1 o 2 frases cortas en español: qué pasó, solo con datos del material",
  "porque_importa": "1 frase: qué le cambia a una persona concreta (quien edita, programa, enseña, comunica). Sin forzar la región",
  "naturaleza": "lanzamiento | investigacion | caso_cliente | opinion | promocion | evento | otro",
  "angulo": "una línea que serviría de gancho para redes",
  "formato": "reel | carrusel | post | hilo | agenda | streaming",
  "descarte": "si alguna nota es baja, por qué en una frase corta; si no, vacío"}]}\nSé breve: cada campo, una o dos líneas como máximo.
"""
)


SISTEMA_PIEZAS = (
    config.VOZ_MUTUO
    + """
Ahora sos guionista y redactor. Con las notas aprobadas del brief armás piezas listas para revisar.
Usá SOLO los datos de cada nota y de su campo "fuente". Si una fecha o cifra no está en la fuente, no la escribas.
Si una nota es un anuncio de empresa, decilo como anuncio: "X dice que…", no como hecho comprobado.
Respondé SOLO con un objeto JSON con esta forma:
{"reel": {"nota": "id", "titulo": "...", "beats": [{"t": "0:00", "texto": "lo que se dice", "pantalla": "lo que se ve"}]},
 "carrusel": {"nota": "id", "titulo": "...", "placas": ["texto placa 1", "... hasta 6"]},
 "post": {"nota": "id", "titulo": "...", "texto": "post de LinkedIn, párrafos cortos separados por línea en blanco"},
 "hilo": {"nota": "id", "titulo": "...", "partes": ["parte 1", "... 4 a 6 partes"]},
 "opencast": {"notas": ["id", "id"], "preguntas": ["3 preguntas incómodas y honestas para el streaming"]}}
El reel dura unos 40 segundos y tiene 5 o 6 beats. Cada pieza sale de una nota distinta cuando se pueda.
"""
)


SISTEMA_AGRUPAR = """Sos editor de una mesa de noticias. Te paso titulares de distintas fuentes.
Agrupá SOLO los que cuentan el MISMO hecho concreto (el mismo anuncio, lanzamiento, estudio o evento).
Que hablen del mismo tema o de la misma empresa NO alcanza: tiene que ser la misma noticia.
SÍ cuentan como el mismo hecho dos notas que cubren el mismo anuncio desde ángulos distintos
(por ejemplo: "X cambia sus términos" y "X ahora puede usar tus datos para entrenar" si es el mismo cambio).
Leé el resumen, no solo el título. Si dos notas no comparten el hecho central, no las agrupes.
Respondé SOLO con JSON: {"grupos": [["h01", "h07"], ["h03", "h12", "h15"]]}
Incluí únicamente grupos de 2 o más. Si no hay ninguno: {"grupos": []}"""


def unir_por_modelo(grupos, cliente):
    """Junta historias que el agrupador por palabras no vio (títulos distintos, mismo hecho)."""
    if len(grupos) < 2:
        return grupos
    lista = "\n".join(
        f'{g["id"]} [{g["principal"]["fuente"]}] {g["principal"]["titulo"]} — {g["principal"]["resumen"][:140]}' for g in grupos
    )
    try:
        datos = cliente.pedir_json(SISTEMA_AGRUPAR, "Titulares:\n" + lista, max_tokens=900)
    except SinModelo:
        return grupos
    por_id = {g["id"]: g for g in grupos}
    absorbidos = set()
    for conjunto in (datos.get("grupos") or []) if isinstance(datos, dict) else []:
        ids = [i for i in conjunto if isinstance(i, str) and i in por_id and i not in absorbidos] if isinstance(conjunto, list) else []
        if len(ids) < 2:
            continue
        base = por_id[ids[0]]
        for otro in ids[1:]:
            base["items"].extend(por_id[otro]["items"])
            absorbidos.add(otro)
        # la fuente principal pasa a ser la de mayor jerarquía (oficial > medio > comunidad)
        base["items"].sort(key=lambda i: {"oficial": 0, "medio": 1, "comunidad": 2}[i["tipo"]])
        base["principal"] = base["items"][0]
    return [g for g in grupos if g["id"] not in absorbidos]


def _para_modelo(grupo):
    p = grupo["principal"]
    otras = [i["fuente"] for i in grupo["items"][1:]]
    return {
        "id": grupo["id"],
        "titulo": p["titulo"],
        "resumen": p["resumen"][:280],
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
            datos = cliente.pedir_json(SISTEMA_PUNTAJE, pedido, max_tokens=config.MAX_TOKENS_PUNTAJE)
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
            g["naturaleza"] = (h.get("naturaleza") or "otro").strip().lower()
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
    """Devuelve (publicables, sin_confirmar, comunicados, descartados)."""
    orden = sorted(grupos, key=lambda g: (g["total"], g["puntos"]["antihype"]), reverse=True)
    # Sin modelo el puntaje es grueso: se baja el umbral y manda la verificación.
    umbral = config.UMBRAL_PUBLICABLE if any(not g.get("respaldo") for g in grupos) else 8
    estado = lambda g: g["verificacion"]["estado"]
    verificadas = [g for g in orden if estado(g) == "verificada"]
    publicables = [g for g in verificadas if g["total"] >= umbral]
    if len(publicables) < config.MINIMO_PUBLICABLES:
        extra = [g for g in verificadas if g not in publicables and g["total"] >= config.PISO_PUBLICABLE]
        publicables += extra[: config.MINIMO_PUBLICABLES - len(publicables)]
    publicables = publicables[: config.MAX_PUBLICABLES]
    # Lo sin confirmar que más interés despierta: se muestra para no esconderlo.
    sin_confirmar = [g for g in orden if estado(g) == "sin_confirmar" and g["total"] >= umbral - 2]
    sin_confirmar = sin_confirmar[: config.MAX_SIN_VERIFICAR]
    comunicados = [g for g in orden if estado(g) == "comunicado"][: config.MAX_COMUNICADOS]
    elegidos = {g["id"] for g in publicables + sin_confirmar + comunicados}
    # Descartados: los que más ruido hacían (más fuentes o más conversación) y no pasaron.
    resto = [g for g in grupos if g["id"] not in elegidos and not g.get("respaldo")]
    resto.sort(key=lambda g: (g["puntos"]["conversacion"], -g["puntos"]["antihype"]), reverse=True)
    descartados = [g for g in resto if g.get("descarte")][: config.MAX_DESCARTADOS]
    return publicables, sin_confirmar, comunicados, descartados


SISTEMA_NOTA_DIA = (
    config.VOZ_MUTUO
    + """
Sos el editor jefe. De las notas aprobadas, elegí LA que más importa hoy y escribí la postura del brief.
"tesis": 2 frases que dicen qué significa, no qué pasó. Una postura que se pueda discutir, sostenida en los datos de la nota.
La tesis NO repite el anuncio con otras palabras. Si la nota es un lanzamiento de una empresa, decí qué no dice el anuncio
(precio, resultados, a quién deja afuera) o qué tensión abre.
Preferí una nota con "cobertura_independiente": true.
MAL: "La nueva laptop permite ejecutar IA localmente y lleva la potencia a un dispositivo portátil."
BIEN: "Correr modelos en la propia máquina deja de ser cosa de laboratorio. Lo que nadie dijo todavía es cuánto cuesta."
"mirar": 1 frase con lo que conviene seguir en los próximos días (un dato que falta, una decisión pendiente).
Usá solo datos del material. Respondé SOLO con JSON: {"nota": "id", "tesis": "...", "mirar": "..."}"""
)


def _independiente(g):
    return any(i["tipo"] == "medio" for i in g["items"])


def nota_del_dia(publicables, cliente):
    if not publicables:
        return None
    from .fidelidad import material

    notas = [
        {"id": g["id"], "titular": g["titular"], "resumen": g["resumen"], "porque_importa": g["porque_importa"],
         "puntaje": g["total"], "fuente": material(g)[:500], "cobertura_independiente": _independiente(g)}
        for g in sorted(publicables, key=lambda g: (_independiente(g), g["total"]), reverse=True)[:5]
    ]
    try:
        datos = cliente.pedir_json(SISTEMA_NOTA_DIA, "Notas aprobadas:\n" + json.dumps(notas, ensure_ascii=False, indent=1), max_tokens=700)
    except SinModelo:
        return None
    if not isinstance(datos, dict):
        return None
    ids = {g["id"] for g in publicables}
    nid = datos.get("nota") if datos.get("nota") in ids else notas[0]["id"]
    # Regla del código: si hay alguna nota con cobertura independiente, la nota del día sale de ahí.
    if any(_independiente(g) for g in publicables) and not _independiente(next(g for g in publicables if g["id"] == nid)):
        return None
    tesis = str(datos.get("tesis") or "").strip()
    if not tesis:
        return None
    return {"nota": nid, "tesis": tesis, "mirar": str(datos.get("mirar") or "").strip()}


def redactar_piezas(publicables, cliente):
    if not publicables:
        return None
    from .fidelidad import material

    notas = [
        {
            "id": g["id"],
            "titular": g["titular"],
            "resumen": g["resumen"],
            "porque_importa": g["porque_importa"],
            "angulo": g["angulo"],
            "formato_sugerido": g["formato"],
            "fuente": material(g)[:600],
        }
        for g in publicables[:5]
    ]
    pedido = "Notas aprobadas del brief de hoy:\n" + json.dumps(notas, ensure_ascii=False, indent=1)
    try:
        datos = cliente.pedir_json(SISTEMA_PIEZAS, pedido, max_tokens=config.MAX_TOKENS_PIEZAS)
    except SinModelo:
        return None
    return datos if isinstance(datos, dict) else None
