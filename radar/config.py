"""Configuración del Radar: fuentes, rúbrica, modelos y voz editorial.

Todo lo que un editor querría cambiar sin tocar la lógica vive acá.
"""

from datetime import timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    ZONA = ZoneInfo("America/Montevideo")
except Exception:  # sin base de zonas horarias: Uruguay no usa horario de verano
    ZONA = timezone(timedelta(hours=-3), "UYT")

# --- Fuentes -----------------------------------------------------------------
# tipo "oficial": el propio laboratorio o empresa. Cuenta como fuente primaria.
# tipo "medio": prensa. Necesita una segunda fuente independiente para verificar.
# tipo "comunidad": agregadores. Sirven para medir conversación, no para verificar.
FUENTES = [
    {"nombre": "OpenAI", "url": "https://openai.com/news/rss.xml", "tipo": "oficial"},
    {"nombre": "Google AI", "url": "https://blog.google/technology/ai/rss/", "tipo": "oficial"},
    {"nombre": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml", "tipo": "oficial"},
    {"nombre": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "tipo": "oficial"},
    {"nombre": "Microsoft", "url": "https://blogs.microsoft.com/ai/feed/", "tipo": "oficial", "solo_ia": True},
    {"nombre": "NVIDIA", "url": "https://blogs.nvidia.com/feed/", "tipo": "oficial", "solo_ia": True},
    {"nombre": "TechCrunch", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "tipo": "medio"},
    {"nombre": "The Verge", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "tipo": "medio"},
    {"nombre": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "tipo": "medio", "solo_ia": True},
    {"nombre": "VentureBeat", "url": "https://venturebeat.com/category/ai/feed/", "tipo": "medio"},
    {"nombre": "MIT Technology Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed", "tipo": "medio"},
    {"nombre": "Xataka", "url": "https://www.xataka.com/feedburner.xml", "tipo": "medio", "solo_ia": True},
    {"nombre": "Hacker News", "url": "https://hnrss.org/newest?points=150&q=AI+OR+LLM+OR+OpenAI+OR+Anthropic+OR+Gemini", "tipo": "comunidad"},
    # Medios especializados en IA
    {"nombre": "The Decoder", "url": "https://the-decoder.com/feed/", "tipo": "medio"},
    {"nombre": "Wired", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "tipo": "medio"},
    # En español, y con mirada regional real
    {"nombre": "Genbeta", "url": "https://www.genbeta.com/feedburner.xml", "tipo": "medio", "solo_ia": True},
    {"nombre": "Hipertextual", "url": "https://hipertextual.com/feed", "tipo": "medio", "solo_ia": True},
    {"nombre": "Xataka México", "url": "https://www.xataka.com.mx/feedburner.xml", "tipo": "medio", "solo_ia": True},
    {"nombre": "WWWhat's new", "url": "https://wwwhatsnew.com/feed/", "tipo": "medio", "solo_ia": True},
    {"nombre": "Infobae", "url": "https://www.infobae.com/arc/outboundfeeds/rss/category/tecno/", "tipo": "medio", "solo_ia": True, "max_items": 30},
    {"nombre": "El Observador", "url": "https://www.elobservador.com.uy/rss/pages/home.xml", "tipo": "medio", "solo_ia": True},
    # Investigación y voces técnicas
    {"nombre": "Google Research", "url": "https://research.google/blog/rss/", "tipo": "oficial", "max_items": 15},
    {"nombre": "arXiv", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.CL+OR+cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=40",
     "tipo": "oficial", "investigacion": True, "max_items": 6},
    {"nombre": "Simon Willison", "url": "https://simonwillison.net/atom/everything/", "tipo": "comunidad", "max_items": 10},
]

# Fuentes con "solo_ia": publican de todo; se quedan solo las notas que hablan de IA.
PALABRAS_IA = [
    "ia", "ai", "inteligencia artificial", "artificial intelligence", "llm", "modelo de lenguaje",
    "language model", "chatgpt", "openai", "anthropic", "claude", "gemini", "deepmind", "copilot",
    "llama", "mistral", "deepseek", "qwen", "agentic", "machine learning",
    "aprendizaje automático", "neural", "neuronal", "generativa", "generative", "gpt", "nemotron",
    "chatbot", "diffusion", "sora", "veo", "midjourney", "hugging face", "inference", "inferencia",
]

# Ventana de tiempo: se mira hacia atrás esta cantidad de horas.
# Si entra muy poco material, se amplía una vez a VENTANA_AMPLIADA.
VENTANA_HORAS = 36
VENTANA_AMPLIADA = 72
MINIMO_ITEMS = 12

# --- Rúbrica -----------------------------------------------------------------
EJES = [
    ("senal", "Señal", "¿Es un hecho nuevo y concreto, o es ruido, opinión o refrito?"),
    ("impacto", "Impacto", "¿Le cambia algo práctico a creativos, marcas o gente que trabaja con IA en la región?"),
    ("conversacion", "Conversación", "¿Da para debate, tiene tensión, la gente va a querer opinar?"),
    ("antihype", "Antihype", "¿Se sostiene sin exagerar? 5 = datos verificables; 0 = puro marketing o cifra sin fuente."),
]
PUNTAJE_MAXIMO = 5 * len(EJES)
UMBRAL_PUBLICABLE = 10  # sobre 20
MINIMO_PUBLICABLES = 3  # un brief diario siempre trae al menos las 3 mejores verificadas
PISO_PUBLICABLE = 7    # salvo que ni siquiera lleguen a este piso
MAX_PUBLICABLES = 8
MAX_SIN_VERIFICAR = 2
MAX_DESCARTADOS = 4
MAX_COMUNICADOS = 4

# --- Modelos -----------------------------------------------------------------
# Groq: plan gratuito, sin tarjeta. La key va como secreto GROQ_API_KEY del
# repositorio, nunca en el código. Si un modelo falla, se prueba el siguiente.
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELOS_GROQ = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "openai/gpt-oss-20b"]

