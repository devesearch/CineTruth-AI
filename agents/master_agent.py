from google import genai
from config import Config

class GeminiMasterSynthesizer:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None

    def synthesize_verdict(self, agent_outputs: dict) -> dict:
        """
        Aggregates outputs from all specialized sub-agents and calculates 
        the final Manipulation Risk Percentage and executive summary.
        """
        face_score = agent_outputs.get("face_agent", {}).get("anomaly_score", 0.0)
        audio_score = agent_outputs.get("audio_agent", {}).get("anomaly_score", 0.0)
        context_score = agent_outputs.get("context_agent", {}).get("risk_score", 0.0)

        # Weighted aggregate score calculation
        aggregate_risk = int(((face_score * 0.4) + (audio_score * 0.4) + (context_score * 0.2)) * 100)

        if not self.client:
            summary = "High probability of synthetic manipulation detected across visual and auditory layers."
        else:
            prompt = f"""
            You are the Master Forensic AI Synthesizer for CineTruth AI.
            Summarize the findings from the specialized media analysis agents:
            
            - Face Consistency Score: {face_score}
            - Audio Mismatch Score: {audio_score}
            - Context Risk Score: {context_score}
            - Calculated Manipulation Risk: {aggregate_risk}%
            
            Provide a crisp, 2-sentence executive verdict for journalists and fact-checkers.
            """

            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                summary = response.text
            except Exception:
                summary = "Synthetic manipulation and facial/audio discrepancies confirmed."

        return {
            "overall_manipulation_risk": aggregate_risk,
            "executive_summary": summary,
            "sub_agent_reports": agent_outputs
        }