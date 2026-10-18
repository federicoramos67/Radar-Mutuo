"""Arma la página HTML del brief. Un solo archivo, sin JavaScript, liviano en el celular."""

from html import escape

from . import config

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
NOMBRE_FORMATO = {"reel": "reel", "carrusel": "carrusel", "post": "post", "hilo": "hilo", "agenda": "agenda", "streaming": "guion de streaming"}


def fecha_larga(d):
    return f"{DIAS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]} de {d.year}"


def e(texto):
    return escape(str(texto or ""), quote=True)


CSS = """
:root{--bg:#F4F5F7;--surface:#FFFFFF;--ink:#14161B;--muted:#5A6271;--rule:#DCDFE6;--rule-soft:#E9EBF0;
--accent:#8E3B5E;--ok:#2E6F4E;--warn:#8A6100;--warn-soft:#FBF1D9;--off:#C7CBD4;
--display:"Newsreader",Georgia,"Times New Roman",serif;--body:"Source Sans 3",system-ui,-apple-system,"Segoe UI",sans-serif;
--mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#101217;--surface:#171A21;--ink:#E8EAEF;--muted:#99A1B0;
--rule:#262A33;--rule-soft:#1F232B;--accent:#E489AC;--ok:#63BE8E;--warn:#D9AE3F;--warn-soft:#2A2314;--off:#333845;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#101217;--surface:#171A21;--ink:#E8EAEF;--muted:#99A1B0;--rule:#262A33;--rule-soft:#1F232B;
--accent:#E489AC;--ok:#63BE8E;--warn:#D9AE3F;--warn-soft:#2A2314;--off:#333845;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6;margin:0;padding:0 16px 64px}
.wrap{max-width:720px;margin:0 auto}
a{color:inherit;text-decoration-color:var(--rule);text-underline-offset:3px}
a:hover{text-decoration-color:var(--accent)}
header{border-bottom:2px solid var(--ink);padding-block:40px 18px}
.kicker,.tag,.lab,.num,.dateline,.tally,.fmt,.from,.stamp,.score-chip,.src,.script dt{font-family:var(--mono)}
.kicker{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 10px}
h1{font-family:var(--display);font-weight:600;font-size:clamp(2.1rem,7vw,3.1rem);line-height:1.05;letter-spacing:-.02em;margin:0}
.dateline{font-size:12.5px;color:var(--muted);margin:10px 0 0}
.tally{display:flex;flex-wrap:wrap;gap:0 22px;list-style:none;padding:0;margin:18px 0 0;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.tally b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
.standfirst{font-family:var(--display);font-size:1.18rem;line-height:1.5;color:var(--muted);border-bottom:1px solid var(--rule);padding-block:22px 26px;margin:0;max-width:60ch}
.aviso{background:var(--warn-soft);border-left:3px solid var(--warn);padding:14px 18px;margin:24px 0 0;font-size:15px}
article{border-bottom:1px solid var(--rule);padding-block:34px}
.head{display:grid;grid-template-columns:auto 1fr;gap:0 16px;align-items:start}
.num{font-size:12px;font-weight:600;color:var(--accent);padding-top:.45em;letter-spacing:.06em}
h2{font-family:var(--display);font-weight:600;font-size:clamp(1.4rem,4.4vw,1.85rem);line-height:1.18;letter-spacing:-.015em;margin:0;text-wrap:balance;min-width:0}
.scores{display:flex;flex-wrap:wrap;gap:14px 20px;margin:16px 0 20px;padding-block:12px;border-top:1px solid var(--rule-soft);border-bottom:1px solid var(--rule-soft)}
.lab{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.bars{display:flex;gap:3px;align-items:center}
.seg{width:13px;height:7px;background:var(--off);border-radius:1px}
.seg.on{background:var(--accent)}
.metric.flag .seg.on{background:var(--warn)}
.val{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--muted);margin-left:5px;font-variant-numeric:tabular-nums}
.total{margin-left:auto;align-self:center;font-family:var(--mono);font-size:13px;font-weight:600;font-variant-numeric:tabular-nums}
.total span{color:var(--muted);font-weight:400}
p{margin:0 0 1em;max-width:62ch}
.tag{font-size:10.5px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;color:var(--accent);display:block;margin-bottom:4px}
.angle{background:var(--surface);border-left:3px solid var(--accent);padding:16px 18px;margin-top:20px}
.angle .line{font-family:var(--display);font-size:1.12rem;font-weight:600;margin:0;max-width:62ch}
.srcs{list-style:none;padding:0;margin:18px 0 0;display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px}
.src{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-right:4px}
.ok{color:var(--ok)}
article.unverified{background:var(--warn-soft);border-left:3px solid var(--warn);padding-inline:18px;margin-block:34px;border-bottom:none}
.stamp{display:inline-block;font-size:10.5px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--warn);border:1px solid var(--warn);border-radius:2px;padding:3px 8px;margin-bottom:12px}
article.unverified .num,article.unverified .tag{color:var(--warn)}
article.unverified .seg.on{background:var(--warn)}
h3{font-family:var(--display);font-size:1.5rem;font-weight:600;letter-spacing:-.01em;margin:0 0 6px}
section{padding-block:36px;border-bottom:1px solid var(--rule)}
.piece{border-top:1px solid var(--rule-soft);padding-block:26px}
.piece:first-of-type{border-top:none;padding-top:20px}
.piece-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px;margin-bottom:14px}
.fmt{font-size:10.5px;font-weight:600;letter-spacing:.11em;text-transform:uppercase;color:var(--surface);background:var(--accent);border-radius:2px;padding:3px 8px}
.from{font-size:11px;color:var(--muted);letter-spacing:.04em}
.piece h4{font-family:var(--display);font-size:1.2rem;font-weight:600;margin:0;width:100%;text-wrap:balance}
.script{display:grid;grid-template-columns:auto 1fr;gap:10px 16px;margin:0;font-size:15px}
.script dt{font-size:11.5px;font-weight:600;color:var(--accent);padding-top:.3em;white-space:nowrap}
.script dd{margin:0;min-width:0}
.onscreen{display:block;font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:3px}
.slides{padding-left:1.4em;margin:0;display:grid;gap:10px}
.slides li::marker{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--accent)}
.draft{background:var(--surface);border:1px solid var(--rule);padding:18px;margin:0;font-size:15.5px;white-space:pre-line;max-width:62ch}
.qs{margin:0;padding-left:1.1em;max-width:62ch}
.qs li{margin-bottom:.5em}
.cut-list{list-style:none;padding:0;margin:22px 0 0;display:grid;gap:16px}
.cut-list li{display:grid;grid-template-columns:1fr auto;gap:4px 16px;align-items:baseline;padding-bottom:16px;border-bottom:1px solid var(--rule-soft)}
.cut-list li:last-child{border-bottom:none;padding-bottom:0}
.what{font-weight:600;min-width:0}
.why{grid-column:1/-1;color:var(--muted);font-size:15px;max-width:62ch}
.score-chip{font-size:10.5px;font-weight:600;letter-spacing:.06em;color:var(--muted);white-space:nowrap;border:1px solid var(--rule);border-radius:2px;padding:2px 7px}
footer{padding-block:34px;color:var(--muted);font-size:14.5px}
footer .tag{color:var(--muted)}
.estado{list-style:none;padding:0;margin:0 0 1em;font-size:13.5px;columns:2;column-gap:24px}
.estado li{break-inside:avoid}
.archivo{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:6px 14px;font-family:var(--mono);font-size:12.5px}
.lead{background:var(--ink);color:var(--bg);padding:26px 24px 24px;margin:30px 0 4px}
.lead .tag{color:var(--accent)}
.lead h2{color:var(--bg);margin:6px 0 14px}
.lead .tesis{font-family:var(--display);font-size:1.28rem;line-height:1.45;margin:0 0 14px;max-width:60ch}
.lead .mirar{font-size:15px;opacity:.8;margin:0}
.lead a{color:inherit}
.fid{font-family:var(--mono);font-size:11.5px;letter-spacing:.04em;margin:14px 0 0;max-width:62ch}
.fid.ok{color:var(--ok)}
.fid.warn{color:var(--warn)}
.fid li{margin:4px 0 0 1.1em}
.com-list{list-style:none;padding:0;margin:20px 0 0;display:grid;gap:14px}
.com-list li{border-left:3px solid var(--off);padding:2px 0 2px 14px}
.com-list .what{display:block}
.com-list .why{display:block;color:var(--muted);font-size:14.5px;grid-column:auto}
@media (max-width:460px){.head{grid-template-columns:1fr;gap:6px}.num{padding-top:0}.total{margin-left:0;width:100%}.estado{columns:1}}
"""


