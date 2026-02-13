"""Formula database for all scenarios."""

bs = chr(92)  # backslash for LaTeX

_immobilien_formeln = [
    {
        "Name": "AfA (Absetzung für Abnutzung)",
        "Kategorie": "Immobilie",
        "Beschreibung": "Jährlicher steuerlicher Abschreibungsbetrag auf das Gebäude.",
        "Formel": f"AfA = (Kaufpreis {bs}times (1 - {bs}frac{{Grundstücksanteil}}{{100}})) {bs}times 0.02"
    },
    {
        "Name": "Brutto-Mietrendite",
        "Kategorie": "Immobilie",
        "Beschreibung": "Verhältnis der Jahresmiete zum Kaufpreis.",
        "Formel": f"Rendite = {bs}frac{{Monatsmiete {bs}times 12}}{{Kaufpreis}} {bs}times 100"
    },
    {
        "Name": "Cashflow (nach Steuer)",
        "Kategorie": "Immobilie",
        "Beschreibung": "Geldfluss nach allen Einnahmen und Ausgaben.",
        "Formel": "CF = Miete - (Zins + Tilgung) - Instandhaltung - Mietausfall + Steuerersparnis"
    },
    {
        "Name": "Eigenkapitalquote",
        "Kategorie": "Immobilie",
        "Beschreibung": "Anteil des Eigenkapitals.",
        "Formel": f"EK_{{Quote}} = {bs}frac{{Eigenkapital}}{{Kaufpreis}} {bs}times 100"
    },
    {
        "Name": "Kaufnebenkosten",
        "Kategorie": "Immobilie",
        "Beschreibung": "Zusatzkosten beim Kauf.",
        "Formel": f"Kosten = Kaufpreis {bs}times {bs}frac{{Notar{bs}% + Grunderwerbsteuer{bs}%}}{{100}}"
    },
    {
        "Name": "Kaufpreisfaktor",
        "Kategorie": "Immobilie",
        "Beschreibung": "Jahresmieten bis Kaufpreis bezahlt.",
        "Formel": f"Faktor = {bs}frac{{Kaufpreis}}{{Monatsmiete {bs}times 12}}"
    },
    {
        "Name": "Kreditbetrag",
        "Kategorie": "Immobilie",
        "Beschreibung": "Finanzierungsbedarf.",
        "Formel": "Kredit = (Kaufpreis + Nebenkosten) - Eigenkapital"
    },
    {
        "Name": "Monatliche Rate",
        "Kategorie": "Immobilie",
        "Beschreibung": "Annuität an die Bank.",
        "Formel": f"Rate = Kreditbetrag {bs}times {bs}frac{{Zins{bs}% + Tilgung{bs}%}}{{100}} {bs}times {bs}frac{{1}}{{12}}"
    },
    {
        "Name": "Steuerersparnis",
        "Kategorie": "Immobilie",
        "Beschreibung": "Differenz Steuerlast mit vs. ohne Immobilie.",
        "Formel": f"{bs}Delta Steuer = Steuer_{{ohne}} - Steuer_{{mit}}"
    },
    {
        "Name": "Äquivalente ETF-Sparrate",
        "Kategorie": "Vergleich",
        "Beschreibung": "Monatliche Sparrate, die nötig ist, um mit einem ETF das gleiche Endvermögen zu erreichen wie mit der Immobilie. Hierbei wird angenommen, dass das Startkapital (Eigenkapital) bereits zu Beginn angelegt wird.",
        "Formel": f"Sparrate = {bs}frac{{Endvermoegen - Startkapital {bs}cdot (1+i)^n}}{{ {bs}frac{{(1+i)^n - 1}}{{i}} }} {bs}quad (i = {bs}frac{{Rendite_{{p.a.}}}}{{12 {bs}cdot 100}}, n = Monate)"
    },
    {
        "Name": "Zugewinn (Scheidung)",
        "Kategorie": "Risiko",
        "Beschreibung": "Wertzuwachs während der Ehe (vereinfacht).",
        "Formel": "Zugewinn = (Wert_{aktuell} - Schulden_{aktuell}) - (Wert_{Start} - Schulden_{Start})"
    },
]

