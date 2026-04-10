import requests
import streamlit as st
import time

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# GLOBAL STYLES (GLASS + MODERN)
# =============================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #f5f5f5;
    font-family: 'Segoe UI', sans-serif;
}
.block-container {
    padding-top: 1rem;
    max-width: 1400px;
}
.card {
    border-radius: 18px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    border: 1px solid rgba(255,255,255,0.1);
    padding: 6px;
}
.card:hover {
    transform: translateY(-8px) scale(1.05);
    box-shadow: 0 16px 40px rgba(0,0,0,0.6);
}
.movie-title {
    font-size: 0.95rem;
    padding-top: 8px;
    color: #f5f5f5;
    font-weight: 600;
    text-align: center;
}
.small-muted {
    color: #9ca3af;
    font-size: 0.8rem;
}
.sidebar .stButton>button {
    background: linear-gradient(90deg, #ff416c, #ff4b2b);
    color: white;
    border-radius: 10px;
    font-weight: bold;
    transition: 0.3s;
}
.sidebar .stButton>button:hover {
    background: linear-gradient(90deg, #ff4b2b, #ff416c);
    transform: scale(1.05);
}
.hero-banner {
    position: relative;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    margin-bottom: 20px;
}
.hero-banner img {
    width: 100%;
    height: 350px;
    object-fit: cover;
    filter: brightness(45%);
}
.hero-banner .overlay {
    position: absolute;
    bottom: 30px;
    left: 40px;
    color: white;
}
.hero-banner h2 {
    font-size: 2rem;
    font-weight: bold;
}
.hero-banner p {
    max-width: 650px;
    font-size: 1rem;
    color: #d1d5db;
}
</style>
""", unsafe_allow_html=True)

# =============================
# STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"

if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

if "history" not in st.session_state:
    st.session_state.history = []

# =============================
# NAVIGATION
# =============================
def goto_home():
    st.session_state.view = "home"
    st.rerun()

def goto_details(tmdb_id):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    st.session_state.history.append(tmdb_id)
    st.rerun()

# =============================
# API
# =============================
@st.cache_data(ttl=30)
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
        return r.json()
    except:
        return None

# =============================
# HERO BANNER
# =============================
def hero_banner(movie):
    if not movie:
        return
    st.markdown(f"""
    <div class="hero-banner">
        <img src="{movie.get('backdrop_url','')}">
        <div class="overlay">
            <h2>{movie.get('title')}</h2>
            <p>{movie.get('overview','')[:180]}...</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# GRID
# =============================
def poster_grid(cards, cols=6):
    if not cards:
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0

    for _ in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            m = cards[idx]
            idx += 1

            with colset[c]:
                poster = m.get("poster_url")
                if poster:
                    st.markdown(f"""
                    <div class="card">
                        <img src="{poster}" style="width:100%; border-radius:12px;">
                    </div>
                    """, unsafe_allow_html=True)

                if st.button("▶", key=f"{idx}_{m.get('tmdb_id')}"):
                    goto_details(m.get("tmdb_id"))

                st.markdown(f"<div class='movie-title'>{m.get('title')}</div>", unsafe_allow_html=True)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.title("🎬 Menu")

    if st.button("🏠 Home"):
        goto_home()

    st.markdown("---")

    category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing"]
    )

    cols = st.slider("Grid Columns", 4, 8, 6)

    st.markdown("### 🎛️ Filters")
    year_filter = st.slider("Year", 1980, 2025, (2000, 2025))
    rating_filter = st.slider("Rating", 0.0, 10.0, (5.0, 10.0))

# =============================
# HEADER
# =============================
st.title("🎬 Advanced Movie Recommender")

# =============================
# HOME
# =============================
if st.session_state.view == "home":

    # HERO
    hero = api_get("/home", {"category": "trending", "limit": 1})
    if hero:
        hero_banner(hero[0])

    # SEARCH
    query = st.text_input("Search movies...")

    if query:
        with st.spinner("Searching..."):
            data = api_get("/tmdb/search", {"query": query})

        if data and "results" in data:
            cards = [
                {
                    "tmdb_id": m["id"],
                    "title": m["title"],
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None,
                    "year": int(m.get("release_date", "2000")[:4]) if m.get("release_date") else 2000,
                    "rating": m.get("vote_average", 0)
                }
                for m in data["results"]
            ]

            # FILTER
            cards = [
                c for c in cards
                if year_filter[0] <= c["year"] <= year_filter[1]
                and rating_filter[0] <= c["rating"] <= rating_filter[1]
            ]

            st.caption(f"{len(cards)} results found")
            poster_grid(cards, cols)

    else:
        cards = api_get("/home", {"category": category, "limit": 24})
        if cards:
            poster_grid(cards, cols)

    # HISTORY
    if st.session_state.history:
        st.markdown("### 🕘 Recently Viewed")
        hist_cards = api_get("/recommend/genre", {
            "tmdb_id": st.session_state.history[-1],
            "limit": 12
        })
        if hist_cards:
            poster_grid(hist_cards, cols)

# =============================
# DETAILS (ONLY RECOMMENDATIONS)
# =============================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id

    if st.button("← Back"):
        goto_home()

    data = api_get(f"/movie/id/{tmdb_id}")

    if not data:
        st.error("Failed to load movie")
        st.stop()

    # BACKDROP HEADER
    st.markdown(f"""
    <div style="position:relative;">
        <img src="{data.get('backdrop_url','')}" 
        style="width:100%; height:350px; object-fit:cover; filter:brightness(50%); border-radius:16px;">
        <h1 style="position:absolute; bottom:20px; left:30px;">
            {data.get('title')}
        </h1>
    </div>
    """, unsafe_allow_html=True)

    # RATING
    rating = data.get("vote_average", 0)
    st.markdown(f"""
    <span style="background:#22c55e; padding:6px 10px; border-radius:8px;">
    ⭐ {rating}
    </span>
    """, unsafe_allow_html=True)

    # RECOMMENDATIONS ONLY
    st.markdown("## 🎯 Recommendations")

    placeholder = st.empty()

    with placeholder.container():
        with