def _barras(n, flag=False):
    segs = "".join(f'<i class="seg{" on" if s <= n else ""}"></i>' for s in range(1, 6))
    return f'<div class="bars">{segs}<span class="val">{n}/5</span></div>'


def _medidores(g):
    partes = []
    for clave, nombre, _ in config.EJES:
        n = g["puntos"][clave]
        flag = clave == "antihype" and n <= 1
        partes.append(f'<div class="metric{" flag" if flag else ""}"><span class="lab">{nombre}</span>{_barras(n)}</div>')
    partes.append(f'<div class="total">{g["total"]}<span>/{config.PUNTAJE_MAXIMO}</span></div>')
    return f'<div class="scores">{"".join(partes)}</div>'


def _fuentes(g):
    items = []
    for f in g["verificacion"]["fuentes"]:
        items.append(f'<li><span class="src">{e(f["tipo"])}</span><a href="{e(f["link"])}" rel="noopener">{e(f["nombre"])}</a></li>')
    return f'<ul class="srcs">{"".join(items)}</ul>'


def _alertas(alertas, titulo):
    items = "".join(f"<li>{e(a['detalle'])}</li>" for a in alertas[:4])
    return f'<div class="fid warn">⚠ {e(titulo)}:<ul>{items}</ul></div>'


