import streamlit as st


def show_data_issues(summary, report_info):
    st.subheader("Data issues")

    problems = 0

    for _, row in summary.iterrows():
        pollutant = row["pollutant"]
        reporting = int(row["sites_reporting"])
        missing = int(row["sites_missing"])
        if missing == 0:
            continue

        problems += 1
        names = report_info["missing_sites"].get(pollutant, [])
        which = f" ({', '.join(names)})" if names else ""
        st.warning(
            f"**{pollutant}:** {missing} of {reporting + missing} monitoring sites "
            f"did not have a full day of data{which}, so the average uses "
            f"{reporting} sites."
        )

    if summary["daqi_max"].isna().any():
        problems += 1
        st.info("The official air quality index was not published for some pollutants.")

    if problems == 0:
        st.success("All monitoring sites reported and the official index was published.")

    if report_info["made"]:
        st.caption(f"Data report made {report_info['made']}.")