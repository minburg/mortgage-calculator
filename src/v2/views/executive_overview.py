"""Executive Overview — 3-column summary of all scenarios."""

import streamlit as st
import pandas as pd
import altair as alt


def _nav_to(page: str):
    st.session_state["v2_page"] = page


def _fmt(val, suffix="€"):
    try:
        return f"{int(round(float(val))):,} {suffix}".replace(",", ".")
    except (TypeError, ValueError):
        return str(val)


def render():
    results = st.session_state.get("v2_results", {})

    if not results:
        st.error("Keine Ergebnisse vorhanden. Bitte starten Sie den Wizard erneut.")
        if st.button("← Zurück zum Start"):
            _nav_to("wizard_1")
            st.rerun()
        return

    st.markdown(
        '''
        <style>
        .stMainBlockContainer {
            padding-top: 2rem !important;
        }
        /* Style the scenario columns as cards */
        [data-testid="column"]:has(.material-card), 
        [data-testid="stColumn"]:has(.material-card),
        .stColumn:has(.material-card) {
            background-color: white !important;
            border: 1px solid rgba(128,128,128,0.2) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            box-shadow: 0 8px 16px rgba(0,0,0,0.05) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
            position: relative !important;
        }
        [data-testid="column"]:has(.material-card):hover,
        [data-testid="stColumn"]:has(.material-card):hover,
        .stColumn:has(.material-card):hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 12px 20px rgba(0,0,0,0.1) !important;
        }
        /* Hide graph toolbars */
        [data-testid="column"]:has(.material-card) [data-testid="stElementToolbar"],
        [data-testid="column"]:has(.material-card) [data-testid="stToolbar"] {
            display: none !important;
        }
        @media (prefers-color-scheme: dark) {
            [data-testid="column"]:has(.material-card),
            [data-testid="stColumn"]:has(.material-card),
            .stColumn:has(.material-card) {
                background-color: #1e1e24 !important;
                border: 1px solid #333 !important;
                box-shadow: 0 8px 16px rgba(0,0,0,0.3) !important;
            }
        }
        </style>
        ''',
        unsafe_allow_html=True
    )

    def _render_sparkline(verlauf):
        df = pd.DataFrame({"Jahr": range(1, len(verlauf) + 1), "Eigenaufwand": verlauf})
        chart = (
            alt.Chart(df)
            .mark_area(opacity=0.3, line=True)
            .encode(
                x=alt.X("Jahr:Q", axis=alt.Axis(labels=False, ticks=False, title=None, grid=False, domain=False)),
                y=alt.Y("Eigenaufwand:Q", axis=alt.Axis(labels=False, ticks=False, title=None, grid=False, domain=False)),
                tooltip=alt.value(None)
            )
            .properties(height=120)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart, use_container_width=True)

    _, col_main, _ = st.columns([2, 6, 2])
    with col_main:

        st.title("📊 Executive Overview")
        st.caption("Kompakte Gegenüberstellung aller drei Szenarien")
        # --- 3 columns: one per scenario ---
        col_immo, col_nb, col_etf = st.columns(3)

        immo = results.get("immo", {})
        neubau = results.get("neubau", {})
        etf = results.get("etf", {})

        # ------------------------------------------------------------------ Immo
        with col_immo:
            st.markdown('<span class="material-card"></span>', unsafe_allow_html=True)
            st.markdown("### 🏠 Immobilienkauf\n*(Familienverkauf)*")
            st.markdown("---")
            if "error" in immo:
                st.error(immo["error"])
            else:
                st.metric(
                    "Endvermögen",
                    _fmt(immo.get("endvermoegen", 0)),
                    help="Immobilienwert minus Restschuld am Ende der Volltilgung.",
                )
                st.metric(
                    "Monatliche Rate (Bank)",
                    _fmt(immo.get("monatliche_rate", 0)),
                    help="Annuität: Zins + Tilgung pro Monat.",
                )
                st.metric(
                    "Ø Monatlicher Eigenaufwand",
                    _fmt(immo.get("monatlicher_eigenaufwand", 0)),
                    help="Ø monatliche Zuzahlung aus eigenem Nettoeinkommen (Rate + Kosten − Miete).",
                )
                st.metric(
                    "Gesamte Steuerersparnis",
                    _fmt(immo.get("steuerersparnis_gesamt", 0)),
                    help="Summe der jährlichen Steuerersparnisse (AfA + Zinsen als Werbungskosten).",
                )
                st.metric(
                    "Volltilgung nach",
                    f"{immo.get('laufzeit_jahre', '?')} Jahren",
                    help="Jahre bis das Darlehen vollständig getilgt ist.",
                )
                st.markdown("---")
                verlauf = immo.get("eigenaufwand_verlauf", [])
                if verlauf:
                    st.caption("Verlauf: Monatlicher Eigenaufwand")
                    _render_sparkline(verlauf)

        # ----------------------------------------------------------------- Neubau
        with col_nb:
            st.markdown('<span class="material-card"></span>', unsafe_allow_html=True)
            st.markdown("### 🏗️ Neubau\n*(Investitions-Immobilie)*")
            st.markdown("---")
            if "error" in neubau:
                st.error(neubau["error"])
            else:
                st.metric(
                    "Endvermögen",
                    _fmt(neubau.get("endvermoegen", 0)),
                    help="Immobilienwert minus Restschuld am Ende der Volltilgung.",
                )
                st.metric(
                    "Monatliche Rate (Bank)",
                    _fmt(neubau.get("monatliche_rate", 0)),
                )
                st.metric(
                    "Ø Monatlicher Eigenaufwand",
                    _fmt(neubau.get("monatlicher_eigenaufwand", 0)),
                )
                st.metric(
                    "Gesamte Steuerersparnis",
                    _fmt(neubau.get("steuerersparnis_gesamt", 0)),
                )
                st.metric(
                    "Volltilgung nach",
                    f"{neubau.get('laufzeit_jahre', '?')} Jahren",
                )
                st.markdown("---")
                verlauf = neubau.get("eigenaufwand_verlauf", [])
                if verlauf:
                    st.caption("Verlauf: Monatlicher Eigenaufwand")
                    _render_sparkline(verlauf)

        # ------------------------------------------------------------------- ETF
        with col_etf:
            laufzeit = immo.get("laufzeit_jahre", 30)
            st.markdown('<span class="material-card"></span>', unsafe_allow_html=True)
            st.markdown(f"### 📈 ETF-Sparplan\n*({laufzeit} Jahre)*")
            st.markdown("---")
            if "error" in etf:
                st.error(etf["error"])
            else:
                sparrate = etf.get("monatliche_rate", 0)
                st.metric(
                    "Endvermögen (Netto)",
                    _fmt(etf.get("endvermoegen", 0)),
                    help="Netto-Vermögen nach Kapitalertragsteuer.",
                )
                st.metric(
                    "Monatliche Sparrate",
                    _fmt(sparrate),
                    help="Äquivalente Sparrate — entspricht dem Ø Eigenaufwand aus dem Immobilien-Szenario.",
                )
                st.metric(
                    "Ø Monatlicher Eigenaufwand",
                    _fmt(sparrate),
                )
                st.metric(
                    "Gesamtgewinn (brutto)",
                    _fmt(etf.get("total_gewinn", 0)),
                    help="Kursgewinne vor Steuer.",
                )
                etf_rendite = st.session_state.get("v2_etf_rendite", 7.0)
                st.metric(
                    "Laufzeit / Rendite",
                    f"{laufzeit} J. / {float(etf_rendite):.1f}%",
                )
                st.markdown("---")
                verlauf = etf.get("eigenaufwand_verlauf", [])
                if verlauf:
                    st.caption("Verlauf: Monatlicher Eigenaufwand")
                    _render_sparkline(verlauf)

        # --- Bottom navigation ---
        st.markdown("---")
        btn_l, _, btn_r = st.columns([3, 4, 4])
        with btn_l:
            if st.button("← Zurück zum Wizard", use_container_width=True):
                _nav_to("wizard_3")
                st.rerun()
        with btn_r:
            if st.button("Zeige ausführliche Berechnung und Daten →", type="primary", use_container_width=True):
                _nav_to("professional")
                st.rerun()
