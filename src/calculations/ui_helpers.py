"""Reusable UI helper functions shared across all scenarios."""

import streamlit as st
import altair as alt


def render_toggles():
    """Render the inflation / analysis toggle row. Returns (show_analysis, show_inflation)."""
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        show_analysis = st.toggle("Analyse & Risiken anzeigen", value=False)
    with t_col2:
        show_inflation = st.toggle(
            "Inflationsbereinigt anzeigen",
            value=False,
            help="Rechnet alle zukünftigen Werte auf die heutige Kaufkraft herunter.",
        )
    return show_analysis, show_inflation


def apply_inflation(df, inflationsrate, exclude_cols=None):
    """Return a copy of *df* with all numeric columns deflated by *inflationsrate*.

    Columns listed in *exclude_cols* are left untouched.
    """
    if exclude_cols is None:
        exclude_cols = ["Jahr"]
    df_display = df.copy()
    cols_to_adjust = [c for c in df_display.columns if c not in exclude_cols]
    for col in cols_to_adjust:
        df_display[col] = df_display.apply(
            lambda row, _c=col: row[_c] / ((1 + inflationsrate / 100) ** row["Jahr"]),
            axis=1,
        )
    return df_display


def render_graph_tab(df_display, default_cols, key_suffix=""):
    """Render an Altair line chart with multiselect column picker."""
    st.subheader("Visuelle Auswertung")
    available_cols = [
        c
        for c in df_display.columns
        if c not in ["Jahr", "Grenzsteuersatz (%)", "AfA (Methode)"]
    ]
    selected_cols = st.multiselect(
        "Wähle Werte für die Grafik:",
        available_cols,
        default=[d for d in default_cols if d in available_cols],
        key=f"graph_select_{key_suffix}" if key_suffix else None,
    )

    if selected_cols:
        chart_data = df_display.melt(
            "Jahr", value_vars=selected_cols, var_name="Kategorie", value_name="Wert"
        )
        chart = (
            alt.Chart(chart_data)
            .mark_line(point=True)
            .encode(
                x=alt.X("Jahr:O", title="Jahr"),
                y=alt.Y("Wert:Q", title="Betrag (€)", scale=alt.Scale(zero=False)),
                color="Kategorie:N",
                tooltip=[
                    alt.Tooltip("Jahr", title="Jahr"),
                    alt.Tooltip("Kategorie", title="Kategorie"),
                    alt.Tooltip("Wert", title="Wert", format=".2s"),
                ],
            )
            .properties(height=600)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Bitte wähle mindestens einen Wert aus.")


def render_formeln_tab(formeln, key_suffix=""):
    """Render the formula reference tab with search."""
    st.subheader("📚 Formel-Verzeichnis")
    st.caption("Hier finden Sie alle verwendeten Berechnungen transparent erklärt.")
    search_term = st.text_input(
        "🔍 Formel suchen...",
        "",
        key=f"formel_search_{key_suffix}" if key_suffix else None,
    ).lower()

    for item in formeln:
        if search_term in item["Name"].lower() or search_term in item["Beschreibung"].lower():
            with st.expander(f"{item['Name']} ({item['Kategorie']})"):
                st.markdown(f"**Beschreibung:** {item['Beschreibung']}")
                st.latex(item["Formel"])