def _nota(g, numero, pendientes=None):
    sin = g["verificacion"]["estado"] != "verificada"
    clase = ' class="unverified"' if sin else ""
    sello = '<span class="stamp">Sin confirmar · no se publica</span>' if sin else ""
    cuerpo = [f"<p>{e(g['resumen'])}</p>"] if g.get("resumen") else []
    if g.get("porque_importa"):
        cuerpo.append(f'<p><span class="tag">Por qué importa</span>{e(g["porque_importa"])}</p>')
    estado_tag = "Qué falta" if sin else "Verificación"
    clase_estado = "" if sin else ' class="ok"'
    cuerpo.append(f'<p><span class="tag">{estado_tag}</span><span{clase_estado}>{e(g["verificacion"]["motivo"])}</span></p>')
    alertas = [a for a in (pendientes or []) if a["donde"].startswith(f"nota:{g['id']}:")]
    if alertas:
        cuerpo.append(_alertas(alertas, "Dato a revisar antes de publicar"))
    angulo = ""
    if g.get("angulo") and not sin:
        angulo = (
            f'<div class="angle"><span class="tag">Ángulo · {e(NOMBRE_FORMATO.get(g["formato"], g["formato"]))}</span>'
            f'<p class="line">{e(g["angulo"])}</p></div>'
        )
    elif sin:
        angulo = '<div class="angle" style="background:transparent;border:none;padding-left:0"><span class="tag">Decisión</span><p>Queda en observación. Entra al brief cuando aparezca la fuente original o una segunda fuente independiente.</p></div>'
    return (
        f"<article{clase}>{sello}<div class=\"head\"><span class=\"num\">{numero:02d}</span>"
        f"<h2>{e(g['titular'] or g['principal']['titulo'])}</h2></div>{_medidores(g)}"
        f"{''.join(cuerpo)}{angulo}{_fuentes(g)}</article>"
    )


def _desde(ids, numeros):
    nums = [f"{numeros[i]:02d}" for i in ids if i in numeros]
    if not nums:
        return ""
    return ("de la nota " if len(nums) == 1 else "de las notas ") + ", ".join(nums)


