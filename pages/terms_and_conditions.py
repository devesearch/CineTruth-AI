import streamlit as st


st.markdown(
    """
    <div class="ct-page-head">
        <div class="ct-kicker">Legal</div>
        <h1>Terms & Conditions</h1>
        <p>These starter terms describe the intended use of CineTruth AI and should be reviewed and finalized before a production launch.</p>
    </div>

    <div class="ct-info-panel">
        <h3>Use of the service</h3>
        <p>CineTruth AI provides automated analysis signals for informational purposes. Results should not be treated as guaranteed facts or professional advice.</p>

        <h3>User responsibility</h3>
        <p>You are responsible for the content, links and media you submit and for ensuring that your use complies with applicable laws and platform rules.</p>

        <h3>Analysis limitations</h3>
        <p>Automated sentiment analysis can be inaccurate, especially for sarcasm, slang, mixed-language content or limited context. Deep-Fake Analysis is not yet available and no detection result is currently provided.</p>

        <h3>Changes to the service</h3>
        <p>Features and terms may be updated as CineTruth AI evolves.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
