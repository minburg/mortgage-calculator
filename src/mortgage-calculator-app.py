import streamlit as st
import pandas as pd
import altair as alt

# --- Konfiguration der Seite ---
st.set_page_config(layout="wide", page_title="Immobilienrechner & ETF-Vergleich")

# --- Titel ---
st.title("📊 Vermögensrechner: Investitions-Immobilie vs. ETF Sparplan")

# --- Seitenleiste: Szenario-Auswahl ---
st.sidebar.header("Szenario wählen")
szenario = st.sidebar.radio(
    "Was möchtest du berechnen?",
    ["Immobilienkauf (innerhalb Familie)", "ETF-Sparplan (Alternative)"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.header("Eingabeparameter")

# --- Gemeinsame Parameter (Eigenkapital) ---
with st.sidebar.expander("1. Startkapital", expanded=True):
    st.caption("Verfügbares Vermögen für beide Szenarien")
    eigenkapital_kaeufer = st.number_input(
        "Dein Eigenkapital (€)",
        min_value=0.0, value=100000.0, step=5000.0,
        help="Geld, das du auf dem Konto hast und für den (Haus/ETF)Kauf verwendest. Je mehr Eigenkapital, desto weniger Zinsen zahlst du (Haus)."
    )
    geschenk = st.number_input(
        "Schenkung (z.B. von Eltern) (€)",
        min_value=0.0, value=440000.0, step=5000.0,
        help="Falls dir die Verkäufer einen Teil des Kaufpreises schenken, reduziert das deinen Kreditbedarf. Achtung: Schenkungssteuerfreibeträge beachten!"
    )
    startkapital_gesamt = eigenkapital_kaeufer + geschenk

# --- Szenario A: Immobilienkauf ---
if szenario == "Immobilienkauf (Familie)":
    # --- Kaufpreis ---
    with st.sidebar.expander("2. Kauf & Finanzierung", expanded=True):
        st.caption("Wie viel kostet das Haus und wie viel Geld bringst du selbst mit?")
        kaufpreis = st.number_input(
            "Kaufpreis der Immobilie (€)",
            min_value=50000.0, max_value=5000000.0, value=1150000.0, step=10000.0,
            help="Der Preis, der im Kaufvertrag steht. Auf diesen Betrag beziehen sich Finanzierung und Abschreibung."
        )
        anteil_grundstueck = st.slider(
            "Anteil des Grundstückswerts (%)",
            min_value=10, max_value=80, value=40,
            help="Wichtig für die Steuer: Nur das Gebäude nutzt sich ab und kann abgeschrieben werden (AfA), das Grundstück nicht. Ein typischer Wert ist 20-30%."
        )
    
    # --- Kredit ---
    with st.sidebar.expander("3. Kreditkonditionen", expanded=False):
        st.caption("Was verlangt die Bank?")
        zinssatz = st.slider(
            "Zinssatz pro Jahr (%)",
            min_value=0.5, max_value=10.0, value=3.2, step=0.1,
            help="Die 'Gebühr' der Bank für das Leihen des Geldes. Aktuell sind ca. 3.5% - 4.5% üblich."
        )
        tilgung = st.slider(
            "Anfängliche Tilgung (%)",
            min_value=1.0, max_value=10.0, value=2.0, step=0.1,
            help="Der Teil deiner Rate, der den Schuldenberg tatsächlich verkleinert. Empfohlen sind mind. 2%."
        )
        zinsbindung = st.slider(
            "Zinsbindung (Jahre)",
            min_value=5, max_value=30, value=10,
            help="So lange garantiert dir die Bank den Zinssatz. Danach wird neu verhandelt (Risiko steigender Zinsen!)."
        )

    # --- Miete & Kosten ---
    with st.sidebar.expander("4. Miete & Ausgaben", expanded=False):
        st.caption("Einnahmen und laufende Kosten")
        mieteinnahmen_pm = st.number_input(
            "Monatliche Kaltmiete (€)",
            min_value=0.0, value=2116.0, step=50.0,
            help="Die Miete, die du bekommst (ohne Nebenkosten)."
        )
        mietsteigerung_pa = st.slider(
            "Jährliche Mietsteigerung (%)",
            min_value=0.0, max_value=5.0, value=3.0, step=0.1,
            help="Um wie viel Prozent erhöhst du die Miete jährlich? (Inflationsausgleich)"
        )
        instandhaltung_pa = st.number_input(
            "Rücklage Instandhaltung/Jahr (€)",
            min_value=0.0, value=4000.0, step=100.0,
            help="Geld, das du für Reparaturen (Dach, Heizung, etc.) zurücklegen solltest. Faustformel: 10-15€ pro m² Wohnfläche im Jahr."
        )
        mietausfall_pa = st.slider(
            "Risiko Mietausfall (%)",
            min_value=0.0, max_value=10.0, value=2.0, step=0.5,
            help="Kalkuliere ein, dass die Wohnung mal leer steht oder Mieter nicht zahlen. 2% entspricht ca. 1 Woche Leerstand pro Jahr."
        )
        kostensteigerung_pa = st.slider(
            "Kostensteigerung pro Jahr (%)",
            min_value=0.0, max_value=5.0, value=2.0, step=0.1,
            help="Handwerker und Material werden teurer. Wie stark steigen deine Instandhaltungskosten?"
        )
        wertsteigerung_pa = st.slider(
            "Wertsteigerung Immobilie (%)",
            min_value=0.0, max_value=10.0, value=2.0, step=0.1,
            help="Gewinnt das Haus an Wert? Historisch oft 1-3%, aber keine Garantie!"
        )

    # --- Steuer ---
    with st.sidebar.expander("5. Einkommen & Steuer", expanded=True):
        st.caption("Deine Steuersituation beeinflusst die Rendite stark.")
        st.markdown("### Standard Einkommen (zu versteuern)")
        std_einkommen_mann = st.number_input("Einkommen Person A (Standard) €", value=71000, step=1000)
        std_einkommen_frau = st.number_input("Einkommen Person B (Standard) €", value=80000, step=1000)
        st.info(f"Summe Standard: {std_einkommen_mann + std_einkommen_frau:,.2f} €")
        
        st.markdown("### Sonderzeitraum (optional)")
        nutze_sonderzeitraum = st.checkbox("Sonderzeitraum aktivieren (z.B. Elternzeit/Teilzeit)", value=False)
        
        if nutze_sonderzeitraum:
            sonder_jahre = st.slider("Zeitraum (Jahre)", 1, 40, (3, 7))
            sonder_einkommen_mann = st.number_input("Einkommen Person A (Sonder) €", value=71000, step=1000)
            sonder_einkommen_frau = st.number_input("Einkommen Person B (Sonder) €", value=20000, step=1000)
            st.info(f"Summe Sonder: {sonder_einkommen_mann + sonder_einkommen_frau:,.2f} €")
        else:
            sonder_jahre = (0, 0)
            sonder_einkommen_mann = 0
            sonder_einkommen_frau = 0

# --- Szenario B: ETF-Sparplan ---
else:
    with st.sidebar.expander("2. ETF-Parameter", expanded=True):
        st.caption("Annahmen für die Alternativanlage")
        etf_rendite = st.slider(
            "Erwartete Rendite pro Jahr (%)", 
            min_value=0.0, max_value=15.0, value=7.0, step=0.1,
            help="Langfristiger Durchschnitt des MSCI World liegt oft bei ca. 7-8%."
        )
        etf_sparrate = st.number_input(
            "Monatliche Sparrate (€)", 
            min_value=0.0, value=1000.0, step=50.0,
            help="Wie viel Geld steckst du jeden Monat zusätzlich in den ETF? (Vergleichbar mit dem Eigenaufwand beim Hauskauf)"
        )
        etf_steuer = st.slider(
            "Steuersatz auf Gewinne (%)", 
            min_value=0.0, max_value=30.0, value=18.5, step=0.5,
            help="Kapitalertragsteuer (25%) + Soli. Bei Aktienfonds oft Teilfreistellung (30% steuerfrei), daher effektiv ca. 18.5%."
        )
        laufzeit_etf = st.slider(
            "Laufzeit (Jahre)", 
            min_value=5, max_value=60, value=30,
            help="Wie lange soll der Sparplan laufen?"
        )

# --- Inflation (Common) ---
with st.sidebar.expander("Inflation & Sonstiges", expanded=False):
    st.caption("Annahme für die Geldentwertung")
    inflationsrate = st.slider(
        "Angenommene Inflation pro Jahr (%)",
        min_value=0.0, max_value=10.0, value=2.0, step=0.1,
        help="Um diesen Wert verringert sich die Kaufkraft des Geldes jährlich. Wenn du die 'Inflationsbereinigung' aktivierst, werden alle zukünftigen Werte auf heutige Kaufkraft umgerechnet."
    )


# ==============================================================================
# LOGIK: IMMOBILIENKAUF
# ==============================================================================
if szenario == "Immobilienkauf (Familie)":
    # --- Hilfsfunktion: Grenzsteuersatz ---
    def get_grenzsteuersatz(zve_gemeinsam):
        zve = zve_gemeinsam / 2
        grundfreibetrag = 12500
        eckwert_zone1 = 18000
        eckwert_42 = 70000
        eckwert_45 = 285000

        if zve <= grundfreibetrag: return 0.0
        elif zve <= eckwert_zone1: return 0.14 + (zve - grundfreibetrag) / (eckwert_zone1 - grundfreibetrag) * (0.24 - 0.14)
        elif zve <= eckwert_42: return 0.24 + (zve - eckwert_zone1) / (eckwert_42 - eckwert_zone1) * (0.42 - 0.24)
        elif zve <= eckwert_45: return 0.42
        else: return 0.45

    kreditbetrag = kaufpreis - startkapital_gesamt
    if kreditbetrag <= 0:
        st.error("Das Eigenkapital übersteigt den Kaufpreis. Es ist kein Kredit notwendig.")
        st.stop()

    jaehrliche_rate = kreditbetrag * (zinssatz / 100 + tilgung / 100)
    monatliche_rate = jaehrliche_rate / 12
    gebaeudewert = kaufpreis * (1 - anteil_grundstueck / 100)
    jaehrliche_afa = gebaeudewert * 0.02

    jahres_daten = []
    restschuld = kreditbetrag
    aktuelle_jahresmiete = mieteinnahmen_pm * 12
    aktuelle_instandhaltung = instandhaltung_pa
    aktueller_hauswert = kaufpreis
    vermoegen_vorjahr = kaufpreis - kreditbetrag
    jahr = 0
    max_laufzeit = 80

    while restschuld > 1.0 and jahr < max_laufzeit:
        jahr += 1
        
        if nutze_sonderzeitraum and sonder_jahre[0] <= jahr <= sonder_jahre[1]:
            zve_aktuell = sonder_einkommen_mann + sonder_einkommen_frau
        else:
            zve_aktuell = std_einkommen_mann + std_einkommen_frau
            
        aktueller_steuersatz = get_grenzsteuersatz(zve_aktuell)
        zinsanteil_jahr = restschuld * (zinssatz / 100)
        tilgungsanteil_jahr = jaehrliche_rate - zinsanteil_jahr
        
        if tilgungsanteil_jahr > restschuld:
            tilgungsanteil_jahr = restschuld
            jaehrliche_rate_effektiv = zinsanteil_jahr + tilgungsanteil_jahr
        else:
            jaehrliche_rate_effektiv = jaehrliche_rate

        restschuld -= tilgungsanteil_jahr
        werbungskosten = zinsanteil_jahr + jaehrliche_afa + aktuelle_instandhaltung
        zu_versteuernde_einnahmen = aktuelle_jahresmiete - werbungskosten
        steuerersparnis = -zu_versteuernde_einnahmen * aktueller_steuersatz
        
        mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
        cashflow_vor_steuer = aktuelle_jahresmiete - jaehrliche_rate_effektiv - aktuelle_instandhaltung - mietausfall_betrag
        cashflow_nach_steuer = cashflow_vor_steuer + steuerersparnis
        
        monatliche_gesamtkosten = (jaehrliche_rate_effektiv + aktuelle_instandhaltung + mietausfall_betrag) / 12
        monatlicher_eigenaufwand = monatliche_gesamtkosten - (aktuelle_jahresmiete / 12)

        aktueller_hauswert *= (1 + wertsteigerung_pa / 100)
        aktuelles_vermoegen = aktueller_hauswert - restschuld
        zuwachs_vermoegen = aktuelles_vermoegen - vermoegen_vorjahr
        vermoegen_vorjahr = aktuelles_vermoegen

        jahres_daten.append({
            "Jahr": int(jahr),
            "Einkommen (zvE)": zve_aktuell,
            "Grenzsteuersatz (%)": round(aktueller_steuersatz * 100, 1),
            "Restschuld": max(0, restschuld),
            "Mieteinnahmen": aktuelle_jahresmiete,
            "Instandhaltung": aktuelle_instandhaltung,
            "Mietausfall": mietausfall_betrag,
            "Zinsanteil": zinsanteil_jahr,
            "Tilgungsanteil": tilgungsanteil_jahr,
            "Monatliche Gesamtkosten": monatliche_gesamtkosten,
            "Monatlicher Eigenaufwand": monatlicher_eigenaufwand,
            "AfA": jaehrliche_afa,
            "Steuerersparnis": steuerersparnis,
            "Cashflow": cashflow_nach_steuer,
            "Hauswert": aktueller_hauswert,
            "Vermögen": aktuelles_vermoegen,
            "Zuwachs Vermögen": zuwachs_vermoegen
        })
        
        aktuelle_jahresmiete *= (1 + mietsteigerung_pa / 100)
        aktuelle_instandhaltung *= (1 + kostensteigerung_pa / 100)

    df_projektion = pd.DataFrame(jahres_daten)
    
    # --- Anzeige Immobilien ---
    col1, col2 = st.columns([1, 5])
    
    # Toggles
    with col2:
        t_col1, t_col2 = st.columns(2)
        with t_col1: show_analysis = st.toggle("Analyse & Risiken anzeigen", value=True)
        with t_col2: show_inflation = st.toggle("Inflationsbereinigt anzeigen", value=False, help="Rechnet alle zukünftigen Werte auf die heutige Kaufkraft herunter.")

    # Inflation
    if show_inflation and inflationsrate > 0:
        df_display = df_projektion.copy()
        cols_to_adjust = [c for c in df_display.columns if c not in ["Jahr", "Grenzsteuersatz (%)"]]
        for col in cols_to_adjust:
            df_display[col] = df_display.apply(lambda row: row[col] / ((1 + inflationsrate/100) ** row['Jahr']), axis=1)
    else:
        df_display = df_projektion

    with col1:
        st.subheader("Übersicht")
        if show_inflation: st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")
        
        st.metric(
            "Kreditbetrag",
            f"{kreditbetrag:,.2f} €",
            help="Der Betrag, der von der Bank geliehen wird (Kaufpreis - Eigenkapital)."
        )
        st.metric(
            "Monatliche Rate (Bank)",
            f"{monatliche_rate:,.2f} €",
            help="Die monatliche Zahlung an die Bank (Zins + Tilgung)."
        )
        
        avg_monatliche_gesamtkosten = df_display['Monatliche Gesamtkosten'].mean() if not df_display.empty else 0
        st.metric(
            "Ø Monatliche Gesamtkosten",
            f"{avg_monatliche_gesamtkosten:,.2f} €",
            help="Durchschnittliche monatliche Gesamtausgaben (Rate an Bank + Instandhaltung + Mietausfall)."
        )
        
        avg_eigenaufwand = df_display['Monatlicher Eigenaufwand'].mean() if not df_display.empty else 0
        st.metric(
            "Ø Monatlicher Eigenaufwand",
            f"{avg_eigenaufwand:,.2f} €",
            help="Was du monatlich wirklich draufzahlst (Kosten minus Mieteinnahmen). Negativ bedeutet Gewinn."
        )
        
        restschuld_zinsbindung = 0.0
        if not df_display.empty:
            row = df_display[df_display['Jahr'] == zinsbindung]
            if not row.empty:
                restschuld_zinsbindung = row.iloc[0]['Restschuld']
            else:
                restschuld_zinsbindung = 0.0
                
        st.metric(
            f"Restschuld nach {zinsbindung} Jahren",
            f"{restschuld_zinsbindung:,.2f} €",
            help="Der verbleibende Kreditbetrag nach Ablauf der Zinsbindung. Dieser muss neu finanziert oder abgelöst werden."
        )
        st.metric(
            "Laufzeit bis Volltilgung",
            f"{jahr} Jahre",
            help="Die geschätzte Zeit, bis der Kredit bei gleichbleibenden Konditionen vollständig zurückgezahlt ist."
        )
        
        st.markdown("---")
        avg_cashflow = df_display['Cashflow'].mean() if not df_display.empty else 0
        st.metric(
            "Ø Cashflow (nach Steuer)",
            f"{avg_cashflow:,.2f} €",
            help="Der durchschnittliche jährliche Überschuss oder Fehlbetrag nach allen Kosten und Steuern."
        )
        
        end_vermoegen = df_display.iloc[-1]['Vermögen'] if not df_display.empty else 0
        st.metric(
            "Vermögen am Ende",
            f"{end_vermoegen:,.2f} €",
            help="Der Wert der Immobilie abzüglich der Restschuld am Ende der Laufzeit."
        )

    with col2:
        if show_analysis:
            st.subheader("💡 Analyse & Risiken")
            if show_inflation:
                st.caption(f"Hinweis: Die Analyse basiert auf den inflationsbereinigten Werten ({inflationsrate}% p.a.).")
            
            hints_col1, hints_col2 = st.columns(2)
            
            with hints_col1:
                if avg_cashflow < 0:
                    st.error(f"⚠️ **Negativer Cashflow:** Du musst durchschnittlich **{abs(avg_cashflow):,.2f} € pro Jahr** zuschießen. Kannst du dir das dauerhaft leisten?")
                else:
                    st.success(f"✅ **Positiver Cashflow:** Die Immobilie erwirtschaftet einen Überschuss von ca. **{avg_cashflow:,.2f} € pro Jahr**.")

                if restschuld_zinsbindung > 0:
                    st.warning(f"⚠️ **Zinsrisiko:** Nach {zinsbindung} Jahren hast du noch **{restschuld_zinsbindung:,.2f} € Schulden**. Wenn die Zinsen dann höher sind (z.B. 6%), steigt deine Rate deutlich!")
            
            with hints_col2:
                kosten_quote = (avg_monatliche_gesamtkosten / (df_display['Mieteinnahmen'].mean()/12)) * 100 if df_display['Mieteinnahmen'].mean() > 0 else 0
                
                if kosten_quote > 100:
                    st.warning(f"⚠️ **Hohe Kosten:** Deine monatlichen Ausgaben sind **{kosten_quote:.0f}%** deiner Mieteinnahmen. Du bist auf Steuerersparnisse oder Wertsteigerung angewiesen.")
                else:
                    st.success(f"✅ **Deckung:** Deine Mieteinnahmen decken die laufenden Kosten (ohne Steuer).")
                    
                if nutze_sonderzeitraum:
                    st.info(f"ℹ️ **Einkommensschwankung:** Du hast einen Sonderzeitraum von Jahr {sonder_jahre[0]} bis {sonder_jahre[1]} definiert. Prüfe in der Tabelle, ob der Cashflow in diesen Jahren tragbar ist.")

            st.markdown("---")

        tab_t, tab_g = st.tabs(["Tabelle", "Graph"])
        with tab_t:
            cols_to_show = [
                "Jahr", "Einkommen (zvE)", "Grenzsteuersatz (%)", "Restschuld", "Mieteinnahmen", "Instandhaltung", "Mietausfall",
                "Zinsanteil", "Tilgungsanteil", "Monatliche Gesamtkosten", "Monatlicher Eigenaufwand", "AfA", "Steuerersparnis",
                "Cashflow", "Hauswert", "Vermögen", "Zuwachs Vermögen"
            ]
            format_dict = {col: "{:,.2f} €" for col in cols_to_show if col not in ["Jahr", "Grenzsteuersatz (%)"]}
            format_dict["Jahr"] = "{:.0f}"
            format_dict["Grenzsteuersatz (%)"] = "{:.1f} %"

            styler = df_display[cols_to_show].style.format(format_dict)
            styler.hide(axis="index")
            styler.set_properties(subset=["AfA"], **{'background-color': '#e8f5e9', 'color': 'black'})
            
            if nutze_sonderzeitraum:
                def highlight_sonder(row):
                    if sonder_jahre[0] <= row['Jahr'] <= sonder_jahre[1]:
                        return ['background-color: #fff3cd; color: black' if col == 'Einkommen (zvE)' else '' for col in row.index]
                    return ['' for _ in row.index]
                styler.apply(highlight_sonder, axis=1)

            def color_cashflow(val):
                if val < 0: return 'background-color: #ffcdd2; color: black'
                elif val > 0: return 'background-color: #c8e6c9; color: black'
                return ''
            styler.applymap(color_cashflow, subset=['Cashflow'])

            def color_growth(val):
                if val > 0: return 'background-color: #dcedc8; color: black'
                return ''
            styler.applymap(color_growth, subset=['Zuwachs Vermögen'])

            def color_tax_savings(val):
                if val > 0: return 'background-color: #e1bee7; color: black'
                return ''
            styler.applymap(color_tax_savings, subset=['Steuerersparnis'])
            
            def color_eigenaufwand(val):
                if val > 0: return 'background-color: #ffebee; color: black'
                elif val < 0: return 'background-color: #e8f5e9; color: black'
                return ''
            styler.applymap(color_eigenaufwand, subset=['Monatlicher Eigenaufwand'])

            st.dataframe(styler, use_container_width=True, height=800)
            
        with tab_g:
            st.subheader("Visuelle Auswertung")
            default_cols = ["Restschuld", "Hauswert", "Vermögen"]
            available_cols = [c for c in df_display.columns if c not in ["Jahr", "Grenzsteuersatz (%)"]]
            selected_cols = st.multiselect("Wähle Werte für die Grafik:", available_cols, default=default_cols)
            
            if selected_cols:
                chart_data = df_display.melt('Jahr', value_vars=selected_cols, var_name='Kategorie', value_name='Wert')
                chart = alt.Chart(chart_data).mark_line(point=True).encode(
                    x=alt.X('Jahr:O', title='Jahr'),
                    y=alt.Y('Wert:Q', title='Betrag (€)', scale=alt.Scale(zero=False)),
                    color='Kategorie:N',
                    tooltip=[alt.Tooltip('Jahr', title='Jahr'), alt.Tooltip('Kategorie', title='Kategorie'), alt.Tooltip('Wert', title='Wert', format='.2s')]
                ).properties(height=600).interactive()
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Bitte wähle mindestens einen Wert aus.")


# ==============================================================================
# LOGIK: ETF-SPARPLAN
# ==============================================================================
else:
    # --- Berechnung ETF ---
    etf_daten = []
    aktuelles_kapital = startkapital_gesamt
    eingezahltes_kapital = startkapital_gesamt
    
    for jahr in range(1, laufzeit_etf + 1):
        # Zinseszins auf Startkapital + Sparrate
        # Vereinfacht: Sparrate wird monatlich eingezahlt
        # Endwert = Start * (1+r) + Sparrate * 12 * ... (grobe Näherung oder genaue Formel)

        # Genaue Berechnung Monatlich:
        # Kapital_neu = Kapital_alt * (1 + r) + Sparrate * 12 * (1 + r/2) # Näherung für unterjährige Verzinsung

        # Wir machen es iterativ monatlich für Genauigkeit
        for m in range(12):
            aktuelles_kapital = aktuelles_kapital * (1 + etf_rendite/100/12) + etf_sparrate
            eingezahltes_kapital += etf_sparrate
            
        # Steuer am Ende des Jahres (fiktiv für Netto-Vermögens-Sicht)
        # Gewinn = Aktuell - Eingezahlt
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
        t_col1, t_col2 = st.columns(2)
        with t_col1: show_analysis = st.toggle("Analyse anzeigen", value=False)
        with t_col2: show_inflation = st.toggle("Inflationsbereinigt anzeigen", value=False, help="Rechnet alle zukünftigen Werte auf die heutige Kaufkraft herunter.")

    # Inflation
    if show_inflation and inflationsrate > 0:
        df_display = df_etf.copy()
        cols_to_adjust = [c for c in df_display.columns if c != "Jahr"]
        for col in cols_to_adjust:
            df_display[col] = df_display.apply(lambda row: row[col] / ((1 + inflationsrate/100) ** row['Jahr']), axis=1)
    else:
        df_display = df_etf

    with col1:
        st.subheader("Übersicht")
        if show_inflation: st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")
        
        st.metric("Startkapital", f"{startkapital_gesamt:,.2f} €")
        st.metric("Monatliche Sparrate", f"{etf_sparrate:,.2f} €")
        
        end_netto = df_display.iloc[-1]['Netto Vermögen (n. St.)']
        st.metric("Netto-Vermögen am Ende", f"{end_netto:,.2f} €", help="Nach Abzug der Kapitalertragsteuer.")
        
        total_invest = df_display.iloc[-1]['Eingezahltes Kapital']
        st.metric("Gesamt Investiert", f"{total_invest:,.2f} €")

    with col2:
        if show_analysis:
            st.subheader("💡 Analyse: ETF vs. Immobilie")
            st.info("""
            **Vorteile ETF:**
            *   Hohe Flexibilität (jederzeit verkaufbar)
            *   Kein Instandhaltungsaufwand
            *   Breite Risikostreuung (bei All-World ETF)
            
            **Nachteile ETF:**
            *   Kein "Hebeleffekt" (Leverage) durch Fremdkapital
            *   Keine steuerliche Abschreibung (AfA)
            *   Miete muss weiterhin gezahlt werden (wobei in diesem Szenario über die gesamte Finanzierungsdauer auch beim Immobilienkauf eine zusätzliche Miete gezahlt werden muss)
            """)
            st.markdown("---")

        tab_t, tab_g = st.tabs(["Tabelle", "Graph"])
        with tab_t:
            st.dataframe(df_display.style.format("{:,.2f} €", subset=[c for c in df_display.columns if c != "Jahr"]).hide(axis="index"), use_container_width=True, height=600)
        with tab_g:
            st.subheader("Visuelle Auswertung")
            sel_cols = st.multiselect("Werte", [c for c in df_display.columns if c != "Jahr"], default=["Eingezahltes Kapital", "Brutto Vermögen", "Netto Vermögen (n. St.)"])
            if sel_cols:
                chart_data = df_display.melt('Jahr', value_vars=sel_cols, var_name='Kategorie', value_name='Wert')
                c = alt.Chart(chart_data).mark_line(point=True).encode(
                    x=alt.X('Jahr:O', title='Jahr'), 
                    y=alt.Y('Wert:Q', title='Betrag (€)', scale=alt.Scale(zero=False)), 
                    color='Kategorie:N', 
                    tooltip=[alt.Tooltip('Jahr', title='Jahr'), alt.Tooltip('Kategorie', title='Kategorie'), alt.Tooltip('Wert', title='Wert', format='.2s')]
                ).properties(height=600).interactive()
                st.altair_chart(c, use_container_width=True)
            else:
                st.info("Bitte wähle mindestens einen Wert aus.")
