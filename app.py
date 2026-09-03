import os
import uuid
from urllib.parse import urlparse

import requests
import streamlit as st

from config import Config
from database.clickhouse_db import db_manager
from main import Pipeline
from agents.takedown_agent import takedown_agent
from utils.report_generator import generate_report

st.set_page_config(
    page_title="CineTruth AI — Forensic Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as fh:
            st.markdown(f"<style>{fh.read()}</style>", unsafe_allow_html=True)


def save_uploaded_file(uploaded_file) -> str:
    safe_name = f"{uuid.uuid4().hex[:8]}_{os.path.basename(uploaded_file.name)}"
    path = os.path.join(Config.TEMP_DIR, safe_name)
    with open(path, "wb") as fh:
        fh.write(uploaded_file.getbuffer())
    return path


def download_media_url(url: str) -> str:
    response = requests.get(
        url,
        timeout=40,
        stream=True,
        headers={"User-Agent": "CineTruthAI/1.0"},
        allow_redirects=True,
    )
    response.raise_for_status()

    content_type = (response.headers.get("content-type") or "").split(";")[0].lower()
    parsed_path = urlparse(response.url).path
    ext = os.path.splitext(parsed_path)[1].lower()

    if not ext:
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
            "video/webm": ".webm",
        }
        ext = ext_map.get(content_type, ".bin")

    allowed = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm", ".avi", ".mkv"}
    if ext not in allowed:
        raise ValueError(f"Unsupported media type from URL: {content_type or ext}")

    target = os.path.join(Config.TEMP_DIR, f"url_{uuid.uuid4().hex[:10]}{ext}")
    total = 0
    max_bytes = 100 * 1024 * 1024
    with open(target, "wb") as fh:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                fh.close()
                os.remove(target)
                raise ValueError("Media URL is larger than the 100 MB test limit.")
            fh.write(chunk)
    return target


load_css("assets/style.css")
pipeline = Pipeline()

