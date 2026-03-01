"""Scenario: Neubau (Investitions-Immobilie) — V2.

Adapted from v1: accepts optional wizard_defaults dict to override
default field values from wizard inputs.
"""

import streamlit as st
import pandas as pd

from calculations.tax import get_steuerlast_zusammen
from calculations.formulas import get_formeln
from calculations.ui_helpers import render_toggles, apply_inflation, render_graph_tab, render_formeln_tab
from calculations.state_management import (
    persistent_number_input,
    persistent_slider,
    persistent_radio,
    persistent_selectbox,
    persistent_checkbox,
)


def _d(wizard_defaults, key, fallback):
    val = wizard_defaults[key] if wizard_defaults and key in wizard_defaults else fallback
    if isinstance(fallback, float):
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return val


def berechne_neubau_afa(baukosten, methode, switch_year, wohnflaeche_m2=0, max_years=50):
    """Return a list of dicts with annual AFA info for each year."""
    gebaeudewert = baukosten
    nutzungsdauer = 100 / 3
    buchwert = gebaeudewert
    ergebnisse = []

    for jahr in range(1, max_years + 1):
        if buchwert <= 0:
            ergebnisse.append({'afa': 0.0, 'buchwert': 0.0, 'methode_label': '—', 'sonder_afa': 0.0})
            continue

        sonder_afa = 0.0
        if methode == "Linear (3%)":
            afa = gebaeudewert * 0.03
            afa = min(afa, buchwert)
            label = "Linear 3%"
        elif methode in ("Degressiv (5%)", "Degressiv + §7b Sonder-AfA"):
            if jahr < switch_year:
                afa = buchwert * 0.05
                label = "Degressiv 5%"
            else:
                remaining_years = nutzungsdauer - (jahr - 1)
                if remaining_years > 0:
                    afa = buchwert / remaining_years
                    label = f"Linear (Switch J{switch_year})"
                else:
                    afa = buchwert
                    label = "Linear (Rest)"
            if methode == "Degressiv + §7b Sonder-AfA" and jahr <= 4:
                kosten_pro_m2 = baukosten / wohnflaeche_m2 if wohnflaeche_m2 > 0 else float('inf')
                if kosten_pro_m2 <= 5200:
                    sonder_afa = gebaeudewert * 0.05
                    label += " + §7b"
        else:
            afa = 0.0
            label = "—"

        gesamt_afa_jahr = afa + sonder_afa
        if gesamt_afa_jahr > buchwert:
            factor = buchwert / gesamt_afa_jahr
            afa *= factor
            sonder_afa *= factor
            gesamt_afa_jahr = buchwert
        buchwert -= gesamt_afa_jahr
        ergebnisse.append({'afa': afa, 'buchwert': max(0, buchwert), 'methode_label': label, 'sonder_afa': sonder_afa})

    return ergebnisse


