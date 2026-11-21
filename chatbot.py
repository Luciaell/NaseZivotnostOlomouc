"""AI chatbot that summarizes the amenities around a selected address.

Streamlit-free: front_end.py owns the UI and session state. See CHATBOT.md.
"""

import anthropic

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 16000
EFFORT = "low"            # chat-style answers; raise to "medium" if summaries feel shallow
FALLBACK_BETA = "server-side-fallback-2026-07-01"
WALK_M_PER_MIN = 80       # average walking speed used for the minute estimates
TOP_N = 3                 # how many nearest results per type go into the prompt

# Types whose datasets are known to be incomplete (see md files of datasets/).
INCOMPLETE = {
    "sports_halls": "dataset obsahuje jen 1 halu",
    "places_of_worship": "dataset obsahuje jen malé kaple",
    "restaurants": "jen restaurace, bez hospod a barů",
}

SYSTEM_PROMPT = """\
You are the assistant of "Walker15", an app that rates how livable \
an address in Olomouc (Czech Republic) is.

You receive a list of amenities found within a fixed radius of one address. \
Use only that data. Never invent amenities, names or distances. If the user asks \
about something the data does not cover, say so plainly.

The data may list hidden categories ("Skryté kategorie"). The user turned these off \
in the app's settings. They are a user choice, not missing amenities and not a gap \
in the data: never present them as missing, and leave them out of the summary. If \
the user asks about a hidden category, say it is turned off in the settings and can \
be turned back on there. Only a shown category with none in the radius is a real gap.

Always answer in Czech, in Markdown.

The data includes the app's livability score ("Hodnocení aplikace"). The app shows \
this score on the page, so never compute, change or round your own score. Always use \
the given number exactly as written.

When asked for the area summary, use this structure:
**Hodnocení: X/10** with the app's score, then one short sentence explaining what \
raises or lowers it. If the data has no score, leave out the score line.
Then at most 3 short bullet points, one line each: the main strength, the main gap \
within the radius (if any), and who the location suits best (e.g. families, seniors, \
students, car-free commuters). Keep the whole summary under about 80 words. \
Do not list every amenity; the user sees the full list next to the chat and can \
ask follow-up questions for details.

How the app computes the score, so you can explain it: everyday needs (public \
transport, supermarket, pharmacy, kindergarten, primary school) give up to 8 of the \
10 points; the other types give up to 2 bonus points. The closer the nearest amenity, \
the more it counts; a type with none in the radius counts zero. Types marked as \
incomplete data do not lower the score. Hidden categories are not part of the score.

For follow-up questions, answer briefly and concretely, using names and distances \
from the data. Walking times are approximate.
"""


def make_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def walk_minutes(distance_m: float) -> int:
    return max(1, round(distance_m / WALK_M_PER_MIN))


def build_context(address: str, results: dict[str, list[dict]],
                  radius_m: int, labels: dict[str, str], score: float | None = None,
                  hidden: list[str] | None = None) -> str:
    """First user message: the area data plus the request for a summary.

    `score` is the app's livability score (front_end.livability_score); the model
    repeats it instead of inventing its own. Format it the same way as the page does.
    `hidden` lists the type keys the user turned off in the settings, so the model
    does not mistake them for missing amenities.
    """
    lines = [f"Adresa: {address}", f"Okruh: {radius_m} m"]
    if score is not None:
        lines.append(f"Hodnocení aplikace: {score:.1f}/10")
    if hidden:
        names = ", ".join(labels.get(kind, kind) for kind in hidden)
        lines.append(f"Skryté kategorie (uživatel je vypnul v nastavení): {names}")
    lines.append("")
    for kind, found in results.items():
        label = labels.get(kind, kind)
        note = f" [neúplná data: {INCOMPLETE[kind]}]" if kind in INCOMPLETE else ""
        if not found:
            lines.append(f"- {label}: žádné v okruhu{note}")
            continue
        nearest = ", ".join(
            f"{item['name']} {item['distance_m']} m (~{walk_minutes(item['distance_m'])} min pěšky)"
            for item in found[:TOP_N]
        )
        lines.append(f"- {label}: {len(found)}×; nejbližší: {nearest}{note}")
    lines += ["", "Shrň prosím okolí této adresy."]
    return "\n".join(lines)


def stream_reply(client: anthropic.Anthropic, messages: list[dict]):
    """Yield the assistant's answer as text chunks.

    `messages` is the full history: [{"role": "user"|"assistant", "content": str}, ...],
    starting with the build_context() message. API errors propagate to the caller.
    """
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=messages,
        output_config={"effort": EFFORT},
        # On a safety refusal, the API retries the request on a fallback model.
        betas=[FALLBACK_BETA],
        fallbacks="default",
    ) as stream:
        yield from stream.text_stream
        final = stream.get_final_message()

    if final.stop_reason == "refusal":
        yield "\n\n_Na tento dotaz nemohu odpovědět._"
    elif final.stop_reason == "max_tokens":
        yield "\n\n_(Odpověď byla zkrácena.)_"
