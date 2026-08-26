import streamlit as st


st.markdown(
    """
    <section class="ct-hero">
        <div class="ct-kicker">AI-powered content intelligence</div>
        <h1>Understand what content <span class="ct-gradient-text">really feels like.</span></h1>
        <p>
            CineTruth AI helps you analyze sentiment from text, social-media posts and uploaded media.
            Use the working Post Sentiment analyzer today, while Deep-Fake Analysis is being built for a future release.
        </p>
        <div class="ct-actions">
            <a class="ct-btn primary" href="/post-sentiment" target="_self">Analyze Sentiment →</a>
            <a class="ct-btn secondary" href="/deep-fake-analysis" target="_self">Deep-Fake Analysis</a>
        </div>
    </section>

    <section class="ct-section">
        <div class="ct-section-title">
            <h2>What you can do with CineTruth AI</h2>
            <p>A focused set of tools for analyzing digital content, with clear separation between features that are live and features still under development.</p>
        </div>
        <div class="ct-grid">
            <div class="ct-card">
                <div class="ct-card-icon">💬</div>
                <h3>Post Sentiment</h3>
                <p>Analyze text, public social-media URLs and supported media to estimate polarity and subjectivity.</p>
                <span class="ct-status live">Available now</span>
            </div>
            <div class="ct-card">
                <div class="ct-card-icon">🧬</div>
                <h3>Deep-Fake Analysis</h3>
                <p>A dedicated deep-fake detection experience is planned, but no detector is connected to the product yet.</p>
                <span class="ct-status soon">Coming soon</span>
            </div>
            <div class="ct-card">
                <div class="ct-card-icon">🛡️</div>
                <h3>Clear, responsible results</h3>
                <p>Results are presented as analysis signals, helping users inspect content without pretending an unfinished capability already exists.</p>
            </div>
        </div>
    </section>

    <section class="ct-section">
        <div class="ct-section-title">
            <h2>Simple workflow</h2>
            <p>Start with the content you want to understand and review the sentiment output in seconds.</p>
        </div>
        <div class="ct-grid">
            <div class="ct-card">
                <div class="ct-card-icon">1</div>
                <h3>Choose an input</h3>
                <p>Enter text, paste a supported social-media URL, or upload supported media from the Post Sentiment page.</p>
            </div>
            <div class="ct-card">
                <div class="ct-card-icon">2</div>
                <h3>Run analysis</h3>
                <p>The existing sentiment engine processes the content using the same working logic already present in the project.</p>
            </div>
            <div class="ct-card">
                <div class="ct-card-icon">3</div>
                <h3>Review the result</h3>
                <p>See sentiment classification, polarity, subjectivity and the existing visualization without changing the analyzer behavior.</p>
            </div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)
