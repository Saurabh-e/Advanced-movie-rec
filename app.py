import requests
import streamlit as st

# =============================
# CONFIG
# =============================
# Cleaned up API base (using the production URL as default)
API_BASE = "https://movie-rec-466x.onrender.com" 
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
TMDB_BACKDROP = "https://image.tmdb.org/t/p/original" # Better quality for banners

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# STYLES (Modern, Glassmorphism, Hover Effects)
# =============================
st.markdown(
    """
<style>
    /* Main container spacing */
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }
    
    /* Typography */
    .small-muted { color: #888; font-size: 0.95rem; margin-bottom: 0.5rem; }
    .movie-title { font-size: 1.05rem; font-weight: 600; line-height: 1.3rem; height: 2.6rem; overflow: hidden; margin-top: 8px; text-align: center; }
    
    /* Cards with hover effects (Adapts to Light/Dark mode via rgba) */
    .card { 
        border: 1px solid rgba(128,128,128,0.2); 
        border-radius: 12px; 
        padding: 16px; 
        background: rgba(128,128,128,0.05); 
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    /* Genre Badges */
    .genre-badge {
        display: inline-block;
        padding: 4px 10px;
        margin: 2px 4px 2px 0;
        background-color: rgba(255, 75, 75, 0.15);
        color: #ff4b4b;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# STATE + ROUTING
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"  # home | details
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")
if qp_view in ("home", "details"):
    st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass

def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()

# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=30)
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"

def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                if poster:
                    st.image(poster, use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/500x750?text=No+Poster", use_column_width=True)
                
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)
                
                if st.button("Details", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}", use_container_width=True):
                    if tmdb_id:
                        goto_details(tmdb_id)
                st.markdown("</div>", unsafe_allow_html=True)

def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append({
                "tmdb_id": tmdb["tmdb_id"],
                "title": tmdb.get("title") or x.get("title") or "Untitled",
                "poster_url": tmdb.get("poster_url"),
            })
    return cards

def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    keyword_l = keyword.strip().lower()
    raw_items = []

    if isinstance(data, dict) and "results" in data:
        for m in data.get("results") or []:
            title = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            if not title or not tmdb_id: continue
            raw_items.append({
                "tmdb_id": int(tmdb_id), "title": title,
                "poster_url": f"{TMDB_IMG}{m.get('poster_path')}" if m.get("poster_path") else None,
                "release_date": m.get("release_date", ""),
            })
    elif isinstance(data, list):
        for m in data:
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title = (m.get("title") or "").strip()
            if not title or not tmdb_id: continue
            raw_items.append({
                "tmdb_id": int(tmdb_id), "title": title,
                "poster_url": m.get("poster_url"),
                "release_date": m.get("release_date", ""),
            })
    else:
        return [], []

    matched = [x for x in raw_items if keyword_l in x["title"].lower()]
    final_list = matched if matched else raw_items

    suggestions = []
    for x in final_list[:10]:
        year = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    cards = [{"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]} for x in final_list[:limit]]
    return suggestions, cards

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.title("🎬 MovieRec")
    st.markdown("Discover your next favorite film.")
    if st.button("🏠 Home", use_container_width=True, type="primary"):
        goto_home()
    
    st.divider()
    st.markdown("### Settings")
    grid_cols = st.slider("Grid Columns", min_value=3, max_value=8, value=5)

# ==========================================================
# VIEW: HOME
# ==========================================================
if st.session_state.view == "home":
    # Hero Search Section
    st.markdown("<h1 style='text-align: center;'>What are you watching next?</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        typed = st.text_input("Search movies...", placeholder="Type a movie title (e.g., Inception, The Matrix)...", label_visibility="collapsed")
    
    st.write("") # Spacer

    # SEARCH MODE
    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters for suggestions...")
        else:
            data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})
            if err or data is None:
                st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(data, typed.strip(), limit=24)
                
                if suggestions:
                    labels = ["-- Quick Select --"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Or jump directly to:", labels, index=0)
                    if selected != "-- Quick Select --":
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])
                
                st.markdown("### 🔎 Search Results")
                st.divider()
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")
        st.stop()

    # HOME FEED MODE
    st.markdown("### 🍿 Trending Now")
    
    # Modern Horizontal Category Selector
    home_category = st.radio(
        "Feed Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        horizontal=True,
        label_visibility="collapsed",
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    st.divider()

    home_cards, err = api_get_json("/home", params={"category": home_category, "limit": 24})
    if err or not home_cards:
        st.error(f"Home feed failed: {err or 'Unknown error'}")
        st.stop()

    poster_grid(home_cards, cols=grid_cols, key_prefix="home_feed")

# ==========================================================
# VIEW: DETAILS
# ==========================================================
elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected.")
        if st.button("← Back to Home"): goto_home()
        st.stop()

    # Fetch Details
    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if err or not data:
        st.error(f"Could not load details: {err or 'Unknown error'}")
        if st.button("← Back to Home"): goto_home()
        st.stop()

    # Back Navigation
    if st.button("← Back to Feed"):
        goto_home()

    # 1. Hero Backdrop Banner (If available)
    if data.get("backdrop_url"):
        # We manipulate the URL slightly if we want higher res, assuming the backend sends a standard path
        backdrop_hq = data["backdrop_url"].replace("w500", "original")
        st.image(backdrop_hq, use_column_width=True)

    st.write("") # Spacer

    # 2. Movie Info Core Layout
    left, right = st.columns([1, 2.5], gap="large")

    with left:
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)
        else:
            st.image("https://via.placeholder.com/500x750?text=No+Poster", use_column_width=True)

    with right:
        st.markdown(f"<h1 style='margin-bottom: 0;'>{data.get('title','')}</h1>", unsafe_allow_html=True)
        
        release = data.get("release_date", "Unknown Date")
        st.markdown(f"<div class='small-muted'>📆 Released: {release}</div>", unsafe_allow_html=True)
        
        # Genre Badges
        genres_html = ""
        for g in data.get("genres", []):
            genres_html += f"<span class='genre-badge'>{g['name']}</span>"
        if genres_html:
            st.markdown(genres_html, unsafe_allow_html=True)
        
        st.write("")
        st.markdown("### Synopsis")
        st.write(data.get("overview") or "No overview available for this title.")

    st.divider()

    # 3. Recommendations inside Tabs for cleaner UI
    st.markdown("### ✨ You Might Also Like")
    
    title = (data.get("title") or "").strip()
    if title:
        bundle, err2 = api_get_json(
            "/movie/search",
            params={"query": title, "tfidf_top_n": 15, "genre_limit": 15},
        )

        if not err2 and bundle:
            tab1, tab2 = st.tabs(["🔎 Because you watched this (Similar Story)", "🎭 More Like This (By Genre)"])
            
            with tab1:
                poster_grid(
                    to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
                    cols=grid_cols,
                    key_prefix="details_tfidf",
                )

            with tab2:
                poster_grid(
                    bundle.get("genre_recommendations", []),
                    cols=grid_cols,
                    key_prefix="details_genre",
                )
        else:
            genre_only, err3 = api_get_json("/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 15})
            if not err3 and genre_only:
                st.info("Showing movies with similar genres.")
                poster_grid(genre_only, cols=grid_cols, key_prefix="details_genre_fallback")
            else:
                st.warning("No recommendations available right now.")
    else:
        st.warning("No title available to compute recommendations.")
