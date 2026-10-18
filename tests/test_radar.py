"""Pruebas sin red: feeds de ejemplo y un modelo simulado.

Corren en cada edición antes de armar el brief. Si algo se rompe, el
workflow se detiene y no publica una página a medias.
"""

import json
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

from radar import __main__ as radar_main
from radar import config, editor, fidelidad, fuentes, limpieza
from radar.modelo import Cliente, SinModelo, extraer_json
from radar.verificacion import reclasificar, verificar

AHORA = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


def rss(items):
    cuerpo = "".join(
        f"<item><title>{t}</title><link>{l}</link><description>{d}</description>"
        f"<pubDate>{(AHORA - timedelta(hours=h)).strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate></item>"
        for t, l, d, h in items
    )
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>{cuerpo}</channel></rss>'.encode()


def atom(items):
    cuerpo = "".join(
        f'<entry><title>{t}</title><link rel="alternate" href="{l}"/><summary>{d}</summary>'
        f"<updated>{(AHORA - timedelta(hours=h)).isoformat()}</updated></entry>"
        for t, l, d, h in items
    )
    return f'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>x</title>{cuerpo}</feed>'.encode()


FEEDS = {
    "https://oficial.test/rss": rss([("Nvidia releases Nemotron open agent models that run in 4GB", "https://oficial.test/nemotron", "Open weights.", 3)]),
    "https://medio1.test/rss": rss(
        [
            ("Nvidia's new Nemotron open agent models run in just 4GB", "https://medio1.test/nemotron?utm=x", "Coverage.", 4),
            ("Startup claims its chatbot replaces 1 in 4 jobs", "https://medio1.test/jobs", "No study.", 5),
            ("Old story from last week", "https://medio1.test/old", "Old.", 200),
        ]
    ),
    "https://medio2.test/atom": atom([("Meta opens its ads MCP server to agencies", "https://medio2.test/meta-mcp", "Ads via AI tools.", 6)]),
    "https://medio3.test/rss": rss([("Meta MCP server for ads opens to agencies worldwide", "https://medio3.test/meta", "Agencies.", 7)]),
    "https://comunidad.test/rss": rss([("Rumor: GPT-6 secretly finished training", "https://news.test/item?id=1", "Rumor.", 2)]),
}
FUENTES_PRUEBA = [
    {"nombre": "Lab", "url": "https://oficial.test/rss", "tipo": "oficial"},
    {"nombre": "Medio Uno", "url": "https://medio1.test/rss", "tipo": "medio"},
    {"nombre": "Medio Dos", "url": "https://medio2.test/atom", "tipo": "medio"},
    {"nombre": "Medio Tres", "url": "https://medio3.test/rss", "tipo": "medio"},
    {"nombre": "Foro", "url": "https://comunidad.test/rss", "tipo": "comunidad"},
    {"nombre": "Caída", "url": "https://caida.test/rss", "tipo": "medio"},
]


def descargador_falso(url, timeout=20):
    if url not in FEEDS:
        raise urllib.error.URLError("sin conexión")
    return FEEDS[url]


