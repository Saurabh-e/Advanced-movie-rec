import requests
import streamlit as st

API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", layout="wide")

# =============================
# SAFE API
# =============================
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# =============================
# GRID (SAFE VERSION)
# =============================
def poster_grid(cards, cols=6):
    if not cards:
        st.warning("No data available")
        return

    for i in range(0, len(cards), cols):
        row = st.columns(cols)

        for j, col in enumerate(row):
            if i + j >= len(cards):
                break

            m = cards[i + j]

            with col:
                # SAFE IMAGE
                poster = m.get("poster_url") or m.get("poster_path")

                if poster:
                    if "http" not in poster:
                        poster = f"{TMDB_IMG}{poster}"
                    st.image(poster)

                # SAFE TITLE
                title = m.get("title") or m.get("name") or "No Title"
                st.write(title)

                # SAFE BUTTON
                tmdb_id = m.get("tmdb_id") or m.get("id")

                if tmdb_id:
                    if st.button("▶", key=f"{i}_{j}_{tmdb_id}"):
                        st.session_state.view = "details"
                        st.session_state.selected_tmdb_id = tmdb_id
                        st.rerun()

# =============================
# STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"

if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

# =============================
# HOME
# =============================
st.title("🎬 Movie Recommender")

if st.session_state.view == "home":

    query = st.text_input("Search movies")

    if query:
        data = api_get("/tmdb/search", {"query": query})

        if data and "results" in data:
            poster_grid(data["results"])

    else:
        data = api_get("/home", {"category": "popular", "limit": 24})

        if data:
            poster_grid(data)

# =============================
# DETAILS
# =============================
elif st.session_state.view == "details":

    if st.button("← Back"):
        st.session_state.view = "home"
        st.rerun()

    tmdb_id = st.session_state.selected_tmdb_id

    data = api_get(f"/movie/id/{tmdb_id}")

    if not data:
        st.error("Movie not found")
        st.stop()

    st.header(data.get("title", "No Title"))
    st.write(f"⭐ {data.get('vote_average', 'N/A')}")
    st.write(data.get("overview", "No description"))

    # =============================
    # RECOMMENDATIONS (SAFE)
    # =============================
    st.subheader("🎯 Recommendations")

    recs = api_get("/recommend/hybrid", {
        "tmdb_id": tmdb_id,
        "limit": 24
    })

    if recs and isinstance(recs, list):
        poster_grid(recs)
    else:
        st.warning("No recommendations found or API error")
