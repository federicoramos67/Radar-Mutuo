"""Corre una edición completa del Radar:  python -m radar

Pasos: leer fuentes → filtrar → agrupar → verificar → puntuar → elegir →
redactar piezas → publicar la página y guardar los datos del día.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config, editor, fuentes, limpieza, pagina
from .modelo import Cliente
from .verificacion import verificar

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
        "titulo_original": g["principal"]["titulo"],
    }


def correr(salida=SALIDA, descargador=fuentes.descargar, cliente=None, ahora=None, lista_fuentes=None):
    ahora = ahora or datetime.now(timezone.utc)
    local = ahora.astimezone(config.ZONA)
    cliente = cliente or Cliente()

    items, estado = fuentes.leer_todas(lista_fuentes or config.FUENTES, descargador)
    items = limpieza.deduplicar(items)
    recientes = limpieza.filtrar_por_fecha(items, ahora, config.VENTANA_HORAS)
    if len(recientes) < config.MINIMO_ITEMS:
        recientes = limpieza.filtrar_por_fecha(items, ahora, config.VENTANA_AMPLIADA)
    print(f"Fuentes que respondieron: {sum(f['ok'] for f in estado)}/{len(estado)} · items recientes: {len(recientes)}")

    grupos = limpieza.agrupar(recientes)
    for g in grupos:
        g["verificacion"] = verificar(g)
    print(f"Historias: {len(grupos)} · verificadas: {sum(g['verificacion']['estado'] == 'verificada' for g in grupos)}")

    con_modelo = editor.puntuar(grupos, cliente) if grupos else False
    publicables, sin_confirmar, descartados = editor.seleccionar(grupos)
    piezas = editor.redactar_piezas(publicables, cliente) if con_modelo else None
    print(f"Publicables: {len(publicables)} · sin confirmar: {len(sin_confirmar)} · descartados: {len(descartados)} · piezas: {'sí' if piezas else 'no'}")
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
        "descartados": descartados,
        "piezas": piezas,
        "estado_fuentes": estado,
        "con_modelo": con_modelo,
        "modelos": cliente.usados,
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
        "fuentes": estado,
        "publicables": [_serializable(g) for g in publicables],
        "sin_confirmar": [_serializable(g) for g in sin_confirmar],
        "descartados": [_serializable(g) for g in descartados],
        "piezas": piezas,
    }
    (salida / "datos" / f"{dia}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Página escrita: {salida / 'index.html'}")
    return edicion


if __name__ == "__main__":
    ed = correr()
    # Si no respondió ninguna fuente, es un problema real: que el workflow falle y avise.
    sys.exit(0 if any(f["ok"] for f in ed["estado_fuentes"]) else 1)
