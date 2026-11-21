import os
import unicodedata

import anthropic
import folium
import requests
import streamlit as st
from geopy.geocoders import Nominatim
from folium.plugins import HeatMap
from geopy.point import Point
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox

import back_end
import chatbot

st.set_page_config(page_title="Walker15", layout="wide")  # must run before any other st.* call

USER_AGENT = "walker15/1.0"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
MIN_CHARS = 2      # suggestions appear after this many characters
MAX_RESULTS = 10

# Search radius, chosen with the sidebar slider (metres).
DEFAULT_RADIUS_M = 1000
MIN_RADIUS_M, MAX_RADIUS_M, RADIUS_STEP_M = 200, 2000, 100
DEFAULT_CENTER = [49.5955, 17.2518]
DEFAULT_ZOOM = 12.5
M_PER_DEG_LAT, M_PER_DEG_LON = 111_320, 72_100   # at Olomouc's latitude, to fit the circle in view
MAP_HEIGHT = 500
METRIC_COLUMNS = 4
CHAT_HEIGHT = 380  # scrollable chat history; with the heading and input it lines up with the map
CHAT_ICON = ":material/near_me:"          # diagonal arrowhead in the chat heading
ASSISTANT_AVATAR = ":material/smart_toy:"  # robot next to the AI's messages

# One entry per type in back_end.TYPES: Czech label, map marker style (Font Awesome
# `icon`) and the summary icon (`symbol`, a Google Material Symbol name).
KINDS = {
    "bus_stops":         {"label": "zastávka autobusu", "color": "blue",       "icon": "bus",           "symbol": "directions_bus"},
    "tram_stops":        {"label": "zastávka tramvaje", "color": "darkblue",   "icon": "train-tram",    "symbol": "tram"},
    "train_stations":    {"label": "vlakové nádraží",   "color": "cadetblue",  "icon": "train",         "symbol": "train"},
    "kindergartens":     {"label": "mateřská škola",    "color": "orange",     "icon": "child",         "symbol": "child_care"},
    "schools":           {"label": "základní škola",    "color": "red",        "icon": "school",        "symbol": "school"},
    "libraries":         {"label": "knihovna",          "color": "darkred",    "icon": "book",          "symbol": "local_library"},
    "pharmacies":        {"label": "lékárna",           "color": "green",      "icon": "pills",         "symbol": "local_pharmacy"},
    "supermarkets":      {"label": "supermarket",       "color": "purple",     "icon": "cart-shopping", "symbol": "shopping_cart"},
    "restaurants":       {"label": "restaurace",        "color": "beige",      "icon": "utensils",      "symbol": "restaurant"},
    "theatres":          {"label": "divadlo",           "color": "darkpurple", "icon": "masks-theater", "symbol": "theater_comedy"},
    "cinemas":           {"label": "kino",              "color": "pink",       "icon": "film",          "symbol": "movie"},
    "gyms":              {"label": "posilovna",         "color": "darkgreen",  "icon": "dumbbell",      "symbol": "fitness_center"},
    "sports_halls":      {"label": "sportovní hala",    "color": "lightgreen", "icon": "volleyball",    "symbol": "sports_volleyball"},
    "places_of_worship": {"label": "kostel",            "color": "black",      "icon": "church",        "symbol": "church"},
}
DEFAULT_KIND = {"color": "gray", "icon": "location-dot", "symbol": "location_on"}

# Metric card sections, in display order. Types missing here go under "Ostatní".
GROUPS = {
    "Doprava":            ("bus_stops", "tram_stops", "train_stations"),
    "Vzdělání":           ("kindergartens", "schools", "libraries"),
    "Každodenní potřeby": ("supermarkets", "pharmacies"),
    "Volný čas":          ("restaurants", "theatres", "cinemas", "gyms", "sports_halls",
                           "places_of_worship"),
}

# Livability score (0-10), computed without the AI. Everyday needs make up most of it;
# the remaining types are a bonus. Same weighting as the chatbot prompt.
TRANSPORT = ("bus_stops", "tram_stops")   # either one covers the transport need
EVERYDAY = ("kindergartens", "schools", "pharmacies", "supermarkets")
EVERYDAY_SHARE = 0.8                      # 8 of 10 points; the bonus types give the other 2
EDGE_SCORE = 0.3                          # an amenity at the radius edge counts 30 %, at the door 100 %

