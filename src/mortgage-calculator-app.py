import streamlit as st
import pandas as pd
import altair as alt

# --- Konfiguration der Seite ---
st.set_page_config(layout="wide", page_title="Immobilienrechner für Familienkauf")

# --- Titel ---
st.title("👨‍👩‍👧‍👦 Immobilienrechner: Kauf innerhalb der Familie")
st.markdown("""
**Willkommen!** Dieses Tool hilft dir zu verstehen, ob sich der Kauf einer Immobilie (z.B. von den Eltern) finanziell lohnt.
Es berücksichtigt Steuervorteile, Mieteinnahmen und Kosten.
""")

# --- Seitenleiste für Eingaben ---
st.sidebar.header("Eingabeparameter")

# --- Kaufpreis und Eigenkapital ---
with st.sidebar.expander("1. Kauf & Finanzierung", expanded=True):
    st.caption("Wie viel kostet das Haus und wie viel Geld bringst du selbst mit?")
    kaufpreis = st.number_input(
        "Kaufpreis der Immobilie (€)",
        min_value=200000.0, max_value=3000000.0, value=1150000.0, step=10000.0,
        help="Der Preis, der im Kaufvertrag steht. Auf diesen Betrag beziehen sich Finanzierung und Abschreibung."
    )
    anteil_grundstueck = st.slider(
        "Anteil des Grundstückswerts (%)",
        min_value=10, max_value=50, value=40,
        help="Wichtig für die Steuer: Nur das Gebäude nutzt sich ab und kann abgeschrieben werden (AfA), das Grundstück nicht. Ein typischer Wert ist 20-30%."
    )
    eigenkapital_kaeufer = st.number_input(
        "Dein Eigenkapital (€)",
        min_value=0.0, value=100000.0, step=5000.0,
        help="Geld, das du auf dem Konto hast und für den Kauf verwendest. Je mehr Eigenkapital, desto weniger Zinsen zahlst du."
    )
    geschenk = st.number_input(
        "Schenkung (z.B. von Eltern) (€)",
        min_value=0.0, value=440000.0, step=5000.0,
        help="Falls dir die Verkäufer einen Teil des Kaufpreises schenken, reduziert das deinen Kreditbedarf. Achtung: Schenkungssteuerfreibeträge beachten!"
    )

# --- Kreditdetails ---
with st.sidebar.expander("2. Kreditkonditionen", expanded=False):
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

# --- Miete und Kosten ---
with st.sidebar.expander("3. Miete & Ausgaben", expanded=False):
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

# --- Einkommen & Steuer ---
with st.sidebar.expander("4. Einkommen & Steuer", expanded=True):
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

# --- Inflation ---
with st.sidebar.expander("5. Inflation & Sonstiges", expanded=False):
    st.caption("Annahme für die Geldentwertung")
    inflationsrate = st.slider(
        "Angenommene Inflation pro Jahr (%)",
        min_value=0.0, max_value=10.0, value=2.0, step=0.1,
        help="Um diesen Wert verringert sich die Kaufkraft des Geldes jährlich. Wenn du die 'Inflationsbereinigung' aktivierst, werden alle zukünftigen Werte auf heutige Kaufkraft umgerechnet."
    )

# --- Hilfsfunktion: Grenzsteuersatz (Prognose 2026) ---
def get_grenzsteuersatz(zve_gemeinsam):
    """
    Berechnet den Grenzsteuersatz basierend auf dem Splittingtarif.
    Werte sind eine Prognose für 2026 (erhöhter Grundfreibetrag).
    """
    # Splitting: Wir betrachten das halbe Einkommen
    zve = zve_gemeinsam / 2
    
    # Prognose Werte für 2026 (konservativ geschätzt)
    grundfreibetrag = 12500
    eckwert_zone1 = 18000
    eckwert_42 = 70000
    eckwert_45 = 285000

    if zve <= grundfreibetrag:
        return 0.0
    
    # Zone 1: 14% bis 24% (Progressionszone I)
    elif zve <= eckwert_zone1:
        # Lineare Interpolation
        return 0.14 + (zve - grundfreibetrag) / (eckwert_zone1 - grundfreibetrag) * (0.24 - 0.14)
        
    # Zone 2: 24% bis 42% (Progressionszone II)
    elif zve <= eckwert_42:
        return 0.24 + (zve - eckwert_zone1) / (eckwert_42 - eckwert_zone1) * (0.42 - 0.24)
        
    # Zone 3: 42% (Proportionalzone I)
    elif zve <= eckwert_45:
        return 0.42
        
    # Reichensteuer: 45% (Proportionalzone II)
    else:
        return 0.45

