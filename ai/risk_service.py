from ai.llm import llm_manager

class RiskService:
    """Executes high-level risk isolation, root-cause investigations, and preventive lookups."""

    def evaluate_incident_threat(self, query: str) -> str:
        """Deconstructs safety log strings into critical severity vectors and engineering fixes."""
        prompt = f"""You are a Principal Industrial Safety Engineer.
Analyze the following incident query/context and provide a professional engineering threat-assessment.

Context:
{query}

Your response must strictly follow this format:
### 🚨 Risk Vector Analysis
*Explain exactly why this scenario presents a high operational, legal, or physical hazard.*

### 🛠️ Strategic Preventive Actions
*Provide 2-3 precise, site-executable preventative steps to isolate this hazard permanently.*
"""
        llm = llm_manager.get_fast_llm()
        return llm.invoke(prompt).content