# Start screen examples: the first known address on each street (free text if none is known).
EXAMPLE_STREETS = ["Horní náměstí", "třída Svobody", "Brněnská", "Foerstrova"]

# Felt-temperature heatmap (survey data from back_end.heat_points), toggled in the sidebar.
HEAT_GRADIENT = {0.2: "#2c7bb6", 0.4: "#abd9e9", 0.6: "#ffffbf", 0.8: "#fdae61", 1.0: "#d7191c"}
HEAT_RADIUS = 25      # px per point
HEAT_BLUR = 20
HEAT_MAX_ZOOM = 12    # full intensity from this zoom on, so the layer doesn't fade at city zoom

CARTO_STYLES = {"voyager": "voyager", "positron": "light_all", "dark_matter": "dark_all"}
CARTO_ATTR = (
    '&copy; přispěvatelé <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, '
    '&copy; <a href="https://carto.com/attributions">CARTO</a>'
)

geolocator = Nominatim(user_agent=USER_AGENT)


# --- address search ---

def normalize(s: str) -> str:
    # Lowercase and strip diacritics, so 'kat' matches 'Kateřinská'.
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


@st.cache_data(show_spinner=False)
def get_city_bbox(city: str):
    loc = geolocator.geocode(city, timeout=10)
    if not loc:
        return None
    south, north, west, east = map(float, loc.raw["boundingbox"])
    return (south, west, north, east)


@st.cache_data(ttl=60 * 60 * 24, show_spinner="Načítání adres...")
def fetch_addresses() -> dict[str, list[float]]:
    # Returns {"Kateřinská 12": [lat, lon], ...} for all address points in the box.
    south, west, north, east = get_city_bbox("Olomouc")
    query = f"""
    [out:json][timeout:40];
    nwr["addr:housenumber"]["addr:street"]({south},{west},{north},{east});
    out tags center qt;
    """
    last_error = None
    for url in OVERPASS_URLS:
        try:
            r = requests.post(url, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=60)
            r.raise_for_status()
            data = r.json()
            if "elements" not in data:
                raise RuntimeError(data.get("remark", "odpověď neobsahuje žádná data"))
            addresses = {}
            for el in data["elements"]:
                tags = el["tags"]
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if lat is None:
                    continue
                # Czech style: conscription number / orientation number (e.g. 123/4)
                cp, co = tags.get("addr:conscriptionnumber"), tags.get("addr:streetnumber")
                number = f"{cp}/{co}" if cp and co else tags["addr:housenumber"]
                addresses[f"{tags['addr:street']} {number}"] = [lat, lon]
            return addresses
        except Exception as e:
            last_error = e
    raise RuntimeError(f"žádný server Overpass neodpověděl: {last_error}")  # not cached; shown in the UI warning


def get_addresses() -> dict[str, list[float]]:
    try:
        return fetch_addresses()
    except Exception as e:
        st.warning(f"Seznam adres není dostupný ({e}). Textové vyhledávání stále funguje.")
        return {}


@st.cache_data(show_spinner=False)
def search_location(query: str):
    bbox = get_city_bbox("Olomouc")
    if bbox is None:
        return None
    south, west, north, east = bbox
    loc = geolocator.geocode(
        query,
        timeout=10,
        viewbox=[Point(south, west), Point(north, east)],
        bounded=True,
        addressdetails=True,
    )
    return [loc.latitude, loc.longitude] if loc else None


addresses = get_addresses()
normalized = [(normalize(label), label) for label in sorted(addresses)]


def suggest(searchterm: str) -> list[str]:
    # Called by the searchbox on every keystroke.
    if len(searchterm) < MIN_CHARS:
        return []
    term = normalize(searchterm)
    starts = [lab for n, lab in normalized if n.startswith(term)]
    contains = [lab for n, lab in normalized if term in n and not n.startswith(term)]
    results = (starts + contains)[:MAX_RESULTS]
    # let the user pick their exact text even if it's not in the list
    if searchterm not in results:
        results.append(searchterm)
    return results


# --- map ---

