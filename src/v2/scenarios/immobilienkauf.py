"""Scenario: Immobilienkauf (innerhalb Familie) — V2.

Adapted from v1: accepts optional wizard_defaults dict to override
default field values from wizard inputs.
"""

import streamlit as st
import pandas as pd

from calculations.tax import berechne_einkommensteuer, get_steuerlast_zusammen
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
    """Get a wizard default value or fall back to the given default."""
    val = wizard_defaults[key] if wizard_defaults and key in wizard_defaults else fallback
    if isinstance(fallback, float):
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return val


def render(inflationsrate: float, wizard_defaults: dict = None):
    """Renders the complete Immobilienkauf scenario with optional wizard pre-fills."""

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

    # --- 1. Startkapital (Eigenkapital) ---
    with st.sidebar.expander("1. Startkapital (Eigenkapital)", expanded=True):
        st.caption("Wie viel Geld ist bereits vorhanden?")

        eigentums_modus = persistent_radio(
            "Eigentumsverhältnisse",
            ["Alleineigentum (Eine Person)", "Gemeinschaftseigentum (nach EK-Anteil)"],
            key="immo_eigentum_modus",
        )

        if eigentums_modus == "Alleineigentum (Eine Person)":
            eigentuemer = persistent_selectbox(
                "Wer ist der Eigentümer (Grundbuch)?",
                ["Person A (meist Hauptverdiener)", "Person B"],
                key="immo_eigentuemer",
            )
            st.caption("Das Eigenkapital wird dem Eigentümer zugerechnet.")
            eigenkapital_a = persistent_number_input(
                "Eigenkapital Käufer (€)",
                value=_d(wizard_defaults, "v2_ek_a", 100_000.0),
                step=5_000.0, key="shared_ek_a",
                help="Geld, das du auf dem Konto hast und für den Kauf verwendest.",
            )
            geschenk_a = persistent_number_input(
                "Schenkung an Käufer (€)",
                value=_d(wizard_defaults, "v2_geschenk_a", 440_000.0),
                step=5_000.0, key="shared_geschenk_a",
                help="Falls dir die Verkäufer einen Teil des Kaufpreises schenken.",
            )
            startkapital_gesamt = eigenkapital_a + geschenk_a

            vertrag_ausschluss_zugewinn = persistent_checkbox(
                "Ehevertrag: Immobilie aus Zugewinn ausgeschlossen?",
                value=_d(wizard_defaults, "v2_ehevertrag", False),
                key="immo_vertrag_zugewinn",
                help="Gütertrennung für diesen Gegenstand.",
            )
        else:
            st.caption("Beide Partner bringen Kapital ein.")
            col_ek1, col_ek2 = st.columns(2)
            with col_ek1:
                eigenkapital_a = persistent_number_input(
                    "Eigenkapital Person A (€)",
                    value=_d(wizard_defaults, "v2_ek_a", 50_000.0),
                    step=5_000.0, key="shared_ek_a",
                )
                geschenk_a = persistent_number_input(
                    "Schenkung an A (€)",
                    value=_d(wizard_defaults, "v2_geschenk_a", 220_000.0),
                    step=5_000.0, key="shared_geschenk_a",
                )
            with col_ek2:
                eigenkapital_b = persistent_number_input(
                    "Eigenkapital Person B (€)",
                    value=_d(wizard_defaults, "v2_ek_b", 50_000.0),
                    step=5_000.0, key="shared_ek_b",
                )
                geschenk_b = persistent_number_input(
                    "Schenkung an B (€)",
                    value=_d(wizard_defaults, "v2_geschenk_b", 220_000.0),
                    step=5_000.0, key="shared_geschenk_b",
                )
            startkapital_gesamt = eigenkapital_a + geschenk_a + eigenkapital_b + geschenk_b

    # --- 2. Objekt (Kaufpreis) ---
    with st.sidebar.expander("2. Objekt (Kaufpreis)", expanded=True):
        st.caption("Was kostet die Immobilie?")
        kaufpreis = persistent_number_input(
            "Kaufpreis der Immobilie (€)",
            min_value=50_000.0, max_value=5_000_000.0,
            value=_d(wizard_defaults, "v2_kaufpreis", 1_150_000.0),
            step=10_000.0, key="immo_kaufpreis",
        )

        st.markdown("##### Kaufnebenkosten")
        col_nk1, col_nk2 = st.columns(2)
        with col_nk1:
            notar_grundbuch_prozent = persistent_number_input(
                "Notar & Grundbuch (%)", value=2.0, step=0.1, key="immo_notar",
                help="Kosten für Beurkundung und Grundbucheintrag. Faustformel: 1.5% - 2.0% des Kaufpreises."
            )
        with col_nk2:
            grunderwerbsteuer_prozent = persistent_number_input(
                "Grunderwerbsteuer (%)", value=0.0, step=0.5, key="immo_grunderwerb",
                help="Steuer beim Immobilienkauf (je nach Bundesland 3.5% - 6.5%). WICHTIG: Bei Verkauf an Kinder/Ehepartner meist 0%!"
            )
        anteil_grundstueck = persistent_slider(
            "Anteil des Grundstückswerts (%)", 10, 80, 40, key="immo_grundstuecksanteil",
            help="Wichtig für die Steuer: Nur das Gebäude nutzt sich ab und kann abgeschrieben werden (AfA), das Grundstück nicht. Ein typischer Wert ist 20-30%."
        )

    # --- 3. Kredit & Finanzierung ---
    with st.sidebar.expander("3. Kreditkonditionen & Finanzierung", expanded=True):
        st.caption("Finanzierungsparameter")
        zinssatz = persistent_slider("Zinssatz pro Jahr (%)", 0.5, 10.0, 3.2, 0.1, key="shared_zinssatz",
                                     help="Die 'Gebühr' der Bank für das Leihen des Geldes. Aktuell sind ca. 3.5% - 4.5% üblich.")
        tilgung = persistent_slider("Anfängliche Tilgung (%)", 1.0, 10.0, 2.0, 0.1, key="immo_tilgung",
                                    help="Der Teil deiner Rate, der den Schuldenberg tatsächlich verkleinert. Empfohlen sind mind. 2%.")
        zinsbindung = persistent_slider("Zinsbindung (Jahre)", 5, 30, 15, key="immo_zinsbindung",
                                        help="So lange garantiert dir die Bank den Zinssatz. Danach wird neu verhandelt (Risiko steigender Zinsen!).")

    # --- 4. Laufende Kosten & Einnahmen ---
    with st.sidebar.expander("4. Laufende Kosten & Einnahmen", expanded=False):
        st.caption("Was kommt rein, was geht raus?")
        mieteinnahmen_pm = persistent_number_input(
            "Monatliche Kaltmiete (€)",
            value=_d(wizard_defaults, "v2_kaltmiete", 2_116.0),
            step=50.0, key="immo_miete", help="Die Miete, die du bekommst (ohne Nebenkosten)."
        )
        mietsteigerung_pa = persistent_slider("Jährliche Mietsteigerung (%)", 0.0, 5.0, 3.0, 0.1,
                                              key="immo_mietsteigerung",
                                              help="Um wie viel Prozent erhöhst du die Miete jährlich? (Inflationsausgleich)")
        instandhaltung_pa = persistent_number_input("Rücklage Instandhaltung/Jahr (€)", value=4_000.0, step=100.0,
                                                    key="immo_instandhaltung",
                                                    help="Geld, das du für Reparaturen (Dach, Heizung, etc.) zurücklegen solltest. Faustformel: 10-15€ pro m² Wohnfläche im Jahr.")
        mietausfall_pa = persistent_slider("Risiko Mietausfall (%)", 0.0, 10.0, 2.0, 0.5, key="immo_mietausfall",
                                           help="Kalkuliere ein, dass die Wohnung mal leer steht oder Mieter nicht zahlen. 2% entspricht ca. 1 Woche Leerstand pro Jahr.")
        kostensteigerung_pa = persistent_slider("Kostensteigerung pro Jahr (%)", 0.0, 5.0, 2.0, 0.1,
                                                key="immo_kostensteigerung",
                                                help="Handwerker und Material werden teurer. Wie stark steigen deine Instandhaltungskosten?")
        wertsteigerung_pa = persistent_slider("Wertsteigerung Immobilie (%)", 0.0, 10.0, 2.0, 0.1,
                                              key="shared_wertsteigerung",
                                              help="Gewinnt das Haus an Wert? Historisch oft 1-3%, aber keine Garantie!")

    # --- 5. Einkommen & Steuer ---
    with st.sidebar.expander("5. Einkommen & Steuer (2026)", expanded=False):
        st.caption("Einkommen für Zusammenveranlagung (Ehegattensplitting)")
        std_einkommen_mann = persistent_number_input(
            "Brutto-Einkommen Person A (Standard) €",
            value=_d(wizard_defaults, "v2_einkommen_a", 71_000),
            step=1_000, key="shared_ek_mann", help="Zu versteuerndes Jahreseinkommen Person A."
        )
        std_einkommen_frau = persistent_number_input(
            "Brutto-Einkommen Person B (Standard) €",
            value=_d(wizard_defaults, "v2_einkommen_b", 80_000),
            step=1_000, key="shared_ek_frau", help="Zu versteuerndes Jahreseinkommen Person B."
        )
        st.info(f"Summe Standard: {std_einkommen_mann + std_einkommen_frau:,.2f} €")

        st.markdown("### Sonderzeitraum")
        nutze_sonderzeitraum = persistent_checkbox(
            "Sonderzeitraum aktivieren", value=False, key="immo_sonderzeitraum",
            help="Z.B. für Elternzeit oder Teilzeit."
        )
        if nutze_sonderzeitraum:
            sonder_jahre = persistent_slider("Zeitraum (Jahre)", 1, 40, _d(wizard_defaults, "v2_sonder_jahre", (3, 7)),
                                             key="immo_sonder_jahre")
            sonder_einkommen_mann = persistent_number_input("Einkommen Person A (Sonder) €",
                                                            value=_d(wizard_defaults, "v2_sonder_mann", 71_000),
                                                            step=1_000, key="immo_sonder_mann")
            sonder_einkommen_frau = persistent_number_input("Einkommen Person B (Sonder) €",
                                                            value=_d(wizard_defaults, "v2_sonder_frau", 20_000),
                                                            step=1_000, key="immo_sonder_frau")
            st.info(f"Summe Sonder: {sonder_einkommen_mann + sonder_einkommen_frau:,.2f} €")
        else:
            sonder_jahre = (0, 0)
            sonder_einkommen_mann = 0
            sonder_einkommen_frau = 0

    # --- 6. Exit-Szenario ---
    with st.sidebar.expander("6. Exit-Szenario", expanded=False):
        st.caption("Parameter für den Fall eines vorzeitigen Verkaufs")
        marktzins_verkauf = persistent_slider("Marktzins bei Verkauf (%)", 0.0, 10.0, 1.5, 0.1,
                                              key="immo_exit_marktzins",
                                              help="Wird benötigt, um die Vorfälligkeitsentschädigung zu schätzen. Ist der Marktzins niedriger als dein Vertragszins, verlangt die Bank eine Entschädigung.")
        verkaufskosten_prozent = persistent_slider("Verkaufskosten (%)", 0.0, 10.0, 3.0, 0.5, key="immo_exit_kosten",
                                                   help="Kosten, die beim Verkauf vom Erlös abgehen.")

    # ===========================================================================
    # LOGIK
    # ===========================================================================
    nebenkosten_betrag = kaufpreis * ((notar_grundbuch_prozent + grunderwerbsteuer_prozent) / 100)
    gesamtinvestition = kaufpreis + nebenkosten_betrag
    kreditbetrag = gesamtinvestition - startkapital_gesamt

    if kreditbetrag <= 0:
        st.error(
            f"Das Eigenkapital ({startkapital_gesamt:,.2f} €) deckt Kaufpreis + Nebenkosten ({gesamtinvestition:,.2f} €). Kein Kredit notwendig.")
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
    anfangs_vermoegen_netto = startkapital_gesamt
    vermoegen_vorjahr = kaufpreis - kreditbetrag

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

    kumulierte_afa = 0.0
    jahr = 0
    max_laufzeit = 80

    while restschuld > 1.0 and jahr < max_laufzeit:
        jahr += 1

        if nutze_sonderzeitraum and sonder_jahre[0] <= jahr <= sonder_jahre[1]:
            ek_a = sonder_einkommen_mann
            ek_b = sonder_einkommen_frau
        else:
            ek_a = std_einkommen_mann
            ek_b = std_einkommen_frau

        zinsanteil_jahr = restschuld * (zinssatz / 100)
        tilgungsanteil_jahr = jaehrliche_rate - zinsanteil_jahr
        if tilgungsanteil_jahr > restschuld:
            tilgungsanteil_jahr = restschuld
            jaehrliche_rate_effektiv = zinsanteil_jahr + tilgungsanteil_jahr
        else:
            jaehrliche_rate_effektiv = jaehrliche_rate
        restschuld -= tilgungsanteil_jahr

        werbungskosten = zinsanteil_jahr + jaehrliche_afa + aktuelle_instandhaltung
        ergebnis_vv = aktuelle_jahresmiete - werbungskosten
        steuer_ohne = get_steuerlast_zusammen(ek_a, ek_b)
        ek_a_mit = ek_a + (ergebnis_vv * anteil_a_prozent)
        ek_b_mit = ek_b + (ergebnis_vv * anteil_b_prozent)
        steuer_mit = get_steuerlast_zusammen(ek_a_mit, ek_b_mit)
        steuerersparnis = steuer_ohne - steuer_mit
        grenzsteuersatz = (steuerersparnis / abs(ergebnis_vv)) if ergebnis_vv != 0 else 0.0

        mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
        cashflow_vor_steuer = aktuelle_jahresmiete - jaehrliche_rate_effektiv - aktuelle_instandhaltung - mietausfall_betrag
        cashflow_nach_steuer = cashflow_vor_steuer + steuerersparnis
        monatliche_gesamtkosten = (jaehrliche_rate_effektiv + aktuelle_instandhaltung + mietausfall_betrag) / 12
        monatlicher_eigenaufwand = monatliche_gesamtkosten - (aktuelle_jahresmiete / 12)

        aktueller_hauswert *= (1 + wertsteigerung_pa / 100)
        aktuelles_vermoegen_netto = aktueller_hauswert - restschuld

        zugewinn_gesamt = aktuelles_vermoegen_netto - anfangs_vermoegen_netto
        ausgleichszahlung_scheidung = 0.0
        if eigentums_modus == "Alleineigentum (Eine Person)":
            if not vertrag_ausschluss_zugewinn and zugewinn_gesamt > 0:
                ausgleichszahlung_scheidung = zugewinn_gesamt / 2

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
            "Scheidung: Ausgleichszahlung": ausgleichszahlung_scheidung,
        })

        vermoegen_vorjahr = aktuelles_vermoegen_netto
        aktuelle_jahresmiete *= (1 + mietsteigerung_pa / 100)
        aktuelle_instandhaltung *= (1 + kostensteigerung_pa / 100)
        kumulierte_afa += jaehrliche_afa

    df_projektion = pd.DataFrame(jahres_daten)

    # ===========================================================================
    # ANZEIGE
    # ===========================================================================
    col1, col2 = st.columns([1, 3])
    with col2:
        show_inflation = render_toggles()

    if show_inflation and inflationsrate > 0:
        df_display = apply_inflation(df_projektion, inflationsrate, exclude_cols=["Jahr", "Grenzsteuersatz (%)"])
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

            r_etf_pa = st.session_state.get("v2_etf_rendite") or st.session_state.get("etf_rendite", 7.0)
            r_monatlich = r_etf_pa / 100 / 12
            n_monate = len(df_projektion) * 12
            if n_monate > 0:
                fv_nom = df_projektion.iloc[-1]["Vermögen"]
                pv = startkapital_gesamt
                zinsfaktor = (1 + r_monatlich) ** n_monate
                if zinsfaktor > 1:
                    etf_rate = (fv_nom - pv * zinsfaktor) * r_monatlich / (zinsfaktor - 1)
                else:
                    etf_rate = 0
                if etf_rate > 0:
                    st.metric("Äquivalente ETF-Sparrate", f"{etf_rate:,.0f} €")
                else:
                    st.metric("Äquivalente ETF-Sparrate", "0 €")

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
        formeln = get_formeln("Immobilienkauf (innerhalb Familie)")
        tab_t, tab_g, tab_a, tab_f = st.tabs(["Tabelle", "Graph", "Analyse & Risiken", "📚 Formeln"])

        with tab_t:
            cols_all = df_display.columns.tolist()
            cols_default = ["Jahr", "Restschuld", "Mieteinnahmen", "Instandhaltung", "AfA", "Steuerersparnis",
                            "Cashflow", "Vermögen"]
            cols_selected = st.multiselect("Spalten anzeigen:", cols_all, default=cols_default)
            df_filtered = df_display[cols_selected]
            format_dict = {col: "{:,.2f} €" for col in cols_selected if col not in ["Jahr", "Grenzsteuersatz (%)"]}
            if "Jahr" in cols_selected: format_dict["Jahr"] = "{:.0f}"
            if "Grenzsteuersatz (%)" in cols_selected: format_dict["Grenzsteuersatz (%)"] = "{:.1f} %"
            styler = df_filtered.style.format(format_dict).hide(axis="index")
            st.dataframe(styler, use_container_width=True, height=700, hide_index=True)

        with tab_g:
            render_graph_tab(df_display,
                             default_cols=["Restschuld", "Hauswert", "Vermögen", "Netto-Erlös bei Verkauf (Exit)"],
                             key_suffix="immo_v2")

        with tab_a:
            st.markdown("## 🧐 Experteneinschätzung & Risiko-Check (2026)")
            if show_inflation:
                st.caption(f"⚠️ Hinweis: Alle Beträge sind inflationsbereinigt ({inflationsrate}% p.a.).")

            with st.expander("1. Vermögensaufbau & Opportunitätskosten", expanded=True):
                netto_mietrendite = (aktuelle_jahresmiete - aktuelle_instandhaltung) / gesamtinvestition * 100
                st.metric("Netto-Mietrendite (Start)", f"{netto_mietrendite:.2f} %")
                if netto_mietrendite < zinssatz:
                    st.warning(
                        f"⚠️ **Negativer Leverage-Effekt:** Netto-Mietrendite ({netto_mietrendite:.2f}%) < Kreditzins ({zinssatz}%).")
                    if wertsteigerung_pa < 2.0:
                        st.error(
                            "🔴 **Vorsicht:** Ohne signifikante Wertsteigerung (>2%) ist dieses Investment ein Verlustgeschäft.")
                else:
                    st.success(f"✅ **Positiver Leverage:** {netto_mietrendite:.2f}% > {zinssatz}%.")

            with st.expander("2. Cashflow-Falle & Instandhaltung", expanded=True):
                if avg_eigenaufwand > 0:
                    st.error(f"🔴 **Liquiditäts-Falle:** {avg_eigenaufwand:,.0f} €/Monat Zuzahlung erforderlich.")
                else:
                    st.success(f"🟢 **Cashflow-Positiv:** {abs(avg_eigenaufwand):,.0f} €/Monat Überschuss.")
                if instandhaltung_pa < (gebaeudewert * 0.01):
                    st.warning(f"⚠️ Instandhaltung {instandhaltung_pa:,.0f} €/J möglicherweise zu niedrig.")
                else:
                    st.success("✅ Realistische Instandhaltungsrücklage.")

            with st.expander("3. Klumpenrisiko & Exit-Schutz", expanded=True):
                if eigentums_modus == "Alleineigentum (Eine Person)" and not vertrag_ausschluss_zugewinn:
                    st.error("🔴 **Scheidungs-Risiko (Zugewinn):** Ohne Ehevertrag Wertzuwachs hälftig auszugleichen.")
                elif eigentums_modus == "Gemeinschaftseigentum (nach EK-Anteil)":
                    st.info(
                        "ℹ️ **Teilungsversteigerung:** Bei Streitigkeiten kann jeder Partner die Versteigerung beantragen.")
                if restschuld_zinsbindung > 0:
                    st.warning(
                        f"Anschlussfinanzierung in {zinsbindung} Jahren: {restschuld_zinsbindung:,.0f} € Restschuld.")
                else:
                    st.success("Kein Zinsrisiko: Darlehen ist innerhalb der Zinsbindung getilgt.")

        with tab_f:
            render_formeln_tab(formeln, key_suffix="immo_v2")
