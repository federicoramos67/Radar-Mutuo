"""Cliente mínimo para modelos de lenguaje compatibles con la API de OpenAI.

Proveedores, en orden:
  1. GitHub Models (gratis dentro de GitHub Actions, usa el token del repositorio).
  2. Groq, solo si existe la variable GROQ_API_KEY.
Si un modelo falla (cuota, caída, respuesta rota) se pasa al siguiente.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request

from . import config


class RespuestaRara(Exception):
    """El servidor respondió algo que no es JSON."""


class SinModelo(Exception):
    """Ningún proveedor respondió. El Radar sigue en modo sin modelo."""


def _proveedores():
    lista = []
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        for m in config.MODELOS_GITHUB:
            lista.append(("GitHub Models", config.GITHUB_MODELS_URL, token, m))
    groq = os.environ.get("GROQ_API_KEY")
    if groq:
        for m in config.MODELOS_GROQ:
            lista.append(("Groq", config.GROQ_URL, groq, m))
    return lista


def extraer_json(texto):
    """Saca el JSON de la respuesta aunque venga envuelto en ``` o con texto alrededor."""
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto)
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        inicio = min((p for p in (texto.find("{"), texto.find("[")) if p != -1), default=-1)
        if inicio == -1:
            raise
        cierre = max(texto.rfind("}"), texto.rfind("]"))
        return json.loads(texto[inicio : cierre + 1])


def _post(url, token, cuerpo, timeout=90):
    pedido = urllib.request.Request(
        url,
        data=json.dumps(cuerpo).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(pedido, timeout=timeout) as r:
        crudo = r.read()
        estado, tipo = r.status, r.headers.get("Content-Type", "")
    try:
        return json.loads(crudo)
    except ValueError:
        raise RespuestaRara(f"HTTP {estado} {tipo} {len(crudo)}B: {crudo[:200]!r}") from None


class Cliente:
    def __init__(self, enviar=_post, proveedores=None, esperar=time.sleep):
        self.enviar = enviar
        self.proveedores = proveedores if proveedores is not None else _proveedores()
        self.esperar = esperar
        self.usados = []  # para el pie de página: qué modelo hizo el trabajo
        self.errores = []

    @property
    def disponible(self):
        return bool(self.proveedores)

    def pedir_json(self, sistema, usuario, max_tokens=3000):
        self.llamadas = getattr(self, "llamadas", 0) + 1
        if not self.proveedores:
            self.errores.append("sin proveedores: no hay GITHUB_TOKEN ni GROQ_API_KEY")
            raise SinModelo("No hay GITHUB_TOKEN ni GROQ_API_KEY.")
        for nombre, url, token, modelo in list(self.proveedores):
            cuerpo = {
                "model": modelo,
                "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
                "temperature": 0.4,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            for intento in range(2):
                try:
                    r = self.enviar(url, token, cuerpo)
                    eleccion = r["choices"][0]
                    contenido = eleccion["message"].get("content") or ""
                    try:
                        datos = extraer_json(contenido)
                    except ValueError:
                        self.errores.append(
                            f"{modelo}: JSON inválido (fin={eleccion.get('finish_reason')}, {len(contenido)} caracteres, termina en {contenido[-60:]!r})"
                        )
                        if eleccion.get("finish_reason") == "length":
                            break  # cortado por largo: reintentar igual no sirve
                        raise
                    etiqueta = f"{modelo} ({nombre})"
                    if etiqueta not in self.usados:
                        self.usados.append(etiqueta)
                    return datos
                except urllib.error.HTTPError as e:
                    try:
                        detalle = e.read().decode("utf-8", "replace")[:240]
                    except Exception:
                        detalle = ""
                    self.errores.append(f"{modelo}: HTTP {e.code} {detalle}".strip())
                    if e.code == 429 and intento == 0:
                        self.esperar(20)  # cuota por minuto: esperar y reintentar una vez
                        continue
                    if e.code in (401, 403, 404, 413, 429):
                        break  # este modelo no va a funcionar hoy: probar el siguiente
                except Exception as e:  # red, timeout, JSON roto
                    if not isinstance(e, ValueError):
                        self.errores.append(f"{modelo}: {type(e).__name__} {e}"[:300])
                if intento == 0:
                    self.esperar(3)
        raise SinModelo("; ".join(self.errores[-4:]))
