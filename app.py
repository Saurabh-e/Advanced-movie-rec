import requests
import streamlit as st
import time

# =============================
# CONFIG & PAGE SETUP
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
FALLBACK_IMG = "https://via.placeholder.com/500x750?text=No+Image"

st.set_page_config(page_title="Cinematch Dashboard", page_icon="🍿", layout="wide")

# =============================
# GLOBAL STYLE (CLEAN DASHBOARD)
# =============================
st.markdown("""
<style>
    /* Minimalist styling for containers */
    div[data-testid="stVerticalBlock"] { gap: 0.5rem; }
    .movie-title { font-size: 1.4rem; font-weight: 600; margin-bottom: 0.2rem; }
    .movie-meta { font-size: 0.9rem; color: #555; margin-bottom: 1rem; }
    hr { margin: 1em 0; }
</style>
""", unsafe_allow_html=True)

# =============================
# STATE MANAGEMENT
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None
if "history" not in st.session_state:
    st.session_state.history = []

# =============================
# NAVIGATION CALLBACKS
# =============================
def goto_home():
    st.session_state.view = "home"
    st.rerun()

def goto_details(tmdb_id):
    if not tmdb_id:
        return
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    if tmdb_id not in st.session_state.history:
        st.session_state.history.append(tmdb_id)
    st.rerun()

# =============================
# API FETCHING
# =============================
@st.cache_data(ttl=60)
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("API ERROR:", e)
        return None

# =============================
# UI COMPONENTS
# =============================
def render_list_view(cards):
    """Renders movies as horizontal data rows instead of a grid."""
    if not cards:
        st.info("No movies found matching your criteria.")
        return

    for idx, m in enumerate(cards):
        tmdb_id = m.get("tmdb_id")
        poster = m.get("poster_url") or FALLBACK_IMG
        title = m.get("title", "Unknown Title")
        year = m.get("year", "N/A")
        rating = m.get("rating", 0.0)
        overview = m.get("overview", "No synopsis available.")[:180] + "..."

        with st.container():
            col1, col2, col3 = st.columns([1, 6, 2])
            
            with col1:
                st.image(poster, use_container_width=True)
                
            with col2:
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='movie-meta'>📅 {year} | ⭐ {round(rating, 1)}/10</div>", unsafe_allow_html=True)
                st.write(overview)
                
            with col3:
                st.write("") # Spacing
                st.write("")
                if st.button("View Details ➔", key=f"btn_{tmdb_id}_{idx}", use_container_width=True):
                    goto_details(tmdb_id)
                    
        st.divider()

# =============================
# TOP NAVIGATION BAR
# =============================
top_col1, top_col2 = st.columns([4, 1])
with top_col1:
    st.title("🍿 Cinematch Dashboard")
with top_col2:
    st.write("")
    if st.session_state.view == "details":
        if st.button("🏠 Return Home", use_container_width=True):
            goto_home()

# =============================
# VIEW: HOME
# =============================
if st.session_state.view == "home":
    
    # --- Search & Filters ---
    search_query = st.text_input("Search for a movie...", placeholder="e.g. Inception, The Matrix...")
    
    with st.expander("⚙️ Advanced Filters"):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            year_filter = st.slider("Release Year", 1970, 2026, (1990, 2026))
        with f_col2:
            rating_filter = st.slider("Minimum Rating", 0.0, 10.0, 5.0)

    # --- Search Results ---
    if search_query:
        st.subheader(f"Search Results for '{search_query}'")
        with st.spinner("Searching database..."):
            data = api_get("/tmdb/search", {"query": search_query})

        if data and "results" in data:
            cards = []
            for m in data["results"]:
                year = int(m.get("release_date", "2000")[:4]) if m.get("release_date") else 2000
                cards.append({
                    "tmdb_id": m.get("id"),
                    "title": m.get("title", "No Title"),
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None,
                    "year": year,
                    "rating": m.get("vote_average", 0),
                    "overview": m.get("overview", "")
                })

            # Apply filters
            filtered_cards = [
                c for c in cards 
                if year_filter[0] <= c["year"] <= year_filter[1] and c["rating"] >= rating_filter
            ]
            render_list_view(filtered_cards)
        else:
            st.warning("No results found.")

    # --- Default Dashboard (Tabs) ---
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["🔥 Trending", "🌟 Popular", "🏆 Top Rated", "🕒 History"])
        
        with tab1:
            data = api_get("/home", {"category": "trending", "limit": 10})
            render_list_view(data)
            
        with tab2:
            data = api_get("/home", {"category": "popular", "limit": 10})
            render_list_view(data)
            
        with tab3:
            data = api_get("/home", {"category": "top_rated", "limit": 10})
            render_list_view(data)
            
        with tab4:
            if not st.session_state.history:
                st.info("Your viewing history is empty. Go look at some movies!")
            else:
                # Fetch recently viewed based on last clicked
                hist_data = api_get("/recommend/genre", {
                    "tmdb_id": st.session_state.history[-1],
                    "limit": 5
                })
                if hist_data:
                    st.write("Because you recently viewed a movie, you might like:")
                    render_list_view(hist_data)

# =============================
# VIEW: DETAILS
# =============================
elif st.session_state.view == "details":
    
    tmdb_id = st.session_state.selected_tmdb_id
    with st.spinner("Loading movie insights..."):
        data = api_get(f"/movie/id/{tmdb_id}")

    if not data:
        st.error("Failed to load movie data.")
        st.stop()

    # Create a 2-column layout for details
    det_col1, det_col2 = st.columns([1, 2.5])
    
    with det_col1:
        poster = data.get("poster_url") or FALLBACK_IMG
        st.image(poster, use_container_width=True)
        
    with det_col2:
        st.title(data.get("title", "Unknown Title"))
        
        # Metrics Dashboard
        m1, m2, m3 = st.columns(3)
        m1.metric("Rating", f"⭐ {round(data.get('vote_average', 0), 1)}/10")
        m2.metric("Release Date", data.get("release_date", "N/A"))
        m3.metric("Status", data.get("status", "Released"))
        
        st.subheader("Synopsis")
        st.write(data.get("overview", "No synopsis provided for this movie."))

    # Recommendations Section
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("🎯 See Similar Movies", expanded=True):
        with st.spinner("Analyzing genres..."):
            time.sleep(0.3)
            rec = api_get("/movie/search", {"query": data.get("title")})
        
        if rec and "genre_recommendations" in rec:
            render_list_view(rec["genre_recommendations"][:5]) # Show top 5
        else:
            st.info("No direct recommendations found for this title.")
