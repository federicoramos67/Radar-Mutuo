"""Cliente mínimo para modelos de lenguaje compatibles con la API de OpenAI.

Usa Groq (plan gratuito) con la key del secreto GROQ_API_KEY.
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
        self.llamadas = 0

    @property
    def disponible(self):
        return bool(self.proveedores)

    def pedir_json(self, sistema, usuario, max_tokens=3000):
        if not self.proveedores:
            if "falta la key" not in self.errores:
                self.errores.append("falta la key")
            raise SinModelo("Falta el secreto GROQ_API_KEY.")
        if self.llamadas:
            self.esperar(config.PAUSA_ENTRE_PEDIDOS)
        self.llamadas += 1
        for nombre, url, token, modelo in list(self.proveedores):
            cuerpo = {
                "model": modelo,
                "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
                "temperature": 0.4,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            if "gpt-oss" in modelo:
                cuerpo["reasoning_effort"] = "low"  # menos tokens pensando, más para la respuesta
                cuerpo["max_tokens"] = max_tokens + 2000
            for intento in range(3):
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
                    if e.code == 429 and intento < 2:
                        try:
                            espera = float(e.headers.get("retry-after", 20))
                        except (TypeError, ValueError, AttributeError):
                            espera = 20
                        self.esperar(min(max(espera, 5), 60))  # cuota por minuto: esperar y reintentar
                        continue
                    if e.code in (401, 403, 404, 413, 429):
                        break  # este modelo no va a funcionar hoy: probar el siguiente
                except Exception as e:  # red, timeout, JSON roto
                    if not isinstance(e, ValueError):
                        self.errores.append(f"{modelo}: {type(e).__name__} {e}"[:300])
                if intento == 0:
                    self.esperar(3)
                else:
                    break
        raise SinModelo("; ".join(self.errores[-4:]))
