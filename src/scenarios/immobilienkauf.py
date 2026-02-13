"""Scenario: Immobilienkauf (innerhalb Familie).

Move-only refactor — logic is 100 % unchanged from the monolith.
"""

import streamlit as st
import pandas as pd
import altair as alt

from calculations.tax import berechne_einkommensteuer, get_steuerlast_zusammen
from calculations.formulas import get_formeln
from calculations.ui_helpers import render_toggles, apply_inflation, render_graph_tab, render_formeln_tab


def render(inflationsrate: float):
    """Renders the complete Immobilienkauf scenario — sidebar inputs, calculation loop, overview, tabs."""

    # --- Globale Variablen ---
    eigenkapital_a = 0.0
    eigenkapital_b = 0.0
    geschenk_a = 0.0
    geschenk_b = 0.0
    startkapital_gesamt = 0.0
    vertrag_ausschluss_zugewinn = False

    # --- 1. Eigentumsverhältnisse & Kapital ---
    with st.sidebar.expander("1. Eigentum & Kapital", expanded=True):
        eigentums_modus = st.radio("Eigentumsverhältnisse", ["Alleineigentum (Eine Person)", "Gemeinschaftseigentum (nach EK-Anteil)"])
        
        if eigentums_modus == "Alleineigentum (Eine Person)":
            eigentuemer = st.selectbox("Wer ist der Eigentümer (Grundbuch)?", ["Person A (meist Hauptverdiener)", "Person B"])
            st.caption("Das Eigenkapital wird dem Eigentümer zugerechnet.")
            eigenkapital_a = st.number_input("Eigenkapital Käufer (€)", value=100000.0, step=5000.0, help="Geld, das du auf dem Konto hast und für den Kauf verwendest.")
            geschenk_a = st.number_input("Schenkung an Käufer (€)", value=440000.0, step=5000.0, help="Falls dir die Verkäufer einen Teil des Kaufpreises schenken.")
            startkapital_gesamt = eigenkapital_a + geschenk_a
            
            # Neuer Parameter: Vertraglicher Ausschluss
            vertrag_ausschluss_zugewinn = st.checkbox(
                "Ehevertrag: Immobilie aus Zugewinn ausgeschlossen?", 
                value=False,
                help="Wenn aktiviert, wird angenommen, dass ein Ehevertrag existiert, der die Immobilie aus dem Zugewinnausgleich herausnimmt (Gütertrennung für diesen Gegenstand)."
            )
            
        else:
            st.caption("Beide Partner bringen Kapital ein. Eigentumsanteile basieren auf dem eingebrachten Kapital (EK + Schenkung).")
            col_ek1, col_ek2 = st.columns(2)
            with col_ek1:
                eigenkapital_a = st.number_input("Eigenkapital Person A (€)", value=50000.0, step=5000.0, help="Eigenkapital von Person A.")
                geschenk_a = st.number_input("Schenkung an A (€)", value=220000.0, step=5000.0, help="Schenkung an Person A.")
            with col_ek2:
                eigenkapital_b = st.number_input("Eigenkapital Person B (€)", value=50000.0, step=5000.0, help="Eigenkapital von Person B.")
                geschenk_b = st.number_input("Schenkung an B (€)", value=220000.0, step=5000.0, help="Schenkung an Person B.")
            startkapital_gesamt = eigenkapital_a + geschenk_a + eigenkapital_b + geschenk_b

    # --- 2. Kaufpreis ---
    with st.sidebar.expander("2. Kauf & Finanzierung", expanded=True):
        st.caption("Wie viel kostet das Haus und wie viel Geld bringst du selbst mit?")
        kaufpreis = st.number_input(
            "Kaufpreis der Immobilie (€)",
            min_value=50000.0, max_value=5000000.0, value=1150000.0, step=10000.0,
            help="Der Preis, der im Kaufvertrag steht. Auf diesen Betrag beziehen sich Finanzierung und Abschreibung."
        )
        
        st.markdown("##### Kaufnebenkosten")
        col_nk1, col_nk2 = st.columns(2)
        with col_nk1:
            notar_grundbuch_prozent = st.number_input("Notar & Grundbuch (%)", value=2.0, step=0.1, help="Kosten für Beurkundung und Grundbucheintrag. Faustformel: 1.5% - 2.0% des Kaufpreises.")
        with col_nk2:
            grunderwerbsteuer_prozent = st.number_input("Grunderwerbsteuer (%)", value=0.0, step=0.5, help="Steuer beim Immobilienkauf (je nach Bundesland 3.5% - 6.5%). WICHTIG: Bei Verkauf an Kinder/Ehepartner meist 0%!")
            
        anteil_grundstueck = st.slider("Anteil des Grundstückswerts (%)", 10, 80, 40, help="Wichtig für die Steuer: Nur das Gebäude nutzt sich ab und kann abgeschrieben werden (AfA), das Grundstück nicht. Ein typischer Wert ist 20-30%.")
    
    # --- 3. Kredit ---
    with st.sidebar.expander("3. Kreditkonditionen", expanded=False):
        st.caption("Was verlangt die Bank?")
        zinssatz = st.slider("Zinssatz pro Jahr (%)", 0.5, 10.0, 3.2, 0.1, help="Die 'Gebühr' der Bank für das Leihen des Geldes. Aktuell sind ca. 3.5% - 4.5% üblich.")
        tilgung = st.slider("Anfängliche Tilgung (%)", 1.0, 10.0, 2.0, 0.1, help="Der Teil deiner Rate, der den Schuldenberg tatsächlich verkleinert. Empfohlen sind mind. 2%.")
        zinsbindung = st.slider("Zinsbindung (Jahre)", 5, 30, 10, help="So lange garantiert dir die Bank den Zinssatz. Danach wird neu verhandelt (Risiko steigender Zinsen!).")

    # --- 4. Miete & Kosten ---
    with st.sidebar.expander("4. Miete & Ausgaben", expanded=False):
        st.caption("Einnahmen und laufende Kosten")
        mieteinnahmen_pm = st.number_input("Monatliche Kaltmiete (€)", value=2116.0, step=50.0, help="Die Miete, die du bekommst (ohne Nebenkosten).")
        mietsteigerung_pa = st.slider("Jährliche Mietsteigerung (%)", 0.0, 5.0, 3.0, 0.1, help="Um wie viel Prozent erhöhst du die Miete jährlich? (Inflationsausgleich)")
        instandhaltung_pa = st.number_input("Rücklage Instandhaltung/Jahr (€)", value=4000.0, step=100.0, help="Geld, das du für Reparaturen (Dach, Heizung, etc.) zurücklegen solltest. Faustformel: 10-15€ pro m² Wohnfläche im Jahr.")
        mietausfall_pa = st.slider("Risiko Mietausfall (%)", 0.0, 10.0, 2.0, 0.5, help="Kalkuliere ein, dass die Wohnung mal leer steht oder Mieter nicht zahlen. 2% entspricht ca. 1 Woche Leerstand pro Jahr.")
        kostensteigerung_pa = st.slider("Kostensteigerung pro Jahr (%)", 0.0, 5.0, 2.0, 0.1, help="Handwerker und Material werden teurer. Wie stark steigen deine Instandhaltungskosten?")
        wertsteigerung_pa = st.slider("Wertsteigerung Immobilie (%)", 0.0, 10.0, 2.0, 0.1, help="Gewinnt das Haus an Wert? Historisch oft 1-3%, aber keine Garantie!")

    # --- 5. Steuer ---
    with st.sidebar.expander("5. Einkommen & Steuer (2026)", expanded=True):
        st.caption("Einkommen für Zusammenveranlagung (Ehegattensplitting)")
        std_einkommen_mann = st.number_input("Brutto-Einkommen Person A (Standard) €", value=71000, step=1000, help="Zu versteuerndes Jahreseinkommen Person A.")
        std_einkommen_frau = st.number_input("Brutto-Einkommen Person B (Standard) €", value=80000, step=1000, help="Zu versteuerndes Jahreseinkommen Person B.")
        st.info(f"Summe Standard: {std_einkommen_mann + std_einkommen_frau:,.2f} €")
        
        st.markdown("### Sonderzeitraum")
        nutze_sonderzeitraum = st.checkbox("Sonderzeitraum aktivieren", value=False, help="Z.B. für Elternzeit oder Teilzeit.")
        if nutze_sonderzeitraum:
            sonder_jahre = st.slider("Zeitraum (Jahre)", 1, 40, (3, 7))
            sonder_einkommen_mann = st.number_input("Einkommen Person A (Sonder) €", value=71000, step=1000)
            sonder_einkommen_frau = st.number_input("Einkommen Person B (Sonder) €", value=20000, step=1000)
            st.info(f"Summe Sonder: {sonder_einkommen_mann + sonder_einkommen_frau:,.2f} €")
        else:
            sonder_jahre = (0, 0)
            sonder_einkommen_mann = 0
            sonder_einkommen_frau = 0

    # --- 6. Exit ---
    with st.sidebar.expander("6. Exit-Szenario", expanded=False):
        st.caption("Parameter für den Fall eines vorzeitigen Verkaufs")
        marktzins_verkauf = st.slider("Marktzins bei Verkauf (%)", 0.0, 10.0, 1.5, 0.1, help="Wird benötigt, um die Vorfälligkeitsentschädigung zu schätzen. Ist der Marktzins niedriger als dein Vertragszins, verlangt die Bank eine Entschädigung.")
        verkaufskosten_prozent = st.slider("Verkaufskosten (%)", 0.0, 10.0, 3.0, 0.5, help="Kosten, die beim Verkauf vom Erlös abgehen.")

    # ==============================================================================
    # LOGIK: IMMOBILIENKAUF
    # ==============================================================================

    # --- Berechnung mit Nebenkosten ---
    nebenkosten_betrag = kaufpreis * ((notar_grundbuch_prozent + grunderwerbsteuer_prozent) / 100)
    gesamtinvestition = kaufpreis + nebenkosten_betrag
    kreditbetrag = gesamtinvestition - startkapital_gesamt
    
    if kreditbetrag <= 0:
        st.error(f"Das Eigenkapital ({startkapital_gesamt:,.2f} €) deckt Kaufpreis + Nebenkosten ({gesamtinvestition:,.2f} €). Kein Kredit notwendig.")
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
    
    # Startvermögen für Zugewinn-Berechnung
    anfangs_vermoegen_netto = startkapital_gesamt
    vermoegen_vorjahr = kaufpreis - kreditbetrag
    
    # Eigentumsanteile berechnen (für Gemeinschaftseigentum)
    if eigentums_modus == "Gemeinschaftseigentum (nach EK-Anteil)":
        kapital_a = eigenkapital_a + geschenk_a
        kapital_b = eigenkapital_b + geschenk_b
        anteil_kredit_pro_kopf = kreditbetrag / 2
        invest_a = kapital_a + anteil_kredit_pro_kopf
        invest_b = kapital_b + anteil_kredit_pro_kopf
        
        anteil_a_prozent = invest_a / gesamtinvestition
        anteil_b_prozent = invest_b / gesamtinvestition
    else:
        # Alleineigentum
        if "Person A" in eigentuemer:
            anteil_a_prozent = 1.0
            anteil_b_prozent = 0.0
        else:
            anteil_a_prozent = 0.0
            anteil_b_prozent = 1.0
    
    kumulierte_afa = 0.0
    jahr = 0
    max_laufzeit = 80

    while restschuld > 1.0 and jahr < max_laufzeit:
        jahr += 1
        
        # 1. Einkommen bestimmen
        if nutze_sonderzeitraum and sonder_jahre[0] <= jahr <= sonder_jahre[1]:
            ek_a = sonder_einkommen_mann
            ek_b = sonder_einkommen_frau
        else:
            ek_a = std_einkommen_mann
            ek_b = std_einkommen_frau
            
        # 2. Immobilien-Ergebnis (V+V) berechnen
        zinsanteil_jahr = restschuld * (zinssatz / 100)
        tilgungsanteil_jahr = jaehrliche_rate - zinsanteil_jahr
        if tilgungsanteil_jahr > restschuld:
            tilgungsanteil_jahr = restschuld
            jaehrliche_rate_effektiv = zinsanteil_jahr + tilgungsanteil_jahr
        else:
            jaehrliche_rate_effektiv = jaehrliche_rate
            
        restschuld -= tilgungsanteil_jahr
        
        # Werbungskosten & Ergebnis V+V
        werbungskosten = zinsanteil_jahr + jaehrliche_afa + aktuelle_instandhaltung
        ergebnis_vv = aktuelle_jahresmiete - werbungskosten  # Negativ = Verlust
        
        # 3. Steuerberechnung mit Eigentümer-Logik
        steuer_ohne = get_steuerlast_zusammen(ek_a, ek_b)
        
        ek_a_mit = ek_a + (ergebnis_vv * anteil_a_prozent)
        ek_b_mit = ek_b + (ergebnis_vv * anteil_b_prozent)
        
        steuer_mit = get_steuerlast_zusammen(ek_a_mit, ek_b_mit)
        steuerersparnis = steuer_ohne - steuer_mit
        
        # Grenzsteuersatz (informativ)
        grenzsteuersatz = (steuerersparnis / abs(ergebnis_vv)) if ergebnis_vv != 0 else 0.0

        # 4. Cashflow
        mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
        cashflow_vor_steuer = aktuelle_jahresmiete - jaehrliche_rate_effektiv - aktuelle_instandhaltung - mietausfall_betrag
        cashflow_nach_steuer = cashflow_vor_steuer + steuerersparnis
        
        monatliche_gesamtkosten = (jaehrliche_rate_effektiv + aktuelle_instandhaltung + mietausfall_betrag) / 12
        monatlicher_eigenaufwand = monatliche_gesamtkosten - (aktuelle_jahresmiete / 12)

        # 5. Vermögensentwicklung
        aktueller_hauswert *= (1 + wertsteigerung_pa / 100)
        aktuelles_vermoegen_netto = aktueller_hauswert - restschuld
        
        # 6. Exit: Scheidung (Zugewinn)
        zugewinn_gesamt = aktuelles_vermoegen_netto - anfangs_vermoegen_netto
        
        ausgleichszahlung_scheidung = 0.0
        if eigentums_modus == "Alleineigentum (Eine Person)":
            if vertrag_ausschluss_zugewinn:
                ausgleichszahlung_scheidung = 0.0
            else:
                if zugewinn_gesamt > 0:
                    ausgleichszahlung_scheidung = zugewinn_gesamt / 2
        else:
            ausgleichszahlung_scheidung = 0.0 

        # 7. Exit: Verkauf
        vorfaelligkeitsentschaedigung = 0.0
        if jahr < zinsbindung:
            restlaufzeit = zinsbindung - jahr
            zinsdifferenz = max(0, zinssatz - marktzins_verkauf)
            vorfaelligkeitsentschaedigung = restschuld * (zinsdifferenz / 100) * restlaufzeit
        
        verkaufskosten = aktueller_hauswert * (verkaufskosten_prozent / 100)
        spekulationssteuer = 0.0
        if jahr < 10:
            buchwert = kaufpreis - kumulierte_afa
            veraeusserungsgewinn = (aktueller_hauswert - verkaufskosten) - buchwert
            if veraeusserungsgewinn > 0:
                spekulationssteuer = veraeusserungsgewinn * grenzsteuersatz
        
        netto_erloes_verkauf = aktueller_hauswert - restschuld - vorfaelligkeitsentschaedigung - verkaufskosten - spekulationssteuer

        jahres_daten.append({
            "Jahr": int(jahr),
            "Einkommen (zvE)": ek_a + ek_b,
            "Grenzsteuersatz (%)": round(grenzsteuersatz * 100, 1),
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
            "Vermögen": aktuelles_vermoegen_netto,
            "Zuwachs Vermögen": aktuelles_vermoegen_netto - vermoegen_vorjahr,
            "Vorfälligkeitsentschädigung (Exit)": vorfaelligkeitsentschaedigung,
            "Netto-Erlös bei Verkauf (Exit)": netto_erloes_verkauf,
            "Scheidung: Ausgleichszahlung": ausgleichszahlung_scheidung
        })
        
        vermoegen_vorjahr = aktuelles_vermoegen_netto
        aktuelle_jahresmiete *= (1 + mietsteigerung_pa / 100)
        aktuelle_instandhaltung *= (1 + kostensteigerung_pa / 100)
        kumulierte_afa += jaehrliche_afa

    df_projektion = pd.DataFrame(jahres_daten)
    
    # --- Anzeige Immobilien ---
    col1, col2 = st.columns([1, 5])
    
    # Toggles
    with col2:
        show_analysis, show_inflation = render_toggles()

    # Inflation
    if show_inflation and inflationsrate > 0:
        df_display = apply_inflation(df_projektion, inflationsrate, exclude_cols=["Jahr", "Grenzsteuersatz (%)"])
    else:
        df_display = df_projektion

    with col1:
        st.subheader("Übersicht")
        if show_inflation: st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")
        
        st.metric(
            "Kreditbetrag",
            f"{kreditbetrag:,.2f} €",
            help=f"Kaufpreis ({kaufpreis:,.0f}) + Nebenkosten ({nebenkosten_betrag:,.0f}) - Eigenkapital ({startkapital_gesamt:,.0f})."
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

            # --- 1. Eigentümer & Steuer-Effekt ---
            with st.expander("1. Eigentumsverhältnisse & Steuer-Effekt (AfA)", expanded=True):
                st.info(f"**Modus:** {eigentums_modus}")
                
                if eigentums_modus == "Alleineigentum (Eine Person)":
                    st.write(f"Eigentümer ist **{eigentuemer}**. Die Mieteinnahmen und die AfA werden steuerlich dieser Person zugeordnet.")
                    st.markdown("""
                    **Steuer-Mythos:** "Der Besserverdiener muss die Immobilie kaufen, um mehr Steuern zu sparen."
                    *   **Realität (Zusammenveranlagung):** In Deutschland werden Ehepartner gemeinsam veranlagt (Splittingtarif). Es werden erst alle Einkünfte addiert `(Einkommen A + Einkommen B + Miete - AfA)` und dann versteuert.
                    *   **Ergebnis:** Es ist für die *laufende* Steuerlast rechnerisch **egal**, wem das Haus gehört. Die Steuerersparnis ist identisch.
                    *   **Aber:** Bei Scheidung oder Erbe macht es einen riesigen Unterschied (siehe Punkt 4).
                    """)
                else:
                    st.write(f"Beide Partner sind Eigentümer. Aufteilung basierend auf Investition (EK + 50% Kredit): **A: {anteil_a_prozent*100:.1f}% / B: {anteil_b_prozent*100:.1f}%**.")
                    st.success("✅ **Fairness:** Die Eigentumsanteile spiegeln das eingebrachte Kapital wider. Miete und AfA werden entsprechend geteilt.")

            # --- 2. Finanzierung ---
            with st.expander("2. Finanzierung & Eigenkapital", expanded=True):
                ek_quote = (startkapital_gesamt / kaufpreis) * 100 if kaufpreis > 0 else 0
                st.metric("Eigenkapitalquote", f"{ek_quote:.1f} %", help="Berechnung: (Eigenkapital + Schenkung) / Kaufpreis * 100. Diese Kennzahl zeigt, wie viel Prozent des Kaufpreises Sie ohne Kredit finanzieren. Je höher die Quote, desto besser die Kreditkonditionen und desto geringer das Risiko.")
                st.metric("Kaufnebenkosten (verloren)", f"{nebenkosten_betrag:,.2f} €", help=f"Notar/Grundbuch ({notar_grundbuch_prozent}%) + Grunderwerbsteuer ({grunderwerbsteuer_prozent}%). Diese Kosten sind 'weg' und erhöhen den Wert der Immobilie nicht.")
                
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
            with st.expander("3. Rentabilität & Kaufpreis-Check", expanded=True):
                brutto_mietrendite = (mieteinnahmen_pm * 12 / kaufpreis) * 100 if kaufpreis > 0 else 0
                kaufpreisfaktor = kaufpreis / (mieteinnahmen_pm * 12) if mieteinnahmen_pm > 0 else 0
                
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Brutto-Mietrendite", f"{brutto_mietrendite:.2f} %", help="Berechnung: (Monatliche Kaltmiete * 12) / Kaufpreis * 100. Sie gibt das Verhältnis der Mieteinnahmen zum Kaufpreis an. Eine hohe Rendite ist wünschenswert, sie sollte idealerweise über dem Kreditzins liegen.")
                    st.metric("Kaufpreisfaktor", f"{kaufpreisfaktor:.1f}", help="Berechnung: Kaufpreis / (Monatliche Kaltmiete * 12). Gibt an, wie viele Jahresmieten Sie für den Kauf der Immobilie aufwenden müssen. Ein niedriger Faktor (< 25) gilt oft als günstiger Kauf.")
                with col_b:
                    if brutto_mietrendite < zinssatz:
                        st.warning(f"🟠 **Negative Hebelwirkung:** Mietrendite ({brutto_mietrendite:.2f}%) < Kreditzins ({zinssatz}%). Die Immobilie trägt sich nicht selbst. Du zahlst jeden Monat drauf. Das lohnt sich nur bei hoher Wertsteigerung oder extremen Steuervorteilen.")
                    elif brutto_mietrendite < zinssatz + 1.5:
                        st.info(f"🟡 **Neutraler Bereich:** Die Miete deckt Zins und etwas Verwaltung, aber kaum Tilgung. Cashflow ist vermutlich negativ.")
                    else:
                        st.success(f"🟢 **Positiver Cashflow-Treiber:** Die Mietrendite ist deutlich höher als der Zins. Die Immobilie hilft aktiv bei der Tilgung.")

                    if kaufpreisfaktor > 30:
                        st.error("🔴 **Teuer eingekauft (Faktor > 30):** Typisch für München oder Top-Lagen. In B/C-Lagen viel zu teuer. Wertsteigerungspotenzial ist begrenzt, Rückschlagrisiko hoch.")
                    elif kaufpreisfaktor > 25:
                        st.warning("🟠 **Marktüblich bis Teuer (Faktor 25-30):** In A-Städten normal, in B-Lagen ambitioniert. Achte auf den Zustand (Sanierungsstau?).")
                    else:
                        st.success("🟢 **Günstiger Einkauf (Faktor < 25):** Hier ist rechnerisch ein positiver Cashflow möglich. Prüfe aber: Warum ist es so günstig? (Lage, Bausubstanz, GEG-Sanierungspflicht?)")

            # --- 4. Cashflow & Tragbarkeit ---
            with st.expander("4. Cashflow & Monatliche Belastung", expanded=True):
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

            # --- 5. Zinsänderungsrisiko ---
            with st.expander("5. Zinsänderungsrisiko (Der 'Zins-Hammer')", expanded=True):
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

            # --- 6. Exit: Scheidung ---
            with st.expander("6. Exit-Strategie: Scheidung (Der 'Rosenkrieg')", expanded=True):
                st.markdown("Was passiert mit der Immobilie, wenn die Ehe scheitert?")
                
                row_10y = df_display[df_display['Jahr'] == 10]
                if not row_10y.empty:
                    ausgleich = row_10y.iloc[0]['Scheidung: Ausgleichszahlung']
                    vermoegen = row_10y.iloc[0]['Vermögen']
                else:
                    ausgleich = 0
                    vermoegen = 0
                
                if eigentums_modus == "Alleineigentum (Eine Person)":
                    if vertrag_ausschluss_zugewinn:
                        st.success("✅ **Vertraglich gesichert:** Durch den Ehevertrag ist die Immobilie vom Zugewinn ausgeschlossen. Keine Ausgleichszahlung nötig.")
                    else:
                        st.warning(f"⚠️ **Risiko für Eigentümer:** Da du Alleineigentümer bist, musst du im Scheidungsfall (Zugewinngemeinschaft) dem Partner die Hälfte des Wertzuwachses auszahlen.")
                        st.metric("Mögliche Auszahlung an Ex-Partner (nach 10 Jahren)", f"{ausgleich:,.2f} €", help="Hälfte des Netto-Vermögenszuwachses.")
                        if ausgleich > 50000:
                            st.error("🔴 **Liquiditäts-Gefahr:** Könntest du diesen Betrag sofort bar auszahlen? Wenn nicht, muss das Haus zwangsverkauft werden, um den Partner auszuzahlen.")
                else:
                    st.success("✅ **Neutral:** Da beiden das Haus gehört, muss niemand ausgezahlt werden. Aber: Wenn ihr euch nicht einig werdet, droht die Teilungsversteigerung (Verlustgeschäft).")

            st.markdown("---")

        # --- Tabs ---
        formeln = get_formeln("Immobilienkauf (innerhalb Familie)")
        tab_t, tab_g, tab_f = st.tabs(["Tabelle", "Graph", "📚 Formeln"])
        with tab_t:
            cols_to_show = [
                "Jahr", "Einkommen (zvE)", "Grenzsteuersatz (%)", "Restschuld", "Mieteinnahmen", "Instandhaltung", "Mietausfall",
                "Zinsanteil", "Tilgungsanteil", "Monatliche Gesamtkosten", "Monatlicher Eigenaufwand", "AfA", "Steuerersparnis",
                "Cashflow", "Hauswert", "Vermögen", "Zuwachs Vermögen",
                "Vorfälligkeitsentschädigung (Exit)", "Netto-Erlös bei Verkauf (Exit)", "Scheidung: Ausgleichszahlung"
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
            styler.map(color_cashflow, subset=['Cashflow'])

            def color_growth(val):
                if val > 0: return 'background-color: #dcedc8; color: black'
                return ''
            styler.map(color_growth, subset=['Zuwachs Vermögen'])

            def color_tax_savings(val):
                if val > 0: return 'background-color: #e1bee7; color: black'
                return ''
            styler.map(color_tax_savings, subset=['Steuerersparnis'])
            
            def color_eigenaufwand(val):
                if val > 0: return 'background-color: #ffebee; color: black'
                elif val < 0: return 'background-color: #e8f5e9; color: black'
                return ''
            styler.map(color_eigenaufwand, subset=['Monatlicher Eigenaufwand'])
            
            def color_exit(val):
                if val > 0: return 'background-color: #c8e6c9; color: black'
                elif val < 0: return 'background-color: #ffcdd2; color: black'
                return ''
            styler.map(color_exit, subset=['Netto-Erlös bei Verkauf (Exit)'])

            st.dataframe(styler, use_container_width=True, height=700, hide_index=True)
            
        with tab_g:
            render_graph_tab(
                df_display,
                default_cols=["Restschuld", "Hauswert", "Vermögen", "Netto-Erlös bei Verkauf (Exit)"],
                key_suffix="immo",
            )
        
        with tab_f:
            render_formeln_tab(formeln, key_suffix="immo")
