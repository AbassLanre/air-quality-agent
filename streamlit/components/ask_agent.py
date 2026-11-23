import streamlit as st

from config import AGENT_URL


def show_ask_agent():
    with st.container(border=True):
        left, right = st.columns([3, 1], vertical_alignment="center")
        with left:
            st.markdown("**What does this mean, and what should we do?**")
            st.caption(
                "This page shows what happened. The agent reads the same figures, "
                "explains them and suggests an action."
            )
        with right:
            if AGENT_URL:
                st.link_button("Ask the agent", AGENT_URL, type="primary")
            else:
                st.button("Ask the agent", disabled=True, help="Agent link coming soon")