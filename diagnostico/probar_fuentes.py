"""Prueba feeds candidatos desde GitHub Actions y guarda qué responde y cuántos items trae."""
import json, sys
from datetime import datetime, timezone
sys.path.insert(0, ".")
from radar import fuentes

CANDIDATOS = [
    ("The Decoder", "https://the-decoder.com/feed/", "medio"),
    ("Wired IA", "https://www.wired.com/feed/tag/ai/latest/rss", "medio"),
    ("Genbeta", "https://www.genbeta.com/feedburner.xml", "medio"),
    ("Hipertextual", "https://hipertextual.com/feed", "medio"),
    ("El País Tecnología", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia/portada", "medio"),
    ("Infobae Tecno", "https://www.infobae.com/arc/outboundfeeds/rss/category/tecno/", "medio"),
    ("Xataka México", "https://www.xataka.com.mx/feedburner.xml", "medio"),
    ("WWWhat's new", "https://wwwhatsnew.com/feed/", "medio"),
    ("El Observador", "https://www.elobservador.com.uy/rss/pages/home.xml", "medio"),
    ("arXiv cs.CL", "https://rss.arxiv.org/rss/cs.CL", "investigacion"),
    ("arXiv cs.AI", "https://rss.arxiv.org/rss/cs.AI", "investigacion"),
    ("HF Daily Papers", "https://jamesg.blog/hf-papers.xml", "investigacion"),
    ("GitHub Trending Python", "https://mshibanami.github.io/GitHubTrendRSS/daily/python.xml", "comunidad"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/", "comunidad"),
    ("Google Research", "https://research.google/blog/rss/", "oficial"),
    ("Meta AI", "https://ai.meta.com/blog/rss/", "oficial"),
    ("Mistral", "https://mistral.ai/news/rss.xml", "oficial"),
    ("AWS Machine Learning", "https://aws.amazon.com/blogs/machine-learning/feed/", "oficial"),
]
ahora = datetime.now(timezone.utc)
salida = []
for nombre, url, tipo in CANDIDATOS:
    r = {"nombre": nombre, "url": url, "tipo": tipo}
    try:
        items = fuentes.parsear(fuentes.descargar(url), {"nombre": nombre, "tipo": tipo})
        con_fecha = [i for i in items if i["fecha"]]
        r.update(ok=True, items=len(items),
                 ultimas_48h=sum((ahora - i["fecha"]).total_seconds() < 172800 for i in con_fecha),
                 ejemplo=items[0]["titulo"] if items else "")
    except Exception as e:
        r.update(ok=False, error=f"{type(e).__name__}: {e}"[:160])
    salida.append(r)
    print(r)
json.dump(salida, open("diagnostico/fuentes.json", "w"), ensure_ascii=False, indent=1)
