import uuid
from google import genai
from config import Config
from database.clickhouse_db import db_manager

class TakedownAgent:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None

    def search_unauthorized_matches(self, reference_identity_name: str = "Uploaded Identity") -> list:
        """
        Simulates autonomous web-crawling & face embedding matching across public portals.
        Returns discovered target URLs with high similarity scores.
        """
        discovered_targets = [
            {
                "target_url": "https://unauthorized-deepfake-vault.com/video/90213",
                "platform": "Underground Video Host",
                "similarity_score": 96.4,
                "status": "UNAUTHORIZED_MATCH"
            },
            {
                "target_url": "https://social-impersonator-bot.net/profile/clip_441",
                "platform": "Social Media Mirror",
                "similarity_score": 91.8,
                "status": "UNAUTHORIZED_MATCH"
            },
            {
                "target_url": "https://synthetic-media-archive.org/file_88192.mp4",
                "platform": "Public File Storage",
                "similarity_score": 88.2,
                "status": "UNAUTHORIZED_MATCH"
            }
        ]
        return discovered_targets

    def generate_notice(self, target_url: str, similarity_score: float, notice_type: str) -> dict:
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        prompt = f"""
        Draft an official, formal Legal Takedown Notice for unauthorized synthetic media.
        
        Details:
        - Request ID: {request_id}
        - Target URL: {target_url}
        - Facial Embedding Match: {similarity_score}%
        - Portal Type: {notice_type}
        """

        notice_text = ""
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                notice_text = response.text
            except Exception:
                pass

        if not notice_text:
            notice_text = f"""[OFFICIAL LEGAL TAKEDOWN NOTICE]
Request ID: {request_id}
Target URL: {target_url}
Match Confidence: {similarity_score}%
Notice Type: {notice_type}

To Platform Administrator / DMCA Agent,

This serves as formal notice under Copyright and Privacy Enforcement Laws. The media found at {target_url} contains an unauthorized synthetic deepfake/identity depiction matching our verified identity database with {similarity_score}% confidence.

We demand immediate de-indexing, takedown, and removal of this infringing material.

Verification Hash: {uuid.uuid4().hex}
Status: PENDING IMMEDIATE REMOVAL"""

        db_manager.log_takedown_request(
            request_id=request_id,
            target_url=target_url,
            similarity_score=float(similarity_score),
            notice_type=notice_type
        )

        return {
            "request_id": request_id,
            "target_url": target_url,
            "notice_type": notice_type,
            "notice_body": notice_text
        }