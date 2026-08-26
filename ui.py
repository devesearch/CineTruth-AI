import html
import streamlit as st


NAV_ITEMS = [
    ("Home", "/"),
    ("Post Sentiment", "/post-sentiment"),
    ("Deep-Fake Analysis", "/deep-fake-analysis"),
    ("About Us", "/about-us"),
    ("Contact Us", "/contact-us"),
]

FOOTER_ITEMS = [
    ("Privacy Policy", "/privacy-policy"),
    ("Terms & Conditions", "/terms-and-conditions"),
]


def inject_global_styles():
    st.markdown(
        """
        <style>
        :root {
            --ct-bg: #06111f;
            --ct-panel: #0b1a2b;
            --ct-panel-2: #10243a;
            --ct-text: #f6f8fc;
            --ct-muted: #9fb0c7;
            --ct-accent: #ff4b55;
            --ct-accent-2: #ff7b55;
            --ct-border: rgba(255,255,255,.10);
        }

        /* Hide Streamlit's native top chrome so the CineTruth navbar is the true top bar. */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],
        #MainMenu {
            display: none !important;
            visibility: hidden !important;
        }

        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        .stApp {
            background:
                radial-gradient(circle at 15% 0%, rgba(88, 80, 236, .16), transparent 32rem),
                radial-gradient(circle at 92% 12%, rgba(255, 75, 85, .12), transparent 28rem),
                var(--ct-bg);
            color: var(--ct-text);
        }

        .block-container {
            padding-top: .45rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }

        h1, h2, h3, h4, p, label, .stMarkdown {
            color: var(--ct-text);
        }

        .ct-navbar {
            position: sticky;
            top: 0;
            z-index: 999;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: .82rem 1rem;
            margin: 0 0 2rem 0;
            border: 1px solid var(--ct-border);
            border-radius: 18px;
            background: rgba(8, 20, 35, .91);
            backdrop-filter: blur(18px);
            box-shadow: 0 18px 44px rgba(0,0,0,.22);
        }

        .ct-brand {
            display: inline-flex;
            align-items: center;
            gap: .65rem;
            color: #fff !important;
            text-decoration: none !important;
            font-size: 1.05rem;
            font-weight: 800;
            letter-spacing: -.02em;
            white-space: nowrap;
        }

        .ct-brand-mark {
            width: 34px;
            height: 34px;
            display: grid;
            place-items: center;
            border-radius: 11px;
            background: linear-gradient(135deg, var(--ct-accent), var(--ct-accent-2));
            box-shadow: 0 8px 24px rgba(255,75,85,.30);
        }

        .ct-nav-links {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: .25rem;
            flex-wrap: wrap;
        }

        .ct-nav-link {
            color: #cbd7e7 !important;
            text-decoration: none !important;
            font-size: .88rem;
            font-weight: 650;
            padding: .56rem .72rem;
            border-radius: 10px;
            transition: .2s ease;
            white-space: nowrap;
        }

        .ct-nav-link:hover,
        .ct-nav-link.active {
            color: #fff !important;
            background: rgba(255,255,255,.08);
        }

        .ct-nav-link.active {
            box-shadow: inset 0 0 0 1px rgba(255,255,255,.08);
        }

        .ct-soon-badge {
            display: inline-block;
            margin-left: .28rem;
            padding: .10rem .34rem;
            border-radius: 999px;
            font-size: .57rem;
            letter-spacing: .04em;
            color: #ffd5d8;
            background: rgba(255,75,85,.15);
            border: 1px solid rgba(255,75,85,.25);
            vertical-align: middle;
        }

        .ct-hero {
            padding: 4.6rem 1rem 4.2rem;
            text-align: center;
        }

        .ct-kicker {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .42rem .72rem;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,.10);
            background: rgba(255,255,255,.045);
            color: #c5d4e7;
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .04em;
            text-transform: uppercase;
        }

        .ct-hero h1 {
            max-width: 900px;
            margin: 1.25rem auto 1rem;
            font-size: clamp(2.5rem, 6vw, 5rem);
            line-height: .98;
            letter-spacing: -.055em;
        }

        .ct-gradient-text {
            background: linear-gradient(90deg, #ff6b72, #ffb46b);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .ct-hero p {
            max-width: 720px;
            margin: 0 auto;
            color: var(--ct-muted);
            font-size: 1.07rem;
            line-height: 1.75;
        }

        .ct-actions {
            display: flex;
            justify-content: center;
            gap: .8rem;
            flex-wrap: wrap;
            margin-top: 1.8rem;
        }

        .ct-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: .78rem 1.05rem;
            border-radius: 12px;
            text-decoration: none !important;
            font-weight: 750;
            border: 1px solid var(--ct-border);
            color: #fff !important;
        }

        .ct-btn.primary {
            background: linear-gradient(135deg, var(--ct-accent), var(--ct-accent-2));
            border: none;
            box-shadow: 0 12px 30px rgba(255,75,85,.24);
        }

        .ct-btn.secondary {
            background: rgba(255,255,255,.045);
        }

        .ct-section {
            padding: 1rem 0 3.4rem;
        }

        .ct-section-title {
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .ct-section-title h2 {
            font-size: clamp(1.75rem, 4vw, 2.65rem);
            margin-bottom: .45rem;
        }

        .ct-section-title p {
            color: var(--ct-muted);
            margin: 0 auto;
            max-width: 680px;
        }

        .ct-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 1rem;
        }

        .ct-card {
            min-height: 210px;
            padding: 1.35rem;
            border: 1px solid var(--ct-border);
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(16,36,58,.88), rgba(8,22,38,.88));
            box-shadow: 0 18px 50px rgba(0,0,0,.14);
        }

        .ct-card-icon {
            width: 43px;
            height: 43px;
            display: grid;
            place-items: center;
            border-radius: 12px;
            background: rgba(255,255,255,.07);
            font-size: 1.25rem;
            margin-bottom: .9rem;
        }

        .ct-card h3 {
            margin: .2rem 0 .5rem;
            font-size: 1.12rem;
        }

        .ct-card p {
            color: var(--ct-muted);
            line-height: 1.65;
            font-size: .92rem;
        }

        .ct-status {
            display: inline-flex;
            margin-top: .55rem;
            padding: .28rem .55rem;
            border-radius: 999px;
            font-size: .72rem;
            font-weight: 700;
        }

        .ct-status.live {
            color: #a7f3d0;
            background: rgba(16,185,129,.12);
            border: 1px solid rgba(16,185,129,.22);
        }

        .ct-status.soon {
            color: #ffd0d4;
            background: rgba(255,75,85,.10);
            border: 1px solid rgba(255,75,85,.18);
        }

        .ct-page-head {
            padding: 1.2rem 0 1.7rem;
        }

        .ct-page-head h1 {
            font-size: clamp(2rem, 5vw, 3.4rem);
            letter-spacing: -.04em;
            margin-bottom: .5rem;
        }

        .ct-page-head p {
            color: var(--ct-muted);
            max-width: 760px;
            line-height: 1.7;
        }

        .ct-coming {
            text-align: center;
            padding: 5rem 1.25rem;
            margin: 1rem 0 3rem;
            border: 1px solid var(--ct-border);
            border-radius: 22px;
            background: linear-gradient(145deg, rgba(16,36,58,.78), rgba(8,22,38,.82));
        }

        .ct-coming .icon {
            font-size: 3rem;
            margin-bottom: .8rem;
        }

        .ct-coming h2 {
            font-size: clamp(2rem, 5vw, 3.4rem);
            margin: 0 0 .65rem;
        }

        .ct-coming p {
            max-width: 620px;
            margin: 0 auto;
            color: var(--ct-muted);
            line-height: 1.7;
        }

        .ct-info-panel {
            padding: 1.4rem;
            border: 1px solid var(--ct-border);
            border-radius: 18px;
            background: rgba(12,29,48,.78);
            margin-bottom: 1rem;
        }

        .ct-info-panel p, .ct-info-panel li {
            color: #b6c5d8;
            line-height: 1.75;
        }

        .ct-footer {
            margin-top: 3rem;
            padding: 2.2rem 0 1rem;
            border-top: 1px solid var(--ct-border);
        }

        .ct-footer-inner {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1.5rem;
            flex-wrap: wrap;
        }

        .ct-footer-brand {
            max-width: 420px;
        }

        .ct-footer-brand strong {
            font-size: 1.08rem;
        }

        .ct-footer-brand p {
            color: var(--ct-muted);
            margin-top: .4rem;
            line-height: 1.6;
            font-size: .88rem;
        }

        .ct-footer-links {
            display: flex;
            gap: .9rem;
            flex-wrap: wrap;
        }

        .ct-footer-links a {
            color: #c1cede !important;
            text-decoration: none !important;
            font-size: .86rem;
        }

        .ct-footer-links a:hover {
            color: #fff !important;
        }

        .ct-copyright {
            margin-top: 1.3rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255,255,255,.06);
            color: #8294aa;
            font-size: .78rem;
        }

        @media (max-width: 900px) {
            .ct-navbar {
                align-items: flex-start;
                flex-direction: column;
            }
            .ct-nav-links {
                justify-content: flex-start;
                width: 100%;
            }
            .ct-grid {
                grid-template-columns: 1fr;
            }
            .ct-hero {
                padding-top: 3rem;
            }
        }

        @media (max-width: 560px) {
            .block-container {
                padding-left: .85rem;
                padding-right: .85rem;
            }
            .ct-navbar {
                top: 0;
                border-radius: 14px;
            }
            .ct-nav-links {
                overflow-x: auto;
                flex-wrap: nowrap;
                padding-bottom: .2rem;
            }
            .ct-nav-link {
                font-size: .80rem;
                padding: .48rem .56rem;
            }
            .ct-hero {
                padding-left: 0;
                padding-right: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_navbar(current_title: str):
    links = []
    for label, route in NAV_ITEMS:
        active = " active" if label == current_title else ""
        badge = '<span class="ct-soon-badge">SOON</span>' if label == "Deep-Fake Analysis" else ""
        links.append(
            f'<a class="ct-nav-link{active}" href="{html.escape(route)}" target="_self">'
            f'{html.escape(label)}{badge}</a>'
        )

    st.markdown(
        f"""
        <nav class="ct-navbar">
            <a class="ct-brand" href="/" target="_self">
                <span class="ct-brand-mark">🎬</span>
                <span>CineTruth AI</span>
            </a>
            <div class="ct-nav-links">
                {''.join(links)}
            </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    nav_links = ''.join(
        f'<a href="{route}" target="_self">{html.escape(label)}</a>'
        for label, route in NAV_ITEMS
    )
    legal_links = ''.join(
        f'<a href="{route}" target="_self">{html.escape(label)}</a>'
        for label, route in FOOTER_ITEMS
    )

    st.markdown(
        f"""
        <footer class="ct-footer">
            <div class="ct-footer-inner">
                <div class="ct-footer-brand">
                    <strong>🎬 CineTruth AI</strong>
                    <p>AI-assisted sentiment intelligence for understanding text, social posts and media context. Deep-Fake Analysis is currently under development.</p>
                </div>
                <div>
                    <div class="ct-footer-links">{nav_links}</div>
                    <div class="ct-footer-links" style="margin-top:.75rem">{legal_links}</div>
                </div>
            </div>
            <div class="ct-copyright">© 2026 CineTruth AI. All rights reserved.</div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
