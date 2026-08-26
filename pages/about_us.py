import streamlit as st


st.markdown(
    """
    <div class="ct-page-head">
        <div class="ct-kicker">About CineTruth AI</div>
        <h1>Building clearer signals for digital content.</h1>
        <p>CineTruth AI is designed to help users inspect the emotional tone and context of digital content through accessible AI-assisted analysis.</p>
    </div>

    <div class="ct-info-panel">
        <h3>Our focus</h3>
        <p>The current working product focuses on sentiment analysis for text, social-media content and supported media inputs. The application surfaces polarity and subjectivity signals in a simple visual format.</p>
    </div>

    <div class="ct-info-panel">
        <h3>What comes next</h3>
        <p>Deep-Fake Analysis is planned as a separate capability. It is intentionally shown as Coming Soon until a real detection model and validation pipeline are integrated.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
