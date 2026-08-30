import json
from google import genai
from config import Config
from database.clickhouse_db import db_manager

class ContextVerificationAgent:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None

    def verify_context(self, session_id: str, transcript_or_claim: str) -> dict:
        if not self.client:
            return {
                "agent": "Context Verification Agent",
                "status": "FAILED",
                "risk_score": 0.5,
                "details": "Gemini API key missing."
            }

        prompt = f"""
        You are a Forensic Verification Agent.
        Analyze this media input source: "{transcript_or_claim}".
        
        Evaluate risk of synthetic deepfake/manipulation.
        Return ONLY valid JSON with no markdown formatting:
        {{
            "risk_score": 0.82,
            "summary": "Short 1-sentence finding about context credibility."
        }}
        """

        try:
            # Official stable model alias for GenAI SDK
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            risk_score = float(data.get("risk_score", 0.78))
            details = data.get("summary", "Context analysis completed successfully via Gemini.")
            
            db_manager.log_agent_execution(
                session_id=session_id,
                agent_name="Context Verification Agent",
                anomaly_score=risk_score,
                status="COMPLETED",
                details=details
            )

            return {
                "agent": "Context Verification Agent",
                "status": "COMPLETED",
                "risk_score": risk_score,
                "details": details
            }

        except Exception as e:
            return {
                "agent": "Context Verification Agent",
                "status": "ERROR",
                "risk_score": 0.65,
                "details": f"Context Scan Error: {str(e)}"
            }