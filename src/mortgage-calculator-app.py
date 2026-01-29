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
if szenario == "Immobilienkauf (innerhalb Familie)":
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

    # --- Exit Szenario ---
    with st.sidebar.expander("6. Exit-Szenario (Verkauf)", expanded=False):
        st.caption("Parameter für den Fall eines vorzeitigen Verkaufs")
        marktzins_verkauf = st.slider(
            "Angenommener Marktzins bei Verkauf (%)",
            min_value=0.0, max_value=10.0, value=1.5, step=0.1,
            help="Wird benötigt, um die Vorfälligkeitsentschädigung zu schätzen. Ist der Marktzins niedriger als dein Vertragszins, verlangt die Bank eine Entschädigung."
        )
        verkaufskosten_prozent = st.slider(
            "Verkaufskosten (Makler, Notar etc.) (%)",
            min_value=0.0, max_value=10.0, value=3.0, step=0.5,
            help="Kosten, die beim Verkauf vom Erlös abgehen."
        )

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
if szenario == "Immobilienkauf (innerhalb Familie)":
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
    kumulierte_afa = 0.0
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
        kumulierte_afa += jaehrliche_afa

        # --- Exit / Verkauf Berechnung ---
        vorfaelligkeitsentschaedigung = 0.0
        if jahr < zinsbindung:
            restlaufzeit = zinsbindung - jahr
            # Vereinfachte Schätzung: Zinsdifferenz * Restschuld * Restlaufzeit
            # Wenn Marktzins > Vertragszins, dann meist 0 Entschädigung
            zinsdifferenz = max(0, zinssatz - marktzins_verkauf)
            vorfaelligkeitsentschaedigung = restschuld * (zinsdifferenz / 100) * restlaufzeit
        
        verkaufskosten = aktueller_hauswert * (verkaufskosten_prozent / 100)
        
        # Spekulationssteuer (nur wenn < 10 Jahre)
        spekulationssteuer = 0.0
        if jahr < 10:
            buchwert = kaufpreis - kumulierte_afa
            veraeusserungsgewinn = (aktueller_hauswert - verkaufskosten) - buchwert
            if veraeusserungsgewinn > 0:
                spekulationssteuer = veraeusserungsgewinn * aktueller_steuersatz
        
        netto_erloes_verkauf = aktueller_hauswert - restschuld - vorfaelligkeitsentschaedigung - verkaufskosten - spekulationssteuer

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
            "Zuwachs Vermögen": zuwachs_vermoegen,
            "Vorfälligkeitsentschädigung (Exit)": vorfaelligkeitsentschaedigung,
            "Netto-Erlös bei Verkauf (Exit)": netto_erloes_verkauf
        })
        
        aktuelle_jahresmiete *= (1 + mietsteigerung_pa / 100)
        aktuelle_instandhaltung *= (1 + kostensteigerung_pa / 100)

    df_projektion = pd.DataFrame(jahres_daten)
    
    # --- Anzeige Immobilien ---
    col1, col2 = st.columns([1, 5])
    
    # Toggles
    with col2:
        t_col1, t_col2 = st.columns(2)
        with t_col1: show_analysis = st.toggle("Analyse & Risiken anzeigen", value=False)
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
            st.markdown("## 🧐 Experten-Analyse & Risikobewertung (Stand 2026)")
            if show_inflation:
                st.caption(f"⚠️ Hinweis: Die Analyse basiert auf den inflationsbereinigten Werten ({inflationsrate}% p.a.), außer bei Kredit-Nennwerten.")

            # --- 1. Kennzahlen Berechnung ---
            ek_quote = (startkapital_gesamt / kaufpreis) * 100 if kaufpreis > 0 else 0
            brutto_mietrendite = (mieteinnahmen_pm * 12 / kaufpreis) * 100 if kaufpreis > 0 else 0
            kaufpreisfaktor = kaufpreis / (mieteinnahmen_pm * 12) if mieteinnahmen_pm > 0 else 0
            
            # --- 2. Finanzierungs-Struktur (Eigenkapital) ---
            with st.expander("1. Finanzierungs-Struktur & Eigenkapital", expanded=True):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Eigenkapitalquote", f"{ek_quote:.1f} %", help="Berechnung: (Eigenkapital + Schenkung) / Kaufpreis * 100. Diese Kennzahl zeigt, wie viel Prozent des Kaufpreises Sie ohne Kredit finanzieren. Je höher die Quote, desto besser die Kreditkonditionen und desto geringer das Risiko.")
                with col_b:
                    if ek_quote < 10:
                        st.error("🔴 **Kritisches Risiko (<10%):** Banken verlangen massive Risikoaufschläge. In 2026 ist eine Finanzierung ohne volle Nebenkostenübernahme (ca. 10-12%) aus Eigenmitteln fast unmöglich.")
                    elif ek_quote < 20:
                        st.warning("🟠 **Erhöhtes Risiko (10-20%):** Das Minimum für solide Konditionen. Versuche, zumindest die Kaufnebenkosten komplett selbst zu tragen, um den Zinssatz zu drücken.")
                    elif ek_quote < 30:
                        st.success("🟢 **Solide Basis (20-30%):** Du erhältst gute Zinsen. Du bist gegen kurzfristige Wertschwankungen (z.B. 10% Preisrückgang) abgesichert.")
                    else:
                        st.success("🟢 **Exzellente Sicherheit (>30%):** Bestkonditionen! Überlege strategisch: Lohnt sich mehr Eigenkapital, oder ist die Rendite am Kapitalmarkt (ETF) höher als der Kreditzins? (Leverage-Effekt).")
                
                st.info("💡 **Experten-Tipp:** Banken finanzieren ungern über 100% des Beleihungswertes. Kaufnebenkosten (Notar, Steuer, Makler) sind sofort weg und sollten immer 'Cash' vorhanden sein.")

            # --- 3. Rentabilität & Marktpreis ---
            with st.expander("2. Rentabilität & Kaufpreis-Check", expanded=True):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Brutto-Mietrendite", f"{brutto_mietrendite:.2f} %", help="Berechnung: (Monatliche Kaltmiete * 12) / Kaufpreis * 100. Sie gibt das Verhältnis der Mieteinnahmen zum Kaufpreis an. Eine hohe Rendite ist wünschenswert, sie sollte idealerweise über dem Kreditzins liegen.")
                    st.metric("Kaufpreisfaktor", f"{kaufpreisfaktor:.1f}", help="Berechnung: Kaufpreis / (Monatliche Kaltmiete * 12). Gibt an, wie viele Jahresmieten Sie für den Kauf der Immobilie aufwenden müssen. Ein niedriger Faktor (< 25) gilt oft als günstiger Kauf.")
                with col_b:
                    # Bewertung Mietrendite vs Zins
                    if brutto_mietrendite < zinssatz:
                        st.warning(f"🟠 **Negative Hebelwirkung:** Mietrendite ({brutto_mietrendite:.2f}%) < Kreditzins ({zinssatz}%). Die Immobilie trägt sich nicht selbst. Du zahlst jeden Monat drauf. Das lohnt sich nur bei hoher Wertsteigerung oder extremen Steuervorteilen.")
                    elif brutto_mietrendite < zinssatz + 1.5:
                        st.info(f"🟡 **Neutraler Bereich:** Die Miete deckt Zins und etwas Verwaltung, aber kaum Tilgung. Cashflow ist vermutlich negativ.")
                    else:
                        st.success(f"🟢 **Positiver Cashflow-Treiber:** Die Mietrendite ist deutlich höher als der Zins. Die Immobilie hilft aktiv bei der Tilgung.")

                    # Bewertung Kaufpreisfaktor
                    if kaufpreisfaktor > 30:
                        st.error("🔴 **Teuer eingekauft (Faktor > 30):** Typisch für München oder Top-Lagen. In B/C-Lagen viel zu teuer. Wertsteigerungspotenzial ist begrenzt, Rückschlagrisiko hoch.")
                    elif kaufpreisfaktor > 25:
                        st.warning("🟠 **Marktüblich bis Teuer (Faktor 25-30):** In A-Städten normal, in B-Lagen ambitioniert. Achte auf den Zustand (Sanierungsstau?).")
                    else:
                        st.success("🟢 **Günstiger Einkauf (Faktor < 25):** Hier ist rechnerisch ein positiver Cashflow möglich. Prüfe aber: Warum ist es so günstig? (Lage, Bausubstanz, GEG-Sanierungspflicht?)")

            # --- 4. Cashflow & Tragbarkeit ---
            with st.expander("3. Cashflow & Monatliche Belastung", expanded=True):
                avg_cf = df_display['Cashflow'].mean() if not df_display.empty else 0
                if avg_cf < 0:
                    st.error(f"🔴 **Unterdeckung:** Du musst monatlich ca. **{abs(avg_cf)/12:,.0f} €** zuschießen (nach Steuern!).")
                    st.markdown("""
                    **Risiko-Check:**
                    *   Ist dieser Betrag auch bei Elternzeit, Teilzeit oder Arbeitslosigkeit leistbar?
                    *   Hast du Rücklagen für Sonderumlagen (WEG) oder Heizungstausch (Wärmepumpe)?
                    """)
                else:
                    st.success(f"🟢 **Cashflow Positiv:** Die Immobilie bringt dir monatlich ca. **{avg_cf/12:,.0f} €** zusätzlich ein (nach Steuern).")
                
                st.markdown(f"**Tilgungs-Check:** Du tilgst mit {tilgung}%.")
                if tilgung < 2.0:
                    st.warning("⚠️ **Tilgung zu niedrig (<2%):** Das Zinsänderungsrisiko am Ende der Laufzeit ist enorm, da die Restschuld kaum sinkt.")
                elif tilgung > 3.0:
                    st.info("ℹ️ **Hohe Tilgung (>3%):** Sehr gut für die Zinssicherheit, aber bindet viel Liquidität. Prüfe, ob du Sondertilgungs-Optionen hast, statt die Rate fix so hoch zu setzen.")

            # --- 5. Zinsänderungsrisiko (Szenario-Rechnung) ---
            with st.expander("4. Zinsänderungsrisiko (Der 'Zins-Hammer')", expanded=True):
                # Wir nutzen df_projektion (nominal), da Schulden nominal sind
                row_zinsbindung = df_projektion[df_projektion['Jahr'] == zinsbindung] if not df_projektion.empty else pd.DataFrame()
                if not row_zinsbindung.empty:
                    restschuld_ende = row_zinsbindung.iloc[0]['Restschuld']
                else:
                    restschuld_ende = 0.0
                
                st.write(f"Nach Ablauf der Zinsbindung ({zinsbindung} Jahre) hast du noch **{restschuld_ende:,.2f} €** Schulden.")
                
                if restschuld_ende > 1000:
                    st.markdown("Was passiert, wenn die Zinsen dann bei **6%** oder **8%** liegen?")
                    col_z1, col_z2 = st.columns(2)
                    
                    rate_6 = restschuld_ende * (0.06 + tilgung/100) / 12
                    rate_8 = restschuld_ende * (0.08 + tilgung/100) / 12
                    
                    with col_z1:
                        diff_6 = rate_6 - monatliche_rate
                        st.metric("Rate bei 6% Zins", f"{rate_6:,.2f} €", delta=f"{diff_6:,.2f} €", delta_color="inverse", help=f"Berechnung: Restschuld * (6% Zins + {tilgung}% Tilgung) / 12. Simuliert die neue monatliche Rate, wenn der Zins für die Anschlussfinanzierung auf 6% steigt.")
                    with col_z2:
                        diff_8 = rate_8 - monatliche_rate
                        st.metric("Rate bei 8% Zins", f"{rate_8:,.2f} €", delta=f"{diff_8:,.2f} €", delta_color="inverse", help=f"Berechnung: Restschuld * (8% Zins + {tilgung}% Tilgung) / 12. Simuliert die neue monatliche Rate, wenn der Zins für die Anschlussfinanzierung auf 8% steigt.")
                    
                    st.caption(f"Annahme: Anschlussfinanzierung mit {tilgung}% Tilgung auf die Restschuld. Delta zeigt die Mehrbelastung zur heutigen Rate.")
                    if (rate_6 - monatliche_rate) > 400:
                        st.error("🔴 **Anschlussfinanzierungs-Schock:** Deine Rate könnte massiv steigen. Empfehlung: Längere Zinsbindung wählen oder Bausparvertrag zur Absicherung prüfen!")
                else:
                    st.success("Du bist bis dahin schuldenfrei (oder fast). Kein Zinsrisiko.")

            st.markdown("---")

        tab_t, tab_g = st.tabs(["Tabelle", "Graph"])
        with tab_t:
            cols_to_show = [
                "Jahr", "Einkommen (zvE)", "Grenzsteuersatz (%)", "Restschuld", "Mieteinnahmen", "Instandhaltung", "Mietausfall",
                "Zinsanteil", "Tilgungsanteil", "Monatliche Gesamtkosten", "Monatlicher Eigenaufwand", "AfA", "Steuerersparnis",
                "Cashflow", "Hauswert", "Vermögen", "Zuwachs Vermögen",
                "Vorfälligkeitsentschädigung (Exit)", "Netto-Erlös bei Verkauf (Exit)"
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
            
            def color_exit(val):
                if val > 0: return 'background-color: #c8e6c9; color: black'
                elif val < 0: return 'background-color: #ffcdd2; color: black'
                return ''
            styler.applymap(color_exit, subset=['Netto-Erlös bei Verkauf (Exit)'])

            st.dataframe(styler, use_container_width=True, height=700, hide_index=True)
            
        with tab_g:
            st.subheader("Visuelle Auswertung")
            default_cols = ["Restschuld", "Hauswert", "Vermögen", "Netto-Erlös bei Verkauf (Exit)"]
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
                
                # Zinseszins-Anteil berechnen
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

        tab_t, tab_g = st.tabs(["Tabelle", "Graph"])
        with tab_t:
            st.dataframe(df_display.style.format("{:,.2f} €", subset=[c for c in df_display.columns if c != "Jahr"]).hide(axis="index"), use_container_width=True, height=700, hide_index=True)
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