st.markdown(
    """
<div class="main-header">
    <div class="main-title">🛡️ CineTruth AI & Rights Protect</div>
    <div class="main-subtitle">Autonomous Deepfake Detection, Identity Protection & Legal Takedown Suite</div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ System Telemetry")
    gemini_status = "🟢 Configured" if Config.GEMINI_API_KEY else "🔴 Missing API Key"
    clickhouse_status = "🟢 Connected" if db_manager.client else ("🟡 Not configured" if not db_manager.configured else "🔴 Connection failed")
    serp_status = "🟢 Configured" if Config.SERP_API_KEY else "🔴 Missing"
    imgbb_status = "🟢 Configured" if Config.IMGBB_API_KEY else "🔴 Missing"

    st.caption(f"**Gemini:** {gemini_status}")
    st.caption(f"**SerpAPI:** {serp_status}")
    st.caption(f"**ImgBB:** {imgbb_status}")
    st.caption(f"**ClickHouse:** {clickhouse_status}")
    st.divider()
    st.info("ClickHouse is optional during local functional testing.")


tab1, tab2 = st.tabs(["🎬 Deepfake Media Detection", "👤 Identity Shield & Auto-Web Takedown"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    media_loaded = False
    local_media_path = None
    source_label = ""

    with col1:
        st.subheader("📁 Media Input Workspace")
        input_type = st.radio(
            "Choose Input Type:",
            ["Upload File (Video/Image)", "Direct Media URL"],
            horizontal=True,
        )

        if input_type == "Upload File (Video/Image)":
            uploaded_file = st.file_uploader(
                "Upload Media (MP4, MOV, JPG, PNG)",
                type=["mp4", "mov", "webm", "avi", "mkv", "jpg", "jpeg", "png", "webp"],
            )
            if uploaded_file:
                try:
                    local_media_path = save_uploaded_file(uploaded_file)
                    source_label = uploaded_file.name
                    media_loaded = True
                    if uploaded_file.type and uploaded_file.type.startswith("video"):
                        st.video(local_media_path)
                    else:
                        st.image(uploaded_file, caption="Uploaded Image Preview", use_container_width=True)
                    st.success(f"Media loaded: `{uploaded_file.name}` ({uploaded_file.size/(1024*1024):.2f} MB)")
                except Exception as exc:
                    st.error(f"Could not save uploaded media: {exc}")
        else:
            media_url = st.text_input(
                "Enter Direct Video or Image URL:",
                placeholder="https://example.com/suspect_media.mp4",
            )
            if media_url:
                source_label = media_url
                if st.button("⬇️ Load URL Media", use_container_width=True):
                    try:
                        with st.spinner("Downloading media URL for local analysis..."):
                            local_media_path = download_media_url(media_url)
                        st.session_state["url_media_path"] = local_media_path
                        st.session_state["url_media_label"] = media_url
                    except Exception as exc:
                        st.error(f"Could not load media URL: {exc}")

                local_media_path = st.session_state.get("url_media_path")
                if local_media_path and os.path.exists(local_media_path):
                    media_loaded = True
                    source_label = st.session_state.get("url_media_label", media_url)
                    ext = os.path.splitext(local_media_path)[1].lower()
                    if ext in {".mp4", ".mov", ".webm", ".avi", ".mkv"}:
                        st.video(local_media_path)
                    else:
                        st.image(local_media_path, caption="URL Image Preview", use_container_width=True)

    with col2:
        st.subheader("📊 Manipulation Verdict & Multi-Agent Telemetry")
        if media_loaded and local_media_path:
            if st.button("🚀 Run Deepfake Scan Pipeline", type="primary", use_container_width=True):
                session_id = f"session_{uuid.uuid4().hex[:8]}"
                try:
                    with st.status("🔍 Agents analyzing media...", expanded=True) as status:
                        st.write("🖼️ Metadata + representative frame extraction")
                        st.write("👤 Visual consistency analysis with Gemini")
                        st.write("🎵 Audio/AV consistency analysis with Gemini (video only)")
                        st.write("🌐 Context consistency analysis with Gemini")
                        st.write("🤖 Master synthesis")
                        result = pipeline.execute(
                            local_media_path,
                            source_label=source_label,
                            session_id=session_id,
                        )
                        st.session_state["last_forensic_result"] = result
                        status.update(label="✅ Forensic scan complete", state="complete", expanded=False)
                except Exception as exc:
                    st.error(f"Pipeline failed: {exc}")

        result = st.session_state.get("last_forensic_result")
        if result:
            verdict = result["final_verdict"]
            agents = result["agents"]
            risk_score = verdict.get("overall_manipulation_risk", 0)

            card_class = "risk-card-high" if risk_score >= 60 else "risk-card-high"
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div style="font-weight:600;color:#f43f5e;font-size:1.1rem;">MANIPULATION INDICATOR RISK</div>
                    <div class="risk-score-text">{risk_score}%</div>
                    <div style="color:#fda4af;font-size:0.9rem;">{verdict.get('executive_summary','')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### Detailed Findings")
            face_res = agents.get("face_agent", {})
            audio_res = agents.get("audio_agent", {})
            context_res = agents.get("context_agent", {})
            st.info(f"**Visual [{face_res.get('status','N/A')}]:** {face_res.get('details','N/A')}")
            st.info(f"**Audio/AV [{audio_res.get('status','N/A')}]:** {audio_res.get('details','N/A')}")
            st.info(f"**Context [{context_res.get('status','N/A')}]:** {context_res.get('details','N/A')}")

            with st.expander("Metadata & raw agent output"):
                st.json(
                    {
                        "session_id": result.get("session_id"),
                        "media_type": result.get("media_type"),
                        "frames_sampled": result.get("frames_sampled"),
                        "metadata": result.get("metadata"),
                        "agents": agents,
                    }
                )

            report_path = os.path.join(Config.TEMP_DIR, f"report_{result['session_id']}.txt")
            generate_report(result, report_path)
            with open(report_path, "rb") as fh:
                st.download_button(
                    "📥 Download Forensic Report",
                    data=fh.read(),
                    file_name=f"CineTruth_{result['session_id']}.txt",
                    mime="text/plain",
                )
        elif not media_loaded:
            st.caption("Awaiting media file or URL input.")


with tab2:
    st.subheader("🔎 Identity Matching & Reverse Web-Search Suite")
    st.caption("Upload a reference photo or use a public photo URL to run Google Lens via SerpAPI.")

    col_a, col_b = st.columns([1, 1], gap="large")
    with col_a:
        st.markdown("### Step 1: Reference Image")
        id_input_type = st.radio(
            "Reference Photo Source:",
            ["Upload Local Photo", "Photo URL"],
            horizontal=True,
        )
        ref_photo_loaded = False
        ref_payload = None

        if id_input_type == "Upload Local Photo":
            ref_image = st.file_uploader("Upload Reference Face Photo", type=["jpg", "png", "jpeg", "webp"], key="identity_file")
            if ref_image:
                st.image(ref_image, caption="Reference Identity Loaded", width=200)
                ref_photo_loaded = True
                ref_payload = ref_image
        else:
            ref_image_url = st.text_input("Enter Reference Photo URL:", placeholder="https://example.com/photo.jpg")
            if ref_image_url:
                st.image(ref_image_url, caption="Reference Image Loaded from Link", width=200)
                ref_photo_loaded = True
                ref_payload = ref_image_url

        if ref_photo_loaded and st.button("🔍 Run Autonomous Web Reverse-Search", type="primary", use_container_width=True):
            with st.spinner("Running Google Lens visual search through SerpAPI..."):
                matches = takedown_agent.search_unauthorized_matches(ref_payload)
                st.session_state["discovered_matches"] = matches
            if matches:
                st.success(f"Found {len(matches)} visual-search candidate(s).")
            else:
                st.warning("No visual-search candidates returned. Check SERP_API_KEY/IMGBB_API_KEY and the input image.")

    with col_b:
        st.markdown("### Step 2: Search Candidates & Review Notices")
        matches = st.session_state.get("discovered_matches", [])
        if matches:
            for idx, item in enumerate(matches):
                with st.expander(f"Candidate #{idx+1} — {item.get('platform','Web')}", expanded=(idx == 0)):
                    st.markdown(f"**URL:** `{item.get('target_url','')}`")
                    st.write(f"**Status:** {item.get('status','')}")
                    st.caption("Google Lens candidate ≠ verified biometric identity match. Human verification is required.")
                    if item.get("thumbnail"):
                        st.image(item["thumbnail"], width=120)

                    portal_type = st.selectbox(
                        f"Notice Type (Candidate #{idx+1}):",
                        ["Platform Content Review Request", "Copyright/DMCA Review Draft", "Cyber Crime Incident Draft"],
                        key=f"portal_{idx}",
                    )
                    if st.button(f"⚖️ Generate Draft for Candidate #{idx+1}", key=f"gen_btn_{idx}"):
                        nd = takedown_agent.generate_notice(
                            target_url=item["target_url"],
                            similarity_score=item.get("similarity_score"),
                            notice_type=portal_type,
                        )
                        st.session_state[f"notice_{idx}"] = nd

                    if f"notice_{idx}" in st.session_state:
                        nd = st.session_state[f"notice_{idx}"]
                        st.success(f"Draft generated. Request ID: `{nd['request_id']}`")
                        st.code(nd["notice_body"], language="text")
                        st.download_button(
                            "📥 Download Notice (.txt)",
                            data=nd["notice_body"],
                            file_name=f"Takedown_{nd['request_id']}.txt",
                            mime="text/plain",
                            key=f"dl_{idx}",
                        )
        else:
            st.info("Run a reverse search from the left panel to show live visual-search candidates here.")


st.divider()
with st.expander("🛠️ System / ClickHouse telemetry"):
    st.json(
        {
            "gemini_configured": bool(Config.GEMINI_API_KEY),
            "serpapi_configured": bool(Config.SERP_API_KEY),
            "imgbb_configured": bool(Config.IMGBB_API_KEY),
            "clickhouse_configured": db_manager.configured,
            "clickhouse_connected": bool(db_manager.client),
            "clickhouse_last_error": db_manager.last_error,
            "tables_when_enabled": ["detection_telemetry", "identity_takedowns"],
        }
    )
