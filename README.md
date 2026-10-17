# Radar Mutuo

Brief editorial diario de IA, armado solo todas las mañanas para un medio como Canal Mutuo.

**[Ver la edición de hoy →](https://federicoramos67.github.io/radar-mutuo/)**

## Qué hace

Cada día a las 07:18 (hora de Montevideo):

1. **Lee 13 fuentes**: laboratorios (OpenAI, Google, DeepMind, NVIDIA, Microsoft, Hugging Face), medios (TechCrunch, The Verge, Ars Technica, VentureBeat, MIT Technology Review, Xataka) y Hacker News.
2. **Agrupa** las notas que cuentan la misma historia desde distintos lugares.
3. **Verifica** cada historia con reglas fijas, sin depender del modelo:
   - la publicó la propia empresa → fuente primaria, verificada;
   - la cuentan dos medios de dominios distintos → corroborada, verificada;
   - la cuenta un solo medio o solo un agregador → **sin confirmar**. Se muestra marcada y no entra a lo publicable.
4. **Puntúa** con una rúbrica de cuatro ejes (señal, impacto, conversación y antihype, de 0 a 5 cada uno) y explica por qué importa.
5. **Redacta borradores** en voseo y en el tono del canal: guion de reel, carrusel, post de LinkedIn, hilo de Threads y preguntas para el Opencast.
6. **Publica** la página y guarda la edición y sus datos en `docs/`, que funciona como archivo histórico.

La máquina ordena, puntúa y justifica. Lo que se publica lo decide una persona.

## Por qué la verificación no la hace el modelo

Un modelo de lenguaje puede sonar seguro sin tener razón. Por eso el estado de verificación lo calcula el código con reglas que se pueden leer y auditar ([`radar/verificacion.py`](radar/verificacion.py)). El modelo opina sobre el interés de una historia; nunca decide si es cierta.

## Cómo funciona por dentro

| Pieza | Archivo |
|---|---|
| Fuentes, rúbrica, voz editorial | [`radar/config.py`](radar/config.py) |
| Lectura de RSS y Atom | [`radar/fuentes.py`](radar/fuentes.py) |
| Deduplicación y agrupación | [`radar/limpieza.py`](radar/limpieza.py) |
| Verificación cruzada | [`radar/verificacion.py`](radar/verificacion.py) |
| Puntaje y piezas | [`radar/editor.py`](radar/editor.py) |
| Modelos con respaldo | [`radar/modelo.py`](radar/modelo.py) |
| Página | [`radar/pagina.py`](radar/pagina.py) |
| Ejecución diaria | [`.github/workflows/radar.yml`](.github/workflows/radar.yml) |

- **Costo cero.** Corre en GitHub Actions y usa GitHub Models con el token propio del repositorio, sin API keys. Si hay un secreto `GROQ_API_KEY`, Groq queda como respaldo.
- **Sin dependencias.** Usa solo la biblioteca estándar de Python.
- **Tolerante a fallas.** Si una fuente se cae, sigue con las demás y lo informa en la página. Si el modelo no responde, igual publica con un puntaje de respaldo, avisa en la página y la verificación sigue funcionando.
- **Probado.** Antes de cada edición corren las pruebas (`python -m unittest discover -s tests`). Si alguna falla, ese día no se publica nada.

## Correrlo a mano

En la pestaña **Actions** → **Radar diario** → **Run workflow**.

---

Hecho por [Federico Ramos](https://github.com/federicoramos67), Montevideo.