# --- Berechnungen ---
gesamtes_eigenkapital = eigenkapital_kaeufer + geschenk
kreditbetrag = kaufpreis - gesamtes_eigenkapital

if kreditbetrag <= 0:
    st.error("Das Eigenkapital übersteigt den Kaufpreis. Es ist kein Kredit notwendig.")
    st.stop()

# Annuität
jaehrliche_rate = kreditbetrag * (zinssatz / 100 + tilgung / 100)
monatliche_rate = jaehrliche_rate / 12

# AfA
gebaeudewert = kaufpreis * (1 - anteil_grundstueck / 100)
afa_satz = 0.02
jaehrliche_afa = gebaeudewert * afa_satz

# --- Projektion ---
jahres_daten = []
restschuld = kreditbetrag
aktuelle_jahresmiete = mieteinnahmen_pm * 12
aktuelle_instandhaltung = instandhaltung_pa
aktueller_hauswert = kaufpreis
vermoegen_vorjahr = kaufpreis - kreditbetrag # Startvermögen (Eigenkapital)

jahr = 0
max_laufzeit = 80  # Sicherheitslimit

while restschuld > 1.0 and jahr < max_laufzeit:
    jahr += 1
    
    # Einkommen für dieses Jahr bestimmen
    if nutze_sonderzeitraum and sonder_jahre[0] <= jahr <= sonder_jahre[1]:
        zve_aktuell = sonder_einkommen_mann + sonder_einkommen_frau
    else:
        zve_aktuell = std_einkommen_mann + std_einkommen_frau
        
    # Grenzsteuersatz berechnen
    aktueller_steuersatz = get_grenzsteuersatz(zve_aktuell)
    
    zinsanteil_jahr = restschuld * (zinssatz / 100)
    tilgungsanteil_jahr = jaehrliche_rate - zinsanteil_jahr
    
    # Wenn Restschuld kleiner als reguläre Tilgung, dann Restschuld komplett tilgen
    if tilgungsanteil_jahr > restschuld:
        tilgungsanteil_jahr = restschuld
        jaehrliche_rate_effektiv = zinsanteil_jahr + tilgungsanteil_jahr
    else:
        jaehrliche_rate_effektiv = jaehrliche_rate

    restschuld -= tilgungsanteil_jahr
    
    # Steuer
    werbungskosten = zinsanteil_jahr + jaehrliche_afa + aktuelle_instandhaltung
    zu_versteuernde_einnahmen = aktuelle_jahresmiete - werbungskosten
    
    # Steuerersparnis: Negatives Ergebnis mindert das zu versteuernde Einkommen
    # Wir nehmen hier den Grenzsteuersatz an
    steuerersparnis = -zu_versteuernde_einnahmen * aktueller_steuersatz
    
    # Cashflow
    mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
    cashflow_vor_steuer = aktuelle_jahresmiete - jaehrliche_rate_effektiv - aktuelle_instandhaltung - mietausfall_betrag
    cashflow_nach_steuer = cashflow_vor_steuer + steuerersparnis
    
    # Monatliche Gesamtkosten
    monatliche_gesamtkosten = (jaehrliche_rate_effektiv + aktuelle_instandhaltung + mietausfall_betrag) / 12
    
    # Monatlicher Eigenaufwand (Realbelastung)
    # Was muss ich wirklich draufzahlen (oder bekomme ich raus)?
    # Kosten - Einnahmen. Wenn positiv: Ich muss zahlen. Wenn negativ: Ich bekomme Geld.
    monatlicher_eigenaufwand = monatliche_gesamtkosten - (aktuelle_jahresmiete / 12)

    # Vermögensentwicklung
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
    
    # Inflation
    aktuelle_jahresmiete *= (1 + mietsteigerung_pa / 100)
    aktuelle_instandhaltung *= (1 + kostensteigerung_pa / 100)

df_projektion = pd.DataFrame(jahres_daten)

# --- Ergebnisse ---
# Layout Anpassung: 1 Teil Übersicht, 4 Teile Verlauf (20% / 80%)
col1, col2 = st.columns([1, 5])

