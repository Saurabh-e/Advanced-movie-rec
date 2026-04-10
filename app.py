import requests
import streamlit as st

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# GLOBAL STYLES
# =============================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #f5f5f5;
}
.card {
    border-radius: 18px;
    overflow: hidden;
    background: rgba(255,255,255,0.05);
    padding: 6px;
    transition: 0.3s;
}
.card:hover {
    transform: scale(1.05);
}
.movie-title {
    font-size: 0.9rem;
    text-align: center;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# =============================
# SESSION STATE
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
# API CALL
# =============================
@st.cache_data(ttl=30)
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        return r.json()
    except:
        return None

# =============================
# GRID DISPLAY
# =============================
def poster_grid(cards, cols=6):
    if not cards:
        return

    for i in range(0, len(cards), cols):
        row = st.columns(cols)
        for j, col in enumerate(row):
            if i + j >= len(cards):
                break

            m = cards[i + j]
            with col:
                if m.get("poster_url"):
                    st.image(m["poster_url"])

                if st.button("▶", key=f"{i+j}_{m.get('tmdb_id')}"):
                    goto_details(m.get("tmdb_id"))

                st.markdown(f"<div class='movie-title'>{m.get('title')}</div>", unsafe_allow_html=True)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.title("🎬 Menu")

    if st.button("🏠 Home"):
        goto_home()

    category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing"]
    )

    cols = st.slider("Columns", 4, 8, 6)

    year_filter = st.slider("Year", 1980, 2025, (2000, 2025))
    rating_filter = st.slider("Rating", 0.0, 10.0, (5.0, 10.0))

# =============================
# TITLE
# =============================
st.title("🎬 Movie Recommender")

# =============================
# HOME VIEW
# =============================
if st.session_state.view == "home":

    query = st.text_input("Search movies...")

    if query:
        with st.spinner("Searching..."):
            data = api_get("/tmdb/search", {"query": query})

        if data and "results" in data:
            cards = []
            for m in data["results"]:
                year = int(m.get("release_date", "2000")[:4]) if m.get("release_date") else 2000
                rating = m.get("vote_average", 0)

                if year_filter[0] <= year <= year_filter[1] and rating_filter[0] <= rating <= rating_filter[1]:
                    cards.append({
                        "tmdb_id": m["id"],
                        "title": m["title"],
                        "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None
                    })

            st.write(f"{len(cards)} results")
            poster_grid(cards, cols)

    else:
        cards = api_get("/home", {"category": category, "limit": 24})
        if cards:
            poster_grid(cards, cols)

    # HISTORY
    if st.session_state.history:
        st.subheader("Recently Viewed")

        hist_cards = api_get("/recommend/genre", {
            "tmdb_id": st.session_state.history[-1],
            "limit": 12
        })

        if hist_cards:
            poster_grid(hist_cards, cols)

# =============================
# DETAILS VIEW
# =============================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id

    if st.button("← Back"):
        goto_home()

    data = api_get(f"/movie/id/{tmdb_id}")

    if not data:
        st.error("Failed to load movie")
        st.stop()

    # TITLE + IMAGE
    st.image(data.get("backdrop_url", ""))
    st.header(data.get("title"))

    st.write(f"⭐ Rating: {data.get('vote_average', 0)}")
    st.write(data.get("overview", ""))

    # =============================
    # RECOMMENDATIONS (FIXED)
    # =============================
    st.subheader("🎯 Recommendations")

    with st.spinner("Fetching recommendations..."):
        recs = api_get("/recommend/hybrid", {
            "tmdb_id": tmdb_id,
            "limit": 24
        })

    if recs:
        poster_grid(recs, cols)
    else:
        st.warning("No recommendations found")
