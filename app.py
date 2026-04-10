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
# GLOBAL STYLE (NETFLIX STYLE)
# =============================
st.markdown("""
<style>
body {background-color:#0e1117; color:white;}
.block-container {padding-top:1rem; max-width:1400px;}
.movie-card:hover {transform:scale(1.05);}
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
    if not tmdb_id:
        return
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    st.session_state.history.append(tmdb_id)
    st.rerun()

# =============================
# API (SAFE)
# =============================
@st.cache_data(ttl=30)
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("API ERROR:", e)
        return None

# =============================
# HERO
# =============================
def hero_banner(movie):
    if not movie:
        return
    st.markdown(f"""
    <div style="position:relative;">
        <img src="{movie.get('backdrop_url','')}" 
        style="width:100%; height:350px; object-fit:cover; filter:brightness(40%); border-radius:15px;">
        <div style="position:absolute; bottom:30px; left:30px;">
            <h1>{movie.get('title','No Title')}</h1>
            <p style="max-width:600px;">{movie.get('overview','')[:150]}...</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================
# POSTER GRID (ADVANCED UI)
# =============================
def poster_grid(cards, cols=6):
    if not cards:
        st.warning("No movies found")
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
                title = m.get("title", "No Title")
                rating = m.get("rating", 0)
                tmdb_id = m.get("tmdb_id")

                st.markdown(f"""
                <div class="movie-card" style="position:relative;">
                    <img src="{poster}" style="width:100%; border-radius:12px;">
                    <div style="
                        position:absolute;
                        bottom:0;
                        width:100%;
                        background:linear-gradient(transparent, black);
                        padding:6px;
                        border-radius:0 0 12px 12px;
                    ">
                        <div style="font-size:12px;">{title}</div>
                        <div style="font-size:11px; color:#22c55e;">⭐ {rating}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button("▶", key=f"{tmdb_id}_{idx}"):
                    goto_details(tmdb_id)

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

    cols = st.slider("Columns", 4, 8, 6)

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

    hero = api_get("/home", {"category": "trending", "limit": 1})
    if hero:
        hero_banner(hero[0])

    query = st.text_input("🔍 Search movies...")

    if query:
        with st.spinner("Searching..."):
            data = api_get("/tmdb/search", {"query": query})

        if data and "results" in data:
            cards = []

            for m in data["results"]:
                try:
                    year = int(m.get("release_date", "2000")[:4])
                except:
                    year = 2000

                cards.append({
                    "tmdb_id": m.get("id"),
                    "title": m.get("title", "No Title"),
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None,
                    "year": year,
                    "rating": m.get("vote_average", 0)
                })

            cards = [
                c for c in cards
                if year_filter[0] <= c["year"] <= year_filter[1]
                and rating_filter[0] <= c["rating"] <= rating_filter[1]
            ]

            st.caption(f"{len(cards)} results")
            poster_grid(cards, cols)
        else:
            st.warning("No results found")

    else:
        cards = api_get("/home", {"category": category, "limit": 24})
        if cards:
            poster_grid(cards, cols)

    # HISTORY
    if st.session_state.history:
        st.markdown("### 🕘 Recently Viewed")
        hist = api_get("/recommend/genre", {
            "tmdb_id": st.session_state.history[-1],
            "limit": 12
        })
        if hist:
            poster_grid(hist, cols)

# =============================
# DETAILS
# =============================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id

    if st.button("← Back"):
        goto_home()

    data = api_get(f"/movie/id/{tmdb_id}")

    if not data:
        st.error("Failed to load movie")
        st.stop()

    # HERO
    st.markdown(f"""
    <div style="position:relative;">
        <img src="{data.get('backdrop_url','')}" 
        style="width:100%; height:400px; object-fit:cover; filter:brightness(40%); border-radius:15px;">
        <div style="position:absolute; bottom:30px; left:30px;">
            <h1>{data.get('title')}</h1>
            <p>{data.get('overview','')[:200]}...</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write(f"⭐ Rating: {data.get('vote_average', 0)}")

    # RECOMMENDATIONS
    st.markdown("## 🎯 Recommendations")

    with st.spinner("Fetching recommendations..."):
        time.sleep(0.3)
        rec = api_get("/movie/search", {"query": data.get("title")})

    if rec and "genre_recommendations" in rec:
        poster_grid(rec["genre_recommendations"], cols)
    else:
        st.warning("No recommendations found.")
