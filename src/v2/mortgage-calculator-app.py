"""V2 Mortgage Calculator — Entry Point."""

import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Immobilienrechner V2",
    page_icon="🏡",
)

# --- Initialize page state ---
if "v2_page" not in st.session_state:
    st.session_state["v2_page"] = "wizard_1"

page = st.session_state.get("v2_page", "wizard_1")

if page == "wizard_1":
    from wizard import step1_personen
    step1_personen.render()
elif page == "wizard_2":
    from wizard import step2_investition
    step2_investition.render()
elif page == "wizard_3":
    from wizard import step3_berechnen
    step3_berechnen.render()
elif page == "executive":
    from views import executive_overview
    executive_overview.render()
elif page == "professional":
    from views import professional_plan
    professional_plan.render()
