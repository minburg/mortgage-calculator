"""Compute executive-overview summary statistics for all 3 scenarios."""

from calculations.tax import get_steuerlast_zusammen


def compute_all_scenarios(wizard_defaults: dict) -> dict:
    """
    Run lightweight versions of all 3 scenario calculations using wizard defaults
    and return a dict of summary metrics for the executive overview.
    """
    results = {}

    ek_a = float(wizard_defaults.get("v2_ek_a", 100_000))
    ek_b = float(wizard_defaults.get("v2_ek_b", 0))
    geschenk_a = float(wizard_defaults.get("v2_geschenk_a", 440_000))
    geschenk_b = float(wizard_defaults.get("v2_geschenk_b", 0))
    startkapital = ek_a + ek_b + geschenk_a + geschenk_b

    einkommen_a = float(wizard_defaults.get("v2_einkommen_a", 71_000))
    einkommen_b = float(wizard_defaults.get("v2_einkommen_b", 80_000))

    kaufpreis = float(wizard_defaults.get("v2_kaufpreis", 1_150_000))
    kaltmiete_pm = float(wizard_defaults.get("v2_kaltmiete", 2_116))
    etf_rendite = float(wizard_defaults.get("v2_etf_rendite", 7.0))

    # --- Shared defaults ---
    zinssatz = 3.2
    tilgung = 2.0
    zinsbindung = 15
    wertsteigerung_pa = 2.0
    instandhaltung_pa = 4_000.0
    mietausfall_pa = 2.0
    inflationsrate = 2.0

    # =========================================================================
    # SCENARIO 1: Immobilienkauf
    # =========================================================================
    results["immo"] = _calc_immo(
        startkapital=startkapital,
        kaufpreis=kaufpreis,
        kaltmiete_pm=kaltmiete_pm,
        einkommen_a=einkommen_a,
        einkommen_b=einkommen_b,
        zinssatz=zinssatz,
        tilgung=tilgung,
        zinsbindung=zinsbindung,
        wertsteigerung_pa=wertsteigerung_pa,
        instandhaltung_pa=instandhaltung_pa,
        mietausfall_pa=mietausfall_pa,
    )

    # =========================================================================
    # SCENARIO 2: Neubau
    # =========================================================================
    # For Neubau defaults, split kaufpreis into land/build
    grundstueck = 350_200.0
    baukosten = 679_800.0
    baunebenkosten = baukosten * 0.15
    kaufnebenkosten = grundstueck * 0.085
    gesamtkosten_nb = grundstueck + baukosten + baunebenkosten + kaufnebenkosten

    results["neubau"] = _calc_neubau(
        startkapital=startkapital,
        gesamtkosten=gesamtkosten_nb,
        baukosten=baukosten,
        kaltmiete_pm=kaltmiete_pm,
        einkommen_a=einkommen_a,
        einkommen_b=einkommen_b,
        zinssatz=zinssatz,
        tilgung=tilgung,
        zinsbindung=zinsbindung,
        wertsteigerung_pa=wertsteigerung_pa,
        instandhaltung_pa=instandhaltung_pa,
        mietausfall_pa=mietausfall_pa,
    )

    # =========================================================================
    # SCENARIO 3: ETF-Sparplan
    # =========================================================================
    # Use average eigenaufwand from immo as ETF Sparrate equivalent
    immo_eigenaufwand = results["immo"].get("monatlicher_eigenaufwand", 1_000.0)
    sparrate = max(0.0, float(immo_eigenaufwand))

    results["etf"] = _calc_etf(
        startkapital=startkapital,
        etf_rendite=etf_rendite,
        sparrate=sparrate,
        laufzeit=results["immo"].get("laufzeit_jahre", 30),
    )

    return results


def _calc_immo(
    startkapital, kaufpreis, kaltmiete_pm, einkommen_a, einkommen_b,
    zinssatz, tilgung, zinsbindung, wertsteigerung_pa, instandhaltung_pa, mietausfall_pa
):
    notar = 0.02
    grst = 0.0
    nebenkosten = kaufpreis * (notar + grst)
    gesamtinvestition = kaufpreis + nebenkosten
    kreditbetrag = gesamtinvestition - startkapital

    if kreditbetrag <= 0:
        return {"error": "Eigenkapital deckt Kaufpreis"}

    jaehrliche_rate = kreditbetrag * (zinssatz / 100 + tilgung / 100)
    monatliche_rate = jaehrliche_rate / 12
    gebaeudewert = kaufpreis * 0.60
    jaehrliche_afa = gebaeudewert * 0.02

    restschuld = kreditbetrag
    aktuelle_jahresmiete = kaltmiete_pm * 12
    aktuelle_instandhaltung = instandhaltung_pa
    aktueller_hauswert = kaufpreis
    jd = []
    steuerersparnis_total = 0.0
    eigenaufwand_sum = 0.0
    eigenaufwand_verlauf = []
    jahr = 0
    max_laufzeit = 80

    while restschuld > 1.0 and jahr < max_laufzeit:
        jahr += 1
        zinsanteil = restschuld * (zinssatz / 100)
        tilgungsanteil = jaehrliche_rate - zinsanteil
        if tilgungsanteil > restschuld:
            tilgungsanteil = restschuld
            jaehrliche_rate_eff = zinsanteil + tilgungsanteil
        else:
            jaehrliche_rate_eff = jaehrliche_rate
        restschuld -= tilgungsanteil

        werbungskosten = zinsanteil + jaehrliche_afa + aktuelle_instandhaltung
        ergebnis_vv = aktuelle_jahresmiete - werbungskosten
        steuer_ohne = get_steuerlast_zusammen(einkommen_a, einkommen_b)
        steuer_mit = get_steuerlast_zusammen(einkommen_a + ergebnis_vv, einkommen_b)
        steuerersparnis = steuer_ohne - steuer_mit
        steuerersparnis_total += steuerersparnis

        mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
        monatl_gesamtkosten = (jaehrliche_rate_eff + aktuelle_instandhaltung + mietausfall_betrag) / 12
        monatl_eigenaufwand = monatl_gesamtkosten - (aktuelle_jahresmiete / 12)
        eigenaufwand_sum += monatl_eigenaufwand
        eigenaufwand_verlauf.append(monatl_eigenaufwand)

        aktueller_hauswert *= (1 + wertsteigerung_pa / 100)
        aktuelle_jahresmiete *= 1.03
        aktuelle_instandhaltung *= 1.02

    endvermoegen = aktueller_hauswert - max(0, restschuld)
    avg_eigenaufwand = eigenaufwand_sum / max(1, jahr)

    return {
        "endvermoegen": endvermoegen,
        "monatliche_rate": monatliche_rate,
        "monatlicher_eigenaufwand": avg_eigenaufwand,
        "steuerersparnis_gesamt": steuerersparnis_total,
        "laufzeit_jahre": jahr,
        "zinsbindung": zinsbindung,
        "kreditbetrag": kreditbetrag,
        "eigenaufwand_verlauf": eigenaufwand_verlauf,
    }