class ModeloFalso:
    """Imita la API: puntúa según palabras clave y devuelve piezas."""

    def __init__(self):
        self.llamadas = 0
        self.correcciones = None

    def __call__(self, url, token, cuerpo):
        self.llamadas += 1
        sistema = cuerpo["messages"][0]["content"]
        usuario = cuerpo["messages"][1]["content"]
        if "MISMO hecho" in sistema:
            ids = {l.split(" ", 1)[0]: l for l in usuario.splitlines()[1:]}
            juntos = [i for i, l in ids.items() if "rumor" in l.lower() or "gpt-6" in l.lower() or "mismo-hecho" in l.lower()]
            contenido = json.dumps({"grupos": [juntos] if len(juntos) > 1 else []})
            return {"choices": [{"message": {"content": contenido}}]}
        if "verificador de datos" in sistema:
            alertas = []
            if "diez veces" in usuario:
                alertas.append({"donde": "pieza:post", "frase": "diez veces más rápido", "problema": "la fuente no da esa cifra"})
            return {"choices": [{"message": {"content": json.dumps({"alertas": alertas})}}]}
        if "Te paso textos redactados" in sistema:
            paquete = json.loads(usuario)
            self.correcciones = paquete["problemas"]
            piezas = json.loads(json.dumps(paquete["piezas"], ensure_ascii=False).replace("Crece diez veces más rápido. ", ""))
            return {"choices": [{"message": {"content": json.dumps({"notas": {}, "piezas": piezas, "nota_dia": paquete["nota_dia"]})}}]}
        if "editor jefe" in sistema:
            notas = json.loads(usuario.split("\n", 1)[1])
            contenido = json.dumps({"nota": notas[0]["id"], "tesis": "Lo importante no es el modelo sino dónde corre.", "mirar": "Si publican precios."})
            return {"choices": [{"message": {"content": contenido}}]}
        if "rúbrica" in sistema and "historias" in sistema:
            historias = json.loads(usuario.split("\n", 1)[1])
            salida = []
            for h in historias:
                t = h["titulo"].lower()
                alto = "nemotron" in t or "mcp" in t
                rumor = "rumor" in t or "gpt-6" in t
                p = (5, 5, 4, 4) if alto else ((4, 4, 5, 1) if rumor else (1, 2, 4, 0))
                salida.append(
                    {"id": h["id"], "senal": p[0], "impacto": p[1], "conversacion": p[2], "antihype": p[3],
                     "titular": "Titular " + h["id"], "resumen": "Resumen.", "porque_importa": "Importa.",
                     "angulo": "Gancho.", "formato": "reel", "descarte": "" if alto else "Cifra sin estudio.",
                     "naturaleza": "caso_cliente" if "how acme" in t else "lanzamiento"}
                )
            contenido = json.dumps({"historias": salida})
        else:
            notas = json.loads(usuario.split("\n", 1)[1])
            i = notas[0]["id"]
            contenido = "```json\n" + json.dumps(
                {
                    "reel": {"nota": i, "titulo": "Reel", "beats": [{"t": "0:00", "texto": "Hola.", "pantalla": "Placa."}]},
                    "carrusel": {"nota": i, "titulo": "Carrusel", "placas": ["Uno", "Dos"]},
                    "post": {"nota": i, "titulo": "Post", "texto": "Crece diez veces más rápido. Párrafo.\n\nOtro <b>no html</b>."},
                    "hilo": {"nota": i, "titulo": "Hilo", "partes": ["a", "b"]},
                    "opencast": {"notas": [i], "preguntas": ["¿Por qué?"]},
                }
            ) + "\n```"
        return {"choices": [{"message": {"content": contenido}}]}


def cliente_falso(enviar=None):
    return Cliente(enviar=enviar or ModeloFalso(), proveedores=[("Falso", "https://x", "t", "falso-1")], esperar=lambda s: None)


class PruebasFuentes(unittest.TestCase):
    def test_rss_y_atom(self):
        items, estado = fuentes.leer_todas(FUENTES_PRUEBA, descargador_falso)
        self.assertEqual(len(items), 7)
        self.assertFalse(estado[-1]["ok"])  # la fuente caída no frena a las demás
        self.assertTrue(all(i["fecha"] is not None for i in items))
        self.assertIn("https://medio2.test/meta-mcp", [i["link"] for i in items])

    def test_limpiar_html(self):
        self.assertEqual(fuentes.limpiar_texto("<p>Hola &amp; <b>chau</b></p>"), "Hola & chau")


