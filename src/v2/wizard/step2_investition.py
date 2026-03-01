"""Wizard Step 2 — Investitionsparameter."""

import streamlit as st


def _nav_to(page: str):
    st.session_state["v2_page"] = page


def render():


    _, col_main, _ = st.columns([2, 6, 2])
    with col_main:
        st.title("🏡 Immobilienrechner V2")
        st.progress(2 / 3, text="Schritt 2 von 3 — Investitionsparameter")
        st.markdown("---")
        st.subheader("🏠 Investitionsparameter")

        col1, col2 = st.columns(2)
        with col1:
            kaufpreis = st.number_input(
                "Kaufpreis der Immobilie (€)",
                min_value=50_000,
                max_value=10_000_000,
                value=int(st.session_state.get("v2_kaufpreis", 1_150_000)),
                step=10_000,
                key="v2_kaufpreis_input",
                help="Der Kaufpreis laut Kaufvertrag. Beim Neubau-Vergleich: Grundstück + Bau.",
            )
            kaltmiete = st.number_input(
                "Monatliche Kaltmieteinnahmen durch Vermietung (€)",
                min_value=0,
                max_value=20_000,
                value=int(st.session_state.get("v2_kaltmiete", 2_116)),
                step=50,
                key="v2_kaltmiete_input",
                help="Erwartete Mieteinnahmen pro Monat (Netto-Kaltmiete).",
            )
        with col2:
            etf_rendite = st.slider(
                "ETF/Anlagen-Rendite (%)",
                min_value=0.0,
                max_value=15.0,
                value=float(st.session_state.get("v2_etf_rendite", 7.0)),
                step=0.1,
                key="v2_etf_rendite_input",
                help="Angenommene jährliche Rendite für den ETF-Sparplan-Vergleich. Historischer MSCI-World-Durchschnitt: ~7-8%.",
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
                _nav_to("wizard_1")
                st.rerun()
        with btn_r:
            if st.button("Weiter →", type="primary", use_container_width=True):
                st.session_state["v2_kaufpreis"] = kaufpreis
                st.session_state["v2_kaltmiete"] = kaltmiete
                st.session_state["v2_etf_rendite"] = etf_rendite
                _nav_to("wizard_3")
                st.rerun()
