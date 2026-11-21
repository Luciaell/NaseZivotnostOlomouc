import os
import unicodedata

import anthropic
import folium
import requests
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.point import Point
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox

import back_end
import chatbot

st.set_page_config(page_title="Naše životnost Olomouc", layout="wide")  # must run before any other st.* call

USER_AGENT = "nase-zivotnost-ol/1.0"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
MIN_CHARS = 2      # suggestions appear after this many characters
MAX_RESULTS = 10

RADIUS_M = 1000
DEFAULT_CENTER = [49.5955, 17.2518]
DEFAULT_ZOOM = 12.5
SELECTED_ZOOM = 15

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


def find_missing(results: dict[str, list]) -> int:
    return sum(1 for found in results.values() if not found)


def circle_color(results: dict[str, list]) -> str:
    missing = find_missing(results)
    if missing == 0:
        return "green"
    if missing == 1:
        return "#ff6600"
    return "red"


def dist_color(dist: float) -> str:
    if dist < RADIUS_M / 2:
        return "green"
    if dist < RADIUS_M:
        return "orange"
    return "red"


def draw_selected_location(m: folium.Map, coords, color: str):
    folium.Circle(
        location=coords,
        radius=RADIUS_M,
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


def summary_heading(missing: int, results: dict[str, list]):
    if missing == 0:
        st.success(f"Všechny služby jsou dostupné v okruhu {RADIUS_M} m.")
    else:
        st.error(f"Chybí: {missing} z {len(results)} služeb.")


def show_metric(kind: str, found: list[dict]):
    style = KINDS.get(kind, DEFAULT_KIND)
    label = style.get("label", kind).capitalize()
    with st.container(border=True):
        if not found:
            st.metric(f":red[:material/{style['symbol']}: {label}]", f"> {RADIUS_M} m")
            st.caption("Žádné v okolí")
            return
        nearest = found[0]  # back_end returns results sorted by distance
        color = dist_color(nearest["distance_m"])
        st.metric(f":{color}[:material/{style['symbol']}: {label}]", f"{nearest['distance_m']} m")
        name = nearest["name"]
        if len(name) > 30:
            st.caption(name[:30] + "…", help=name)
        else:
            st.caption(name)


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
    with st.chat_message("assistant"):
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


def show_chatbot(address: str, results: dict[str, list]):
    st.subheader(":material/smart_toy: AI shrnutí okolí")
    key = get_anthropic_key()
    if not key:
        st.info("AI shrnutí je vypnuté: chybí ANTHROPIC_API_KEY v .streamlit/secrets.toml.")
        return
    client = get_chat_client(key)

    # One conversation per address and category selection; changing either starts over.
    chat_key = (address, tuple(results))
    chat = st.session_state.get("chat")
    if not chat or chat["key"] != chat_key:
        labels = {kind: style["label"] for kind, style in KINDS.items()}
        context = chatbot.build_context(address, results, RADIUS_M, labels)
        chat = {"key": chat_key, "messages": [{"role": "user", "content": context}]}
        st.session_state["chat"] = chat
    messages = chat["messages"]

    for msg in messages[1:]:   # messages[0] is the hidden data prompt
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if len(messages) == 1:     # summary not generated yet
        respond(client, messages)

    question = st.chat_input("Zeptejte se na okolí této adresy…")
    if question:
        messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        if not respond(client, messages):
            messages.pop()     # keep the history valid for the next try


def show_results(coords, address: str, enabled, col_map, col_text):
    m = make_map(coords, SELECTED_ZOOM)
    results = {kind: back_end.find_institutions(coords, kind, RADIUS_M / 1000)
               for kind in enabled}
    for kind, found in results.items():
        for item in found:
            add_marker(m, kind, item)
    draw_selected_location(m, coords, circle_color(results))

    with col_map:
        st_folium(m, use_container_width=True, height=500, key="map", returned_objects=[])
    with col_text:
        if not enabled:
            st.info("Vyberte alespoň jednu kategorii.")
        else:
            summary_heading(find_missing(results), results)
            grid = st.columns(2)
            for i, (kind, found) in enumerate(results.items()):
                with grid[i % 2]:
                    show_metric(kind, found)

    if enabled:
        show_chatbot(address, results)   # full width, below both columns


def settings() -> list[str]:
    with st.popover("Nastavení zobrazených kategorií"):
        st.header("Nastavení")
        return st.pills(
            "Zobrazit kategorie",
            options=list(back_end.TYPES),
            default=list(back_end.TYPES),
            selection_mode="multi",
            format_func=lambda k: KINDS.get(k, DEFAULT_KIND).get("label", k).capitalize(),
        )

# --- page ---

selected = st_searchbox(suggest, placeholder="Zadejte adresu", key="address_search")

col_map, col_text = st.columns([1, 1])

with col_text:
    enabled = settings()

if not selected:
    with col_map:
        st_folium(make_map(DEFAULT_CENTER, DEFAULT_ZOOM), use_container_width=True,
                  height=500, key="map", returned_objects=[])
else:
    coords = addresses.get(selected) or search_location(selected)
    if not coords:
        st.error("Adresa nenalezena.")
    elif not back_end.is_in_olomouc(*coords):
        st.error("Adresa je mimo Olomouc.")
    else:
        show_results(coords, selected, enabled, col_map, col_text)