def _calc_neubau(
    startkapital, gesamtkosten, baukosten, kaltmiete_pm, einkommen_a, einkommen_b,
    zinssatz, tilgung, zinsbindung, wertsteigerung_pa, instandhaltung_pa, mietausfall_pa
):
    kreditbetrag = gesamtkosten - startkapital
    if kreditbetrag <= 0:
        return {"error": "Eigenkapital deckt Gesamtkosten"}

    jaehrliche_rate = kreditbetrag * (zinssatz / 100 + tilgung / 100)
    monatliche_rate = jaehrliche_rate / 12
    jaehrliche_afa = baukosten * 0.03

    restschuld = kreditbetrag
    aktuelle_jahresmiete = kaltmiete_pm * 12
    aktuelle_instandhaltung = instandhaltung_pa
    aktueller_hauswert = gesamtkosten
    steuerersparnis_total = 0.0
    eigenaufwand_sum = 0.0
    eigenaufwand_verlauf = []
    jahr = 0
    max_laufzeit = 80

    while restschuld > 1.0 and jahr < max_laufzeit:
        jahr += 1
        zinsanteil = restschuld * (zinssatz / 100)
        tilgungsanteil = jaehrliche_rate - zinsanteil
        if tilgungsanteil > restschuld:
            tilgungsanteil = restschuld
            jaehrliche_rate_eff = zinsanteil + tilgungsanteil
        else:
            jaehrliche_rate_eff = jaehrliche_rate
        restschuld -= tilgungsanteil

        werbungskosten = zinsanteil + jaehrliche_afa + aktuelle_instandhaltung
        ergebnis_vv = aktuelle_jahresmiete - werbungskosten
        steuer_ohne = get_steuerlast_zusammen(einkommen_a, einkommen_b)
        steuer_mit = get_steuerlast_zusammen(einkommen_a + ergebnis_vv, einkommen_b)
        steuerersparnis = steuer_ohne - steuer_mit
        steuerersparnis_total += steuerersparnis

        mietausfall_betrag = aktuelle_jahresmiete * (mietausfall_pa / 100)
        monatl_gesamtkosten = (jaehrliche_rate_eff + aktuelle_instandhaltung + mietausfall_betrag) / 12
        monatl_eigenaufwand = monatl_gesamtkosten - (aktuelle_jahresmiete / 12)
        eigenaufwand_sum += monatl_eigenaufwand
        eigenaufwand_verlauf.append(monatl_eigenaufwand)

        aktueller_hauswert *= (1 + wertsteigerung_pa / 100)
        aktuelle_jahresmiete *= 1.03
        aktuelle_instandhaltung *= 1.02

    endvermoegen = aktueller_hauswert - max(0, restschuld)
    avg_eigenaufwand = eigenaufwand_sum / max(1, jahr)

    return {
        "endvermoegen": endvermoegen,
        "monatliche_rate": monatliche_rate,
        "monatlicher_eigenaufwand": avg_eigenaufwand,
        "steuerersparnis_gesamt": steuerersparnis_total,
        "laufzeit_jahre": jahr,
        "zinsbindung": zinsbindung,
        "kreditbetrag": kreditbetrag,
        "eigenaufwand_verlauf": eigenaufwand_verlauf,
    }


def _calc_etf(startkapital, etf_rendite, sparrate, laufzeit):
    kapital = float(startkapital)
    eingezahlt = float(startkapital)
    r_monatlich = etf_rendite / 100 / 12

    for _ in range(laufzeit):
        for _m in range(12):
            kapital = kapital * (1 + r_monatlich) + sparrate
            eingezahlt += sparrate

    gewinn = kapital - eingezahlt
    steuer = max(0.0, float(gewinn) * 0.185)
    netto = kapital - steuer

    return {
        "endvermoegen": netto,
        "monatliche_rate": sparrate,
        "monatlicher_eigenaufwand": sparrate,
        "steuerersparnis_gesamt": 0.0,  # ETF has no income tax savings
        "laufzeit_jahre": laufzeit,
        "total_gewinn": gewinn,
        "eigenaufwand_verlauf": [sparrate] * laufzeit,
    }