_neubau_formeln = [
    {
        "Name": "AfA Linear (§7 Abs. 4)",
        "Kategorie": "Neubau",
        "Beschreibung": "Lineare Abschreibung: 3% der Baukosten pro Jahr für 33⅓ Jahre. Gilt für Gebäude mit Fertigstellung nach 31.12.2022.",
        "Formel": f"AfA_{{linear}} = Baukosten {bs}times 0.03"
    },
    {
        "Name": "AfA Degressiv (§7 Abs. 5a)",
        "Kategorie": "Neubau",
        "Beschreibung": "Degressive Abschreibung: 5% des verbleibenden Buchwerts pro Jahr (declining balance). Gilt für Bauantrag/Kaufvertrag Okt 2023 – Sep 2029.",
        "Formel": f"AfA_{{degressiv}}(t) = Buchwert(t-1) {bs}times 0.05"
    },
    {
        "Name": "Wechsel Degressiv → Linear",
        "Kategorie": "Neubau",
        "Beschreibung": "Einmaliger, unwiderruflicher Wechsel zur linearen Methode. Optimal wenn linearer Betrag > degressiver Betrag.",
        "Formel": f"AfA_{{linear,neu}} = {bs}frac{{Buchwert(t)}}{{Restnutzungsdauer}}"
    },
    {
        "Name": "§7b Sonder-AfA",
        "Kategorie": "Neubau",
        "Beschreibung": "Zusätzliche Abschreibung von 5% der Baukosten für die ersten 4 Jahre. Voraussetzung: QNG-Zertifizierung, max. €5.200/m² Baukosten.",
        "Formel": f"Sonder_{{AfA}} = Baukosten {bs}times 0.05 {bs}quad (Jahr 1{bs}text{{-}}4)"
    },
    {
        "Name": "Buchwert Gebäude",
        "Kategorie": "Neubau",
        "Beschreibung": "Verbleibender steuerlicher Wert des Gebäudes nach kumulierter Abschreibung.",
        "Formel": f"Buchwert(t) = Baukosten - {bs}sum_{{i=1}}^{{t}} AfA(i)"
    },
    {
        "Name": "Gesamtinvestition Neubau",
        "Kategorie": "Neubau",
        "Beschreibung": "Summe aller Kosten beim Neubau.",
        "Formel": "Invest = Grundstückspreis + Baukosten + Baunebenkosten + Kaufnebenkosten"
    },
    {
        "Name": "Baunebenkosten",
        "Kategorie": "Neubau",
        "Beschreibung": "Zusatzkosten beim Bauen (Architekt, Genehmigungen, Erschließung).",
        "Formel": f"BNK = Baukosten {bs}times {bs}frac{{BNK{bs}%}}{{100}}"
    },
    {
        "Name": "Brutto-Mietrendite (Neubau)",
        "Kategorie": "Neubau",
        "Beschreibung": "Verhältnis der Jahresmiete zur Gesamtinvestition.",
        "Formel": f"Rendite = {bs}frac{{Monatsmiete {bs}times 12}}{{Gesamtinvestition}} {bs}times 100"
    },
    {
        "Name": "Cashflow (nach Steuer)",
        "Kategorie": "Neubau",
        "Beschreibung": "Geldfluss nach allen Einnahmen und Ausgaben.",
        "Formel": "CF = Miete - (Zins + Tilgung) - Instandhaltung - Mietausfall + Steuerersparnis"
    },
    {
        "Name": "Kreditbetrag (Neubau)",
        "Kategorie": "Neubau",
        "Beschreibung": "Finanzierungsbedarf beim Neubau.",
        "Formel": "Kredit = Gesamtinvestition - Eigenkapital"
    },
    {
        "Name": "Steuerersparnis",
        "Kategorie": "Neubau",
        "Beschreibung": "Differenz Steuerlast mit vs. ohne Immobilie.",
        "Formel": f"{bs}Delta Steuer = Steuer_{{ohne}} - Steuer_{{mit}}"
    },
    {
        "Name": "Zugewinn (Scheidung)",
        "Kategorie": "Risiko",
        "Beschreibung": "Wertzuwachs während der Ehe (vereinfacht).",
        "Formel": "Zugewinn = (Wert_{aktuell} - Schulden_{aktuell}) - (Wert_{Start} - Schulden_{Start})"
    },
]

_etf_formeln = _immobilien_formeln  # ETF scenario currently shares the same formula DB


def get_formeln(scenario):
    """Return sorted formula list for the given scenario."""
    if scenario == "Neubau (Investitions-Immobilie)":
        formeln = list(_neubau_formeln)
    elif scenario == "ETF-Sparplan (Alternative)":
        formeln = list(_etf_formeln)
    else:
        formeln = list(_immobilien_formeln)
    return sorted(formeln, key=lambda x: x["Name"])