def get_carto_key() -> str | None:
    try:
        return st.secrets["CARTO_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("CARTO_API_KEY")


def make_map(coords, zoom, style="voyager") -> folium.Map:
    key = get_carto_key()
    if not key:
        return folium.Map(location=coords, zoom_start=zoom)   # plain OSM fallback
    return folium.Map(
        location=coords,
        zoom_start=zoom,
        tiles=f"https://basemaps.cartocdn.com/rastertiles/{CARTO_STYLES[style]}/{{z}}/{{x}}/{{y}}{{r}}.png?key={key}",
        attr=CARTO_ATTR,
    )


def add_heat_layer(m: folium.Map):
    HeatMap(
        [list(p) for p in back_end.heat_points()],
        name="Pocitová teplota",
        radius=HEAT_RADIUS,
        blur=HEAT_BLUR,
        max_zoom=HEAT_MAX_ZOOM,
        min_opacity=0.3,
        gradient=HEAT_GRADIENT,
    ).add_to(m)


def heat_legend():
    st.caption(
        ":material/thermostat: **Pocitová teplota v létě** (průzkum mezi obyvateli, 2020): "
        ":blue[modrá] = příjemně, :orange[oranžová] až :red[červená] = horko."
    )


def show_map(m: folium.Map, show_heat: bool):
    if show_heat:
        add_heat_layer(m)
    st_folium(m, use_container_width=True, height=MAP_HEIGHT, key="map", returned_objects=[])
    if show_heat:
        heat_legend()


def find_missing(results: dict[str, list]) -> int:
    return sum(1 for found in results.values() if not found)


def circle_color(results: dict[str, list]) -> str:
    missing = find_missing(results)
    if missing == 0:
        return "green"
    if missing == 1:
        return "#ff6600"
    return "red"


def dist_color(dist: float, radius: int) -> str:
    if dist < radius / 2:
        return "green"
    if dist < radius:
        return "orange"
    return "red"


def fit_radius(m: folium.Map, coords, radius: int):
    # Zoom so the whole radius circle is in view, whatever its size.
    lat, lon = coords
    dlat, dlon = radius / M_PER_DEG_LAT, radius / M_PER_DEG_LON
    m.fit_bounds([[lat - dlat, lon - dlon], [lat + dlat, lon + dlon]])


def draw_selected_location(m: folium.Map, coords, color: str, radius: int):
    folium.Circle(
        location=coords,
        radius=radius,
        color=color,
        weight=1,
        fill=True,
        fill_color=color,
        fill_opacity=0.1,
    ).add_to(m)
    icon = folium.Icon(color=color, icon="house", prefix="fa")
    folium.Marker(coords, icon=icon, tooltip="Vybraná adresa").add_to(m)


def add_marker(m: folium.Map, kind: str, item: dict):
    style = KINDS.get(kind, DEFAULT_KIND)
    folium.Marker(
        location=[item["lat"], item["lon"]],
        tooltip=f"{item['name']} ({item['distance_m']} m)",
        icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa"),
    ).add_to(m)


def summary_heading(missing: int, results: dict[str, list], radius: int):
    if missing == 0:
        st.success(f"Všechny služby jsou dostupné v okruhu {radius} m.")
    else:
        st.error(f"Chybí: {missing} z {len(results)} služeb.")


# --- livability score ---

def amenity_score(found: list[dict], radius: int) -> float:
    """0 when none is in the radius, else 1 at the door falling to EDGE_SCORE at the edge."""
    if not found:
        return 0.0
    share = min(found[0]["distance_m"], radius) / radius
    return 1 - (1 - EDGE_SCORE) * share


def livability_score(results: dict[str, list], radius: int) -> float | None:
    everyday, bonus = [], []
    transport = [results[k] for k in TRANSPORT if k in results]
    if transport:
        everyday.append(max(amenity_score(found, radius) for found in transport))
    for kind, found in results.items():
        if kind in TRANSPORT:
            continue
        if not found and kind in chatbot.INCOMPLETE:
            continue   # incomplete data must not lower the score
        (everyday if kind in EVERYDAY else bonus).append(amenity_score(found, radius))

    def mean(xs):
        return sum(xs) / len(xs)

    if everyday and bonus:
        return 10 * (EVERYDAY_SHARE * mean(everyday) + (1 - EVERYDAY_SHARE) * mean(bonus))
    if everyday or bonus:
        return 10 * mean(everyday or bonus)
    return None


def show_score(score: float | None, radius: int):
    if score is None:
        return
    color = "green" if score >= 7 else "orange" if score >= 4 else "red"
    st.metric(
        f":{color}[:material/star: Hodnocení lokality]",
        f"{score:.1f} / 10",
        help=f"Vypočteno z dostupnosti služeb v okruhu {radius} m. Doprava, obchod, lékárna, "
             f"školka a škola tvoří {EVERYDAY_SHARE * 10:.0f} bodů, ostatní služby jsou bonus. "
             "Čím blíž služba je, tím víc bodů.",
    )


# --- metric cards ---

def show_metric(kind: str, found: list[dict], radius: int):
    style = KINDS.get(kind, DEFAULT_KIND)
    label = style.get("label", kind).capitalize()
    with st.container(border=True):
        if not found:
            st.metric(f":red[:material/{style['symbol']}: {label}]", f"> {radius} m")
            st.caption("Žádné v okolí")
            return
        nearest = found[0]  # back_end returns results sorted by distance
        color = dist_color(nearest["distance_m"], radius)
        st.metric(f":{color}[:material/{style['symbol']}: {label}]", f"{nearest['distance_m']} m")
        walk = f":material/directions_walk: {chatbot.walk_minutes(nearest['distance_m'])} min"
        name = nearest["name"]
        if len(name) > 30:
            st.caption(f"{walk} · {name[:30]}…", help=name)
        else:
            st.caption(f"{walk} · {name}")


def show_metric_groups(results: dict[str, list], radius: int):
    grouped = {kind for kinds in GROUPS.values() for kind in kinds}
    sections = {**GROUPS, "Ostatní": tuple(k for k in results if k not in grouped)}
    for title, kinds in sections.items():
        shown = [kind for kind in kinds if kind in results]
        if not shown:
            continue
        st.markdown(f"**{title}**")
        grid = st.columns(METRIC_COLUMNS)
        for i, kind in enumerate(shown):
            with grid[i % METRIC_COLUMNS]:
                show_metric(kind, results[kind], radius)


# --- AI chatbot (see CHATBOT.md) ---

def get_anthropic_key() -> str | None:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("ANTHROPIC_API_KEY")


@st.cache_resource
def get_chat_client(api_key: str) -> anthropic.Anthropic:
    return chatbot.make_client(api_key)


def respond(client: anthropic.Anthropic, messages: list[dict]) -> bool:
    """Stream one assistant reply into the page and append it to `messages`."""
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        try:
            text = st.write_stream(chatbot.stream_reply(client, messages))
        except anthropic.AuthenticationError:
            st.error("Neplatný klíč ANTHROPIC_API_KEY.")
            return False
        except anthropic.RateLimitError:
            st.error("Příliš mnoho dotazů, zkuste to prosím za chvíli.")
            return False
        except anthropic.APIStatusError as e:
            st.error(f"Chyba AI služby ({e.status_code}).")
            return False
        except anthropic.APIConnectionError:
            st.error("AI služba není dostupná, zkontrolujte připojení.")
            return False
    messages.append({"role": "assistant", "content": text})
    return True


def show_chatbot(address: str, results: dict[str, list], score: float | None, radius: int):
    """Render the chat in the current container (the column next to the map)."""
    st.subheader(f"{CHAT_ICON} Shrnutí")
    key = get_anthropic_key()
    if not key:
        st.info("AI shrnutí je vypnuté: chybí ANTHROPIC_API_KEY v .streamlit/secrets.toml.")
        return
    client = get_chat_client(key)

    # One conversation per address, category selection and radius; changing any starts over.
    chat_key = (address, tuple(results), radius)
    chat = st.session_state.get("chat")
    if not chat or chat["key"] != chat_key:
        labels = {kind: style["label"] for kind, style in KINDS.items()}
        hidden = [kind for kind in back_end.TYPES if kind not in results]   # turned off in settings
        context = chatbot.build_context(address, results, radius, labels, score, hidden)
        chat = {"key": chat_key, "messages": [{"role": "user", "content": context}]}
        st.session_state["chat"] = chat
    messages = chat["messages"]

    # Scrollable history keeps the column roughly as tall as the map.
    history = st.container(height=CHAT_HEIGHT)
    question = st.chat_input("Zeptejte se na okolí této adresy…")

    with history:
        for msg in messages[1:]:   # messages[0] is the hidden data prompt
            avatar = ASSISTANT_AVATAR if msg["role"] == "assistant" else None
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if len(messages) == 1:     # summary not generated yet
            respond(client, messages)

        if question:
            messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            if not respond(client, messages):
                messages.pop()     # keep the history valid for the next try


def show_results(coords, address: str, enabled, show_heat: bool, radius: int, col_map, col_text):
    m = make_map(coords, DEFAULT_ZOOM)
    fit_radius(m, coords, radius)
    results = {kind: back_end.find_institutions(coords, kind, radius / 1000)
               for kind in enabled}
    for kind, found in results.items():
        for item in found:
            add_marker(m, kind, item)
    draw_selected_location(m, coords, circle_color(results), radius)
    score = livability_score(results, radius)   # shown on the page and given to the chatbot

    with col_map:
        show_map(m, show_heat)
    with col_text:
        if not enabled:
            st.info("Vyberte alespoň jednu kategorii.")
        else:
            show_chatbot(address, results, score, radius)   # AI summary next to the map

    if enabled:   # score and metric cards full width, below both columns
        col_score, col_heading = st.columns([1, 3], vertical_alignment="center")
        with col_score:
            show_score(score, radius)
        with col_heading:
            summary_heading(find_missing(results), results, radius)
        show_metric_groups(results, radius)


def settings() -> tuple[list[str], bool, int]:
    """Sidebar settings: (enabled categories, show the heatmap, radius in metres)."""
    with st.sidebar:   # left side of the screen; collapsible
        st.header(":material/settings: Nastavení")
        radius = st.slider(
            "Okruh hledání",
            min_value=MIN_RADIUS_M,
            max_value=MAX_RADIUS_M,
            value=DEFAULT_RADIUS_M,
            step=RADIUS_STEP_M,
            format="%d m",
            key="radius",
            help="Jak daleko od adresy se hledají služby. Mění mapu, karty, hodnocení i AI shrnutí.",
        )
        enabled = st.pills(
            "Zobrazit kategorie",
            options=list(back_end.TYPES),
            default=list(back_end.TYPES),
            selection_mode="multi",
            format_func=lambda k: KINDS.get(k, DEFAULT_KIND).get("label", k).capitalize(),
        )
        st.subheader("Vrstvy mapy")
        show_heat = st.toggle(
            "Pocitová teplotní mapa",
            value=False,
            help="Kde se lidé v Olomouci cítí během horkých letních dní nepříjemně (červená) "
                 "nebo příjemně (modrá). Data z průzkumu města z roku 2020.",
        )
    return enabled, show_heat, radius

# --- start screen ---

def example_addresses() -> list[str]:
    examples = []
    for street in EXAMPLE_STREETS:
        prefix = normalize(street) + " "
        match = next((label for n, label in normalized if n.startswith(prefix)), None)
        examples.append(match or street)   # free text goes through Nominatim
    return examples


def bump_search_key():
    # A new key recreates the searchbox, so it picks up the new default.
    st.session_state["search_gen"] = st.session_state.get("search_gen", 0) + 1


def pick_example(address: str):
    st.session_state["example"] = address
    bump_search_key()


def clear_example():
    # Called when the user clears the searchbox; otherwise the example would come back.
    if st.session_state.pop("example", None) is not None:
        bump_search_key()


def show_intro(radius: int):
    st.title("Walker15")
    st.markdown(
        f"Zadejte adresu v Olomouci a zjistěte, jak se tam žije. Aplikace ukáže, co je "
        f"v okruhu **{radius} m** (nastavíte vlevo): zastávky, školy a školky, obchody, lékárny i volný čas. "
        "Lokalitu ohodnotí a AI ji shrne a odpoví na vaše dotazy."
    )
    st.caption("Vyzkoušejte například:")
    for address in example_addresses():
        st.button(address, icon=":material/location_on:", on_click=pick_example, args=(address,))


# --- page ---

example = st.session_state.get("example")
selected = st_searchbox(
    suggest,
    placeholder="Zadejte adresu",
    key=f"address_search_{st.session_state.get('search_gen', 0)}",
    default=example,
    default_searchterm=example or "",
    default_options=[example] if example else None,
    reset_function=clear_example,
)

enabled, show_heat, radius = settings()

col_map, col_text = st.columns([1, 1])

if not selected:
    with col_map:
        show_map(make_map(DEFAULT_CENTER, DEFAULT_ZOOM), show_heat)
    with col_text:
        show_intro(radius)
else:
    coords = addresses.get(selected) or search_location(selected)
    if not coords:
        st.error("Adresa nenalezena.")
    elif not back_end.is_in_olomouc(*coords):
        st.error("Adresa je mimo Olomouc.")
    else:
        show_results(coords, selected, enabled, show_heat, radius, col_map, col_text)
