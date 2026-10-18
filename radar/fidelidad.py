"""Control de fidelidad: que lo redactado diga solo lo que dicen las fuentes.

Verificar que una noticia existe no alcanza. También hay que controlar que el
texto que redactamos no le agregue datos. Esto se hace en tres capas:

  1. Números (código): cada cifra, porcentaje o multiplicador del texto tiene
     que aparecer en el material de la fuente. Es una regla mecánica y no se
     puede convencer.
  2. Frases de folleto (código): expresiones de hype y regionalismo forzado.
  3. Afirmaciones (modelo): una segunda lectura busca afirmaciones de hecho que
     la fuente no sostiene. El modelo marca; no decide solo.

Lo marcado se manda a corregir una vez. Lo que sigue marcado después de
corregir queda visible en la página como "a revisar".
"""

import json
import re
import unicodedata

from .modelo import SinModelo

# --- Normalización -----------------------------------------------------------


def _plano(texto):
    t = unicodedata.normalize("NFKD", str(texto or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


# Multiplicadores escritos con palabras: lo que suele inventarse en un titular.
MULTIPLICADORES = {
    "duplica": "2", "duplico": "2", "doble": "2", "dos veces": "2",
    "triplica": "3", "triplico": "3", "triple": "3", "tres veces": "3",
    "cuadruplica": "4", "cuatro veces": "4", "cinco veces": "5",
    "diez veces": "10", "cien veces": "100", "mil veces": "1000",
    "la mitad": "0.5", "a la mitad": "0.5", "un tercio": "0.33", "un cuarto": "0.25",
}
# Cómo puede aparecer ese mismo dato en una fuente en inglés o español.
EQUIVALENTES = {
    "2": ["2", "two", "double", "doubl", "twice", "dos", "doble", "duplic"],
    "3": ["3", "three", "triple", "tripl", "tres"],
    "4": ["4", "four", "quadrupl", "cuatro", "cuadrupl"],
    "5": ["5", "five", "cinco"],
    "10": ["10", "ten", "tenfold", "diez"],
    "100": ["100", "hundred", "cien"],
    "1000": ["1000", "1,000", "1.000", "thousand", "mil"],
    "0.5": ["half", "halv", "mitad", "50%", "50 %", "50 percent"],
    "0.33": ["third", "tercio", "33%"],
    "0.25": ["quarter", "cuarto", "25%"],
}

_NUMERO = re.compile(r"(?<![\w.])(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(%|x\b)?", re.I)


def _canon(n):
    """'1.000' y '1,000' → '1000'; '3,5' → '3.5'."""
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", n):
        return re.sub(r"[.,]", "", n)
    return n.replace(",", ".")


def numeros(texto):
    """Cifras y multiplicadores de un texto, normalizados."""
    plano = _plano(texto)
    hallados = {_canon(m.group(1)) for m in _NUMERO.finditer(plano)}
    for palabra, valor in MULTIPLICADORES.items():
        if re.search(rf"\b{palabra}\b", plano):
            hallados.add(valor)
    return hallados


def _en_fuente(numero, fuente_plana, numeros_fuente):
    if numero in numeros_fuente:
        return True
    for forma in EQUIVALENTES.get(numero, []):
        if re.search(rf"(?<![\w]){re.escape(forma)}", fuente_plana):
            return True
    return False


def cifras_sin_fuente(texto, fuente):
    fp = _plano(fuente)
    nf = numeros(fuente)
    return sorted(n for n in numeros(texto) if not _en_fuente(n, fp, nf))


# --- Frases de folleto -------------------------------------------------------

FOLLETO = [
    "revolucion", "revoluciona", "cambia todo", "cambiara todo", "sin precedentes", "game changer",
    "increible", "impresionante", "lo nunca visto", "llego para quedarse", "el futuro ya llego",
    "promete revolucionar", "a otro nivel", "disruptiv",
    # llamados a la acción de folleto
    "descubri mas", "descubre mas", "conoce mas", "conoci mas", "no te lo pierdas", "segui leyendo",
    "visita la web", "en la web de", "link en la bio", "seguinos",
]
REGION = ["urugua", "latinoameric", "america latina", "la region", "regional", "montevideo"]
REGION_FUENTE = REGION + [
    "latin america", "latam", "brasil", "brazil", "argentin", "chile", "mexic", "colombia",
    "peru", "uruguay", "sudamerica", "south america", "spanish", "espanol",
]


def folleto(texto):
    p = _plano(texto)
    return [f for f in FOLLETO if f in p]


def region_forzada(texto, fuente):
    """Menciona la región sin que la fuente tenga nada regional."""
    p, fp = _plano(texto), _plano(fuente)
    return any(r in p for r in REGION) and not any(r in fp for r in REGION_FUENTE)


# --- Material de cada nota ---------------------------------------------------


def material(grupo):
    """Todo lo que dicen las fuentes de una historia: es contra lo que se compara."""
    partes = []
    for i in grupo["items"]:
        partes.append(f'[{i["fuente"]}] {i["titulo"]}. {i["resumen"]}')
    return "\n".join(partes)


def _textos_pieza(nombre, pieza):
    """Los textos de una pieza que pueden contener afirmaciones."""
    if not isinstance(pieza, dict):
        return []
    if nombre == "reel":
        out = [pieza.get("titulo", "")]
        for b in pieza.get("beats") or []:
            if isinstance(b, dict):
                out += [b.get("texto", ""), b.get("pantalla", "")]
        return out
    if nombre == "carrusel":
        return [pieza.get("titulo", "")] + [str(p) for p in pieza.get("placas") or []]
    if nombre == "post":
        return [pieza.get("titulo", ""), pieza.get("texto", "")]
    if nombre == "hilo":
        return [pieza.get("titulo", "")] + [str(p) for p in pieza.get("partes") or []]
    if nombre == "opencast":
        return [str(p) for p in pieza.get("preguntas") or []]
    return []


def _ids_pieza(nombre, pieza):
    if nombre == "opencast":
        return [i for i in (pieza.get("notas") or []) if isinstance(i, str)]
    return [pieza.get("nota")] if isinstance(pieza.get("nota"), str) else []


def _fuente_de(ids, por_id, todas):
    elegidas = [por_id[i] for i in ids if i in por_id] or todas
    return "\n".join(material(g) for g in elegidas)


# --- Revisión mecánica -------------------------------------------------------


def revisar_mecanico(publicables, piezas, nota_dia=None):
    """Devuelve alertas: [{"donde": ..., "tipo": ..., "detalle": ...}]."""
    por_id = {g["id"]: g for g in publicables}
    alertas = []

    def chequear(donde, texto, fuente):
        for n in cifras_sin_fuente(texto, fuente):
            alertas.append({"donde": donde, "tipo": "cifra", "detalle": f"«{n}» no aparece en la fuente"})
        for f in folleto(texto):
            alertas.append({"donde": donde, "tipo": "folleto", "detalle": f"frase de folleto: «{f}»"})

    for g in publicables:
        fuente = material(g)
        for campo in ("titular", "resumen", "porque_importa", "angulo"):
            chequear(f"nota:{g['id']}:{campo}", g.get(campo, ""), fuente)
        if region_forzada(g.get("porque_importa", ""), fuente):
            alertas.append({"donde": f"nota:{g['id']}:porque_importa", "tipo": "region",
                            "detalle": "ángulo regional que la fuente no sostiene"})
    for nombre, pieza in (piezas or {}).items():
        if not isinstance(pieza, dict):
            continue
        fuente = _fuente_de(_ids_pieza(nombre, pieza), por_id, publicables)
        chequear(f"pieza:{nombre}", " \n".join(_textos_pieza(nombre, pieza)), fuente)
    if nota_dia:
        g = por_id.get(nota_dia.get("nota"))
        if g:
            chequear("nota_dia", f'{nota_dia.get("tesis", "")} {nota_dia.get("mirar", "")}', material(g))
    # sin duplicados, en orden
    vistos, unicas = set(), []
    for a in alertas:
        k = (a["donde"], a["detalle"])
        if k not in vistos:
            vistos.add(k)
            unicas.append(a)
    return unicas


# --- Revisión y corrección con el modelo -------------------------------------

SISTEMA_REVISAR = """Sos verificador de datos de una redacción. Comparás textos redactados contra el material de sus fuentes.
Marcá SOLO afirmaciones de hecho (qué pasó, quién, cuánto, cuándo, qué hace un producto) que el material NO sostiene.
No marques opiniones, preguntas, interpretaciones, recomendaciones ni consecuencias planteadas como posibilidad.
Ejemplos que NO se marcan: "conviene revisar…", "si tu empresa usa…", "para quien edita, esto implica…", "¿qué harías…?".
Ejemplos que SÍ se marcan: una cifra, un porcentaje, un nombre, una fecha, un "redujo a la mitad", o que la empresa "anunció" algo que no figura.
Ante la duda, no marques. Respondé SOLO con JSON:
{"alertas": [{"donde": "pieza:post", "frase": "fragmento exacto", "problema": "qué no está en la fuente"}]}
Si no hay problemas: {"alertas": []}"""

SISTEMA_CORREGIR = """Sos editor. Te paso textos redactados, el material de sus fuentes y una lista de problemas detectados.
Reescribí SOLO lo necesario para resolver cada problema: sacá el dato que no está en la fuente o reemplazalo por lo que la fuente sí dice.
Si se marca un ángulo regional sin sustento, reemplazalo por la consecuencia concreta para quien trabaja con esto, sin nombrar la región.
Si se marca una frase de folleto, reescribila llana.
Mantené el voseo, el tono y la misma estructura JSON exacta que recibiste. No agregues datos nuevos.
Respondé SOLO con JSON: {"notas": {"id": {"titular": "...", "resumen": "...", "porque_importa": "...", "angulo": "..."}}, "piezas": {...mismas claves...}, "nota_dia": {...o null}}"""


def _paquete(publicables, piezas, nota_dia):
    notas = {g["id"]: {k: g.get(k, "") for k in ("titular", "resumen", "porque_importa", "angulo")} for g in publicables}
    fuentes = {g["id"]: material(g)[:900] for g in publicables}
    return {"fuentes_por_nota": fuentes, "notas": notas, "piezas": piezas or {}, "nota_dia": nota_dia}


CONSEJO = ["conviene", "si tu", "si sos", "si trabajas", "si editas", "si programas", "para quien", "para un", "para una",
           "para los", "para las", "eso significa", "esto significa", "esto implica", "eso implica", "podes",
           "deberias", "deberia", "debera", "convendria", "vale la pena", "tenes que", "?", "¿"]


def revisar_modelo(publicables, piezas, nota_dia, cliente):
    paquete = _paquete(publicables, piezas, nota_dia)
    try:
        datos = cliente.pedir_json(SISTEMA_REVISAR, json.dumps(paquete, ensure_ascii=False), max_tokens=1200, temperatura=0.0)
    except SinModelo:
        return None
    out = []
    for a in (datos.get("alertas") or []) if isinstance(datos, dict) else []:
        frase = _plano(a.get("frase", "") if isinstance(a, dict) else "")
        # Regla del código: una recomendación o una pregunta no es una afirmación de hecho.
        if any(frase.startswith(m) or f" {m} " in f" {frase[:40]} " for m in CONSEJO):
            continue
        if isinstance(a, dict) and a.get("donde"):
            out.append({"donde": str(a["donde"]), "tipo": "afirmacion",
                        "detalle": f'«{str(a.get("frase", ""))[:120]}»: {str(a.get("problema", ""))[:160]}'})
    return out


def corregir(publicables, piezas, nota_dia, alertas, cliente):
    """Una pasada de corrección. Aplica solo campos que vuelven con el tipo esperado."""
    if not alertas:
        return piezas, nota_dia
    paquete = _paquete(publicables, piezas, nota_dia)
    paquete["problemas"] = alertas
    try:
        datos = cliente.pedir_json(SISTEMA_CORREGIR, json.dumps(paquete, ensure_ascii=False), max_tokens=3200, temperatura=0.1)
    except SinModelo:
        return piezas, nota_dia
    if not isinstance(datos, dict):
        return piezas, nota_dia
    por_id = {g["id"]: g for g in publicables}
    for nid, campos in (datos.get("notas") or {}).items():
        g = por_id.get(nid)
        if g and isinstance(campos, dict):
            for k in ("titular", "resumen", "porque_importa", "angulo"):
                if isinstance(campos.get(k), str) and campos[k].strip():
                    g[k] = campos[k].strip()
    nuevas = datos.get("piezas")
    if isinstance(nuevas, dict) and piezas:
        for nombre, original in list(piezas.items()):
            cand = nuevas.get(nombre)
            if isinstance(cand, dict) and set(original) <= set(cand) | {"nota", "notas"}:
                cand.setdefault("nota", original.get("nota"))
                if "notas" in original:
                    cand.setdefault("notas", original.get("notas"))
                piezas[nombre] = cand
    nd = datos.get("nota_dia")
    if nota_dia and isinstance(nd, dict) and isinstance(nd.get("tesis"), str):
        nota_dia = {**nota_dia, "tesis": nd["tesis"].strip(), "mirar": str(nd.get("mirar") or nota_dia.get("mirar", "")).strip()}
    return piezas, nota_dia


def controlar(publicables, piezas, nota_dia, cliente):
    """Revisa, corrige una vez y vuelve a revisar. Devuelve (piezas, nota_dia, informe)."""
    antes = revisar_mecanico(publicables, piezas, nota_dia)
    del_modelo = revisar_modelo(publicables, piezas, nota_dia, cliente) if cliente.disponible else None
    a_corregir = antes + (del_modelo or [])
    if a_corregir and cliente.disponible:
        piezas, nota_dia = corregir(publicables, piezas, nota_dia, a_corregir, cliente)
    despues = revisar_mecanico(publicables, piezas, nota_dia)
    # Lo que el modelo marcó y no se pudo confirmar como resuelto queda a la vista si la
    # frase exacta sigue en el texto.
    textos = json.dumps({"p": piezas, "n": nota_dia, "g": [{k: g.get(k) for k in ("titular", "resumen", "porque_importa", "angulo")} for g in publicables]}, ensure_ascii=False)
    for a in del_modelo or []:
        frase = re.search(r"«(.+?)»", a["detalle"])
        if frase and len(frase.group(1)) > 12 and frase.group(1) in textos:
            despues.append(a)
    informe = {
        "detectadas": len(a_corregir),
        "corregidas": max(0, len(a_corregir) - len(despues)),
        "pendientes": despues,
        "revision_modelo": del_modelo is not None,
    }
    return piezas, nota_dia, informe