class PruebasLimpieza(unittest.TestCase):
    def setUp(self):
        self.items, _ = fuentes.leer_todas(FUENTES_PRUEBA, descargador_falso)

    def test_filtro_de_tema(self):
        items = [
            {"titulo": "Rusia prueba drones con motores a reacción", "resumen": "Defensa.", "fuente": "General"},
            {"titulo": "Meta lanza un agente de IA para anunciantes", "resumen": "", "fuente": "General"},
            {"titulo": "Nueva función de inteligencia artificial en el móvil", "resumen": "", "fuente": "General"},
            {"titulo": "Cualquier cosa", "resumen": "", "fuente": "Especializada"},
        ]
        fuentes_ = [{"nombre": "General", "solo_ia": True}, {"nombre": "Especializada"}]
        quedan = [i["titulo"] for i in limpieza.filtrar_tema(items, fuentes_, config.PALABRAS_IA)]
        self.assertNotIn("Rusia prueba drones con motores a reacción", quedan)
        self.assertEqual(len(quedan), 3)

    def test_filtra_viejos(self):
        recientes = limpieza.filtrar_por_fecha(self.items, AHORA, 36)
        self.assertNotIn("Old story from last week", [i["titulo"] for i in recientes])

    def test_agrupa_misma_historia(self):
        grupos = limpieza.agrupar(limpieza.filtrar_por_fecha(self.items, AHORA, 36))
        nemotron = [g for g in grupos if "nemotron" in g["principal"]["titulo"].lower()]
        self.assertEqual(len(nemotron), 1)
        self.assertEqual(len(nemotron[0]["items"]), 2)
        self.assertEqual(nemotron[0]["principal"]["tipo"], "oficial")


class PruebasVerificacion(unittest.TestCase):
    def setUp(self):
        items, _ = fuentes.leer_todas(FUENTES_PRUEBA, descargador_falso)
        self.grupos = limpieza.agrupar(limpieza.filtrar_por_fecha(items, AHORA, 36))

    def _de(self, palabra):
        return next(g for g in self.grupos if palabra in g["principal"]["titulo"].lower())

    def test_fuente_oficial_verifica(self):
        self.assertEqual(verificar(self._de("nemotron"))["estado"], "verificada")

    def test_dos_medios_verifican(self):
        v = verificar(self._de("mcp"))
        self.assertEqual(v["estado"], "verificada")
        self.assertIn("2 medios", v["motivo"])

    def test_rumor_queda_sin_confirmar(self):
        self.assertEqual(verificar(self._de("rumor"))["estado"], "sin_confirmar")


class PruebasComunicados(unittest.TestCase):
    def _grupo(self, titulo, naturaleza, antihype):
        item = {"titulo": titulo, "link": "https://lab.test/x", "resumen": "", "fecha": AHORA, "fuente": "Lab", "tipo": "oficial"}
        g = {"items": [item], "principal": item, "naturaleza": naturaleza, "puntos": {"antihype": antihype}}
        g["verificacion"] = verificar(g)
        return g

    def test_lanzamiento_con_datos_es_noticia(self):
        g = self._grupo("Lab releases an open model that runs in 4GB", "lanzamiento", 4)
        self.assertEqual(reclasificar(g)["estado"], "verificada")

    def test_caso_de_cliente_es_comunicado_aunque_el_modelo_diga_otra_cosa(self):
        g = self._grupo("How Acme is using ChatGPT to scale support", "lanzamiento", 4)
        self.assertEqual(reclasificar(g)["estado"], "comunicado")
        self.assertIn("caso de cliente", g["verificacion"]["motivo"])

    def test_titulo_promocional_es_comunicado(self):
        g = self._grupo("RTX Spark Ignites Global Celebration as New PCs Arrive", "lanzamiento", 4)
        self.assertEqual(reclasificar(g)["estado"], "comunicado")
        self.assertIn("promoción", g["verificacion"]["motivo"])

    def test_anuncio_sin_datos_es_comunicado(self):
        g = self._grupo("Lab shares its vision for agents", "opinion", 2)
        self.assertEqual(reclasificar(g)["estado"], "comunicado")

    def test_sin_modelo_lo_oficial_solo_es_comunicado(self):
        g = self._grupo("Lab releases a model", None, 0)
        self.assertEqual(reclasificar(g)["estado"], "comunicado")