LOTE_PUNTAJE = 6       # historias por pedido
MAX_HISTORIAS = 30     # se puntúan las 30 más prometedoras del día, para cuidar la cuota
PAUSA_ENTRE_PEDIDOS = 20  # segundos; el plan gratuito limita tokens por minuto
MAX_TOKENS_PUNTAJE = 1800
MAX_TOKENS_PIEZAS = 2800

# --- Voz editorial -----------------------------------------------------------
# Guía de estilo con ejemplos propios. Los ejemplos están escritos para este
# proyecto: muestran el criterio, no copian textos de ningún medio.
VOZ_MUTUO = """\
Escribís para Canal Mutuo (MÜTÜÖ), un medio uruguayo de IA, tecnología y cultura digital.
Su lema: "La actualidad del futuro. Transformamos ruido en conocimiento."

REGLAS
- Español rioplatense con voseo (tenés, podés, mirá). Nunca "tú".
- Frases cortas y con sujeto. Una idea por frase.
- Antihype: nada de "revolucionario", "cambia todo", "promete", "sin precedentes", "increíble".
- Decí qué pasó con el dato concreto que trae la fuente. Si la fuente no trae el dato, no lo pongas.
- El foco es qué le cambia a una persona concreta: quien edita video, quien programa, quien enseña,
  quien maneja la comunicación de una marca. Nombrá a esa persona.
- Mirada regional SOLO si la fuente tiene algo regional (un país, un idioma, un precio, una
  disponibilidad). Si no, no fuerces "en Uruguay" ni "en la región".
- No repitas el marketing de la empresa con otras palabras. Si es un anuncio, decí que es un anuncio.
- Sin hashtags, sin emojis, sin llamados a la acción vacíos. Una buena pregunta vale más.
- Nunca inventes cifras, fechas, nombres ni citas.

EJEMPLOS (mal → bien)
- MAL: "La IA promete respuestas más rápidas y personalizadas."
  BIEN: "El banco dice que su asistente ya atiende a clientes. No publicó cuántos ni con qué resultados."
- MAL: "Los creativos uruguayos podrían aprovechar esta herramienta."
  BIEN: "Si editás video, esto te saca el paso de subtitular a mano."
- MAL: "Un avance revolucionario que cambia las reglas del juego."
  BIEN: "Es el tercer modelo abierto del mes. La novedad no es el modelo: es que entra en una laptop."
- MAL: "¿Estamos listos para el futuro?"
  BIEN: "¿Quién firma una pieza que escribió un agente: el que lo configuró o el que la aprobó?"
"""
