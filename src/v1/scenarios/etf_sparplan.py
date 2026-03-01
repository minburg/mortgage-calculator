"""Scenario: ETF-Sparplan (Alternative).

Move-only refactor — logic is 100 % unchanged from the monolith.
"""

import streamlit as st
import pandas as pd

from calculations.formulas import get_formeln
from calculations.ui_helpers import render_toggles, apply_inflation, render_graph_tab, render_formeln_tab
from calculations.state_management import (
    persistent_number_input,
    persistent_slider,
    persistent_radio,
    persistent_selectbox,
    persistent_checkbox,
)


def render(inflationsrate: float):
    """Renders the complete ETF-Sparplan scenario."""

    # --- Sidebar Inputs ---
    # --- Sidebar Inputs ---
    
    # --- 1. Startkapital ---
    with st.sidebar.expander("1. Startkapital", expanded=True):
        st.caption("Verfügbares Vermögen für beide Szenarien")
        eigenkapital_kaeufer = persistent_number_input("Startkapital (€)", value=100000.0, key="shared_ek_a", help="Geld, das du auf dem Konto hast und für den (Haus/ETF)Kauf verwendest. Je mehr Eigenkapital, desto weniger Zinsen zahlst du (Haus).")
        geschenk = persistent_number_input("Schenkung (€)", value=440000.0, key="shared_geschenk_a", help="Falls dir die Verkäufer einen Teil des Kaufpreises schenken, reduziert das deinen Kreditbedarf. Achtung: Schenkungssteuerfreibeträge beachten!")
        # Optional: Partner capital
        eigenkapital_partner = persistent_number_input("Startkapital Partner (€)", value=0.0, key="shared_ek_b", help="Kapital des Partners (optional).")
        geschenk_partner = persistent_number_input("Schenkung Partner (€)", value=0.0, key="shared_geschenk_b", help="Schenkung an Partner (optional).")
        
        startkapital_gesamt = eigenkapital_kaeufer + geschenk + eigenkapital_partner + geschenk_partner

    # --- 2. ETF-Parameter ---
    with st.sidebar.expander("2. ETF-Parameter", expanded=True):
        st.caption("Annahmen für die Alternativanlage")
        etf_rendite = persistent_slider("Rendite (%)", 0.0, 15.0, 7.0, 0.1, key="etf_rendite", help="Langfristiger Durchschnitt des MSCI World liegt oft bei ca. 7-8%.")
        etf_sparrate = persistent_number_input("Sparrate (€)", value=1000.0, key="etf_sparrate", help="Wie viel Geld steckst du jeden Monat zusätzlich in den ETF? (Vergleichbar mit dem Eigenaufwand beim Hauskauf)")
        etf_steuer = persistent_slider("Steuersatz (%)", 0.0, 30.0, 18.5, 0.5, key="etf_steuersatz", help="Kapitalertragsteuer (25%) + Soli. Bei Aktienfonds oft Teilfreistellung (30% steuerfrei), daher effektiv ca. 18.5%.")
        laufzeit_etf = persistent_slider("Laufzeit (Jahre)", 5, 60, 30, key="etf_laufzeit", help="Wie lange soll der Sparplan laufen?")

    # ==============================================================================
    # LOGIK: ETF-SPARPLAN
    # ==============================================================================
    etf_daten = []
    aktuelles_kapital = startkapital_gesamt
    eingezahltes_kapital = startkapital_gesamt
    
    for jahr in range(1, laufzeit_etf + 1):
        for m in range(12):
            aktuelles_kapital = aktuelles_kapital * (1 + etf_rendite/100/12) + etf_sparrate
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
            "Netto Vermögen (n. St.)": netto_vermoegen
        })
        
    df_etf = pd.DataFrame(etf_daten)
    
    # --- Anzeige ETF ---
    col1, col2 = st.columns([1, 3])
    
    with col2:
        show_analysis, show_inflation = render_toggles()

    # Inflation
    if show_inflation and inflationsrate > 0:
        df_display = apply_inflation(df_etf, inflationsrate, exclude_cols=["Jahr"])
    else:
        df_display = df_etf

    with col1:
        st.subheader("Übersicht")
        if show_inflation: st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")
        
        st.metric("Startkapital", f"{startkapital_gesamt:,.0f} €")
        st.metric("Monatliche Sparrate", f"{etf_sparrate:,.0f} €")
        
        end_netto = df_display.iloc[-1]['Netto Vermögen (n. St.)'] if not df_display.empty else 0
        
        total_invest = df_display.iloc[-1]['Eingezahltes Kapital'] if not df_display.empty else 0
        total_gewinn = df_display.iloc[-1]['Gewinn (unrealisiert)'] if not df_display.empty else 0
        end_steuer = df_display.iloc[-1]['Potenzielle Steuer'] if not df_display.empty else 0

        st.metric(
            "Netto-Vermögen am Ende",
            f"{end_netto:,.0f} €",
            help="Nach Abzug der Kapitalertragsteuer."
        )
        
        st.markdown("---")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Gesamt Investiert", f"{total_invest:,.0f} €")
        with col_m2:
            st.metric("Gesamter Gewinn", f"{total_gewinn:,.0f} €")
            
        st.metric("Latente Steuerlast", f"{end_steuer:,.0f} €", help="Steuer, die bei Verkauf am Ende fällig wäre.")

    with col2:
        if show_analysis:
            st.markdown("## 🧐 Experteneinschätzung: ETF (2026)")
            if show_inflation:
                st.caption(f"⚠️ Hinweis: Die Analyse basiert auf den inflationsbereinigten Werten ({inflationsrate}% p.a.).")

            # --- 1. Der Zinseszins-Effekt ---
            with st.expander("1. Die Macht des Zinseszins (Exponential)", expanded=True):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Angenommene Rendite", f"{etf_rendite:.1f} %")
                with col_b:
                    if etf_rendite > 8.5:
                        st.warning("🟠 **Sehr sportlich:** Nur mit 100% Aktienquote und Glück langfristig erreichbar. Plane lieber mit 7%.")
                    else:
                        st.success("✅ **Realistisch:** Welt-Portfolio Standard.")
                
                total_gewinn = df_display.iloc[-1]['Gewinn (unrealisiert)'] if not df_display.empty else 0
                zinseszins_anteil = (total_gewinn / end_netto * 100) if end_netto > 0 else 0
                st.write(f"In den letzten Jahren explodiert dein Vermögen: **{zinseszins_anteil:.0f}%** des Endkapitals sind reine Kursgewinne.")
                st.info("💡 **Geduld-Probe:** In den ersten 10-15 Jahren sieht der ETF gegen die Immobilie oft 'langweilig' aus (linearer Anstieg). Der Turbo zündet erst später (exponentiell). Halte durch!")

            # --- 2. Psychologie & Disziplin (Das größte Risiko) ---
            with st.expander("2. Psychologie vs. Zwangssparen", expanded=True):
                st.markdown("""
                **ETF vs. Immobilie:**
                *   🏢 **Immobilie (Zwangssparen):** Du *musst* die Rate zahlen, sonst kommt die Bank. Das diszipliniert extrem.
                *   📈 **ETF (Freiwilligkeit):** Wenn du mal knapp bei Kasse bist, setzt du die Sparrate aus. Oder du verkaufst im Crash aus Panik.
                """)
                st.error("🔴 **Der Feind im Spiegel:** Statistisch erreichen Privatanleger deutlich weniger Rendite als der Markt, weil sie hin und her handeln (Market Timing). Wenn du die Sparrate ({:,.0f} €) nicht eisern durchhälst, gewinnt die Immobilie.".format(etf_sparrate))
                
                crash_wert = end_netto * 0.6
                st.warning(f"⚠️ **Crash-Simulation:** Stell dir vor, kurz vor Renteneintritt crasht der Markt um 40%. Dein Depot fällt auf **{crash_wert:,.0f} €**. Kannst du das aussitzen? (Lösung: Umschichten 5-10 Jahre vor Ziel).")

            # --- 3. Flexibilität & Steuern ---
            with st.expander("3. Flexibilität & Steuer-Nachteil", expanded=True):
                st.success("🟢 **Maximale Freiheit:** Du kannst jederzeit an dein Geld (z.B. für Sabbatical, Notfälle). Ein Haus kannst du nicht 'stückweise' verkaufen.")
                
                end_steuer = df_display.iloc[-1]['Potenzielle Steuer'] if not df_display.empty else 0
                st.info(f"ℹ️ **Steuer-Nachteil:** Während Immobilienver Gewinne nach 10 Jahren steuerfrei sind, musst du auf ETF-Gewinne immer Abgeltungssteuer zahlen (hier latente Last: **{end_steuer:,.0f} €**). Dafür hast du keine Instandhaltungskosten.")

            st.markdown("---")

        # --- Tabs ---
        formeln = get_formeln("ETF-Sparplan (Alternative)")
        tab_t, tab_g, tab_f = st.tabs(["Tabelle", "Graph", "📚 Formeln"])
        with tab_t:
             # Default hidden columns
            cols_all = df_display.columns.tolist()
            cols_default = [
                "Jahr", "Eingezahltes Kapital", "Brutto Vermögen", "Netto Vermögen (n. St.)"
            ]
            cols_selected = st.multiselect("Spalten anzeigen:", cols_all, default=cols_default)

            df_filtered = df_display[cols_selected]
            st.dataframe(df_filtered.style.format("{:,.2f} €", subset=[c for c in df_filtered.columns if c != "Jahr"]).hide(axis="index"), use_container_width=True, height=700, hide_index=True)
        with tab_g:
            render_graph_tab(
                df_display,
                default_cols=["Eingezahltes Kapital", "Brutto Vermögen", "Netto Vermögen (n. St.)"],
                key_suffix="etf",
            )
        
        with tab_f:
            render_formeln_tab(formeln, key_suffix="etf")