class PruebasFidelidad(unittest.TestCase):
    def test_cifra_inventada(self):
        self.assertEqual(fidelidad.cifras_sin_fuente("Triplica usuarios y crece diez veces.", "Usage tripled this year."), ["10"])

    def test_formatos_de_numero(self):
        self.assertEqual(fidelidad.cifras_sin_fuente("Llegó a 1.000 empresas y 4,5 millones", "1,000 companies, 4.5 million"), [])

    def test_mitad_inventada(self):
        self.assertEqual(fidelidad.cifras_sin_fuente("Redujo a la mitad la contratación.", "Anthropic nearly stopped hiring juniors."), ["0.5"])
        self.assertEqual(fidelidad.cifras_sin_fuente("Redujo a la mitad la contratación.", "Hiring fell by half."), [])

    def test_porcentaje(self):
        self.assertEqual(fidelidad.cifras_sin_fuente("Bajó un 40%", "costs fell 30%"), ["40"])

    def test_region_forzada(self):
        self.assertTrue(fidelidad.region_forzada("Los uruguayos podrían usarlo.", "A bank in Ohio launched a chatbot."))
        self.assertFalse(fidelidad.region_forzada("Llega a Uruguay.", "Now available in Latin America."))

    def test_frase_de_folleto(self):
        self.assertIn("revolucion", fidelidad.folleto("Una revolución en la edición"))
        self.assertTrue(fidelidad.folleto("Descubrí más en la web de NVIDIA."))


class PruebasModelo(unittest.TestCase):
    def test_extraer_json_con_ruido(self):
        self.assertEqual(extraer_json('Acá va:\n```json\n{"a": 1}\n```'), {"a": 1})

    def test_pasa_al_siguiente_modelo(self):
        def enviar(url, token, cuerpo):
            if cuerpo["model"] == "malo":
                raise urllib.error.HTTPError(url, 403, "no", {}, None)
            return {"choices": [{"message": {"content": '{"ok": true}'}}]}

        c = Cliente(enviar=enviar, proveedores=[("A", "u", "t", "malo"), ("B", "u", "t", "bueno")], esperar=lambda s: None)
        self.assertEqual(c.pedir_json("s", "u"), {"ok": True})
        self.assertEqual(c.usados, ["bueno (B)"])

    def test_espera_y_reintenta_con_cuota_agotada(self):
        esperas, intentos = [], []

        def enviar(url, token, cuerpo):
            intentos.append(1)
            if len(intentos) == 1:
                raise urllib.error.HTTPError(url, 429, "cuota", {"retry-after": "7"}, None)
            return {"choices": [{"message": {"content": '{"ok": 1}'}}]}

        c = Cliente(enviar=enviar, proveedores=[("A", "u", "t", "m")], esperar=esperas.append)
        self.assertEqual(c.pedir_json("s", "u"), {"ok": 1})
        self.assertEqual(esperas, [7.0])

    def test_sin_key_avisa_en_la_pagina(self):
        with tempfile.TemporaryDirectory() as d:
            radar_main.correr(Path(d), descargador_falso, Cliente(proveedores=[]), AHORA, FUENTES_PRUEBA)
            self.assertIn("Falta configurar la key", (Path(d) / "index.html").read_text())

    def test_sin_proveedores(self):
        with self.assertRaises(SinModelo):
            Cliente(proveedores=[]).pedir_json("s", "u")


