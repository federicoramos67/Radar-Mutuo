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
]

# Fuentes con "solo_ia": publican de todo; se quedan solo las notas que hablan de IA.
PALABRAS_IA = [
    "ia", "ai", "inteligencia artificial", "artificial intelligence", "llm", "modelo de lenguaje",
    "language model", "chatgpt", "openai", "anthropic", "claude", "gemini", "deepmind", "copilot",
    "llama", "mistral", "deepseek", "qwen", "agente", "agentes", "agent", "agents", "machine learning",
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
VOZ_MUTUO = """\
Escribís para Canal Mutuo (MÜTÜÖ), un medio uruguayo de IA, tecnología y cultura digital.
Su lema: "La actualidad del futuro. Transformamos ruido en conocimiento."
Reglas de voz:
- Español rioplatense con voseo (tenés, podés, mirá). Nunca "tú".
- Frases cortas. Ritmo de redes, pero con criterio: notas cortas, reflexivas.
- Antihype: nada de "revolucionario", "cambia todo", "increíble". Si algo es exagerado, se dice.
- El foco no es la herramienta sino qué le cambia a la gente que crea y trabaja.
- Mirada regional: cuando aplique, qué significa para Uruguay y América Latina.
- Sin hashtags, sin emojis, sin llamados a la acción vacíos. Una buena pregunta vale más.
- Nunca inventes datos, cifras, fechas ni citas que no estén en el material. Si falta un dato, no lo pongas.
"""
