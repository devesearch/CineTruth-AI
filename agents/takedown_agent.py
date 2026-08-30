import uuid
from google import genai
from config import Config
from database.clickhouse_db import db_manager

class TakedownAgent:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None

    def generate_notice(self, target_url: str, similarity_score: float, notice_type: str) -> dict:
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        if not self.client:
            notice_text = f"[OFFICIAL TAKEDOWN NOTICE]\nRequest ID: {request_id}\nTarget URL: {target_url}\nSimilarity: {similarity_score}%\nNotice Type: {notice_type}\nStatus: Direct Removal Requested."
        else:
            prompt = f"""
            Draft an official, formal Legal Takedown Notice for unauthorized synthetic media.
            
            Details:
            - Request ID: {request_id}
            - Target URL: {target_url}
            - Facial Embedding Match: {similarity_score}%
            - Portal Type: {notice_type}
            """

            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                notice_text = response.text
            except Exception as e:
                notice_text = f"Notice Generation Fallback executed for target URL: {target_url}\nError: {str(e)}"

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