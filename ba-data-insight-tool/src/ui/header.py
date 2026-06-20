"""Header rendering for BA Data Insight Tool."""
from __future__ import annotations

import streamlit as st


def render_header(app_title: str, app_subtitle: str) -> None:
    """Render the app title and subtitle banner.

    The step-by-step progress now lives in the sidebar wizard
    (src/ui/sidebar.py::render_wizard_nav), so this is just the banner.
    """
    st.title(app_title)
    st.caption(app_subtitle)
    st.divider()
