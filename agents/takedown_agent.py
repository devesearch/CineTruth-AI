import uuid
from google import genai
from config import Config
from database.clickhouse_db import db_manager

class TakedownAgent:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None

    def generate_notice(self, target_url: str, similarity_score: float, notice_type: str) -> dict:
        """
        Drafts a formal DMCA or Cyber Crime Legal Complaint using Gemini.
        """
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        if not self.client:
            # Fallback text if API is offline
            notice_text = f"[OFFICIAL TAKEDOWN NOTICE]\nRequest ID: {request_id}\nTarget URL: {target_url}\nSimilarity: {similarity_score}%\nNotice Type: {notice_type}\nStatus: Direct Removal Requested under Copyright/Privacy Laws."
        else:
            prompt = f"""
            Draft an official, highly formal Legal Takedown Notice for unauthorized deepfake/synthetic media.
            
            Details:
            - Request ID: {request_id}
            - Target URL: {target_url}
            - Facial Embedding Match Confidence: {similarity_score}%
            - Notice Type: {notice_type} (Google DMCA Copyright / Govt Cyber Crime Incident)
            
            Include:
            1. Legal basis under IT Act & Copyright Laws.
            2. Demand for immediate de-indexing and deletion.
            3. Verification hash and identity protection disclaimer.
            """

            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                notice_text = response.text
            except Exception:
                notice_text = f"Notice Generation Error. Fallback template executed for URL: {target_url}"

        # Log Takedown Request to ClickHouse DB (Partner Track)
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