def _piezas(piezas, numeros, informe=None):
    if not piezas:
        return ""
    bloques = []
    reel = piezas.get("reel") or {}
    if reel.get("beats"):
        filas = "".join(
            f'<dt>{e(b.get("t"))}</dt><dd>{e(b.get("texto"))}'
            + (f'<span class="onscreen">En pantalla: {e(b.get("pantalla"))}</span>' if b.get("pantalla") else "")
            + "</dd>"
            for b in reel["beats"]
            if isinstance(b, dict)
        )
        bloques.append(("Reel · 40s", [reel.get("nota")], reel.get("titulo"), f'<dl class="script">{filas}</dl>'))
    carr = piezas.get("carrusel") or {}
    if carr.get("placas"):
        placas = "".join(f"<li>{e(p)}</li>" for p in carr["placas"])
        bloques.append((f"Carrusel · {len(carr['placas'])} placas", [carr.get("nota")], carr.get("titulo"), f'<ol class="slides">{placas}</ol>'))
    post = piezas.get("post") or {}
    if post.get("texto"):
        bloques.append(("Post · LinkedIn", [post.get("nota")], post.get("titulo"), f'<p class="draft">{e(post["texto"])}</p>'))
    hilo = piezas.get("hilo") or {}
    if hilo.get("partes"):
        texto = "\n\n↓\n\n".join(str(p) for p in hilo["partes"])
        bloques.append(("Hilo · Threads", [hilo.get("nota")], hilo.get("titulo"), f'<p class="draft">{e(texto)}</p>'))
    oc = piezas.get("opencast") or {}
    if oc.get("preguntas"):
        qs = "".join(f"<li>{e(q)}</li>" for q in oc["preguntas"])
        bloques.append(("Opencast", oc.get("notas") or [], "Preguntas para el streaming", f'<ol class="qs">{qs}</ol>'))
    claves = {"Reel · 40s": "reel", "Post · LinkedIn": "post", "Hilo · Threads": "hilo", "Opencast": "opencast"}
    html = []
    for fmt, ids, titulo, cuerpo in bloques:
        clave = claves.get(fmt) or ("carrusel" if fmt.startswith("Carrusel") else "")
        sello = ""
        if informe is not None:
            pend = [a for a in informe.get("pendientes", []) if a["donde"] == f"pieza:{clave}"]
            sello = _alertas(pend, "Revisar antes de publicar") if pend else '<p class="fid ok">✓ Control de fidelidad: cada cifra está en la fuente.</p>'
        html.append(
            f'<div class="piece"><div class="piece-head"><span class="fmt">{e(fmt)}</span>'
            f'<span class="from">{e(_desde(ids, numeros))}</span><h4>{e(titulo)}</h4></div>{cuerpo}{sello}</div>'
        )
    return (
        '<section><h3>De la nota a la pieza</h3><p>Borradores listos para revisar. Detectar es la mitad del trabajo; '
        "esta es la otra mitad. Nada sale sin que una persona lo apruebe.</p>" + "".join(html) + "</section>"
    )


def _comunicados(lista):
    if not lista:
        return ""
    items = []
    for g in lista:
        f = g["verificacion"]["fuentes"][0]
        items.append(
            f'<li><span class="what"><a href="{e(f["link"])}" rel="noopener">{e(g["titular"] or g["principal"]["titulo"])}</a></span>'
            f'<span class="why">{e(g["verificacion"]["motivo"])}</span></li>'
        )
    return (
        "<section><h3>Comunicados de empresas</h3><p>Es cierto que lo anunciaron. Que sea noticia es otra cosa: "
        f'entran al brief cuando un medio independiente los cubra.</p><ul class="com-list">{"".join(items)}</ul></section>'
    )


def _nota_dia(nd, publicables, numeros, pendientes):
    if not nd:
        return ""
    g = next((x for x in publicables if x["id"] == nd["nota"]), None)
    if not g:
        return ""
    alertas = [a for a in pendientes if a["donde"] == "nota_dia"]
    extra = _alertas(alertas, "Revisar") if alertas else ""
    mirar = f'<p class="mirar"><b>Para seguir:</b> {e(nd["mirar"])}</p>' if nd.get("mirar") else ""
    return (
        f'<section class="lead"><span class="tag">Lo que importa hoy · nota {numeros.get(g["id"], 1):02d}</span>'
        f'<h2>{e(g["titular"] or g["principal"]["titulo"])}</h2><p class="tesis">{e(nd["tesis"])}</p>{mirar}{extra}</section>'
    )


def _descartados(lista):
    if not lista:
        return ""
    items = []
    for g in lista:
        eje = min(config.EJES, key=lambda x: g["puntos"][x[0]])
        items.append(
            f'<li><span class="what">{e(g["titular"] or g["principal"]["titulo"])}</span>'
            f'<span class="score-chip">{e(eje[1])} {g["puntos"][eje[0]]}</span>'
            f'<span class="why">{e(g["descarte"])}</span></li>'
        )
    return (
        "<section><h3>Descartados, y por qué</h3><p>Lo que más ruido hacía y no pasó la rúbrica. "
        f'Decir que no también es trabajo editorial.</p><ul class="cut-list">{"".join(items)}</ul></section>'
    )


def _pie_fidelidad(informe):
    if not informe:
        return ""
    pend = len(informe.get("pendientes", []))
    extra = "" if informe.get("revision_modelo") else " La segunda lectura con el modelo no respondió hoy: solo se aplicó el control de cifras."
    return (
        f'<p><span class="tag">Control de fidelidad</span>Cada cifra de lo redactado se compara con el texto de su fuente, '
        f'y una segunda lectura busca afirmaciones que la fuente no sostiene. Hoy: {informe["detectadas"]} problemas detectados, '
        f'{informe["corregidas"]} corregidos antes de publicar, {pend} marcados para revisión humana.{extra}</p>'
    )


