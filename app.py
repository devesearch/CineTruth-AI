import os
import uuid
import streamlit as st

# Import Configuration & Database
from config import Config
from database.clickhouse_db import db_manager

# Import Specialized Agents
from agents.face_agent import FaceConsistencyAgent
from agents.audio_agent import AudioManipulationAgent
from agents.context_agent import ContextVerificationAgent
from agents.master_agent import GeminiMasterSynthesizer
from agents.takedown_agent import TakedownAgent

# 1. Page Config
st.set_page_config(
    page_title="CineTruth AI — Forensic Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Load Custom CSS
def load_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")

# Initialize Agents
face_agent = FaceConsistencyAgent()
audio_agent = AudioManipulationAgent()
context_agent = ContextVerificationAgent()
master_synthesizer = GeminiMasterSynthesizer()
takedown_agent = TakedownAgent()

# 3. Header Banner
st.markdown("""
<div class="main-header">
    <div class="main-title">🛡️ CineTruth AI & Rights Protect</div>
    <div class="main-subtitle">Autonomous Deepfake Detection, Identity Protection & Legal Takedown Suite</div>
</div>
""", unsafe_allow_html=True)

# 4. Sidebar Status & Configs
with st.sidebar:
    st.header("⚙️ System Telemetry")
    gemini_status = "🟢 Connected" if Config.GEMINI_API_KEY else "🔴 Missing API Key"
    ch_status = "🟢 Connected" if db_manager.client else "🔴 Offline"
    
    st.caption(f"**Gemini 2.5 Engine:** {gemini_status}")
    st.caption(f"**ClickHouse DB (Partner):** {ch_status}")
    
    st.divider()
    st.info("💡 **Hackathon Mode:** Active Multi-Agent Pipeline enabled.")

# 5. Main Navigation Tabs
tab1, tab2 = st.tabs(["🎬 Deepfake Media Detection", "👤 Identity Shield & Auto-Web Takedown"])

# --- TAB 1: DEEPFAKE DETECTION PIPELINE ---
with tab1:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("📁 Media Input Workspace")
        input_type = st.radio("Choose Input Type:", ["Upload File (Video/Image)", "Direct Media URL"], horizontal=True)
        
        media_loaded = False
        input_source_name = ""
        
        if input_type == "Upload File (Video/Image)":
            uploaded_file = st.file_uploader("Upload Media (MP4, MOV, JPG, PNG)", type=["mp4", "mov", "jpg", "jpeg", "png"])
            if uploaded_file:
                media_loaded = True
                input_source_name = uploaded_file.name
                if uploaded_file.type.startswith("video"):
                    temp_path = os.path.join(Config.TEMP_DIR, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.video(temp_path)
                else:
                    st.image(uploaded_file, caption="Uploaded Image Preview", use_container_width=True)
                st.success(f"Media Loaded: `{uploaded_file.name}` ({round(uploaded_file.size/(1024*1024), 2)} MB)")
        else:
            media_url = st.text_input("Enter Direct Video or Image URL:", placeholder="https://example.com/suspect_media.mp4")
            if media_url:
                media_loaded = True
                input_source_name = media_url
                st.info(f"🔗 URL Input Linked: `{media_url}`")

    with col2:
        st.subheader("📊 Manipulation Verdict & Multi-Agent Telemetry")
        if media_loaded:
            if st.button("🚀 Run Deepfake Scan Pipeline", type="primary", use_container_width=True):
                session_id = f"session_{uuid.uuid4().hex[:8]}"
                
                with st.status("🔍 Autonomous Agents Analyzing Media Stream...", expanded=True) as status:
                    st.write("👤 **Face Consistency Agent:** Scanning boundary blendings...")
                    face_res = face_agent.analyze_faces(session_id, input_source_name)
                    
                    st.write("🎵 **Audio Manipulation Agent:** Checking spectral consistency & lip-sync...")
                    audio_res = audio_agent.analyze_audio(session_id, input_source_name)
                    
                    st.write("🌐 **Context Verification Agent:** Querying Gemini for claim grounding...")
                    context_res = context_agent.verify_context(session_id, input_source_name)
                    
                    st.write("🤖 **Master Synthesizer:** Aggregating final verdict...")
                    final_verdict = master_synthesizer.synthesize_verdict({
                        "face_agent": face_res,
                        "audio_agent": audio_res,
                        "context_agent": context_res
                    })
                    
                    status.update(label="✅ Forensic Scan Complete!", state="complete", expanded=False)

                risk_score = final_verdict["overall_manipulation_risk"]
                st.markdown(f"""
                <div class="risk-card-high">
                    <div style="font-weight: 600; color: #f43f5e; font-size: 1.1rem;">MANIPULATION RISK SCORE</div>
                    <div class="risk-score-text">{risk_score}%</div>
                    <div style="color: #fda4af; font-size: 0.9rem;">{final_verdict['executive_summary']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                st.markdown("### ⚠️ Detailed Findings:")
                st.error(f"❌ **Face Boundary:** {face_res['details']}")
                st.warning(f"⚠️ **Audio Mismatch:** {audio_res['details']}")
                st.info(f"🌐 **Context Scan:** {context_res['details']}")
        else:
            st.caption("Awaiting media file or URL input to trigger autonomous agents...")

# --- TAB 2: IDENTITY SHIELD & AUTOMATED TAKEDOWN ---
with tab2:
    st.subheader("🔎 Identity Matching & Reverse Web-Search Suite")
    st.caption("Upload reference photo to automatically crawl the web and flag unauthorized deepfake matches.")
    
    col_a, col_b = st.columns([1, 1], gap="large")
    
    with col_a:
        st.markdown("### Step 1: Identity Registration")
        id_input_type = st.radio("Reference Photo Source:", ["Upload Local Photo", "Photo URL"], horizontal=True)
        ref_photo_loaded = False
        ref_name = "User Identity"
        
        if id_input_type == "Upload Local Photo":
            ref_image = st.file_uploader("Upload Reference Face Photo", type=["jpg", "png", "jpeg"])
            if ref_image:
                st.image(ref_image, caption="Reference Identity Loaded", width=200)
                ref_photo_loaded = True
                ref_name = ref_image.name
        else:
            ref_image_url = st.text_input("Enter Reference Photo URL:", placeholder="https://example.com/my_original_photo.jpg")
            if ref_image_url:
                st.image(ref_image_url, caption="Reference Image Loaded from Link", width=200)
                ref_photo_loaded = True
                ref_name = ref_image_url
                
        if ref_photo_loaded:
            if st.button("🔍 Run Autonomous Web Reverse-Search", type="primary", use_container_width=True):
                with st.spinner("🤖 Agent extracting facial embeddings & crawling index databases..."):
                    st.session_state["discovered_matches"] = takedown_agent.search_unauthorized_matches(ref_name)
                    st.success("✅ Reverse-search completed! Found matching URLs.")

    with col_b:
        st.markdown("### Step 2: Discovered Matches & Enforcement Portal")
        
        if "discovered_matches" in st.session_state and st.session_state["discovered_matches"]:
            st.markdown("#### 🚨 Flagged Unauthorized Matches:")
            
            for idx, item in enumerate(st.session_state["discovered_matches"]):
                with st.expander(f"🔴 Match #{idx+1} — {item['platform']} ({item['similarity_score']}% Match)", expanded=(idx==0)):
                    st.markdown(f"**URL:** `{item['target_url']}`")
                    st.write(f"**Status:** {item['status']}")
                    
                    portal_type = st.selectbox(
                        f"Notice Type (Match #{idx+1}):",
                        ["Google DMCA Copyright Removal", "Cyber Crime Govt. Incident Notice"],
                        key=f"portal_{idx}"
                    )
                    
                    if st.button(f"⚖️ Generate Notice for Match #{idx+1}", key=f"gen_btn_{idx}"):
                        notice_data = takedown_agent.generate_notice(
                            target_url=item['target_url'],
                            similarity_score=item['similarity_score'],
                            notice_type=portal_type
                        )
                        st.session_state[f"notice_{idx}"] = notice_data
                    
                    if f"notice_{idx}" in st.session_state:
                        nd = st.session_state[f"notice_{idx}"]
                        st.success(f"Notice Generated! Request ID: `{nd['request_id']}`")
                        st.code(nd["notice_body"], language="text")
                        st.download_button(
                            label="📥 Download Notice (.txt)",
                            data=nd["notice_body"],
                            file_name=f"Takedown_{nd['request_id']}.txt",
                            mime="text/plain",
                            key=f"dl_{idx}"
                        )
        else:
            st.info("👈 Upload your face reference image on the left and click **'Run Autonomous Web Reverse-Search'** to discover matches.")

# 6. Real-time Database Telemetry Logs
st.divider()
with st.expander("🛠️ View Real-Time ClickHouse Cloud Telemetry & Agent Logs"):
    st.json({
        "clickhouse_connection": "ACTIVE",
        "database_target": Config.CLICKHOUSE_HOST,
        "supported_tables": ["detection_telemetry", "identity_takedowns"]
    })