# Toggles definieren (in col2, damit sie rechts oben sind)
with col2:
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        show_analysis = st.toggle("Analyse & Risiken anzeigen", value=True)
    with t_col2:
        show_inflation = st.toggle("Inflationsbereinigt anzeigen", value=False, help="Rechnet alle zukünftigen Werte auf die heutige Kaufkraft herunter.")

# Datenaufbereitung für Anzeige (Inflation)
if show_inflation and inflationsrate > 0:
    df_display = df_projektion.copy()
    # Alle Spalten außer Jahr und Prozentwerte anpassen
    cols_to_adjust = [c for c in df_display.columns if c not in ["Jahr", "Grenzsteuersatz (%)"]]
    for col in cols_to_adjust:
        # Formel: Wert / ((1 + Inflation/100) ^ Jahr)
        df_display[col] = df_display.apply(lambda row: row[col] / ((1 + inflationsrate/100) ** row['Jahr']), axis=1)
else:
    df_display = df_projektion

with col1:
    st.subheader("Übersicht")
    # Hinweis wenn Inflation aktiv
    if show_inflation:
        st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")
        
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
        # Suche das Jahr der Zinsbindung oder nimm das letzte Jahr
        row = df_display[df_display['Jahr'] == zinsbindung]
        if not row.empty:
            restschuld_zinsbindung = row.iloc[0]['Restschuld']
        else:
            restschuld_zinsbindung = 0.0
            
    st.metric(
        f"Restschuld nach {zinsbindung} Jahren",
        f"{restschuld_zinsbindung:,.2f} €",
        help="Der verbleibende Kreditbetrag nach Ablauf der Zinsbindung."
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
        # --- Analyse & Hinweise (Neu) ---
        st.subheader("💡 Analyse & Risiken")
        if show_inflation:
            st.caption(f"Hinweis: Die Analyse basiert auf den inflationsbereinigten Werten ({inflationsrate}% p.a.).")
        
        hints_col1, hints_col2 = st.columns(2)
        
        with hints_col1:
            # Cashflow Check
            if avg_cashflow < 0:
                st.error(f"⚠️ **Negativer Cashflow:** Du musst durchschnittlich **{abs(avg_cashflow):,.2f} € pro Jahr** zuschießen. Kannst du dir das dauerhaft leisten?")
            else:
                st.success(f"✅ **Positiver Cashflow:** Die Immobilie erwirtschaftet einen Überschuss von ca. **{avg_cashflow:,.2f} € pro Jahr**.")

            # Zinsrisiko Check
            if restschuld_zinsbindung > 0:
                st.warning(f"⚠️ **Zinsrisiko:** Nach {zinsbindung} Jahren hast du noch **{restschuld_zinsbindung:,.2f} € Schulden**. Wenn die Zinsen dann höher sind (z.B. 6%), steigt deine Rate deutlich!")
        
        with hints_col2:
            # Kosten vs. Miete
            # Hier nutzen wir die nominalen Werte für die Quote, da Miete und Kosten im gleichen Jahr anfallen
            # Aber da wir df_display nutzen, sind beide diskontiert, das Verhältnis bleibt also gleich.
            kosten_quote = (avg_monatliche_gesamtkosten / (df_display['Mieteinnahmen'].mean()/12)) * 100 if df_display['Mieteinnahmen'].mean() > 0 else 0
            
            if kosten_quote > 100:
                st.warning(f"⚠️ **Hohe Kosten:** Deine monatlichen Ausgaben sind **{kosten_quote:.0f}%** deiner Mieteinnahmen. Du bist auf Steuerersparnisse oder Wertsteigerung angewiesen.")
            else:
                st.success(f"✅ **Deckung:** Deine Mieteinnahmen decken die laufenden Kosten (ohne Steuer).")
                
            # Sonderzeitraum Hinweis
            if nutze_sonderzeitraum:
                st.info(f"ℹ️ **Einkommensschwankung:** Du hast einen Sonderzeitraum von Jahr {sonder_jahre[0]} bis {sonder_jahre[1]} definiert. Prüfe in der Tabelle, ob der Cashflow in diesen Jahren tragbar ist.")

        st.markdown("---")

    # Tabs für Tabelle und Graph
    tab_tabelle, tab_graph = st.tabs(["Tabelle", "Graph"])
    
    with tab_tabelle:
        # Spaltenauswahl und Reihenfolge
        cols_to_show = [
            "Jahr", "Einkommen (zvE)", "Grenzsteuersatz (%)", "Restschuld", "Mieteinnahmen", "Instandhaltung", "Mietausfall",
            "Zinsanteil", "Tilgungsanteil", "Monatliche Gesamtkosten", "Monatlicher Eigenaufwand", "AfA", "Steuerersparnis",
            "Cashflow", "Hauswert", "Vermögen", "Zuwachs Vermögen"
        ]
        
        # Formatierung
        format_dict = {col: "{:,.2f} €" for col in cols_to_show if col not in ["Jahr", "Grenzsteuersatz (%)"]}
        format_dict["Jahr"] = "{:.0f}"
        format_dict["Grenzsteuersatz (%)"] = "{:.1f} %"

        # Styling
        styler = df_display[cols_to_show].style.format(format_dict)
        
        # Index verstecken
        styler.hide(axis="index")
        
        # 1. AfA grün färben (Spalte)
        styler.set_properties(subset=["AfA"], **{'background-color': '#e8f5e9', 'color': 'black'})
        
        # 2. Einkommen hervorheben (Sonderzeitraum)
        if nutze_sonderzeitraum:
            def highlight_sonder(row):
                if sonder_jahre[0] <= row['Jahr'] <= sonder_jahre[1]:
                    return ['background-color: #fff3cd; color: black' if col == 'Einkommen (zvE)' else '' for col in row.index]
                return ['' for _ in row.index]
            styler.apply(highlight_sonder, axis=1)

        # 3. Cashflow färben (Positiv = Grün, Negativ = Rot)
        def color_cashflow(val):
            if val < 0:
                return 'background-color: #ffcdd2; color: black' # Rot
            elif val > 0:
                return 'background-color: #c8e6c9; color: black' # Grün
            return ''
        styler.applymap(color_cashflow, subset=['Cashflow'])

        # 4. Zuwachs Vermögen färben (Positiv = Grün)
        def color_growth(val):
            if val > 0:
                return 'background-color: #dcedc8; color: black' # Hellgrün
            return ''
        styler.applymap(color_growth, subset=['Zuwachs Vermögen'])

        # 5. Steuerersparnis färben (Positiv = Grün)
        def color_tax_savings(val):
            if val > 0:
                return 'background-color: #e1bee7; color: black' # Lila-ish für Steuer
            return ''
        styler.applymap(color_tax_savings, subset=['Steuerersparnis'])
        
        # 6. Eigenaufwand färben (Positiv = Rot (Zuzahlung), Negativ = Grün (Überschuss))
        def color_eigenaufwand(val):
            if val > 0:
                return 'background-color: #ffebee; color: black' # Leichtes Rot
            elif val < 0:
                return 'background-color: #e8f5e9; color: black' # Leichtes Grün
            return ''
        styler.applymap(color_eigenaufwand, subset=['Monatlicher Eigenaufwand'])

        st.dataframe(
            styler,
            use_container_width=True,
            height=800
        )
        
    with tab_graph:
        st.subheader("Visuelle Auswertung")
        
        # Auswahl der Metriken für den Graphen
        default_cols = ["Restschuld", "Hauswert", "Vermögen"]
        available_cols = [c for c in df_display.columns if c not in ["Jahr", "Grenzsteuersatz (%)"]]
        
        selected_cols = st.multiselect(
            "Wähle Werte für die Grafik:", 
            available_cols, 
            default=default_cols
        )
        
        if selected_cols:
            # Daten für Altair vorbereiten: Schmelzen (Melt) für "Tidy Data"
            chart_data = df_display.melt('Jahr', value_vars=selected_cols, var_name='Kategorie', value_name='Wert')
            
            # Altair Chart erstellen
            chart = alt.Chart(chart_data).mark_line(point=True).encode(
                x=alt.X('Jahr:O', title='Jahr'), # Ordinal für diskrete Jahre
                y=alt.Y('Wert:Q', title='Betrag (€)', scale=alt.Scale(zero=False)), # zero=False erlaubt bessere Skalierung bei negativen Werten
                color='Kategorie:N',
                tooltip=[
                    alt.Tooltip('Jahr', title='Jahr'),
                    alt.Tooltip('Kategorie', title='Kategorie'),
                    alt.Tooltip('Wert', title='Wert', format='.2s') # .2s für SI-Präfixe (k, M, etc.)
                ]
            ).properties(
                height=600 # Feste Höhe für den Graphen
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Bitte wähle mindestens einen Wert aus.")
