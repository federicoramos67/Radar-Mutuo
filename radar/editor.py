"""El trabajo editorial: puntuar con la rúbrica, elegir y redactar las piezas."""

import json
import re

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


SISTEMA_AGRUPAR = """Sos editor de una mesa de noticias. Te paso pares de notas de distintas fuentes.
Para cada par, decidí si cuentan el MISMO hecho concreto: el mismo anuncio, dato, estudio, decisión o evento,
aunque lo cuenten desde ángulos distintos o con títulos distintos.
Que hablen de la misma empresa o del mismo tema NO alcanza.
Ejemplo SÍ: "X says its workforce is less junior" y "X casi dejó de contratar juniors": mismo dato de la misma empresa.
Ejemplo NO: "X lanza un modelo" y "X es demandada en Alemania": misma empresa, hechos distintos.
Respondé SOLO con JSON: {"mismos": ["h01|h07", "h03|h12"]} con los pares que SÍ son el mismo hecho. Si ninguno: {"mismos": []}"""

# Palabras con mayúscula que no son entidades.
_NO_ENTIDAD = {
    "how", "the", "why", "what", "new", "ai", "ia", "el", "la", "los", "las", "un", "una", "como", "cómo", "por",
    "this", "these", "its", "it", "a", "an", "in", "on", "es", "del", "de", "en", "y", "and", "with", "for", "to",
    "qué", "que", "así", "hoy", "más", "your", "you", "is", "are", "after", "now", "here",
}


def _entidades(titulo):
    """Nombres propios de un título: palabras con mayúscula que no son de relleno."""
    out = set()
    for tok in re.findall(r"[A-ZÁÉÍÓÚÑ][\w\-\.]*[\w]|[A-Z]{2,}", titulo or ""):
        t = tok.lower().strip(".")
        if t not in _NO_ENTIDAD and len(t) > 1:
            out.add(t)
    return out


def _pares_candidatos(grupos, maximo=30):
    """Pares de historias que comparten al menos una entidad. Se ordenan por cuántas comparten."""
    from .limpieza import palabras

    datos = [(g, _entidades(" ".join(i["titulo"] for i in g["items"])), palabras(g["principal"]["titulo"])) for g in grupos]
    pares = []
    for a in range(len(datos)):
        for b in range(a + 1, len(datos)):
            ga, ea, pa = datos[a]
            gb, eb, pb = datos[b]
            comunes = ea & eb
            if not comunes:
                continue
            fuentes_a = {i["fuente"] for i in ga["items"]}
            fuentes_b = {i["fuente"] for i in gb["items"]}
            if fuentes_a == fuentes_b and len(fuentes_a) == 1:
                continue  # dos notas de la misma fuente casi nunca son la misma noticia
            pares.append((len(comunes) + len(pa & pb), ga, gb))
    pares.sort(key=lambda x: x[0], reverse=True)
    return [(ga, gb) for _, ga, gb in pares[:maximo]]


def unir_por_modelo(grupos, cliente):
    """Junta historias que el agrupador por palabras no vio: el código propone pares, el modelo decide."""
    pares = _pares_candidatos(grupos)
    if not pares:
        return grupos

    def ficha(g):
        p = g["principal"]
        return f'[{p["fuente"]}] {p["titulo"]} — {p["resumen"][:160]}'

    pedido = [{"par": f'{a["id"]}|{b["id"]}', "a": ficha(a), "b": ficha(b)} for a, b in pares]
    try:
        datos = cliente.pedir_json(SISTEMA_AGRUPAR, "Pares:\n" + json.dumps(pedido, ensure_ascii=False, indent=1),
                                   max_tokens=600, temperatura=0.0)
    except SinModelo:
        return grupos
    validos = {p["par"] for p in pedido}
    padre = {g["id"]: g["id"] for g in grupos}

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for par in (datos.get("mismos") or []) if isinstance(datos, dict) else []:
        if not isinstance(par, str) or par not in validos:
            continue
        a, b = par.split("|")
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[rb] = ra
    por_id = {g["id"]: g for g in grupos}
    absorbidos = set()
    for g in grupos:
        r = raiz(g["id"])
        if r != g["id"]:
            por_id[r]["items"].extend(g["items"])
            absorbidos.add(g["id"])
    for g in grupos:
        if g["id"] not in absorbidos:
            # la fuente principal pasa a ser la de mayor jerarquía (oficial > medio > comunidad)
            g["items"].sort(key=lambda i: {"oficial": 0, "medio": 1, "comunidad": 2}[i["tipo"]])
            g["principal"] = g["items"][0]
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
            datos = cliente.pedir_json(SISTEMA_PUNTAJE, pedido, max_tokens=config.MAX_TOKENS_PUNTAJE, temperatura=0.0)
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
        # Regla del código: que dos redacciones independientes la cubran prueba que es un hecho
        # (señal) y que no es humo (antihype). El modelo puede subir esos ejes, no bajarlos de 3.
        if _medios_independientes(g) >= 2:
            g["puntos"]["senal"] = max(g["puntos"]["senal"], 3)
            g["puntos"]["antihype"] = max(g["puntos"]["antihype"], 3)
            g["corroborada"] = True
        g["total"] = sum(g["puntos"].values())
    return algun_lote_ok


def _medios_independientes(g):
    from .limpieza import dominio

    return len({dominio(i["link"]) for i in g["items"] if i["tipo"] == "medio"})


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
        datos = cliente.pedir_json(SISTEMA_NOTA_DIA, "Notas aprobadas:\n" + json.dumps(notas, ensure_ascii=False, indent=1), max_tokens=700, temperatura=0.4)
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
        datos = cliente.pedir_json(SISTEMA_PIEZAS, pedido, max_tokens=config.MAX_TOKENS_PIEZAS, temperatura=0.5)
    except SinModelo:
        return None
    return datos if isinstance(datos, dict) else None
