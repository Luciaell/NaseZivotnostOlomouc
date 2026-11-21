# CHATBOT.md

The single source of truth for the AI chatbot in **Naše životnost Olomouc**.
Update this file whenever a decision is made or the implementation changes.

Status: **v1 implemented**: area summary with a score, plus follow-up chat. Not yet tested against the live API.
Last updated: 2026-11-21

---

## 1. Goal

After the user selects an address, the chatbot summarizes the area in plain Czech. It covers what is nearby, what is missing and who the location suits. Optionally, the user can ask follow-up questions about the area.

The chatbot uses **only the data the app already has** (`back_end.find_institutions` results). It must not invent amenities.

---

## 2. Data available to the chatbot

For the selected point, `front_end.show_results` already builds
`results = {kind: [ {name, distance_m, lat, lon, osm_id}, ... ]}` for every key in `back_end.TYPES`:

| Key | Czech label | Notes |
|---|---|---|
| `bus_stops` | zastávka | platforms merged by name |
| `tram_stops` | zastávka tramvaje | |
| `train_stations` | vlakové nádraží | |
| `kindergartens` | mateřská škola | |
| `schools` | základní škola | regional data, `osm_id` is None |
| `libraries` | knihovna | regional data |
| `pharmacies` | lékárna | |
| `supermarkets` | supermarket | |
| `restaurants` | restaurace | restaurants only, no pubs/bars yet |
| `theatres` | divadlo | |
| `cinemas` | kino | |
| `gyms` | posilovna | |
| `sports_halls` | sportovní hala | only 1 entry, data incomplete |
| `places_of_worship` | kostel | only small chapels, data incomplete |

Also known: the address label, the coordinates, `RADIUS_M` (500 m), the circle colour and the count of missing types.

**Data quality caveats** (the chatbot must not draw strong conclusions from these): sports halls and places of worship are incomplete, and restaurants exclude pubs and bars.

**Hidden categories are a user choice, not a gap.** `results` contains only the categories enabled in the settings popover. The types the user turned off are passed separately as "hidden". The chatbot must never present them as missing amenities or as gaps in the data, leaves them out of the summary and the score, and, when asked about one, says it is turned off in the settings and can be turned back on there. Only an *enabled* category with no result in the radius counts as a real gap.

---

## 3. Candidate functions (to discuss)

| # | Function | Description | Complexity | Status |
|---|---|---|---|---|
| F1 | **Area summary** | A short paragraph: strengths, what is missing, and the overall verdict. | Low (one API call) | ✅ v1 |
| F2 | **Liveability score** | A score from 0 to 10 with a short reason. | Low | ✅ computed by the app (`front_end.livability_score`); the chatbot repeats it and explains it |
| F3 | **Persona fit** | How well the area suits a family with children, a senior, a student or a car-free commuter. | Low | partly: the summary says who the area suits |
| F4 | **Follow-up chat** | `st.chat_input` with questions like "Kde je nejbližší lékárna?" or "Je to dobré pro rodinu?", answered from the same data. | Medium (session history) | ✅ v1 |
| F5 | **Tool use: wider radius** | The chatbot can call `find_institutions` with a larger radius, e.g. "nearest cinema within 2 km". | Medium | backlog |
| F6 | **Compare two addresses** | Side-by-side comparison of two chosen addresses. | Medium to high (UI change) | backlog |
| F7 | **Walking-time estimates** | Converts distances to walking minutes at about 80 m/min, computed in Python. | Low | ✅ v1 (in the prompt data) |
| F8 | **Future: sensor data** | Air quality, traffic and greenery once datasets exist (see the roadmap). | Later | backlog |

---

## 4. Technical design

