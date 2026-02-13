import streamlit as st

# --- Konfiguration der Seite ---
st.set_page_config(layout="wide", page_title="Immobilienrechner & ETF-Vergleich")

# --- Titel ---
st.title("📊 Vermögensrechner: Investitions-Immobilie vs. ETF Sparplan")

# --- Seitenleiste: Szenario-Auswahl ---
st.sidebar.header("Szenario wählen")
szenario = st.sidebar.radio(
    "Was möchtest du berechnen?",
    [
        "Immobilienkauf (innerhalb Familie)",
        "Neubau (Investitions-Immobilie)",
        "ETF-Sparplan (Alternative)",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.header("Eingabeparameter")

# --- Inflation (shared across all scenarios) ---
with st.sidebar.expander("Inflation", expanded=False):
    st.caption("Annahme für die Geldentwertung")
    inflationsrate = st.slider(
        "Inflation (%)", 0.0, 10.0, 2.0, 0.1,
        help="Um diesen Wert verringert sich die Kaufkraft des Geldes jährlich. "
             "Wenn du die 'Inflationsbereinigung' aktivierst, werden alle zukünftigen "
             "Werte auf heutige Kaufkraft umgerechnet.",
    )

# --- Scenario Dispatch ---
if szenario == "Immobilienkauf (innerhalb Familie)":
    from scenarios.immobilienkauf import render
    render(inflationsrate)
elif szenario == "Neubau (Investitions-Immobilie)":
    from scenarios.neubau import render
    render(inflationsrate)
else:
    from scenarios.etf_sparplan import render
    render(inflationsrate)
