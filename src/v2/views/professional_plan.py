"""Professional Plan — v1-style full calculation with wizard pre-fills."""

import streamlit as st


def _nav_to(page: str):
    st.session_state["v2_page"] = page


def render():
    st.sidebar.header("Szenario wählen")

    szenario = st.sidebar.radio(
        "Was möchtest du berechnen?",
        [
            "Immobilienkauf (innerhalb Familie)",
            "Neubau (Investitions-Immobilie)",
            "ETF-Sparplan (Alternative)",
        ],
        index=0,
        label_visibility="collapsed",
    )

    if st.sidebar.button("← Zurück zur Executive Summary", use_container_width=False):
        _nav_to("executive")
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("Eingabeparameter")

    with st.sidebar.expander("Inflation", expanded=False):
        st.caption("Annahme für die Geldentwertung")
        inflationsrate = st.slider(
            "Inflation (%)", 0.0, 10.0, 2.0, 0.1,
            help="Um diesen Wert verringert sich die Kaufkraft des Geldes jährlich.",
        )

    # --- Build wizard_defaults to pass into scenario renders ---
    wizard_defaults = st.session_state.get("v2_wizard_defaults", {})

    # --- Main content ---
    st.title(f"📊 {szenario}")
    st.caption(
        "Vollständige Projektionsrechnung mit allen Parametern. "
        "Die Wizard-Eingaben sind als Standardwerte vorbelegt."
    )

    if szenario == "Immobilienkauf (innerhalb Familie)":
        from scenarios.immobilienkauf import render as render_immo
        render_immo(inflationsrate, wizard_defaults=wizard_defaults)
    elif szenario == "Neubau (Investitions-Immobilie)":
        from scenarios.neubau import render as render_nb
        render_nb(inflationsrate, wizard_defaults=wizard_defaults)
    else:
        from scenarios.etf_sparplan import render as render_etf
        render_etf(inflationsrate, wizard_defaults=wizard_defaults)