- **Provider:** Anthropic Claude via the official `anthropic` Python SDK (in `requirements.txt`; tested with SDK 2.12.0).
- **Model:** `claude-sonnet-5-5` ($2 / $10 per 1M input / output tokens), effort `low` (chat-style answers). Thinking is left at the model default (adaptive).
- **Refusal fallback:** the request uses the server-side `fallbacks="default"` (beta `server-side-fallback-2026-07-01`). If the safety classifier declines, the API reruns the request on a fallback model. If the whole chain refuses, the user sees a short Czech note.
- **API key:** `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml`, with the environment variable as a fallback (`get_anthropic_key()`, the same pattern as `get_carto_key()`). Without a key, the section shows an info message and makes no API calls.
- **Module split:** `chatbot.py` builds the prompt and calls the API, and has no Streamlit import. `front_end.py` (`show_chatbot`, `respond`) renders it and holds the session state.
- **Prompt input** (`chatbot.build_context`): the address, the radius, the app's score as `Hodnocení aplikace: X.X/10` (omitted when `score` is None), the categories turned off in the settings as `Skryté kategorie (uživatel je vypnul v nastavení): …` (omitted when none are hidden), and per enabled type: the Czech label, the count, the 3 nearest results with distance and walking minutes, and an "incomplete data" note for `sports_halls`, `places_of_worship` and `restaurants`. No coordinates.
- **System prompt** (`chatbot.SYSTEM_PROMPT`, written in English): use only the given data and answer in Czech Markdown. Hidden categories are a user choice: never call them missing, keep them out of the summary, and point to the settings if asked. The summary starts with `**Hodnocení: X/10**` using the app's score exactly as given (the model must never compute, change or round its own; no score in the data → no score line), then one sentence on what raises or lowers it, then at most 3 one-line bullets (main strength, main gap, who the area suits), under about 80 words, without listing every amenity. The prompt describes how the app computes the score (everyday needs up to 8 points, other types up to 2 bonus points, closer counts more, incomplete types don't lower it, hidden categories are not part of it) so the model can explain it. **Keep this description in sync with `front_end.livability_score`.**
- **Conversation state:** `st.session_state["chat"] = {"key", "messages"}`, where `key = (address, enabled categories)`. `messages[0]` is the hidden data prompt. Changing the address or the categories selected in the settings popover resets the conversation (and creates one new summary). With no categories selected, the chatbot is hidden.
- **Radius:** taken from `front_end.RADIUS_M` (currently 1000 m, changed by the settings-menu merge). History is stored as plain text (assistant text only).
- **No re-billing on reruns:** the summary is generated once per address, when `messages` has length 1. Later Streamlit reruns (e.g. after a chat question) only redraw stored messages.
- **Streaming:** `chatbot.stream_reply` is a generator used with `st.write_stream`.
- **Errors:** authentication, rate-limit, API-status and connection errors show a Czech `st.error`. A failed follow-up question is removed from the history.

---

## 5. Open questions

- A per-session request limit is needed only if the app is ever deployed publicly. Today it runs locally.
- Should F3 (persona fit) get its own buttons, e.g. "Pro rodinu", "Pro seniora"?
- Should F5 (tool use with a wider radius) be the next feature?
- Effort: if summaries feel shallow, try `medium` in `chatbot.EFFORT`.

---

## 6. Decisions log

| Date | Decision |
|---|---|
| 2026-11-21 | Created this file; provider is Claude, per roadmap.txt. |
| 2026-11-21 | v1 scope: F1 (summary), F2 (score) and F4 (follow-up chat); F7 walking times are included in the prompt data. |
| 2026-11-21 | Model: Claude Sonnet 5.5. |
| 2026-11-21 | UI: the summary generates automatically below the map and metrics; the follow-up chat input sits at the bottom of the page. |
| 2026-11-21 | Deployment: local only; the team has an API key. No rate limiting for now. |
| 2026-11-21 | Merged with the settings menu (category pills). The chatbot sees only the enabled categories and renders full-width below the map and metric columns. |
| 2026-11-21 | Layout change: the chat (summary, scrollable history of `CHAT_HEIGHT` px, inline chat input) sits in the right column next to the map; the metric cards moved under the map. Summary shortened to ≤ 3 bullets, ~80 words. |
| 2026-11-21 | The score comes from the app (`front_end.livability_score`, shown above the metric cards) and is passed to `build_context`. The chatbot repeats and explains it instead of inventing its own, so the page never shows two different scores. |
| 2026-11-21 | Categories turned off in the settings are passed to `build_context` as `hidden`. The chatbot treats them as the user's choice, not as missing amenities or data gaps. |

---

## 7. Implementation notes

- Files: [chatbot.py](chatbot.py) (logic) and [front_end.py](front_end.py) (`get_anthropic_key`, `get_chat_client`, `respond`, `show_chatbot`). `show_results(coords, address, enabled, col_map, col_text)` computes `score = livability_score(results)` once and calls `show_chatbot(address, results, score)` inside `col_text` (next to the map); the metric cards render full width below both columns.
- Settings to tune are constants at the top of `chatbot.py`: `MODEL`, `MAX_TOKENS`, `EFFORT`, `WALK_M_PER_MIN`, `TOP_N` and `INCOMPLETE`.
- When a new amenity type is added (CLAUDE.md, "Adding a new amenity type"), the chatbot picks it up automatically through `results`. If the dataset is incomplete, add it to `INCOMPLETE`.
- Cost estimate: one summary is about 1.5k input and a few hundred output tokens, roughly $0.01 per address with Sonnet 5.5.
- Verified: `build_context` on real data (Horní náměstí) and compiling `front_end.py`. **Not yet verified: a live API call** (no key in the dev environment).
