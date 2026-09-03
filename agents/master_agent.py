from google import genai
from config import Config


class GeminiMasterSynthesizer:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None

    def synthesize_verdict(self, agent_outputs: dict) -> dict:
        # Use only agents that actually completed, so SKIPPED image-audio does not lower the score.
        weighted = []

        face = agent_outputs.get("face_agent", {})
        if face.get("status") == "COMPLETED":
            weighted.append((float(face.get("anomaly_score", 0.0)), 0.45))

        audio = agent_outputs.get("audio_agent", {})
        if audio.get("status") == "COMPLETED":
            weighted.append((float(audio.get("anomaly_score", 0.0)), 0.35))

        context = agent_outputs.get("context_agent", {})
        if context.get("status") == "COMPLETED":
            weighted.append((float(context.get("risk_score", 0.0)), 0.20))

        if weighted:
            weight_total = sum(weight for _, weight in weighted)
            aggregate = sum(score * weight for score, weight in weighted) / weight_total
        else:
            aggregate = 0.0

        aggregate_risk = max(0, min(100, int(round(aggregate * 100))))

        summary = ""
        if self.client:
            prompt = f"""
You are the Master Forensic AI Synthesizer for CineTruth AI.
The system reports a manipulation-indicator risk of {aggregate_risk}%.
Sub-agent outputs:
{agent_outputs}

Write a concise 2-sentence executive summary. Be calibrated: this is a risk indicator, not definitive proof of a deepfake.
Mention failed/skipped modules if they materially limit confidence.
"""
            try:
                response = self.client.models.generate_content(
                    model=Config.GEMINI_MODEL,
                    contents=prompt,
                )
                summary = (response.text or "").strip()
            except Exception:
                summary = ""

        if not summary:
            completed = sum(1 for value in agent_outputs.values() if value.get("status") == "COMPLETED")
            summary = (
                f"Manipulation-indicator risk is {aggregate_risk}% based on {completed} completed forensic module(s). "
                "Treat this as a screening signal and verify suspicious media with additional evidence."
            )

        return {
            "overall_manipulation_risk": aggregate_risk,
            "executive_summary": summary,
            "sub_agent_reports": agent_outputs,
        }
