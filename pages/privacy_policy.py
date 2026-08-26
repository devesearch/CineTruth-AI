import streamlit as st


st.markdown(
    """
    <div class="ct-page-head">
        <div class="ct-kicker">Legal</div>
        <h1>Privacy Policy</h1>
        <p>This page provides a starter privacy notice for the CineTruth AI interface. Update it with your final hosting, analytics, storage and contact details before production use.</p>
    </div>

    <div class="ct-info-panel">
        <h3>Information you provide</h3>
        <p>CineTruth AI may process text, URLs or media that you submit for analysis. Only submit content that you are authorized to use.</p>

        <h3>How content is used</h3>
        <p>Submitted content is used to generate the requested analysis. Data handling may also depend on the infrastructure and third-party services you connect to the application.</p>

        <h3>Third-party platforms</h3>
        <p>When you provide a public social-media URL, the application may request publicly available content from that platform. Availability depends on the platform's own access rules.</p>

        <h3>Policy updates</h3>
        <p>This policy should be updated whenever the application's collection, storage, analytics or account features change.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
