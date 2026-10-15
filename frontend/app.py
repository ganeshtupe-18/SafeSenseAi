import streamlit as st
from shared.theme.styles import apply_global_styles

st.set_page_config(
    page_title="SafeSense AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_global_styles()

with st.sidebar:
    st.markdown("## 🛡️ SafeSense AI")
    st.caption("Consumer safety platform")
    page = st.radio(
        "Navigation",
        ["Dashboard", "Food Safety", "Medicines", "Cosmetics",
         "Restaurant", "Food Complaints", "AI Assistant", "Safety Alerts"],
    )
    st.divider()
    st.caption("Profile · Settings")

st.title("SafeSense AI")
st.caption("Professional · Modern · Safety-focused")
st.info(f"Starter scaffold is running. Selected section: **{page}**")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Products Analysed", "—", help="Connect product-analysis service to show live data.")
c2.metric("Open Complaints", "—")
c3.metric("Restaurants", "—")
c4.metric("Safety Alerts", "—")

st.subheader("Getting started")
st.write(
    "This is the initial shared UI foundation. Implement authentication, data services, "
    "Food Safety and Complaint workflows in their assigned modules before production use."
)
