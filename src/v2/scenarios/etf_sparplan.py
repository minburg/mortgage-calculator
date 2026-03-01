"""Scenario: ETF-Sparplan (Alternative) — V2.

Adapted from v1: accepts optional wizard_defaults dict to override
default field values from wizard inputs.
"""

import streamlit as st
import pandas as pd

from calculations.formulas import get_formeln
from calculations.ui_helpers import render_toggles, apply_inflation, render_graph_tab, render_formeln_tab
from calculations.state_management import (
    persistent_number_input,
    persistent_slider,
)


def _d(wizard_defaults, key, fallback):
    val = wizard_defaults[key] if wizard_defaults and key in wizard_defaults else fallback
    if isinstance(fallback, float):
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return val


def render(inflationsrate: float, wizard_defaults: dict = None):
    """Renders the ETF-Sparplan scenario with optional wizard pre-fills."""

    # =========================================================================
    # SIDEBAR INPUTS
    # =========================================================================
    with st.sidebar.expander("1. Startkapital", expanded=True):
        st.caption("Verfügbares Vermögen für die Anlage")
        eigenkapital_kaeufer = persistent_number_input(
            "Startkapital (€)",
            value=_d(wizard_defaults, "v2_ek_a", 100_000.0),
            key="shared_ek_a",
            help="Eigenkapital Person A.",
        )
        geschenk = persistent_number_input(
            "Schenkung (€)",
            value=_d(wizard_defaults, "v2_geschenk_a", 440_000.0),
            key="shared_geschenk_a",
        )
        eigenkapital_partner = persistent_number_input(
            "Startkapital Partner (€)",
            value=_d(wizard_defaults, "v2_ek_b", 0.0),
            key="shared_ek_b",
        )
        geschenk_partner = persistent_number_input(
            "Schenkung Partner (€)",
            value=_d(wizard_defaults, "v2_geschenk_b", 0.0),
            key="shared_geschenk_b",
        )
        startkapital_gesamt = eigenkapital_kaeufer + geschenk + eigenkapital_partner + geschenk_partner

    with st.sidebar.expander("2. ETF-Parameter", expanded=True):
        st.caption("Annahmen für die Alternativanlage")
        etf_rendite = persistent_slider(
            "Rendite (%)", 0.0, 15.0,
            _d(wizard_defaults, "v2_etf_rendite", 7.0),
            0.1, key="etf_rendite",
            help="Langfristiger Durchschnitt des MSCI World: ca. 7-8%.",
        )
        etf_sparrate = persistent_number_input(
            "Sparrate (€)", value=1_000.0, key="etf_sparrate",
            help="Monatliche Einzahlung in den ETF.",
        )
        etf_steuer = persistent_slider(
            "Steuersatz (%)", 0.0, 30.0, 18.5, 0.5, key="etf_steuersatz",
            help="Effektiver Steuersatz: Abgeltungssteuer (25%) + Soli, mit Teilfreistellung ≈ 18.5%.",
        )
        laufzeit_etf = persistent_slider(
            "Laufzeit (Jahre)", 5, 60, 30, key="etf_laufzeit",
        )

    # =========================================================================
    # LOGIK
    # =========================================================================
    etf_daten = []
    aktuelles_kapital = float(startkapital_gesamt)
    eingezahltes_kapital = float(startkapital_gesamt)

    for jahr in range(1, laufzeit_etf + 1):
        for _m in range(12):
            aktuelles_kapital = aktuelles_kapital * (1 + etf_rendite / 100 / 12) + etf_sparrate
            eingezahltes_kapital += etf_sparrate

        gewinn = aktuelles_kapital - eingezahltes_kapital
        steuer = max(0, gewinn * (etf_steuer / 100))
        netto_vermoegen = aktuelles_kapital - steuer

        etf_daten.append({
            "Jahr": jahr,
            "Eingezahltes Kapital": eingezahltes_kapital,
            "Brutto Vermögen": aktuelles_kapital,
            "Gewinn (unrealisiert)": gewinn,
            "Potenzielle Steuer": steuer,
            "Netto Vermögen (n. St.)": netto_vermoegen,
        })

    df_etf = pd.DataFrame(etf_daten)

    # =========================================================================
    # ANZEIGE
    # =========================================================================
    col1, col2 = st.columns([1, 3])

    with col2:
        show_inflation = render_toggles()

    if show_inflation and inflationsrate > 0:
        df_display = apply_inflation(df_etf, inflationsrate, exclude_cols=["Jahr"])
    else:
        df_display = df_etf

    with col1:
        st.subheader("Übersicht")
        if show_inflation:
            st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")

        st.metric("Startkapital", f"{startkapital_gesamt:,.0f} €")
        st.metric("Monatliche Sparrate", f"{etf_sparrate:,.0f} €")

        end_netto = df_display.iloc[-1]["Netto Vermögen (n. St.)"] if not df_display.empty else 0
        total_invest = df_display.iloc[-1]["Eingezahltes Kapital"] if not df_display.empty else 0
        total_gewinn = df_display.iloc[-1]["Gewinn (unrealisiert)"] if not df_display.empty else 0
        end_steuer = df_display.iloc[-1]["Potenzielle Steuer"] if not df_display.empty else 0

        st.metric("Netto-Vermögen am Ende", f"{end_netto:,.0f} €", help="Nach Abzug der Kapitalertragsteuer.")
        st.markdown("---")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Gesamt Investiert", f"{total_invest:,.0f} €")
        with col_m2:
            st.metric("Gesamter Gewinn", f"{total_gewinn:,.0f} €")
        st.metric("Latente Steuerlast", f"{end_steuer:,.0f} €", help="Steuer, die bei Verkauf am Ende fällig wäre.")

    with col2:
        formeln = get_formeln("ETF-Sparplan (Alternative)")
        tab_t, tab_g, tab_a, tab_f = st.tabs(["Tabelle", "Graph", "Analyse & Risiken", "📚 Formeln"])
        with tab_t:
            cols_all = df_display.columns.tolist()
            cols_default = ["Jahr", "Eingezahltes Kapital", "Brutto Vermögen", "Netto Vermögen (n. St.)"]
            cols_selected = st.multiselect("Spalten anzeigen:", cols_all, default=cols_default)
            df_filtered = df_display[cols_selected]
            st.dataframe(
                df_filtered.style.format("{:,.2f} €", subset=[c for c in df_filtered.columns if c != "Jahr"]).hide(
                    axis="index"),
                use_container_width=True, height=700, hide_index=True,
            )
        with tab_g:
            render_graph_tab(df_display,
                             default_cols=["Eingezahltes Kapital", "Brutto Vermögen", "Netto Vermögen (n. St.)"],
                             key_suffix="etf_v2")

        with tab_a:
            st.markdown("## 🧐 Experteneinschätzung: ETF (2026)")

            with st.expander("1. Die Macht des Zinseszins (Exponential)", expanded=True):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Angenommene Rendite", f"{etf_rendite:.1f} %")
                with col_b:
                    if etf_rendite > 8.5:
                        st.warning("🟠 **Sehr sportlich:** Nur mit 100% Aktienquote und Glück langfristig erreichbar.")
                    else:
                        st.success("✅ **Realistisch:** Welt-Portfolio Standard.")
                zinseszins_anteil = (total_gewinn / end_netto * 100) if end_netto > 0 else 0
                st.write(f"**{zinseszins_anteil:.0f}%** des Endkapitals sind reine Kursgewinne.")
                st.info("💡 **Geduld:** Der Zinseszins-Turbo zündet erst nach 10-15 Jahren.")

            with st.expander("2. Psychologie vs. Zwangssparen", expanded=True):
                st.markdown(
                    "*   🏢 **Immobilie:** Du *musst* zahlen — extremes Zwangssparen.\n*   📈 **ETF:** Freiwillig — Risiko der Sparraten-Pause oder Panikverkauf.")
                st.error(
                    f"🔴 **Der Feind im Spiegel:** Erziele eisern die Sparrate ({etf_sparrate:,.0f} €), sonst gewinnt die Immobilie.")
                crash_wert = end_netto * 0.6
                st.warning(f"⚠️ **Crash-Simulation (−40%):** Depot fällt auf {crash_wert:,.0f} €.")

            with st.expander("3. Flexibilität & Steuer-Nachteil", expanded=True):
                st.success("🟢 **Maximale Freiheit:** Jederzeit liquide.")
                st.info(
                    f"ℹ️ Latente Steuerlast bei Auflösung: **{end_steuer:,.0f} €** — Immobiliengewinne nach 10J steuerfrei.")

        with tab_f:
            render_formeln_tab(formeln, key_suffix="etf_v2")