def render(edicion, raiz=""):
    """edicion: dict con fecha, publicables, sin_confirmar, descartados, piezas, estado_fuentes, etc."""
    pub, sinc, desc = edicion["publicables"], edicion["sin_confirmar"], edicion["descartados"]
    com = edicion.get("comunicados") or []
    informe = edicion.get("fidelidad")
    pendientes = (informe or {}).get("pendientes", [])
    numeros, notas, n = {}, [], 1
    # La primera nota sin confirmar va después de la mejor publicable, como en una mesa de edición real.
    orden = pub[:1] + sinc + pub[1:]
    for g in orden:
        numeros[g["id"]] = n
        notas.append(_nota(g, n, pendientes))
        n += 1

    ok = [f for f in edicion["estado_fuentes"] if f["ok"]]
    caidas = [f for f in edicion["estado_fuentes"] if not f["ok"]]
    estado = "".join(
        f'<li>{"✓" if f["ok"] else "✗"} {e(f["nombre"])}'
        + (f' · {f["items"]}' if f["ok"] else " · no respondió")
        + "</li>"
        for f in edicion["estado_fuentes"]
    )

    aviso = ""
    if "falta la key" in (edicion.get("errores_modelo") or []):
        aviso = (
            '<p class="aviso">Falta configurar la key del modelo de lenguaje. Este brief se armó con el puntaje de respaldo, '
            "sin redacción ni piezas. La verificación de fuentes sí funcionó, porque no depende del modelo.</p>"
        )
    elif not edicion["con_modelo"]:
        aviso = (
            '<p class="aviso">Hoy el modelo de lenguaje no respondió. Este brief se armó con el puntaje de respaldo, '
            "sin redacción ni piezas. La verificación de fuentes sí funcionó, porque no depende del modelo.</p>"
        )
    if not notas:
        notas.append("<article><p>Hoy no hubo historias que pasaran la rúbrica y la verificación. También es una respuesta.</p></article>")

    archivo = ""
    if edicion.get("archivo"):
        links = "".join(f'<li><a href="{raiz}ediciones/{e(d)}.html">{e(d)}</a></li>' for d in edicion["archivo"][:30])
        archivo = f'<p><span class="tag">Ediciones anteriores</span></p><ul class="archivo">{links}</ul>'

    modelos = ", ".join(edicion.get("modelos") or []) or "ninguno (modo respaldo)"
    f = edicion["fecha"]
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar Mutuo · {e(f.strftime('%d/%m/%Y'))}</title>
<meta name="description" content="Brief editorial diario de IA: detectado, puntuado y verificado automáticamente.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=Source+Sans+3:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header>
<p class="kicker">Brief editorial · Canal Mutuo</p>
<h1>Radar</h1>
<p class="dateline">{e(fecha_larga(f))} · cierre {e(f.strftime('%H:%M'))} · Montevideo</p>
<ul class="tally">
<li><b>{edicion['revisados']}</b> revisados</li>
<li><b>{len(pub)}</b> publicables</li>
<li><b>{len(sinc)}</b> sin confirmar</li>
<li><b>{len(com)}</b> comunicados</li>
<li><b>{len(desc)}</b> descartados con causa</li>
</ul>
</header>
<p class="standfirst">Cada nota entra con su puntaje a la vista y su estado de verificación declarado. Lo que no se pudo confirmar no se esconde: se muestra marcado. Lo que solo dijo una empresa va aparte. Y cada texto redactado se controla contra su fuente.</p>
{aviso}
{_nota_dia(edicion.get('nota_dia'), pub, numeros, pendientes)}
{''.join(notas)}
{_piezas(edicion.get('piezas'), numeros, informe)}
{_comunicados(com)}
{_descartados(desc)}
<footer>
<p><span class="tag">Cómo se armó</span>{edicion['revisados']} items de {len(ok)} fuentes, agrupados en {edicion['historias']} historias. Puntuados con una rúbrica de cuatro ejes —señal, impacto, conversación, antihype—. La verificación la decide el código, no el modelo: dos medios independientes, o fuente primaria con datos concretos. Modelo usado: {e(modelos)}.</p>
{_pie_fidelidad(informe)}
<p>La máquina ordena, puntúa y justifica. Las decisiones editoriales y la redacción final son humanas.</p>
<p><span class="tag">Estado de las fuentes</span></p>
<ul class="estado">{estado}</ul>
{f'<p>{len(caidas)} fuente(s) no respondieron hoy. El brief se armó con las demás.</p>' if caidas else ''}
{archivo}
<p>Código abierto: <a href="https://github.com/federicoramos67/radar-mutuo">github.com/federicoramos67/radar-mutuo</a> · Hecho por Federico Ramos.</p>
</footer>
</div>
</body>
</html>
"""
