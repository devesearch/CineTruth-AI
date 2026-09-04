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


def _download_with_ytdlp(url: str) -> str:
    """Resolve a webpage/video-post URL to a local media file using yt-dlp."""
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "This URL is a webpage, not a direct media file. Install yt-dlp with: pip install yt-dlp"
        ) from exc

    token = uuid.uuid4().hex[:10]
    output_template = os.path.join(Config.TEMP_DIR, f"url_{token}.%(ext)s")
    max_bytes = 100 * 1024 * 1024

    # Modern YouTube videos often expose video and audio as separate streams.
    # Let yt-dlp use its default best-video + best-audio selection instead of
    # forcing a progressive single-file format, which can cause
    # "Requested format is not available" for otherwise valid videos.
    ydl_opts = {
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "max_filesize": max_bytes,
        "socket_timeout": 40,
        "retries": 3,
        "fragment_retries": 3,
        # Prefer a broadly compatible final container when separate streams
        # need to be merged. yt-dlp still falls back to the best available
        # format when a merge is not required.
        "merge_output_format": "mp4",
    }

    # Use imageio-ffmpeg's bundled FFmpeg when available. This avoids requiring
    # a separate system-wide FFmpeg installation on Windows just for URL media.
    try:
        import imageio_ffmpeg

        ydl_opts["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        # If system FFmpeg is on PATH, yt-dlp will discover it automatically.
        pass

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise RuntimeError("No downloadable media was found on this URL.")
    except Exception as exc:
        raise RuntimeError(
            "The URL opened as a webpage, but its video could not be downloaded. "
            "The site may require login/cookies, block automated downloads, or the post may be private. "
            f"Details: {exc}"
        ) from exc

    allowed = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}
    candidates = []
    for name in os.listdir(Config.TEMP_DIR):
        if not name.startswith(f"url_{token}."):
            continue
        path = os.path.join(Config.TEMP_DIR, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in allowed:
            candidates.append(path)

    if not candidates:
        raise RuntimeError("The page was resolved, but no supported image/video file was produced.")

    # yt-dlp may leave more than one candidate; use the largest actual media file.
    target = max(candidates, key=os.path.getsize)
    if os.path.getsize(target) > max_bytes:
        try:
            os.remove(target)
        except OSError:
            pass
        raise ValueError("Resolved media is larger than the 100 MB test limit.")
    return target


def download_media_url(url: str) -> str:
    """Download either a direct media URL or a supported webpage/video-post URL."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Please enter a valid http:// or https:// media URL.")

    response = requests.get(
        url,
        timeout=40,
        stream=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        },
        allow_redirects=True,
    )
    response.raise_for_status()

    content_type = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
    parsed_path = urlparse(response.url).path
    ext = os.path.splitext(parsed_path)[1].lower()

    # A YouTube/Reddit/Instagram/X/etc. share link normally returns HTML.
    # Do not save that HTML as media; resolve the actual video instead.
    if content_type in {"text/html", "application/xhtml+xml"} or content_type.startswith("text/html"):
        response.close()
        return _download_with_ytdlp(url)

    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/webm": ".webm",
        "video/x-msvideo": ".avi",
        "video/x-matroska": ".mkv",
    }
    allowed = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}

    # Prefer the HTTP content type when the URL does not carry a useful extension.
    if ext not in allowed:
        ext = ext_map.get(content_type, "")

    if ext not in allowed:
        response.close()
        raise ValueError(
            f"Unsupported media type from URL: {content_type or 'unknown'}. "
            "Use a direct image/video URL or a supported public video-page URL."
        )

    target = os.path.join(Config.TEMP_DIR, f"url_{uuid.uuid4().hex[:10]}{ext}")
    total = 0
    max_bytes = 100 * 1024 * 1024
    try:
        with open(target, "wb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("Media URL is larger than the 100 MB test limit.")
                fh.write(chunk)
    except Exception:
        if os.path.exists(target):
            try:
                os.remove(target)
            except OSError:
                pass
        raise
    finally:
        response.close()

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
    st.caption(f"**Gemini pipeline:** `{Config.GEMINI_PIPELINE_MODE}`")
    st.caption(f"**SerpAPI:** {serp_status}")
    st.caption(f"**ImgBB:** {imgbb_status}")
    st.caption(f"**ClickHouse:** {clickhouse_status}")
    st.divider()
    st.info("ClickHouse is optional during local functional testing.")


tab1, tab2 = st.tabs(["🎬 Deepfake Media Detection", "👤 Identity Shield & Auto-Web Takedown"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    # Batch items use the same existing single-media Pipeline.execute() method.
    # This keeps all forensic logic unchanged while allowing multiple inputs.
    batch_media_items = []

    with col1:
        st.subheader("📁 Media Input Workspace")
        input_type = st.radio(
            "Choose Input Type:",
            ["Upload Files (Video/Image)", "Media URLs"],
            horizontal=True,
        )

        if input_type == "Upload Files (Video/Image)":
            uploaded_files = st.file_uploader(
                "Upload one or more media files (MP4, MOV, JPG, PNG)",
                type=["mp4", "mov", "webm", "avi", "mkv", "jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                key="forensic_batch_uploads",
            )

            if uploaded_files:
                st.caption(f"{len(uploaded_files)} file(s) selected")
                for idx, uploaded_file in enumerate(uploaded_files, start=1):
                    try:
                        local_path = save_uploaded_file(uploaded_file)
                        item = {
                            "source_label": uploaded_file.name,
                            "media_path": local_path,
                            "input_kind": "upload",
                        }
                        batch_media_items.append(item)

                        with st.expander(f"Preview #{idx}: {uploaded_file.name}", expanded=(idx == 1)):
                            if uploaded_file.type and uploaded_file.type.startswith("video"):
                                st.video(local_path)
                            else:
                                st.image(local_path, caption=uploaded_file.name, use_container_width=True)
                            st.caption(f"Size: {uploaded_file.size/(1024*1024):.2f} MB")
                    except Exception as exc:
                        st.error(f"Could not save `{uploaded_file.name}`: {exc}")

        else:
            urls_text = st.text_area(
                "Enter one media/video-page URL per line:",
                placeholder=(
                    "https://example.com/video.mp4\n"
                    "https://www.youtube.com/watch?v=...\n"
                    "https://example.com/image.jpg"
                ),
                height=140,
                key="forensic_urls_text",
            )

            parsed_urls = []
            seen_urls = set()
            for line in urls_text.splitlines():
                candidate = line.strip()
                if candidate and candidate not in seen_urls:
                    parsed_urls.append(candidate)
                    seen_urls.add(candidate)

            if parsed_urls:
                st.caption(f"{len(parsed_urls)} unique URL(s) entered")

            if st.button(
                "⬇️ Load All URL Media",
                use_container_width=True,
                disabled=not parsed_urls,
                key="load_batch_urls",
            ):
                loaded_items = []
                load_errors = []
                progress = st.progress(0, text="Resolving media URLs...")

                for idx, media_url in enumerate(parsed_urls, start=1):
                    try:
                        local_path = download_media_url(media_url)
                        loaded_items.append(
                            {
                                "source_label": media_url,
                                "media_path": local_path,
                                "input_kind": "url",
                            }
                        )
                    except Exception as exc:
                        load_errors.append({"source": media_url, "error": str(exc)})
                    finally:
                        progress.progress(idx / max(len(parsed_urls), 1), text=f"Resolving URL {idx}/{len(parsed_urls)}")

                progress.empty()
                st.session_state["url_media_items"] = loaded_items
                st.session_state["url_media_errors"] = load_errors

            stored_url_items = st.session_state.get("url_media_items", [])
            stored_url_errors = st.session_state.get("url_media_errors", [])

            for item in stored_url_items:
                path = item.get("media_path")
                if path and os.path.exists(path):
                    batch_media_items.append(item)

            if stored_url_items:
                st.success(f"Loaded {len(batch_media_items)} URL media item(s).")
                for idx, item in enumerate(batch_media_items, start=1):
                    path = item["media_path"]
                    ext = os.path.splitext(path)[1].lower()
                    with st.expander(f"URL Media #{idx}", expanded=(idx == 1)):
                        st.caption(item["source_label"])
                        if ext in {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}:
                            st.video(path)
                        else:
                            st.image(path, caption="Resolved URL Image", use_container_width=True)

            if stored_url_errors:
                with st.expander(f"⚠️ URL load errors ({len(stored_url_errors)})"):
                    for err in stored_url_errors:
                        st.error(f"{err['source']}\n\n{err['error']}")

        if batch_media_items:
            st.info(
                f"Ready to analyze **{len(batch_media_items)}** media item(s). "
                "Items are processed sequentially so one failed item does not stop the whole batch."
            )
            if Config.GEMINI_PIPELINE_MODE != "full":
                st.caption(
                    f"Efficient mode estimate: about {len(batch_media_items)} Gemini request(s) "
                    f"for this batch (approximately 1 per media item)."
                )

    with col2:
        st.subheader("📊 Manipulation Verdict & Multi-Agent Telemetry")

        if batch_media_items:
            button_label = (
                "🚀 Run Deepfake Scan Pipeline"
                if len(batch_media_items) == 1
                else f"🚀 Run Batch Deepfake Scan ({len(batch_media_items)} items)"
            )

            if st.button(button_label, type="primary", use_container_width=True, key="run_forensic_batch"):
                results = []
                errors = []
                progress = st.progress(0, text="Starting forensic batch...")

                for idx, item in enumerate(batch_media_items, start=1):
                    source_label = item["source_label"]
                    local_media_path = item["media_path"]
                    session_id = f"session_{uuid.uuid4().hex[:8]}"

                    try:
                        progress.progress(
                            (idx - 1) / max(len(batch_media_items), 1),
                            text=f"Analyzing {idx}/{len(batch_media_items)}: {source_label}",
                        )
                        result = pipeline.execute(
                            local_media_path,
                            source_label=source_label,
                            session_id=session_id,
                        )
                        result["batch_index"] = idx
                        results.append(result)
                    except Exception as exc:
                        errors.append(
                            {
                                "batch_index": idx,
                                "source": source_label,
                                "error": str(exc),
                            }
                        )
                    finally:
                        progress.progress(
                            idx / max(len(batch_media_items), 1),
                            text=f"Processed {idx}/{len(batch_media_items)}",
                        )

                progress.empty()
                st.session_state["last_forensic_results"] = results
                st.session_state["last_forensic_batch_errors"] = errors
                # Keep backward compatibility for any code that still expects one last result.
                if results:
                    st.session_state["last_forensic_result"] = results[-1]

                if results:
                    st.success(f"Completed {len(results)} of {len(batch_media_items)} media item(s).")
                if errors:
                    st.warning(f"{len(errors)} item(s) failed. Other items were still processed.")

        results = st.session_state.get("last_forensic_results", [])
        batch_errors = st.session_state.get("last_forensic_batch_errors", [])

        if results:
            st.markdown(f"### Batch Results ({len(results)})")

            for result_pos, result in enumerate(results, start=1):
                verdict = result["final_verdict"]
                agents = result["agents"]
                risk_score = verdict.get("overall_manipulation_risk")
                verdict_status = verdict.get("status", "COMPLETED")
                source = result.get("source", f"Media #{result_pos}")
                media_type = result.get("media_type", "media")

                if risk_score is None:
                    title_risk = "No score"
                else:
                    title_risk = f"{risk_score}% risk"

                with st.expander(
                    f"#{result.get('batch_index', result_pos)} · {media_type.title()} · {title_risk} · {source}",
                    expanded=(result_pos == 1),
                ):
                    if verdict_status == "QUOTA_EXCEEDED":
                        st.warning(
                            "Gemini quota is exhausted for this model/project. "
                            "No risk percentage is shown because the AI analysis did not run."
                        )
                    elif risk_score is None:
                        st.error(verdict.get("executive_summary", "No reliable forensic score could be generated."))
                    else:
                        card_class = "risk-card-high"
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

                    st.caption(
                        f"Source: {source} · Pipeline mode: {result.get('pipeline_mode', 'unknown')} · "
                        f"Gemini requests: {verdict.get('gemini_requests_used', 'N/A')}"
                    )

                    st.markdown("#### Detailed Findings")
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

                    report_path = os.path.join(Config.TEMP_DIR, f"report_{result['session_id']}.pdf")
                    generate_report(result, report_path)
                    with open(report_path, "rb") as fh:
                        st.download_button(
                            "📥 Download Forensic Report (PDF)",
                            data=fh.read(),
                            file_name=f"CineTruth_Forensic_{result['session_id']}.pdf",
                            mime="application/pdf",
                            key=f"report_{result['session_id']}",
                        )

        if batch_errors:
            with st.expander(f"❌ Batch analysis errors ({len(batch_errors)})"):
                for err in batch_errors:
                    st.error(f"#{err['batch_index']} — {err['source']}\n\n{err['error']}")

        if not batch_media_items and not results:
            st.caption("Awaiting one or more media files or URLs.")


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
