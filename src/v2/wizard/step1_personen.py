"""Wizard Step 1 — Personen & Eigenkapital."""

import streamlit as st


def _nav_to(page: str):
    st.session_state["v2_page"] = page


def render():

    _, col_main, _ = st.columns([2, 6, 2])
    with col_main:

        st.title("🏡 Immobilienrechner V2")

        # --- Progress indicator ---
        st.progress(1 / 3, text="Schritt 1 von 3 — Personen & Eigenkapital")
        st.markdown("---")
        st.subheader("👤 Personen & Startkapital")
        
        zwei_personen = st.toggle(
            "👩‍❤️‍👨 Kauf zu zweit (z.B. Ehepaar)", 
            value=st.session_state.get("v2_zwei_personen", False),
            key="v2_zwei_personen_input"
        )
        st.session_state["v2_zwei_personen"] = zwei_personen

        if zwei_personen:
            tab_a, tab_b = st.tabs(["👤 Person A", "👤 Person B"])
        else:
            tab_a = st.container()
            tab_b = None
            
        with tab_a:
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                name_a = st.text_input(
                    "Name (Person A)",
                    value=st.session_state.get("v2_name_a", "Person A"),
                    key="v2_name_a_input",
                )
                ek_a = st.number_input(
                    "Eigenkapital (€)",
                    min_value=0,
                    value=int(st.session_state.get("v2_ek_a", 100_000)),
                    step=5_000,
                    key="v2_ek_a_input",
                    help="Verfügbares Eigenkapital für den Kauf.",
                )
            with col_a2:
                einkommen_a = st.number_input(
                    "Brutto-Jahreseinkommen (€)",
                    min_value=0,
                    value=int(st.session_state.get("v2_einkommen_a", 71_000)),
                    step=1_000,
                    key="v2_einkommen_a_input",
                    help="Zu versteuerndes Brutto-Jahreseinkommen (wichtig für die Steuerersparnis).",
                )
                geschenk_a = st.number_input(
                    "Schenkung (€)",
                    min_value=0,
                    value=int(st.session_state.get("v2_geschenk_a", 440_000)),
                    step=5_000,
                    key="v2_geschenk_a_input",
                    help="Geldgeschenke oder vorgezogenes Erbe.",
                )

        if zwei_personen and tab_b is not None:
            with tab_b:
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    name_b = st.text_input(
                        "Name (Person B)",
                        value=st.session_state.get("v2_name_b", "Person B"),
                        key="v2_name_b_input",
                    )
                    ek_b = st.number_input(
                        "Eigenkapital (€)",
                        min_value=0,
                        value=int(st.session_state.get("v2_ek_b", 0)),
                        step=5_000,
                        key="v2_ek_b_input",
                        help="Verfügbares Eigenkapital von Person B.",
                    )
                with col_b2:
                    einkommen_b = st.number_input(
                        "Brutto-Jahreseinkommen (€)",
                        min_value=0,
                        value=int(st.session_state.get("v2_einkommen_b", 80_000)),
                        step=1_000,
                        key="v2_einkommen_b_input",
                        help="Zu versteuerndes Brutto-Jahreseinkommen (wichtig für die Steuerersparnis).",
                    )
                    geschenk_b = st.number_input(
                        "Schenkung (€)",
                        min_value=0,
                        value=int(st.session_state.get("v2_geschenk_b", 0)),
                        step=5_000,
                        key="v2_geschenk_b_input",
                        help="Geldgeschenke oder vorgezogenes Erbe an Person B.",
                    )
                ehevertrag = st.checkbox(
                    "📜 Ehevertrag: Immobilie aus Zugewinngemeinschaft ausgeschlossen",
                    value=st.session_state.get("v2_ehevertrag", False),
                    key="v2_ehevertrag_input",
                    help="Gütertrennung für diesen Gegenstand (verhindert Zugewinnausgleich bei Scheidung).",
                )
        else:
            name_b = st.session_state.get("v2_name_b", "Person B")
            ek_b = st.session_state.get("v2_ek_b", 0)
            geschenk_b = st.session_state.get("v2_geschenk_b", 0)
            einkommen_b = st.session_state.get("v2_einkommen_b", 80_000)
            ehevertrag = st.session_state.get("v2_ehevertrag", False)

        st.markdown("---")
        nutze_sonderzeitraum = st.checkbox(
            "⏱️ Sonderzeitraum aktivieren (z.B. Elternzeit, Teilzeit)",
            value=st.session_state.get("v2_sonderzeitraum", False),
            key="v2_sonderzeitraum_input",
            help="Ermöglicht in der Ausführlichen Berechnung die Definition von reduzierten Einkommen für bestimmte Jahre."
        )

        if nutze_sonderzeitraum:
            st.caption("Geben Sie hier die abweichenden Einkünfte für den jeweiligen Zeitraum ein.")
            sonder_jahre = st.slider(
                "Zeitraum (Jahre ab Kauf)", 1, 40, 
                value=st.session_state.get("v2_sonder_jahre", (3, 7)), 
                key="v2_sonder_jahre_input"
            )
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                sonder_mann = st.number_input(
                    f"Einkommen {name_a} (Sonder) €", 
                    value=int(st.session_state.get("v2_sonder_mann", 71_000)), 
                    step=1_000, 
                    key="v2_sonder_mann_input"
                )
            with col_s2:
                if zwei_personen:
                    sonder_frau = st.number_input(
                        f"Einkommen {name_b} (Sonder) €", 
                        value=int(st.session_state.get("v2_sonder_frau", 20_000)), 
                        step=1_000, 
                        key="v2_sonder_frau_input"
                    )
                else:
                    sonder_frau = 0
        else:
            sonder_jahre = st.session_state.get("v2_sonder_jahre", (3, 7))
            sonder_mann = st.session_state.get("v2_sonder_mann", 71_000)
            sonder_frau = st.session_state.get("v2_sonder_frau", 20_000)

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

    # --- Navigation buttons ---
    footer_l, footer_main, footer_r = st.columns([2, 6, 2])
    with footer_l:
        st.markdown('<div id="fixed-footer" style="display: none;"></div>', unsafe_allow_html=True)
    with footer_main:
        btn_l, _, btn_r = st.columns([2, 6, 2])
        with btn_l:
            pass  # Platzhalter für konsistente Positionierung, im ersten Schritt gibt es kein Zurück
        with btn_r:
            if st.button("Weiter →", type="primary", use_container_width=True):
                # Save to session_state
                st.session_state["v2_name_a"] = name_a
                st.session_state["v2_ek_a"] = ek_a
                st.session_state["v2_geschenk_a"] = geschenk_a
                st.session_state["v2_einkommen_a"] = einkommen_a
                st.session_state["v2_name_b"] = name_b
                st.session_state["v2_ek_b"] = ek_b
                st.session_state["v2_geschenk_b"] = geschenk_b
                st.session_state["v2_einkommen_b"] = einkommen_b
                st.session_state["v2_ehevertrag"] = ehevertrag
                st.session_state["v2_sonderzeitraum"] = nutze_sonderzeitraum
                st.session_state["v2_sonder_jahre"] = sonder_jahre
                st.session_state["v2_sonder_mann"] = sonder_mann
                st.session_state["v2_sonder_frau"] = sonder_frau
                _nav_to("wizard_2")
                st.rerun()
