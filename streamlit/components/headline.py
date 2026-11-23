import streamlit as st

from components.badge import index_badge


def show_headline(summary):
    st.subheader("Summary for " + str(summary["date"].iloc[0]))

    columns = st.columns(4)
    for col, (_, row) in zip(columns, summary.iterrows()):
        with col.container(border=True):
            st.metric(row["pollutant"], f"{row['avg_ugm3']} µg/m³")
            st.write(f"Worse than **{row['today_percentile']}%** of days this year")
            st.markdown(index_badge(row["daqi_max"]), unsafe_allow_html=True)