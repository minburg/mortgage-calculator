"""Scenario: Neubau (Investitions-Immobilie).

Implements German AFA rules for new residential buildings:
- §7 Abs. 4 (Linear 3%)
- §7 Abs. 5a (Degressiv 5%)
- §7b (Sonder-AfA, additional 5% for 4 years)
"""

import streamlit as st
import pandas as pd

from calculations.tax import get_steuerlast_zusammen
from calculations.formulas import get_formeln
from calculations.ui_helpers import render_toggles, apply_inflation, render_graph_tab, render_formeln_tab


# ---------------------------------------------------------------------------
# AFA Calculation
# ---------------------------------------------------------------------------

def berechne_neubau_afa(baukosten, methode, switch_year, wohnflaeche_m2=0, max_years=50):
    """Return a list of dicts with annual AFA info for each year.

    Each dict: {
        'afa': float,          # AFA amount this year
        'buchwert': float,     # remaining book value after this year
        'methode_label': str,  # label for which method was active
        'sonder_afa': float,   # §7b Sonder-AfA this year (if any)
    }

    Rules:
    - Linear (§7 Abs. 4): 3% of Baukosten for 33⅓ years
    - Degressiv (§7 Abs. 5a): 5% of remaining book value, optional switch to linear
    - §7b Sonder-AfA: additional 5% of Baukosten for first 4 years
      (requires baukosten / wohnflaeche_m2 ≤ €5,200)
    """
    gebaeudewert = baukosten  # Grundstück is NOT depreciable
    nutzungsdauer = 100 / 3  # 33⅓ years
    buchwert = gebaeudewert
    ergebnisse = []

    for jahr in range(1, max_years + 1):
        if buchwert <= 0:
            ergebnisse.append({
                'afa': 0.0,
                'buchwert': 0.0,
                'methode_label': '—',
                'sonder_afa': 0.0,
            })
            continue

        sonder_afa = 0.0

        if methode == "Linear (3%)":
            afa = gebaeudewert * 0.03
            afa = min(afa, buchwert)
            label = "Linear 3%"

        elif methode in ("Degressiv (5%)", "Degressiv + §7b Sonder-AfA"):
            if jahr < switch_year:
                # Degressive phase
                afa = buchwert * 0.05
                label = "Degressiv 5%"
            else:
                # Switch to linear on remaining book value / remaining years
                remaining_years = nutzungsdauer - (jahr - 1)
                if remaining_years > 0:
                    afa = buchwert / remaining_years
                    label = f"Linear (Switch J{switch_year})"
                else:
                    afa = buchwert
                    label = "Linear (Rest)"

            # §7b Sonder-AfA: additional 5% of Baukosten for years 1-4
            if methode == "Degressiv + §7b Sonder-AfA" and jahr <= 4:
                kosten_pro_m2 = baukosten / wohnflaeche_m2 if wohnflaeche_m2 > 0 else float('inf')
                if kosten_pro_m2 <= 5200:
                    sonder_afa = gebaeudewert * 0.05
                    label += " + §7b"

        else:
            afa = 0.0
            label = "—"

        # Ensure we don't exceed remaining book value
        gesamt_afa_jahr = afa + sonder_afa
        if gesamt_afa_jahr > buchwert:
            # Proportionally reduce
            factor = buchwert / gesamt_afa_jahr
            afa *= factor
            sonder_afa *= factor
            gesamt_afa_jahr = buchwert

        buchwert -= gesamt_afa_jahr

        ergebnisse.append({
            'afa': afa,
            'buchwert': max(0, buchwert),
            'methode_label': label,
            'sonder_afa': sonder_afa,
        })

    return ergebnisse


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render(inflationsrate: float):
    """Renders the complete Neubau (Investitions-Immobilie) scenario."""

    # --- Globale Variablen ---
    eigenkapital_a = 0.0
    eigenkapital_b = 0.0
    geschenk_a = 0.0
    geschenk_b = 0.0
    startkapital_gesamt = 0.0
    vertrag_ausschluss_zugewinn = False

    # =========================================================================
    # SIDEBAR INPUTS
    # =========================================================================

    # --- 1. Grundstück & Baukosten ---
    with st.sidebar.expander("1. Grundstück & Baukosten", expanded=True):
        st.caption("Kosten für das Grundstück und den Bau des Gebäudes")
        grundstueckspreis = st.number_input(
            "Grundstückspreis (€)", value=300000.0, step=10000.0,
            help="Preis für das Bauland. Das Grundstück ist steuerlich NICHT abschreibbar.",
            key="nb_grundstueckspreis",
        )
        baukosten = st.number_input(
            "Baukosten Gebäude (€)", value=500000.0, step=10000.0,
            help="Reine Baukosten (Gebäude). Nur dieser Betrag ist steuerlich abschreibbar (AfA).",
            key="nb_baukosten",
        )
        baunebenkosten_prozent = st.slider(
            "Baunebenkosten (%)", 10.0, 25.0, 15.0, 0.5,
            help="Zusatzkosten beim Bauen: Architekt, Statik, Genehmigungen, Erschließung. Üblich: 15-20% der Baukosten.",
            key="nb_baunebenkosten",
        )
        baunebenkosten = baukosten * (baunebenkosten_prozent / 100)

        st.markdown("##### Kaufnebenkosten (Grundstück)")
        col_nk1, col_nk2 = st.columns(2)
        with col_nk1:
            notar_grundbuch_prozent = st.number_input(
                "Notar & Grundbuch (%)", value=2.0, step=0.1,
                help="Kosten für Beurkundung und Grundbucheintrag.",
                key="nb_notar",
            )
        with col_nk2:
            grunderwerbsteuer_prozent = st.number_input(
                "Grunderwerbsteuer (%)", value=6.5, step=0.5,
                help="Grunderwerbsteuer auf das Grundstück (je nach Bundesland 3.5%-6.5%).",
                key="nb_grunderwerb",
            )

        kaufnebenkosten = grundstueckspreis * ((notar_grundbuch_prozent + grunderwerbsteuer_prozent) / 100)
        gesamtkosten = grundstueckspreis + baukosten + baunebenkosten + kaufnebenkosten
        st.info(
            f"**Gesamtkosten:** {gesamtkosten:,.0f} €\n\n"
            f"Grundstück: {grundstueckspreis:,.0f} € | "
            f"Bau: {baukosten:,.0f} € | "
            f"Bau-NK: {baunebenkosten:,.0f} € | "
            f"Kauf-NK: {kaufnebenkosten:,.0f} €"
        )

    # --- 2. AFA-Methode ---
    with st.sidebar.expander("2. AfA-Methode", expanded=True):
        st.caption("Steuerliche Abschreibung des Gebäudes")
        afa_methode = st.radio(
            "AfA-Methode wählen",
            ["Linear (3%)", "Degressiv (5%)", "Degressiv + §7b Sonder-AfA"],
            index=0,
            key="nb_afa_methode",
            help=(
                "**Linear (§7 Abs. 4):** 3% p.a. für 33⅓ Jahre.\n\n"
                "**Degressiv (§7 Abs. 5a):** 5% vom Restbuchwert (declining balance). "
                "Möglichkeit zum Wechsel auf linear.\n\n"
                "**Degressiv + §7b:** Zusätzlich 5% Sonder-AfA für die ersten 4 Jahre. "
                "Voraussetzung: QNG-Zertifizierung, max. €5.200/m² Baukosten."
            ),
        )

        wohnflaeche_m2 = 0.0
        switch_year = 999  # default: never switch

        if afa_methode in ("Degressiv (5%)", "Degressiv + §7b Sonder-AfA"):
            switch_year = st.slider(
                "Wechsel zu Linear in Jahr",
                1, 34, 15,
                help="In welchem Jahr soll von degressiver zu linearer AfA gewechselt werden? "
                     "Optimal typischerweise um Jahr 14-17.",
                key="nb_switch_year",
            )

        if afa_methode == "Degressiv + §7b Sonder-AfA":
            wohnflaeche_m2 = st.number_input(
                "Wohnfläche (m²)", value=150.0, step=5.0,
                help="Wird für die §7b-Prüfung benötigt: Baukosten/m² dürfen max. €5.200 betragen.",
                key="nb_wohnflaeche",
            )
            kosten_pro_m2 = baukosten / wohnflaeche_m2 if wohnflaeche_m2 > 0 else float('inf')
            if kosten_pro_m2 <= 5200:
                st.success(f"✅ {kosten_pro_m2:,.0f} €/m² ≤ 5.200 €/m² — §7b Sonder-AfA anwendbar")
            else:
                st.error(f"❌ {kosten_pro_m2:,.0f} €/m² > 5.200 €/m² — §7b Sonder-AfA NICHT anwendbar")

    # --- 3. Kreditkonditionen ---
    with st.sidebar.expander("3. Kreditkonditionen", expanded=False):
        st.caption("Was verlangt die Bank?")
        zinssatz = st.slider(
            "Zinssatz pro Jahr (%)", 0.5, 10.0, 3.5, 0.1,
            help="Aktuell sind ca. 3.5%-4.5% üblich.",
            key="nb_zinssatz",
        )
        tilgung = st.slider(
            "Anfängliche Tilgung (%)", 1.0, 10.0, 2.0, 0.1,
            help="Empfohlen sind mind. 2%.",
            key="nb_tilgung",
        )
        zinsbindung = st.slider(
            "Zinsbindung (Jahre)", 5, 30, 15,
            help="So lange garantiert dir die Bank den Zinssatz.",
            key="nb_zinsbindung",
        )

    # --- 4. Eigentum & Kapital ---
    with st.sidebar.expander("4. Eigentum & Kapital", expanded=True):
        eigentums_modus = st.radio(
            "Eigentumsverhältnisse",
            ["Alleineigentum (Eine Person)", "Gemeinschaftseigentum (nach EK-Anteil)"],
            key="nb_eigentum",
        )

        if eigentums_modus == "Alleineigentum (Eine Person)":
            eigentuemer = st.selectbox(
                "Wer ist der Eigentümer (Grundbuch)?",
                ["Person A (meist Hauptverdiener)", "Person B"],
                key="nb_eigentuemer",
            )
            st.caption("Das Eigenkapital wird dem Eigentümer zugerechnet.")
            eigenkapital_a = st.number_input("Eigenkapital Käufer (€)", value=100000.0, step=5000.0, key="nb_ek_a")
            geschenk_a = st.number_input("Schenkung an Käufer (€)", value=440000.0, step=5000.0, key="nb_geschenk_a")
            startkapital_gesamt = eigenkapital_a + geschenk_a

            vertrag_ausschluss_zugewinn = st.checkbox(
                "Ehevertrag: Immobilie aus Zugewinn ausgeschlossen?",
                value=False,
                help="Gütertrennung für diesen Gegenstand.",
                key="nb_zugewinn",
            )
        else:
            st.caption("Beide Partner bringen Kapital ein.")
            col_ek1, col_ek2 = st.columns(2)
            with col_ek1:
                eigenkapital_a = st.number_input("Eigenkapital Person A (€)", value=50000.0, step=5000.0, key="nb_ek_a2")
                geschenk_a = st.number_input("Schenkung an A (€)", value=220000.0, step=5000.0, key="nb_geschenk_a2")
            with col_ek2:
                eigenkapital_b = st.number_input("Eigenkapital Person B (€)", value=50000.0, step=5000.0, key="nb_ek_b")
                geschenk_b = st.number_input("Schenkung an B (€)", value=220000.0, step=5000.0, key="nb_geschenk_b")
            startkapital_gesamt = eigenkapital_a + geschenk_a + eigenkapital_b + geschenk_b

    # --- 5. Miete & Kosten ---
    with st.sidebar.expander("5. Miete & Ausgaben", expanded=False):
        st.caption("Einnahmen und laufende Kosten")
        mieteinnahmen_pm = st.number_input("Monatliche Kaltmiete (€)", value=2116.0, step=50.0, key="nb_miete")
        mietsteigerung_pa = st.slider("Jährliche Mietsteigerung (%)", 0.0, 5.0, 2.0, 0.1, key="nb_mietsteigerung")
        instandhaltung_pa = st.number_input("Rücklage Instandhaltung/Jahr (€)", value=3000.0, step=100.0, key="nb_instandhaltung")
        mietausfall_pa = st.slider("Risiko Mietausfall (%)", 0.0, 10.0, 2.0, 0.5, key="nb_mietausfall")
        kostensteigerung_pa = st.slider("Kostensteigerung pro Jahr (%)", 0.0, 5.0, 2.0, 0.1, key="nb_kostensteigerung")
        wertsteigerung_pa = st.slider("Wertsteigerung Immobilie (%)", 0.0, 10.0, 2.0, 0.1, key="nb_wertsteigerung")

    # --- 6. Einkommen & Steuer ---
    with st.sidebar.expander("6. Einkommen & Steuer (2026)", expanded=True):
        st.caption("Einkommen für Zusammenveranlagung (Ehegattensplitting)")
        std_einkommen_mann = st.number_input("Brutto-Einkommen Person A (Standard) €", value=71000, step=1000, key="nb_ek_mann")
        std_einkommen_frau = st.number_input("Brutto-Einkommen Person B (Standard) €", value=80000, step=1000, key="nb_ek_frau")
        st.info(f"Summe Standard: {std_einkommen_mann + std_einkommen_frau:,.2f} €")

        st.markdown("### Sonderzeitraum")
        nutze_sonderzeitraum = st.checkbox("Sonderzeitraum aktivieren", value=False, key="nb_sonder")
        if nutze_sonderzeitraum:
            sonder_jahre = st.slider("Zeitraum (Jahre)", 1, 40, (3, 7), key="nb_sonder_jahre")
            sonder_einkommen_mann = st.number_input("Einkommen Person A (Sonder) €", value=71000, step=1000, key="nb_sonder_mann")
            sonder_einkommen_frau = st.number_input("Einkommen Person B (Sonder) €", value=20000, step=1000, key="nb_sonder_frau")
            st.info(f"Summe Sonder: {sonder_einkommen_mann + sonder_einkommen_frau:,.2f} €")
        else:
            sonder_jahre = (0, 0)
            sonder_einkommen_mann = 0
            sonder_einkommen_frau = 0

    # --- 7. Exit-Szenario ---
    with st.sidebar.expander("7. Exit-Szenario", expanded=False):
        st.caption("Parameter für den Fall eines vorzeitigen Verkaufs")
        marktzins_verkauf = st.slider("Marktzins bei Verkauf (%)", 0.0, 10.0, 1.5, 0.1, key="nb_marktzins")
        verkaufskosten_prozent = st.slider("Verkaufskosten (%)", 0.0, 10.0, 3.0, 0.5, key="nb_verkaufskosten")

    # =========================================================================
    # BERECHNUNG
    # =========================================================================

    gesamtinvestition = gesamtkosten  # alias for clarity
    kreditbetrag = gesamtinvestition - startkapital_gesamt

    if kreditbetrag <= 0:
        st.error(
            f"Das Eigenkapital ({startkapital_gesamt:,.2f} €) deckt die Gesamtkosten "
            f"({gesamtinvestition:,.2f} €). Kein Kredit notwendig."
        )
        st.stop()

    jaehrliche_rate = kreditbetrag * (zinssatz / 100 + tilgung / 100)
    monatliche_rate = jaehrliche_rate / 12

    # Pre-compute AFA schedule
    afa_schedule = berechne_neubau_afa(
        baukosten, afa_methode, switch_year, wohnflaeche_m2, max_years=80
    )

    # Initial state
    jahres_daten = []
    restschuld = kreditbetrag
    aktuelle_jahresmiete = mieteinnahmen_pm * 12
    aktuelle_instandhaltung = instandhaltung_pa
    aktueller_immobilienwert = grundstueckspreis + baukosten  # market value at construction

    anfangs_vermoegen_netto = startkapital_gesamt
    vermoegen_vorjahr = (grundstueckspreis + baukosten) - kreditbetrag

    # Eigentumsanteile
    if eigentums_modus == "Gemeinschaftseigentum (nach EK-Anteil)":
        kapital_a = eigenkapital_a + geschenk_a
        kapital_b = eigenkapital_b + geschenk_b
        anteil_kredit_pro_kopf = kreditbetrag / 2
        invest_a = kapital_a + anteil_kredit_pro_kopf
        invest_b = kapital_b + anteil_kredit_pro_kopf
        anteil_a_prozent = invest_a / gesamtinvestition
        anteil_b_prozent = invest_b / gesamtinvestition
    else:
        if "Person A" in eigentuemer:
            anteil_a_prozent = 1.0
            anteil_b_prozent = 0.0
        else:
            anteil_a_prozent = 0.0
            anteil_b_prozent = 1.0

    kumulierte_afa_total = 0.0
    jahr = 0
    max_laufzeit = 80

    while restschuld > 1.0 and jahr < max_laufzeit:
        jahr += 1

        # 1. Einkommen
        if nutze_sonderzeitraum and sonder_jahre[0] <= jahr <= sonder_jahre[1]:
            ek_a = sonder_einkommen_mann
            ek_b = sonder_einkommen_frau
        else:
            ek_a = std_einkommen_mann
            ek_b = std_einkommen_frau

        # 2. Kredit
        zinsanteil_jahr = restschuld * (zinssatz / 100)
        tilgungsanteil_jahr = jaehrliche_rate - zinsanteil_jahr
        if tilgungsanteil_jahr > restschuld:
            tilgungsanteil_jahr = restschuld
            jaehrliche_rate_effektiv = zinsanteil_jahr + tilgungsanteil_jahr
        else:
            jaehrliche_rate_effektiv = jaehrliche_rate

        restschuld -= tilgungsanteil_jahr

        # 3. AfA this year
        afa_info = afa_schedule[jahr - 1] if jahr <= len(afa_schedule) else {
            'afa': 0.0, 'buchwert': 0.0, 'methode_label': '—', 'sonder_afa': 0.0
        }
        afa_jahr = afa_info['afa'] + afa_info['sonder_afa']
        kumulierte_afa_total += afa_jahr

        # 4. Werbungskosten & V+V
        werbungskosten = zinsanteil_jahr + afa_jahr + aktuelle_instandhaltung
        ergebnis_vv = aktuelle_jahresmiete - werbungskosten

        # 5. Steuer
        steuer_ohne = get_steuerlast_zusammen(ek_a, ek_b)
        ek_a_mit = ek_a + (ergebnis_vv * anteil_a_prozent)
        ek_b_mit = ek_b + (ergebnis_vv * anteil_b_prozent)
        steuer_mit = get_steuerlast_zusammen(ek_a_mit, ek_b_mit)
        steuerersparnis = steuer_ohne - steuer_mit

        grenzsteuersatz = (steuerersparnis / abs(ergebnis_vv)) if ergebnis_vv != 0 else 0.0

        # 6. Cashflow
        mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
        cashflow_vor_steuer = aktuelle_jahresmiete - jaehrliche_rate_effektiv - aktuelle_instandhaltung - mietausfall_betrag
        cashflow_nach_steuer = cashflow_vor_steuer + steuerersparnis

        monatliche_gesamtkosten = (jaehrliche_rate_effektiv + aktuelle_instandhaltung + mietausfall_betrag) / 12
        monatlicher_eigenaufwand = monatliche_gesamtkosten - (aktuelle_jahresmiete / 12)

        # 7. Vermögen
        aktueller_immobilienwert *= (1 + wertsteigerung_pa / 100)
        aktuelles_vermoegen_netto = aktueller_immobilienwert - restschuld

        # 8. Exit: Scheidung
        zugewinn_gesamt = aktuelles_vermoegen_netto - anfangs_vermoegen_netto
        ausgleichszahlung_scheidung = 0.0
        if eigentums_modus == "Alleineigentum (Eine Person)":
            if not vertrag_ausschluss_zugewinn and zugewinn_gesamt > 0:
                ausgleichszahlung_scheidung = zugewinn_gesamt / 2

        # 9. Exit: Verkauf
        vorfaelligkeitsentschaedigung = 0.0
        if jahr < zinsbindung:
            restlaufzeit = zinsbindung - jahr
            zinsdifferenz = max(0, zinssatz - marktzins_verkauf)
            vorfaelligkeitsentschaedigung = restschuld * (zinsdifferenz / 100) * restlaufzeit

        verkaufskosten = aktueller_immobilienwert * (verkaufskosten_prozent / 100)
        spekulationssteuer = 0.0
        if jahr < 10:
            buchwert_steuer = (grundstueckspreis + baukosten) - kumulierte_afa_total
            veraeusserungsgewinn = (aktueller_immobilienwert - verkaufskosten) - buchwert_steuer
            if veraeusserungsgewinn > 0:
                spekulationssteuer = veraeusserungsgewinn * grenzsteuersatz

        netto_erloes_verkauf = (
            aktueller_immobilienwert - restschuld
            - vorfaelligkeitsentschaedigung - verkaufskosten - spekulationssteuer
        )

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
            "AfA": afa_info['afa'],
            "Sonder-AfA (§7b)": afa_info['sonder_afa'],
            "AfA Gesamt": afa_jahr,
            "AfA (Methode)": afa_info['methode_label'],
            "Buchwert Gebäude": afa_info['buchwert'],
            "Kumulierte AfA": kumulierte_afa_total,
            "Steuerersparnis": steuerersparnis,
            "Cashflow": cashflow_nach_steuer,
            "Immobilienwert": aktueller_immobilienwert,
            "Vermögen": aktuelles_vermoegen_netto,
            "Zuwachs Vermögen": aktuelles_vermoegen_netto - vermoegen_vorjahr,
            "Vorfälligkeitsentschädigung (Exit)": vorfaelligkeitsentschaedigung,
            "Netto-Erlös bei Verkauf (Exit)": netto_erloes_verkauf,
            "Scheidung: Ausgleichszahlung": ausgleichszahlung_scheidung,
        })

        vermoegen_vorjahr = aktuelles_vermoegen_netto
        aktuelle_jahresmiete *= (1 + mietsteigerung_pa / 100)
        aktuelle_instandhaltung *= (1 + kostensteigerung_pa / 100)

    df_projektion = pd.DataFrame(jahres_daten)

    # =========================================================================
    # ANZEIGE
    # =========================================================================
    col1, col2 = st.columns([1, 5])

    with col2:
        show_analysis, show_inflation = render_toggles()

    if show_inflation and inflationsrate > 0:
        df_display = apply_inflation(
            df_projektion, inflationsrate,
            exclude_cols=["Jahr", "Grenzsteuersatz (%)", "AfA (Methode)"],
        )
    else:
        df_display = df_projektion

    # --- Overview column ---
    with col1:
        st.subheader("Übersicht")
        if show_inflation:
            st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")

        st.metric(
            "Gesamtinvestition",
            f"{gesamtinvestition:,.2f} €",
            help=f"Grundstück ({grundstueckspreis:,.0f}) + Bau ({baukosten:,.0f}) + Bau-NK ({baunebenkosten:,.0f}) + Kauf-NK ({kaufnebenkosten:,.0f}).",
        )
        st.metric(
            "Kreditbetrag",
            f"{kreditbetrag:,.2f} €",
            help=f"Gesamtkosten ({gesamtinvestition:,.0f}) - Eigenkapital ({startkapital_gesamt:,.0f}).",
        )
        st.metric(
            "Monatliche Rate (Bank)",
            f"{monatliche_rate:,.2f} €",
        )

        avg_monatliche_gesamtkosten = df_display['Monatliche Gesamtkosten'].mean() if not df_display.empty else 0
        st.metric("Ø Monatliche Gesamtkosten", f"{avg_monatliche_gesamtkosten:,.2f} €")

        avg_eigenaufwand = df_display['Monatlicher Eigenaufwand'].mean() if not df_display.empty else 0
        st.metric("Ø Monatlicher Eigenaufwand", f"{avg_eigenaufwand:,.2f} €")

        restschuld_zinsbindung = 0.0
        if not df_display.empty:
            row = df_display[df_display['Jahr'] == zinsbindung]
            if not row.empty:
                restschuld_zinsbindung = row.iloc[0]['Restschuld']
        st.metric(f"Restschuld nach {zinsbindung} J.", f"{restschuld_zinsbindung:,.2f} €")
        st.metric("Laufzeit bis Volltilgung", f"{jahr} Jahre")

        st.markdown("---")
        avg_cashflow = df_display['Cashflow'].mean() if not df_display.empty else 0
        st.metric("Ø Cashflow (nach Steuer)", f"{avg_cashflow:,.2f} €")

        end_vermoegen = df_display.iloc[-1]['Vermögen'] if not df_display.empty else 0
        st.metric("Vermögen am Ende", f"{end_vermoegen:,.2f} €")

    # --- Main content ---
    with col2:
        if show_analysis:
            st.markdown("## 🧐 Experten-Analyse: Neubau Investition (Stand 2026)")
            if show_inflation:
                st.caption(f"⚠️ Inflationsbereinigt ({inflationsrate}% p.a.)")

            # 1. AfA-Analyse
            with st.expander("1. AfA-Methode & Steuereffekt", expanded=True):
                st.info(f"**Gewählte Methode:** {afa_methode}")
                # Show first 5 years of AFA
                if len(afa_schedule) >= 5:
                    afa_preview = []
                    for i in range(5):
                        info = afa_schedule[i]
                        afa_preview.append({
                            "Jahr": i + 1,
                            "AfA": f"{info['afa']:,.0f} €",
                            "Sonder-AfA": f"{info['sonder_afa']:,.0f} €",
                            "Buchwert": f"{info['buchwert']:,.0f} €",
                            "Methode": info['methode_label'],
                        })
                    st.table(pd.DataFrame(afa_preview))

                if afa_methode == "Linear (3%)":
                    st.write(f"Jährliche AfA: **{baukosten * 0.03:,.0f} €** für 33⅓ Jahre.")
                elif afa_methode in ("Degressiv (5%)", "Degressiv + §7b Sonder-AfA"):
                    st.write(f"Jahr 1 degressive AfA: **{baukosten * 0.05:,.0f} €** (5% von {baukosten:,.0f} €)")
                    st.write(f"Wechsel zu linear geplant in **Jahr {switch_year}**.")

                    if afa_methode == "Degressiv + §7b Sonder-AfA":
                        kosten_pro_m2 = baukosten / wohnflaeche_m2 if wohnflaeche_m2 > 0 else float('inf')
                        if kosten_pro_m2 <= 5200:
                            st.success(f"✅ §7b Sonder-AfA: zusätzlich **{baukosten * 0.05:,.0f} €/Jahr** für die ersten 4 Jahre.")
                        else:
                            st.error("❌ §7b nicht anwendbar — Baukosten/m² überschreiten €5.200.")

            # 2. Finanzierung
            with st.expander("2. Finanzierung & Eigenkapital", expanded=True):
                ek_quote = (startkapital_gesamt / gesamtinvestition) * 100
                st.metric("Eigenkapitalquote", f"{ek_quote:.1f} %")
                if ek_quote < 20:
                    st.warning("🟠 **Erhöhtes Risiko (<20%):** Bei Neubauten verlangen Banken oft höheres EK.")
                else:
                    st.success("🟢 **Solide Basis:** Gute Voraussetzungen für die Finanzierung.")

            # 3. Rentabilität
            with st.expander("3. Rentabilität", expanded=True):
                brutto_mietrendite = (mieteinnahmen_pm * 12 / gesamtinvestition) * 100
                kaufpreisfaktor = gesamtinvestition / (mieteinnahmen_pm * 12) if mieteinnahmen_pm > 0 else 0
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.metric("Brutto-Mietrendite", f"{brutto_mietrendite:.2f} %")
                    st.metric("Kaufpreisfaktor", f"{kaufpreisfaktor:.1f}")
                with col_b:
                    if brutto_mietrendite < zinssatz:
                        st.warning(f"🟠 Mietrendite ({brutto_mietrendite:.2f}%) < Kreditzins ({zinssatz}%).")
                    else:
                        st.success("🟢 Mietrendite über Kreditzins.")
                    if kaufpreisfaktor > 30:
                        st.error("🔴 Kaufpreisfaktor > 30 — sehr teuer.")
                    elif kaufpreisfaktor > 25:
                        st.warning("🟠 Kaufpreisfaktor 25-30 — marktüblich bis teuer.")
                    else:
                        st.success("🟢 Kaufpreisfaktor < 25 — günstig.")

            st.markdown("---")

        # --- Tabs ---
        formeln = get_formeln("Neubau (Investitions-Immobilie)")
        tab_t, tab_g, tab_f = st.tabs(["Tabelle", "Graph", "📚 Formeln"])

        with tab_t:
            cols_to_show = [
                "Jahr", "Einkommen (zvE)", "Grenzsteuersatz (%)", "Restschuld",
                "Mieteinnahmen", "Instandhaltung", "Mietausfall",
                "Zinsanteil", "Tilgungsanteil",
                "Monatliche Gesamtkosten", "Monatlicher Eigenaufwand",
                "AfA", "Sonder-AfA (§7b)", "AfA Gesamt", "AfA (Methode)",
                "Buchwert Gebäude", "Kumulierte AfA",
                "Steuerersparnis", "Cashflow",
                "Immobilienwert", "Vermögen", "Zuwachs Vermögen",
                "Vorfälligkeitsentschädigung (Exit)", "Netto-Erlös bei Verkauf (Exit)",
                "Scheidung: Ausgleichszahlung",
            ]
            format_dict = {
                col: "{:,.2f} €"
                for col in cols_to_show
                if col not in ["Jahr", "Grenzsteuersatz (%)", "AfA (Methode)"]
            }
            format_dict["Jahr"] = "{:.0f}"
            format_dict["Grenzsteuersatz (%)"] = "{:.1f} %"

            styler = df_display[cols_to_show].style.format(format_dict)
            styler.hide(axis="index")
            styler.set_properties(
                subset=["AfA", "Sonder-AfA (§7b)", "AfA Gesamt"],
                **{'background-color': '#e8f5e9', 'color': 'black'},
            )

            if nutze_sonderzeitraum:
                def highlight_sonder(row):
                    if sonder_jahre[0] <= row['Jahr'] <= sonder_jahre[1]:
                        return [
                            'background-color: #fff3cd; color: black' if col == 'Einkommen (zvE)' else ''
                            for col in row.index
                        ]
                    return ['' for _ in row.index]
                styler.apply(highlight_sonder, axis=1)

            def color_cashflow(val):
                if val < 0:
                    return 'background-color: #ffcdd2; color: black'
                elif val > 0:
                    return 'background-color: #c8e6c9; color: black'
                return ''
            styler.map(color_cashflow, subset=['Cashflow'])

            def color_growth(val):
                if val > 0:
                    return 'background-color: #dcedc8; color: black'
                return ''
            styler.map(color_growth, subset=['Zuwachs Vermögen'])

            def color_tax_savings(val):
                if val > 0:
                    return 'background-color: #e1bee7; color: black'
                return ''
            styler.map(color_tax_savings, subset=['Steuerersparnis'])

            def color_eigenaufwand(val):
                if val > 0:
                    return 'background-color: #ffebee; color: black'
                elif val < 0:
                    return 'background-color: #e8f5e9; color: black'
                return ''
            styler.map(color_eigenaufwand, subset=['Monatlicher Eigenaufwand'])

            def color_exit(val):
                if val > 0:
                    return 'background-color: #c8e6c9; color: black'
                elif val < 0:
                    return 'background-color: #ffcdd2; color: black'
                return ''
            styler.map(color_exit, subset=['Netto-Erlös bei Verkauf (Exit)'])

            st.dataframe(styler, use_container_width=True, height=700, hide_index=True)

        with tab_g:
            render_graph_tab(
                df_display,
                default_cols=["Restschuld", "Immobilienwert", "Vermögen", "Netto-Erlös bei Verkauf (Exit)"],
                key_suffix="neubau",
            )

        with tab_f:
            render_formeln_tab(formeln, key_suffix="neubau")
