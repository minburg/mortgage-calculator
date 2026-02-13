"""Scenario: ETF-Sparplan (Alternative).

Move-only refactor — logic is 100 % unchanged from the monolith.
"""

import streamlit as st
import pandas as pd

from calculations.formulas import get_formeln
from calculations.ui_helpers import render_toggles, apply_inflation, render_graph_tab, render_formeln_tab


def render(inflationsrate: float):
    """Renders the complete ETF-Sparplan scenario."""

    # --- Sidebar Inputs ---
    with st.sidebar.expander("1. Startkapital", expanded=True):
        st.caption("Verfügbares Vermögen für beide Szenarien")
        eigenkapital_kaeufer = st.number_input("Startkapital (€)", value=100000.0, help="Geld, das du auf dem Konto hast und für den (Haus/ETF)Kauf verwendest. Je mehr Eigenkapital, desto weniger Zinsen zahlst du (Haus).")
        geschenk = st.number_input("Schenkung (€)", value=440000.0, help="Falls dir die Verkäufer einen Teil des Kaufpreises schenken, reduziert das deinen Kreditbedarf. Achtung: Schenkungssteuerfreibeträge beachten!")
        startkapital_gesamt = eigenkapital_kaeufer + geschenk

    with st.sidebar.expander("2. ETF-Parameter", expanded=True):
        st.caption("Annahmen für die Alternativanlage")
        etf_rendite = st.slider("Rendite (%)", 0.0, 15.0, 7.0, 0.1, help="Langfristiger Durchschnitt des MSCI World liegt oft bei ca. 7-8%.")
        etf_sparrate = st.number_input("Sparrate (€)", value=1000.0, help="Wie viel Geld steckst du jeden Monat zusätzlich in den ETF? (Vergleichbar mit dem Eigenaufwand beim Hauskauf)")
        etf_steuer = st.slider("Steuersatz (%)", 0.0, 30.0, 18.5, 0.5, help="Kapitalertragsteuer (25%) + Soli. Bei Aktienfonds oft Teilfreistellung (30% steuerfrei), daher effektiv ca. 18.5%.")
        laufzeit_etf = st.slider("Laufzeit (Jahre)", 5, 60, 30, help="Wie lange soll der Sparplan laufen?")

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
    col1, col2 = st.columns([1, 5])
    
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
        
        st.metric("Startkapital", f"{startkapital_gesamt:,.2f} €")
        st.metric("Monatliche Sparrate", f"{etf_sparrate:,.2f} €")
        
        end_netto = df_display.iloc[-1]['Netto Vermögen (n. St.)'] if not df_display.empty else 0
        st.metric("Netto-Vermögen am Ende", f"{end_netto:,.2f} €", help="Nach Abzug der Kapitalertragsteuer.")
        
        total_invest = df_display.iloc[-1]['Eingezahltes Kapital'] if not df_display.empty else 0
        st.metric("Gesamt Investiert", f"{total_invest:,.2f} €")

    with col2:
        if show_analysis:
            st.markdown("## 🧐 Experten-Analyse: ETF-Sparplan (Stand 2026)")
            if show_inflation:
                st.caption(f"⚠️ Hinweis: Die Analyse basiert auf den inflationsbereinigten Werten ({inflationsrate}% p.a.).")

            # --- 1. Rendite-Check & Zinseszins ---
            with st.expander("1. Rendite-Erwartung & Zinseszins-Effekt", expanded=True):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Angenommene Rendite", f"{etf_rendite:.1f} %", help="Die durchschnittliche historische Rendite des MSCI World lag bei ca. 7-8% p.a. (vor Inflation).")
                with col_b:
                    if etf_rendite > 9.0:
                        st.warning("🟠 **Sehr optimistisch (>9%):** Historisch selten langfristig erzielt. Plane lieber konservativer (6-8%), um Enttäuschungen zu vermeiden.")
                    elif etf_rendite < 4.0:
                        st.info("🟡 **Sehr konservativ (<4%):** Das deckt kaum die Inflation. Aktienmärkte bieten langfristig meist mehr Risikoprämie.")
                    else:
                        st.success("🟢 **Realistisch (4-9%):** Deckt sich mit historischen Marktdaten für breit gestreute Welt-ETFs.")
                
                total_gewinn = df_display.iloc[-1]['Gewinn (unrealisiert)'] if not df_display.empty else 0
                zinseszins_anteil = (total_gewinn / end_netto * 100) if end_netto > 0 else 0
                st.write(f"Am Ende bestehen **{zinseszins_anteil:.0f}%** deines Vermögens nur aus Gewinnen (Zinseszins).")
                st.info("💡 **Der Zinseszins-Effekt:** In den ersten Jahren passiert wenig, aber ab Jahr 15-20 explodiert die Kurve. Geduld ist der wichtigste Faktor!")

            # --- 2. Risiko & Volatilität ---
            with st.expander("2. Risiko & Volatilität (Der 'Crash-Test')", expanded=True):
                st.markdown("Aktienmärkte schwanken. Ein Crash von **-50%** ist historisch alle paar Jahrzehnte normal.")
                crash_wert = end_netto * 0.5
                st.metric("Vermögen nach 50% Crash", f"{crash_wert:,.2f} €", delta=f"-{crash_wert:,.2f} €", delta_color="inverse", help="Simulation: Was wäre dein Depot wert, wenn kurz vor der Rente ein massiver Börsencrash passiert?")
                
                st.warning("⚠️ **Sequencing Risk:** Wenn du das Geld zu einem festen Zeitpunkt *brauchst* (z.B. Renteneintritt), musst du 5-10 Jahre vorher anfangen, in sichere Anlagen (Anleihen/Tagesgeld) umzuschichten, um nicht im Crash verkaufen zu müssen.")

            # --- 3. Steuer-Falle & Kosten ---
            with st.expander("3. Steuer & Kosten", expanded=True):
                end_steuer = df_display.iloc[-1]['Potenzielle Steuer'] if not df_display.empty else 0
                st.metric("Latente Steuerlast am Ende", f"{end_steuer:,.2f} €", help="Diesen Betrag schuldest du dem Finanzamt, sobald du verkaufst. Er arbeitet bis dahin aber weiter für dich (Steuerstundungseffekt).")
                
                if etf_steuer < 18.0:
                     st.error("🔴 **Steuer zu niedrig angesetzt?** Kapitalertragsteuer ist 25% + Soli. Mit Teilfreistellung (30% bei Aktienfonds) landest du bei ca. 18,5%. Weniger ist unrealistisch, außer Günstigerprüfung greift.")
                
                st.info("ℹ️ **Vorteil gegenüber Immobilie:** Du zahlst keine Grunderwerbsteuer, Notar oder Grundsteuer. Die laufenden Kosten (TER) eines ETF sind mit 0,2% minimal im Vergleich zur Instandhaltung eines Hauses.")

            # --- 4. Psychologie & Disziplin ---
            with st.expander("4. Psychologie & Disziplin (Der größte Feind)", expanded=True):
                st.markdown("""
                **Gängige Fehlannahmen & Risiken:**
                *   ❌ **"Ich verkaufe, wenn es fällt":** Der größte Renditekiller. Wer im Crash verkauft, realisiert Verluste.
                *   ❌ **Sparrate aussetzen:** Wenn du die Sparrate von **1.000 €** mal ein Jahr aussetzt, fehlen dir am Ende durch den Zinseszins vielleicht **50.000 €**.
                *   ✅ **Flexibilität:** Im Gegensatz zum Hauskredit kannst du die Rate notfalls reduzieren, ohne dass die Bank dir den Vertrag kündigt.
                """)

            st.markdown("---")

        # --- Tabs ---
        formeln = get_formeln("ETF-Sparplan (Alternative)")
        tab_t, tab_g, tab_f = st.tabs(["Tabelle", "Graph", "📚 Formeln"])
        with tab_t:
            st.dataframe(df_display.style.format("{:,.2f} €", subset=[c for c in df_display.columns if c != "Jahr"]).hide(axis="index"), use_container_width=True, height=700, hide_index=True)
        with tab_g:
            render_graph_tab(
                df_display,
                default_cols=["Eingezahltes Kapital", "Brutto Vermögen", "Netto Vermögen (n. St.)"],
                key_suffix="etf",
            )
        
        with tab_f:
            render_formeln_tab(formeln, key_suffix="etf")
