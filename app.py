import streamlit as st

from ui import inject_global_styles, render_footer, render_navbar


st.set_page_config(
    page_title="CineTruth AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


home = st.Page(
    "pages/home.py",
    title="Home",
    icon="🏠",
    default=True,
)

post_sentiment = st.Page(
    "pages/post_sentiment.py",
    title="Post Sentiment",
    icon="💬",
    url_path="post-sentiment",
)

deep_fake = st.Page(
    "pages/deep_fake_analysis.py",
    title="Deep-Fake Analysis",
    icon="🧬",
    url_path="deep-fake-analysis",
)

about = st.Page(
    "pages/about_us.py",
    title="About Us",
    icon="ℹ️",
    url_path="about-us",
)

contact = st.Page(
    "pages/contact_us.py",
    title="Contact Us",
    icon="✉️",
    url_path="contact-us",
)

privacy = st.Page(
    "pages/privacy_policy.py",
    title="Privacy Policy",
    icon="🔒",
    url_path="privacy-policy",
)

terms = st.Page(
    "pages/terms_and_conditions.py",
    title="Terms & Conditions",
    icon="📄",
    url_path="terms-and-conditions",
)


page = st.navigation(
    [
        home,
        post_sentiment,
        deep_fake,
        about,
        contact,
        privacy,
        terms,
    ],
    position="hidden",
)

inject_global_styles()
render_navbar(page.title)
page.run()
render_footer()
