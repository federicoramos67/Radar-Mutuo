"""Corre una edición completa del Radar:  python -m radar

Pasos: leer fuentes → filtrar → agrupar → verificar → puntuar → separar
comunicados → elegir → nota del día → redactar piezas → control de fidelidad →
publicar la página y guardar los datos del día.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config, editor, fidelidad, fuentes, limpieza, pagina
from .modelo import Cliente
from .verificacion import reclasificar, verificar

SALIDA = Path(__file__).resolve().parent.parent / "docs"


def _serializable(g):
    return {
        "id": g["id"],
        "titular": g.get("titular"),
        "resumen": g.get("resumen"),
        "porque_importa": g.get("porque_importa"),
        "angulo": g.get("angulo"),
        "formato": g.get("formato"),
        "puntos": g["puntos"],
        "total": g["total"],
        "verificacion": g["verificacion"],
        "descarte": g.get("descarte"),
        "naturaleza": g.get("naturaleza"),
        "titulo_original": g["principal"]["titulo"],
    }


def correr(salida=SALIDA, descargador=fuentes.descargar, cliente=None, ahora=None, lista_fuentes=None):
    ahora = ahora or datetime.now(timezone.utc)
    local = ahora.astimezone(config.ZONA)
    cliente = cliente or Cliente()

    items, estado = fuentes.leer_todas(lista_fuentes or config.FUENTES, descargador)
    items = limpieza.deduplicar(items)
    items = limpieza.filtrar_tema(items, lista_fuentes or config.FUENTES, config.PALABRAS_IA)
    recientes = limpieza.filtrar_por_fecha(items, ahora, config.VENTANA_HORAS)
    if len(recientes) < config.MINIMO_ITEMS:
        recientes = limpieza.filtrar_por_fecha(items, ahora, config.VENTANA_AMPLIADA)
    print(f"Fuentes que respondieron: {sum(f['ok'] for f in estado)}/{len(estado)} · items recientes: {len(recientes)}")

    grupos = limpieza.agrupar(recientes)

    # Se trabajan las más prometedoras: con más fuentes, con fuente primaria, más recientes.
    def promesa(g):
        fecha = max((i["fecha"] for i in g["items"] if i["fecha"]), default=None)
        # Un paper no compite con una noticia por el primer lugar: solo entra si tiene peso propio.
        oficial = any(i["tipo"] == "oficial" and not i.get("investigacion") for i in g["items"])
        return (len({i["fuente"] for i in g["items"]}), oficial, fecha.timestamp() if fecha else 0)

    grupos = sorted(grupos, key=promesa, reverse=True)[: config.MAX_HISTORIAS + 15]
    grupos = editor.unir_por_modelo(grupos, cliente)
    grupos = sorted(grupos, key=promesa, reverse=True)[: config.MAX_HISTORIAS]
    for g in grupos:
        g["verificacion"] = verificar(g)  # la regla de verificación la aplica el código, siempre
    print(f"Historias: {len(grupos)} · verificadas: {sum(g['verificacion']['estado'] == 'verificada' for g in grupos)}")

    con_modelo = editor.puntuar(grupos, cliente) if grupos else False
    for g in grupos:
        reclasificar(g)  # notas con solo fuente oficial: noticia o comunicado
    publicables, sin_confirmar, comunicados, descartados = editor.seleccionar(grupos)
    nota_dia = editor.nota_del_dia(publicables, cliente) if con_modelo else None
    piezas = editor.redactar_piezas(publicables, cliente) if con_modelo else None
    piezas, nota_dia, informe = fidelidad.controlar(publicables, piezas, nota_dia, cliente) if con_modelo else (piezas, nota_dia, None)
    print(
        f"Publicables: {len(publicables)} · sin confirmar: {len(sin_confirmar)} · comunicados: {len(comunicados)} · "
        f"descartados: {len(descartados)} · piezas: {'sí' if piezas else 'no'} · nota del día: {'sí' if nota_dia else 'no'}"
    )
    if informe:
        print(f"Fidelidad: {informe['detectadas']} detectadas · {informe['corregidas']} corregidas · {len(informe['pendientes'])} pendientes")
    if cliente.errores:
        print("Avisos del modelo:", "; ".join(cliente.errores[-6:]))

    dia = local.strftime("%Y-%m-%d")
    (salida / "ediciones").mkdir(parents=True, exist_ok=True)
    (salida / "datos").mkdir(parents=True, exist_ok=True)
    anteriores = sorted((p.stem for p in (salida / "ediciones").glob("*.html") if p.stem != dia), reverse=True)

    edicion = {
        "fecha": local,
        "revisados": len(recientes),
        "historias": len(grupos),
        "publicables": publicables,
        "sin_confirmar": sin_confirmar,
        "comunicados": comunicados,
        "descartados": descartados,
        "piezas": piezas,
        "nota_dia": nota_dia,
        "fidelidad": informe,
        "estado_fuentes": estado,
        "con_modelo": con_modelo,
        "modelos": cliente.usados,
        "errores_modelo": cliente.errores,
        "archivo": anteriores,
    }
    (salida / "index.html").write_text(pagina.render(edicion, raiz=""), encoding="utf-8")
    (salida / "ediciones" / f"{dia}.html").write_text(pagina.render(edicion, raiz="../"), encoding="utf-8")
    (salida / ".nojekyll").write_text("", encoding="utf-8")
    datos = {
        "fecha": local.isoformat(),
        "revisados": len(recientes),
        "con_modelo": con_modelo,
        "modelos": cliente.usados,
        "errores_modelo": cliente.errores[-10:],
        "pedidos_al_modelo": cliente.llamadas,
        "fuentes": estado,
        "publicables": [_serializable(g) for g in publicables],
        "sin_confirmar": [_serializable(g) for g in sin_confirmar],
        "comunicados": [_serializable(g) for g in comunicados],
        "descartados": [_serializable(g) for g in descartados],
        "nota_dia": nota_dia,
        "piezas": piezas,
        "fidelidad": informe,
    }
    (salida / "datos" / f"{dia}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Página escrita: {salida / 'index.html'}")
    return edicion


if __name__ == "__main__":
    ed = correr()
    # Si no respondió ninguna fuente, es un problema real: que el workflow falle y avise.
    sys.exit(0 if any(f["ok"] for f in ed["estado_fuentes"]) else 1)
