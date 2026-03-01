"""Wizard Step 3 — Zusammenfassung & Berechnen."""

import streamlit as st


def _nav_to(page: str):
    st.session_state["v2_page"] = page


def _format_currency(val) -> str:
    try:
        return f"{int(val):,} €".replace(",", ".")
    except (TypeError, ValueError):
        return str(val)


def render():

    _, col_main, _ = st.columns([2, 6, 2])
    with col_main:
        st.title("🏡 Immobilienrechner V2")
        st.progress(3 / 3, text="Schritt 3 von 3 — Zusammenfassung & Berechnen")
        st.markdown("---")
        st.subheader("📋 Zusammenfassung Ihrer Eingaben")

        # --- Person(en) ---
        name_a = st.session_state.get("v2_name_a", "Person A")
        name_b = st.session_state.get("v2_name_b", "Person B")
        zwei = st.session_state.get("v2_zwei_personen", False)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{name_a}**")
            st.metric("Eigenkapital", _format_currency(st.session_state.get("v2_ek_a", 100_000)))
            st.metric("Schenkung", _format_currency(st.session_state.get("v2_geschenk_a", 440_000)))
            st.metric("Brutto-Einkommen", _format_currency(st.session_state.get("v2_einkommen_a", 71_000)))

        if zwei:
            with col2:
                st.markdown(f"**{name_b}**")
                st.metric("Eigenkapital", _format_currency(st.session_state.get("v2_ek_b", 0)))
                st.metric("Schenkung", _format_currency(st.session_state.get("v2_geschenk_b", 0)))
                st.metric("Brutto-Einkommen", _format_currency(st.session_state.get("v2_einkommen_b", 80_000)))

                if st.session_state.get("v2_ehevertrag", False):
                    st.info("📜 Ehevertrag: Immobilie aus Zugewinngemeinschaft ausgeschlossen")

        st.markdown("---")

        # --- Investitionsparameter ---
        cols = st.columns(3)
        with cols[0]:
            st.metric("Kaufpreis", _format_currency(st.session_state.get("v2_kaufpreis", 1_150_000)))
        with cols[1]:
            st.metric("Monatliche Kaltmieteinnahmen durch Vermietung", _format_currency(st.session_state.get("v2_kaltmiete", 2_116)))
        with cols[2]:
            etf_r = st.session_state.get("v2_etf_rendite", 7.0)
            st.metric("ETF/Anlagen-Rendite", f"{float(etf_r):.1f} %")

        st.info(
            "ℹ️ **Restliche Parameter** (Zinssatz, Tilgung, Zinsbindung, Wertsteigerung etc.) "
            "werden mit professionellen Standardwerten vorbelegt. "
            "Diese können im nächsten Schritt in der **Ausführlichen Berechnung** angepasst werden."
        )

        st.markdown(
            """
            <style>
            .stMainBlockContainer {
                padding-bottom: 120px !important;
            }
            div[data-testid="stHorizontalBlock"]:has(#fixed-footer) {
                position: fixed !important;
                bottom: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                background-color: white !important;
                padding: 1rem 0 !important;
                z-index: 9999 !important;
                border-top: 1px solid rgba(128,128,128,0.2) !important;
                margin: 0 !important;
            }
            @media (prefers-color-scheme: dark) {
                div[data-testid="stHorizontalBlock"]:has(#fixed-footer) {
                    background-color: #0e1117 !important;
                    border-top: 1px solid #333 !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    # Navigation buttons
    footer_l, footer_main, footer_r = st.columns([2, 6, 2])
    with footer_l:
        st.markdown('<div id="fixed-footer" style="display: none;"></div>', unsafe_allow_html=True)
    with footer_main:
        btn_l, _, btn_r = st.columns([2, 6, 2])
        with btn_l:
            if st.button("← Zurück", use_container_width=True):
                _nav_to("wizard_2")
                st.rerun()
        with btn_r:
            if st.button("Berechnen", type="primary", use_container_width=True):
                _run_calculations()
                _nav_to("executive")
                st.rerun()


def _run_calculations():
    """Pre-compute executive overview data for all 3 scenarios and store in session_state."""
    from views.compute import compute_all_scenarios
    wizard_defaults = {
        "v2_ek_a": st.session_state.get("v2_ek_a", 100_000),
        "v2_ek_b": st.session_state.get("v2_ek_b", 0),
        "v2_geschenk_a": st.session_state.get("v2_geschenk_a", 440_000),
        "v2_geschenk_b": st.session_state.get("v2_geschenk_b", 0),
        "v2_einkommen_a": st.session_state.get("v2_einkommen_a", 71_000),
        "v2_einkommen_b": st.session_state.get("v2_einkommen_b", 80_000),
        "v2_kaufpreis": st.session_state.get("v2_kaufpreis", 1_150_000),
        "v2_kaltmiete": st.session_state.get("v2_kaltmiete", 2_116),
        "v2_etf_rendite": st.session_state.get("v2_etf_rendite", 7.0),
        "v2_sonderzeitraum": st.session_state.get("v2_sonderzeitraum", False),
        "v2_sonder_jahre": st.session_state.get("v2_sonder_jahre", (3, 7)),
        "v2_sonder_mann": st.session_state.get("v2_sonder_mann", 71_000),
        "v2_sonder_frau": st.session_state.get("v2_sonder_frau", 20_000),
        "v2_ehevertrag": st.session_state.get("v2_ehevertrag", False),
    }
    results = compute_all_scenarios(wizard_defaults)
    st.session_state["v2_results"] = results
    st.session_state["v2_wizard_defaults"] = wizard_defaults