class PruebasEdicionCompleta(unittest.TestCase):
    def test_con_modelo(self):
        with tempfile.TemporaryDirectory() as d:
            ed = radar_main.correr(Path(d), descargador_falso, cliente_falso(), AHORA, FUENTES_PRUEBA)
            self.assertTrue(ed["con_modelo"])
            titulos = [g["principal"]["titulo"].lower() for g in ed["publicables"]]
            self.assertTrue(any("nemotron" in t for t in titulos))
            self.assertTrue(any("mcp" in t for t in titulos))
            self.assertEqual(len(ed["sin_confirmar"]), 1)  # el rumor se muestra, marcado
            self.assertTrue(ed["piezas"])
            html = (Path(d) / "index.html").read_text()
            self.assertIn("Sin confirmar · no se publica", html)
            self.assertIn("&lt;b&gt;no html&lt;/b&gt;", html)  # el texto del modelo se escapa
            self.assertIn("Caída · no respondió", html)
            # nota del día y control de fidelidad
            self.assertIn("Lo que importa hoy", html)
            self.assertIn("Lo importante no es el modelo sino dónde corre.", html)
            self.assertNotIn("diez veces", html)  # la cifra inventada se corrigió antes de publicar
            self.assertIn("✓ Control de fidelidad", html)
            self.assertGreaterEqual(ed["fidelidad"]["corregidas"], 1)
            self.assertEqual(ed["fidelidad"]["pendientes"], [])
            self.assertTrue((Path(d) / "ediciones" / "2026-10-17.html").exists())
            datos = json.loads((Path(d) / "datos" / "2026-10-17.json").read_text())
            self.assertEqual(len(datos["publicables"]), 2)

    def test_el_modelo_une_pero_la_regla_verifica(self):
        feeds = dict(FEEDS)
        feeds["https://medio4.test/rss"] = rss([("OpenAI's mysterious GPT-6 run is real, insiders say", "https://medio4.test/gpt6", "mismo-hecho", 3)])
        fuentes_ = FUENTES_PRUEBA + [{"nombre": "Medio Cuatro", "url": "https://medio4.test/rss", "tipo": "medio"}]
        with tempfile.TemporaryDirectory() as d:
            ed = radar_main.correr(Path(d), lambda u, timeout=20: feeds[u] if u in feeds else (_ for _ in ()).throw(urllib.error.URLError("x")), cliente_falso(), AHORA, fuentes_)
            todos = ed["publicables"] + ed["sin_confirmar"]
            g = next(g for g in todos if any("gpt-6" in i["titulo"].lower() for i in g["items"]))
            self.assertEqual(len(g["items"]), 2)
            # un foro + un solo medio no alcanza: sigue sin confirmar
            self.assertEqual(g["verificacion"]["estado"], "sin_confirmar")

    def test_sin_modelo_igual_publica(self):
        def caido(url, token, cuerpo):
            raise urllib.error.URLError("caído")

        with tempfile.TemporaryDirectory() as d:
            ed = radar_main.correr(Path(d), descargador_falso, cliente_falso(caido), AHORA, FUENTES_PRUEBA)
            self.assertFalse(ed["con_modelo"])
            html = (Path(d) / "index.html").read_text()
            self.assertIn("el modelo de lenguaje no respondió", html)
            self.assertEqual(len(ed["publicables"]), 2)  # igual sale un brief útil
            # la verificación no depende del modelo: el rumor sigue fuera de lo publicable
            self.assertFalse(any("rumor" in g["principal"]["titulo"].lower() for g in ed["publicables"]))

    def test_archivo_de_ediciones(self):
        with tempfile.TemporaryDirectory() as d:
            radar_main.correr(Path(d), descargador_falso, cliente_falso(), AHORA - timedelta(days=1), FUENTES_PRUEBA)
            radar_main.correr(Path(d), descargador_falso, cliente_falso(), AHORA, FUENTES_PRUEBA)
            html = (Path(d) / "index.html").read_text()
            self.assertIn('href="ediciones/2026-10-16.html"', html)


if __name__ == "__main__":
    unittest.main()
