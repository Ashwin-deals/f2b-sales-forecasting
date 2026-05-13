import streamlit as st
from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="F2B Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS Injection ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif;
    background-color: #F5F7FB; 
}

/* Hide default streamlit sidebar navigation & header */
[data-testid="stSidebarNav"] {display: none !important;}
header {visibility: hidden;}

/* Hero Section */
.hero-container {
    padding: 30px 0 50px 0;
    text-align: left;
}
.hero-title {
    font-size: 40px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    font-size: 18px;
    color: #6B7280;
    font-weight: 400;
}

/* Landing Cards */
.landing-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 32px 24px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.landing-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    border-color: #2563EB;
}
.card-icon {
    font-size: 48px;
    margin-bottom: 20px;
}
.card-title {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 12px;
}
.card-desc {
    font-size: 15px;
    color: #6B7280;
    line-height: 1.5;
    flex-grow: 1;
    margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0; text-align: center;">
            <h2 style="color: #2563EB; font-weight: 700; font-family: 'Inter', sans-serif;">F2B Analytics</h2>
        </div>
    """, unsafe_allow_html=True)
    
    selected_page = option_menu(
        menu_title=None,
        options=["Home", "Demand Intelligence", "Vendor Analysis", "Historical Sales"],
        icons=["house", "graph-up", "shop", "clock-history"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#6B7280", "font-size": "18px"},
            "nav-link": {
                "font-size": "15px", 
                "text-align": "left", 
                "margin": "5px 0", 
                "color": "#4B5563",
                "font-family": "'Inter', sans-serif",
                "border-radius": "8px"
            },
            "nav-link-selected": {"background-color": "#EFF6FF", "color": "#2563EB", "font-weight": "600"},
        }
    )
    
    if selected_page == "Demand Intelligence":
        st.switch_page("pages/1_📊_Demand_Intelligence.py")
    elif selected_page == "Vendor Analysis":
        st.switch_page("pages/2_🏪_Vendor_Analysis.py")
    elif selected_page == "Historical Sales":
        st.switch_page("pages/3_📈_Historical_Sales.py")

# ── Main Content ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Welcome to F2B Analytics 🌿</div>
    <div class="hero-subtitle">Your central hub for demand forecasting, vendor performance, and historical insights.</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="landing-card">
        <div class="card-icon">🔮</div>
        <div class="card-title">Demand Intelligence</div>
        <div class="card-desc">Track real-time demand forecasting, discover priority products, and analyze weekly trends.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Open Demand Intelligence", key="btn_di", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📊_Demand_Intelligence.py")

with c2:
    st.markdown("""
    <div class="landing-card">
        <div class="card-icon">🏪</div>
        <div class="card-title">Vendor Analysis</div>
        <div class="card-desc">Analyze vendor sales, compute profitability, and review product catalogs to optimize supply.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Open Vendor Analysis", key="btn_va", use_container_width=True, type="primary"):
        st.switch_page("pages/2_🏪_Vendor_Analysis.py")

with c3:
    st.markdown("""
    <div class="landing-card">
        <div class="card-icon">📈</div>
        <div class="card-title">Historical Sales</div>
        <div class="card-desc">View and filter historical performance trends by day or month to spot long-term patterns.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    if st.button("Open Historical Sales", key="btn_hs", use_container_width=True, type="primary"):
        st.switch_page("pages/3_📈_Historical_Sales.py")
