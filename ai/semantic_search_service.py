import json
from typing import Dict, Any, List
from datetime import datetime
from ai.llm import llm_manager
# Assuming Chroma/Vector vector store interface hooks:
# from database.vector_db import get_vector_client 

class SemanticSearchService:
    """
    Executes metadata-aware vector space retrieval and constructs 
    high-density context summaries for LLM inference tracking.
    """

    def __init__(self):
        # We leverage the fast LLM path to parse filter parameters instantaneously
        self.meta_extractor_llm = llm_manager.get_fast_llm()

    def _extract_query_metadata(self, query: str) -> Dict[str, Any]:
        """Parses unstructured dialogue into deterministic relational filter schemas."""
        current_year = datetime.now().strftime("%Y")
        
        prompt = f"""You are a database metadata extraction parser. 
Analyze the user safety query and extract structured filter parameters as a raw JSON object.

Available Fields:
- zone: string (e.g., "Zone A", "Zone B")
- event: string (e.g., "no-helmet", "no-vest", "forklift-speeding")
- worker_id: string (e.g., "W104", "W219")
- severity: string ("low", "medium", "high")

Current Reference Context:
- Current Year: {current_year}

Query: "{query}"

Return ONLY a flat JSON dictionary containing keys that are explicitly mentioned or strongly inferred. If a field cannot be inferred, do NOT include it in the JSON object.
"""
        try:
            response = self.meta_extractor_llm.invoke(prompt)
            content = response.content.strip()
            # Clean possible markdown block wrappers if returned by the model
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[1].split("```")[0].strip()
                
            return json.loads(content)
        except Exception:
            return {} # Fallback to completely unrestricted semantic space on parsing bugs

    def retrieve_concise_evidence(self, query: str, limit: int = 4) -> str:
        """
        Executes metadata-prefiltered vector queries and builds a dense text 
        evidence summary block optimized for LLM context windows.
        """
        # 1. Isolate structural metadata parameters dynamically
        metadata_filters = self._extract_query_metadata(query)
        
        # 2. Build out the query parameter payload for your vector engine
        # This example illustrates structural implementation against typical Vector DB APIs
        where_clauses = {}
        for key, val in metadata_filters.items():
            where_clauses[key] = {"$eq": val}
            
        # If multiple conditions exist, wrap them in a logical AND operator structure
        chroma_filter = None
        if len(where_clauses) > 1:
            chroma_filter = {"$and": [ {k: v} for k, v in where_clauses.items() ]}
        elif len(where_clauses) == 1:
            chroma_filter = where_clauses

        try:
            # client = get_vector_client()
            # results = client.query(query_texts=[query], n_results=limit, where=chroma_filter)
            
            # Simulated typical payload structure returned from vector backend storage:
            mock_results = {
                "documents": [
                    "Worker W104 spotted crossing loading dock inside Zone B without high-visibility safety vest vest during regular morning inventory shift.",
                    "Routine check inside Zone B confirmed clearing of main pathways, but operator noted W104 was operating equipment without checking harness clips."
                ],
                "metadatas": [
                    {"worker_id": "W104", "zone": "Zone B", "severity": "high", "timestamp": "2026-07-20"},
                    {"worker_id": "W104", "zone": "Zone B", "severity": "medium", "timestamp": "2026-07-22"}
                ]
            }
            
            # 3. Compile raw matches into a high-density evidence string block
            evidence_lines = []
            for doc, meta in zip(mock_results["documents"], mock_results["metadatas"]):
                timestamp = meta.get("timestamp", "N/A")
                zone = meta.get("zone", "Unknown")
                worker = meta.get("worker_id", "N/A")
                severity = meta.get("severity", "low").upper()
                
                # Format string structure directly to act as clear undeniable proof items
                evidence_lines.append(
                    f"• [{timestamp}] [Zone: {zone}] [Worker: {worker}] [Severity: {severity}]\n  Evidence: {doc.strip()}"
                )
                
            if not evidence_lines:
                return "No matching historical safety logs or semantic evidence clusters could be verified matching those criteria."
                
            return "\n\n".join(evidence_lines)

        except Exception as e:
            return f"Evidence retrieval pipeline failure: {str(e)}"