def render(inflationsrate: float, wizard_defaults: dict = None):
    """Renders the Neubau scenario with optional wizard pre-fills."""

    eigenkapital_a = 0.0
    eigenkapital_b = 0.0
    geschenk_a = 0.0
    geschenk_b = 0.0
    startkapital_gesamt = 0.0
    vertrag_ausschluss_zugewinn = False

    # =========================================================================
    # SIDEBAR INPUTS
    # =========================================================================

    with st.sidebar.expander("1. Startkapital (Eigenkapital)", expanded=True):
        st.caption("Wie viel Geld ist bereits vorhanden?")
        eigentums_modus = persistent_radio(
            "Eigentumsverhältnisse",
            ["Alleineigentum (Eine Person)", "Gemeinschaftseigentum (nach EK-Anteil)"],
            key="nb_eigentum",
        )
        if eigentums_modus == "Alleineigentum (Eine Person)":
            eigentuemer = persistent_selectbox(
                "Wer ist der Eigentümer (Grundbuch)?",
                ["Person A (meist Hauptverdiener)", "Person B"],
                key="nb_eigentuemer",
            )
            st.caption("Das Eigenkapital wird dem Eigentümer zugerechnet.")
            eigenkapital_a = persistent_number_input(
                "Eigenkapital Käufer (€)",
                value=_d(wizard_defaults, "v2_ek_a", 100_000.0),
                step=5_000.0, key="shared_ek_a",
            )
            geschenk_a = persistent_number_input(
                "Schenkung an Käufer (€)",
                value=_d(wizard_defaults, "v2_geschenk_a", 440_000.0),
                step=5_000.0, key="shared_geschenk_a",
            )
            startkapital_gesamt = eigenkapital_a + geschenk_a
            vertrag_ausschluss_zugewinn = persistent_checkbox(
                "Ehevertrag: Immobilie aus Zugewinn ausgeschlossen?",
                value=_d(wizard_defaults, "v2_ehevertrag", False),
                help="Gütertrennung für diesen Gegenstand.",
                key="nb_zugewinn",
            )
        else:
            st.caption("Beide Partner bringen Kapital ein.")
            col_ek1, col_ek2 = st.columns(2)
            with col_ek1:
                eigenkapital_a = persistent_number_input("Eigenkapital Person A (€)",
                                                         value=_d(wizard_defaults, "v2_ek_a", 50_000.0), step=5_000.0,
                                                         key="shared_ek_a")
                geschenk_a = persistent_number_input("Schenkung an A (€)",
                                                     value=_d(wizard_defaults, "v2_geschenk_a", 220_000.0),
                                                     step=5_000.0, key="shared_geschenk_a")
            with col_ek2:
                eigenkapital_b = persistent_number_input("Eigenkapital Person B (€)",
                                                         value=_d(wizard_defaults, "v2_ek_b", 50_000.0), step=5_000.0,
                                                         key="shared_ek_b")
                geschenk_b = persistent_number_input("Schenkung an B (€)",
                                                     value=_d(wizard_defaults, "v2_geschenk_b", 220_000.0),
                                                     step=5_000.0, key="shared_geschenk_b")
            startkapital_gesamt = eigenkapital_a + geschenk_a + eigenkapital_b + geschenk_b

    with st.sidebar.expander("2. Objekt (Grundstück & Bau)", expanded=True):
        st.caption("Kosten für das Grundstück und den Bau des Gebäudes")
        grundstueckspreis = persistent_number_input("Grundstückspreis (€)", value=350_200.0, step=10_000.0,
                                                    key="nb_grundstueckspreis",
                                                    help="Preis für das Bauland. Das Grundstück ist steuerlich NICHT abschreibbar.")
        baukosten = persistent_number_input("Baukosten Gebäude (€)", value=679_800.0, step=10_000.0, key="nb_baukosten",
                                            help="Reine Baukosten (Gebäude). Nur dieser Betrag ist steuerlich abschreibbar (AfA).")
        baunebenkosten_prozent = persistent_slider("Baunebenkosten (%)", 10.0, 25.0, 15.0, 0.5, key="nb_baunebenkosten",
                                                   help="Zusatzkosten beim Bauen: Architekt, Statik, Genehmigungen, Erschließung. Üblich: 15-20% der Baukosten.")
        baunebenkosten = baukosten * (baunebenkosten_prozent / 100)

        st.markdown("##### Kaufnebenkosten (Grundstück)")
        col_nk1, col_nk2 = st.columns(2)
        with col_nk1:
            notar_grundbuch_prozent = persistent_number_input("Notar & Grundbuch (%)", value=2.0, step=0.1,
                                                              key="nb_notar",
                                                              help="Kosten für Beurkundung und Grundbucheintrag.")
        with col_nk2:
            grunderwerbsteuer_prozent = persistent_number_input("Grunderwerbsteuer (%)", value=6.5, step=0.5,
                                                                key="nb_grunderwerb",
                                                                help="Grunderwerbsteuer auf das Grundstück (je nach Bundesland 3.5%-6.5%).")

        kaufnebenkosten = grundstueckspreis * ((notar_grundbuch_prozent + grunderwerbsteuer_prozent) / 100)
        gesamtkosten = grundstueckspreis + baukosten + baunebenkosten + kaufnebenkosten
        st.info(f"**Gesamtkosten:** {gesamtkosten:,.0f} €")

    with st.sidebar.expander("3. Kreditkonditionen", expanded=False):
        zinssatz = persistent_slider("Zinssatz pro Jahr (%)", 0.5, 10.0, 3.2, 0.1, key="shared_zinssatz",
                                     help="Aktuell sind ca. 3.5%-4.5% üblich.")
        tilgung = persistent_slider("Anfängliche Tilgung (%)", 1.0, 10.0, 2.0, 0.1, key="nb_tilgung",
                                    help="Empfohlen sind mind. 2%.")
        zinsbindung = persistent_slider("Zinsbindung (Jahre)", 5, 30, 15, key="nb_zinsbindung",
                                        help="So lange garantiert dir die Bank den Zinssatz.")

    with st.sidebar.expander("4. AfA-Methode", expanded=False):
        st.caption("Steuerliche Abschreibung des Gebäudes")
        afa_methode = persistent_radio(
            "AfA-Methode wählen",
            ["Linear (3%)", "Degressiv (5%)", "Degressiv + §7b Sonder-AfA"],
            index=0, key="nb_afa_methode",
        )
        wohnflaeche_m2 = 0.0
        switch_year = 999
        if afa_methode in ("Degressiv (5%)", "Degressiv + §7b Sonder-AfA"):
            switch_year = persistent_slider("Wechsel zu Linear in Jahr", 1, 34, 15, key="nb_switch_year",
                                            help="In welchem Jahr soll von degressiver zu linearer AfA gewechselt werden? ")
        if afa_methode == "Degressiv + §7b Sonder-AfA":
            wohnflaeche_m2 = persistent_number_input("Wohnfläche (m²)", value=150.0, step=5.0, key="nb_wohnflaeche",
                                                     help="Wird für die §7b-Prüfung benötigt: Baukosten/m² dürfen max. €5.200 betragen.")
            kosten_pro_m2 = baukosten / wohnflaeche_m2 if wohnflaeche_m2 > 0 else float('inf')
            if kosten_pro_m2 <= 5200:
                st.success(f"✅ {kosten_pro_m2:,.0f} €/m² ≤ 5.200 €/m² — §7b anwendbar")
            else:
                st.error(f"❌ {kosten_pro_m2:,.0f} €/m² > 5.200 €/m² — §7b NICHT anwendbar")

    with st.sidebar.expander("5. Miete & Ausgaben", expanded=False):
        mieteinnahmen_pm = persistent_number_input(
            "Monatliche Kaltmiete (€)",
            value=_d(wizard_defaults, "v2_kaltmiete", 2_116.0),
            step=50.0, key="nb_miete", help="Die Miete, die du bekommst (ohne Nebenkosten)."
        )
        mietsteigerung_pa = persistent_slider("Jährliche Mietsteigerung (%)", 0.0, 5.0, 3.0, 0.1,
                                              key="nb_mietsteigerung",
                                              help="Um wie viel Prozent erhöhst du die Miete jährlich? (Inflationsausgleich)")
        instandhaltung_pa = persistent_number_input("Rücklage Instandhaltung/Jahr (€)", value=4_000.0, step=100.0,
                                                    key="nb_instandhaltung",
                                                    help="Geld, das du für Reparaturen (Dach, Heizung, etc.) zurücklegen solltest. Faustformel: 10-15€ pro m² Wohnfläche im Jahr.")
        mietausfall_pa = persistent_slider("Risiko Mietausfall (%)", 0.0, 10.0, 2.0, 0.5, key="nb_mietausfall",
                                           help="Kalkuliere ein, dass die Wohnung mal leer steht oder Mieter nicht zahlen. 2% entspricht ca. 1 Woche Leerstand pro Jahr.")
        kostensteigerung_pa = persistent_slider("Kostensteigerung pro Jahr (%)", 0.0, 5.0, 2.0, 0.1,
                                                key="nb_kostensteigerung",
                                                help="Handwerker und Material werden teurer. Wie stark steigen deine Instandhaltungskosten?")
        wertsteigerung_pa = persistent_slider("Wertsteigerung Immobilie (%)", 0.0, 10.0, 2.0, 0.1,
                                              key="shared_wertsteigerung",
                                              help="Gewinnt das Haus an Wert? Historisch oft 1-3%, aber keine Garantie!")

    with st.sidebar.expander("6. Einkommen & Steuer (2026)", expanded=False):
        std_einkommen_mann = persistent_number_input("Brutto-Einkommen Person A (Standard) €",
                                                     value=_d(wizard_defaults, "v2_einkommen_a", 71_000), step=1_000,
                                                     key="shared_ek_mann",
                                                     help="Zu versteuerndes Jahreseinkommen Person A.")
        std_einkommen_frau = persistent_number_input("Brutto-Einkommen Person B (Standard) €",
                                                     value=_d(wizard_defaults, "v2_einkommen_b", 80_000), step=1_000,
                                                     key="shared_ek_frau",
                                                     help="Zu versteuerndes Jahreseinkommen Person B.")
        st.info(f"Summe Standard: {std_einkommen_mann + std_einkommen_frau:,.2f} €")
        st.markdown("### Sonderzeitraum")
        nutze_sonderzeitraum = persistent_checkbox("Sonderzeitraum aktivieren", value=False, key="nb_sonder",
                                                   help="Z.B. für Elternzeit oder Teilzeit.")
        if nutze_sonderzeitraum:
            sonder_jahre = persistent_slider("Zeitraum (Jahre)", 1, 40, _d(wizard_defaults, "v2_sonder_jahre", (3, 7)),
                                             key="nb_sonder_jahre")
            sonder_einkommen_mann = persistent_number_input("Einkommen Person A (Sonder) €",
                                                            value=_d(wizard_defaults, "v2_sonder_mann", 71_000),
                                                            step=1_000, key="nb_sonder_mann")
            sonder_einkommen_frau = persistent_number_input("Einkommen Person B (Sonder) €",
                                                            value=_d(wizard_defaults, "v2_sonder_frau", 20_000),
                                                            step=1_000, key="nb_sonder_frau")
        else:
            sonder_jahre = (0, 0)
            sonder_einkommen_mann = 0
            sonder_einkommen_frau = 0

    with st.sidebar.expander("7. Exit-Szenario", expanded=False):
        marktzins_verkauf = persistent_slider("Marktzins bei Verkauf (%)", 0.0, 10.0, 1.5, 0.1, key="nb_marktzins",
                                              help="Wird benötigt, um die Vorfälligkeitsentschädigung zu schätzen. Ist der Marktzins niedriger als dein Vertragszins, verlangt die Bank eine Entschädigung.")
        verkaufskosten_prozent = persistent_slider("Verkaufskosten (%)", 0.0, 10.0, 3.0, 0.5, key="nb_verkaufskosten",
                                                   help="Kosten, die beim Verkauf vom Erlös abgehen.")

    # =========================================================================
    # BERECHNUNG
    # =========================================================================
    gesamtinvestition = gesamtkosten
    kreditbetrag = gesamtinvestition - startkapital_gesamt

    if kreditbetrag <= 0:
        st.error(
            f"Das Eigenkapital ({startkapital_gesamt:,.2f} €) deckt die Gesamtkosten ({gesamtinvestition:,.2f} €). Kein Kredit notwendig.")
        st.stop()

    jaehrliche_rate = kreditbetrag * (zinssatz / 100 + tilgung / 100)
    monatliche_rate = jaehrliche_rate / 12
    afa_schedule = berechne_neubau_afa(baukosten, afa_methode, switch_year, wohnflaeche_m2, max_years=80)

    jahres_daten = []
    restschuld = kreditbetrag
    aktuelle_jahresmiete = mieteinnahmen_pm * 12
    aktuelle_instandhaltung = instandhaltung_pa
    aktueller_immobilienwert = grundstueckspreis + baukosten
    anfangs_vermoegen_netto = startkapital_gesamt
    vermoegen_vorjahr = (grundstueckspreis + baukosten) - kreditbetrag

    if eigentums_modus == "Gemeinschaftseigentum (nach EK-Anteil)":
        kapital_a = eigenkapital_a + geschenk_a
        kapital_b = eigenkapital_b + geschenk_b
        anteil_kredit_pro_kopf = kreditbetrag / 2
        anteil_a_prozent = (kapital_a + anteil_kredit_pro_kopf) / gesamtinvestition
        anteil_b_prozent = (kapital_b + anteil_kredit_pro_kopf) / gesamtinvestition
    else:
        anteil_a_prozent = 1.0 if "Person A" in eigentuemer else 0.0
        anteil_b_prozent = 1.0 - anteil_a_prozent

    kumulierte_afa_total = 0.0
    jahr = 0
    max_laufzeit = 80
    grenzsteuersatz = 0.0

    while restschuld > 1.0 and jahr < max_laufzeit:
        jahr += 1
        ek_a = sonder_einkommen_mann if (
                    nutze_sonderzeitraum and sonder_jahre[0] <= jahr <= sonder_jahre[1]) else std_einkommen_mann
        ek_b = sonder_einkommen_frau if (
                    nutze_sonderzeitraum and sonder_jahre[0] <= jahr <= sonder_jahre[1]) else std_einkommen_frau

        zinsanteil_jahr = restschuld * (zinssatz / 100)
        tilgungsanteil_jahr = jaehrliche_rate - zinsanteil_jahr
        if tilgungsanteil_jahr > restschuld:
            tilgungsanteil_jahr = restschuld
            jaehrliche_rate_effektiv = zinsanteil_jahr + tilgungsanteil_jahr
        else:
            jaehrliche_rate_effektiv = jaehrliche_rate
        restschuld -= tilgungsanteil_jahr

        afa_info = afa_schedule[jahr - 1] if jahr <= len(afa_schedule) else {'afa': 0.0, 'buchwert': 0.0,
                                                                             'methode_label': '—', 'sonder_afa': 0.0}
        afa_jahr = afa_info['afa'] + afa_info['sonder_afa']
        kumulierte_afa_total += afa_jahr

        werbungskosten = zinsanteil_jahr + afa_jahr + aktuelle_instandhaltung
        ergebnis_vv = aktuelle_jahresmiete - werbungskosten
        steuer_ohne = get_steuerlast_zusammen(ek_a, ek_b)
        steuer_mit = get_steuerlast_zusammen(ek_a + ergebnis_vv * anteil_a_prozent,
                                             ek_b + ergebnis_vv * anteil_b_prozent)
        steuerersparnis = steuer_ohne - steuer_mit
        grenzsteuersatz = (steuerersparnis / abs(ergebnis_vv)) if ergebnis_vv != 0 else 0.0

        mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
        cashflow_nach_steuer = aktuelle_jahresmiete - jaehrliche_rate_effektiv - aktuelle_instandhaltung - mietausfall_betrag + steuerersparnis
        monatliche_gesamtkosten = (jaehrliche_rate_effektiv + aktuelle_instandhaltung + mietausfall_betrag) / 12
        monatlicher_eigenaufwand = monatliche_gesamtkosten - (aktuelle_jahresmiete / 12)

        aktueller_immobilienwert *= (1 + wertsteigerung_pa / 100)
        aktuelles_vermoegen_netto = aktueller_immobilienwert - restschuld

        zugewinn_gesamt = aktuelles_vermoegen_netto - anfangs_vermoegen_netto
        ausgleichszahlung_scheidung = 0.0
        if eigentums_modus == "Alleineigentum (Eine Person)" and not vertrag_ausschluss_zugewinn and zugewinn_gesamt > 0:
            ausgleichszahlung_scheidung = zugewinn_gesamt / 2

        vorfaelligkeitsentschaedigung = 0.0
        if jahr < zinsbindung:
            vorfaelligkeitsentschaedigung = restschuld * (max(0, zinssatz - marktzins_verkauf) / 100) * (
                        zinsbindung - jahr)

        verkaufskosten = aktueller_immobilienwert * (verkaufskosten_prozent / 100)
        spekulationssteuer = 0.0
        if jahr < 10:
            buchwert_steuer = (grundstueckspreis + baukosten) - kumulierte_afa_total
            veraeusserungsgewinn = (aktueller_immobilienwert - verkaufskosten) - buchwert_steuer
            if veraeusserungsgewinn > 0:
                spekulationssteuer = veraeusserungsgewinn * grenzsteuersatz

        netto_erloes_verkauf = aktueller_immobilienwert - restschuld - vorfaelligkeitsentschaedigung - verkaufskosten - spekulationssteuer

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
    col1, col2 = st.columns([1, 3])
    with col2:
        show_inflation = render_toggles()

    if show_inflation and inflationsrate > 0:
        df_display = apply_inflation(df_projektion, inflationsrate,
                                     exclude_cols=["Jahr", "Grenzsteuersatz (%)", "AfA (Methode)"])
    else:
        df_display = df_projektion

    with col1:
        st.subheader("Übersicht")
        if show_inflation:
            st.caption(f"⚠️ Werte inflationsbereinigt ({inflationsrate}%)")

        avg_monatliche_gesamtkosten = df_display["Monatliche Gesamtkosten"].mean() if not df_display.empty else 0
        avg_eigenaufwand = df_display["Monatlicher Eigenaufwand"].mean() if not df_display.empty else 0
        restschuld_zinsbindung = 0.0
        if not df_display.empty:
            row = df_display[df_display["Jahr"] == zinsbindung]
            if not row.empty:
                restschuld_zinsbindung = row.iloc[0]["Restschuld"]
        total_tax_saved = df_display["Steuerersparnis"].sum() if not df_display.empty else 0
        end_vermoegen = df_display.iloc[-1]["Vermögen"] if not df_display.empty else 0
        avg_cashflow = df_display["Cashflow"].mean() if not df_display.empty else 0

        st.markdown("#### Investition")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Kreditbetrag", f"{kreditbetrag:,.0f} €")
            st.metric("Gesamtinvestition", f"{gesamtinvestition:,.0f} €")
        with col_m2:
            st.metric("Vermögen Ende", f"{end_vermoegen:,.0f} €")

        st.markdown("#### Monatliche Belastung")
        col_m3, col_m4 = st.columns(2)
        with col_m3:
            st.metric("Monatliche Rate (Bank)", f"{monatliche_rate:,.0f} €")
            st.metric("Ø Monatliche Gesamtkosten", f"{avg_monatliche_gesamtkosten:,.0f} €")
        with col_m4:
            st.metric("Ø Monatlicher Eigenaufwand", f"{avg_eigenaufwand:,.0f} €")

        st.markdown("#### Steuer & Cashflow")
        col_m5, col_m6 = st.columns(2)
        with col_m5:
            st.metric("Gesamte Steuerersparnis", f"{total_tax_saved:,.0f} €")
        with col_m6:
            st.metric("Ø Cashflow", f"{avg_cashflow:,.0f} €")

        st.markdown("#### Kredit-Details")
        col_m7, col_m8 = st.columns(2)
        with col_m7:
            st.metric(f"Restschuld ({zinsbindung}J)", f"{restschuld_zinsbindung:,.0f} €")
        with col_m8:
            st.metric("Volltilgung nach", f"{jahr} Jahren")

    with col2:
        formeln = get_formeln("Neubau (Investitions-Immobilie)")
        tab_t, tab_g, tab_a, tab_f = st.tabs(["Tabelle", "Graph", "Analyse & Risiken", "📚 Formeln"])

        with tab_t:
            cols_all = df_display.columns.tolist()
            cols_default = ["Jahr", "Restschuld", "Mieteinnahmen", "Instandhaltung", "AfA", "Sonder-AfA (§7b)",
                            "Steuerersparnis", "Cashflow", "Vermögen"]
            cols_selected = st.multiselect("Spalten anzeigen:", cols_all, default=cols_default)
            df_filtered = df_display[cols_selected]
            format_dict = {col: "{:,.2f} €" for col in cols_selected if
                           col not in ["Jahr", "Grenzsteuersatz (%)", "AfA (Methode)"]}
            if "Jahr" in cols_selected: format_dict["Jahr"] = "{:.0f}"
            styler = df_filtered.style.format(format_dict).hide(axis="index")
            st.dataframe(styler, use_container_width=True, height=700, hide_index=True)

        with tab_g:
            render_graph_tab(df_display, default_cols=["Restschuld", "Immobilienwert", "Vermögen",
                                                       "Netto-Erlös bei Verkauf (Exit)"], key_suffix="neubau_v2")

        with tab_a:
            st.markdown("## 🧐 Experteneinschätzung & Risiko-Check (2026)")

            with st.expander("1. Neubau-Booster & Abschreibung (AfA)", expanded=True):
                afa_jahr1 = afa_schedule[0]['afa'] + afa_schedule[0]['sonder_afa']
                st.write(f"Im ersten Jahr: **{afa_jahr1:,.0f} €** steuerlich absetzbar ({afa_methode}).")
                if afa_methode == "Degressiv + §7b Sonder-AfA":
                    st.success("🚀 **Steuer-Turbo:** Nutze die Liquiditätsspitze für Sondertilgung!")
                elif afa_methode == "Linear (3%)":
                    st.info("ℹ️ **Solide Basis:** 3% AfA — planbar und stetig.")

            with st.expander("2. Cashflow & Instandhaltung", expanded=True):
                st.metric("Ø Cashflow (nach Steuer)", f"{avg_cashflow:,.0f} €")
                if avg_cashflow < 0:
                    st.error("🔴 **Zuzahlungs-Geschäft:** Trotz Steuervorteilen zahlst du drauf.")
                if instandhaltung_pa < (baukosten * 0.005):
                    st.success("✅ **Neubau-Vorteil:** Geringe Reparaturen in den ersten Jahren gerechtfertigt.")

            with st.expander("3. Finanzierung & Zins-Hammer", expanded=True):
                ek_quote = (startkapital_gesamt / gesamtinvestition) * 100
                st.metric("Eigenkapitalquote", f"{ek_quote:.1f} %")
                if restschuld_zinsbindung > 0:
                    st.warning(f"Anschlussfinanzierung in {zinsbindung} Jahren: **{restschuld_zinsbindung:,.0f} €**")
                    if restschuld_zinsbindung > 300_000:
                        st.error("🔴 **Hohes Restschuld-Risiko** — Sondertilgungen nutzen!")
                else:
                    st.success("✅ Schuldenfrei am Ende der Zinsbindung.")

        with tab_f:
            render_formeln_tab(formeln, key_suffix="neubau_v2")
