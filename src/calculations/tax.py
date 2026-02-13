import math


def berechne_einkommensteuer(zve):
    """Vereinfachte Formel EStG 2024/2025 (Progressionszonen).
    Grundtarif für Einzelpersonen, Splitting = 2 * Grundtarif(zve/2).
    """
    zve = max(0, zve)

    # Zonen (ca. Werte 2024)
    grundfreibetrag = 11604
    zone1_limit = 17005
    zone2_limit = 66760
    zone3_limit = 277825

    st = 0.0
    if zve <= grundfreibetrag:
        st = 0.0
    elif zve <= zone1_limit:
        y = (zve - grundfreibetrag) / 10000
        st = (922.98 * y + 1400) * y
    elif zve <= zone2_limit:
        z = (zve - zone1_limit) / 10000
        st = (181.19 * z + 2397) * z + 1082.7
    elif zve <= zone3_limit:
        st = 0.42 * zve - 10633.76
    else:
        st = 0.45 * zve - 18968.51

    return math.floor(st)


def get_steuerlast_zusammen(einkommen_a, einkommen_b):
    """Zusammenveranlagung: Summe bilden, halbieren, Grundtarif, verdoppeln."""
    zve_gesamt = einkommen_a + einkommen_b
    steuer = 2 * berechne_einkommensteuer(zve_gesamt / 2)
    return steuer
