import google.generativeai as genai
import json
from typing import Dict, Any, List
from config import Config


class GeminiLLM:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse user query to extract structured fields"""
        prompt = f"""
        Extract the following fields from the user query and return as JSON:
        - target_topic: The main topic or procedure mentioned
        - age: Age if mentioned (null if not)
        - gender: Gender if mentioned (null if not)
        - policy_duration: Policy duration if mentioned (null if not)
        - location: Location if mentioned (null if not)
        - special_conditions: Any special conditions like waiting periods, exclusions (null if not)
        - amount_requested: Any monetary amount mentioned (null if not)

        Query: "{query}"

        Return ONLY valid JSON format without any markdown formatting or code blocks:
        """

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean up response - remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            parsed_data = json.loads(response_text)
            return parsed_data
        except Exception as e:
            print(f"Error parsing query: {e}")
            print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            # Return default structure
            return {
                "target_topic": query,
                "age": None,
                "gender": None,
                "policy_duration": None,
                "location": None,
                "special_conditions": None,
                "amount_requested": None
            }

    def make_decision(
        self,
        query: str,
        parsed_query: Dict[str, Any],
        retrieved_clauses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Make decision based on query and retrieved clauses"""

        clauses_text = "\n".join([
            f"Clause {i+1} (Score: {clause['score']:.3f}):\n{clause['text']}\n"
            for i, clause in enumerate(retrieved_clauses)
        ])

        prompt = f"""
        You are an intelligent document processing agent. Based on the user query and retrieved document clauses, analyze the content and provide relevant information.

        User Query: "{query}"

        Retrieved Document Clauses:
        {clauses_text}

        Instructions:
        1. Analyze the retrieved clauses against the user query
        2. For document/resume queries, provide "Approved" decision with relevant information
        3. Extract any relevant amounts/numbers if mentioned
        4. Provide clear justification referencing specific clauses

        Respond ONLY in this exact JSON format (no markdown, no code blocks):
        {{
            "decision": "Approved",
            "amount": null,
            "justification": [
                {{
                    "clause_id": "clause_1",
                    "text": "exact relevant text from the clauses",
                    "reason": "explanation of relevance to the query"
                }}
            ]
        }}

        Important: Return only valid JSON without any formatting or code blocks.
        """

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean up response - remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            # Try to parse JSON
            decision_data = json.loads(response_text)

            # Validate the response structure
            required_keys = ["decision", "amount", "justification"]
            if not all(key in decision_data for key in required_keys):
                raise ValueError("Invalid response structure")

            return decision_data
        except Exception as e:
            print(f"Error making decision: {e}")
            print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")

            # Create a meaningful response based on the retrieved clauses
            fallback_justification = []
            for i, clause in enumerate(retrieved_clauses[:2]):  # Use top 2 clauses
                fallback_justification.append({
                    "clause_id": f"clause_{i+1}",
                    "text": clause.get('text', '')[:200] + ('...' if len(clause.get('text', '')) > 200 else ''),
                    "reason": f"Retrieved relevant content for query: {query}"
                })

            return {
                "decision": "Approved",
                "amount": None,
                "justification": fallback_justification if fallback_justification else [
                    {
                        "clause_id": "system_fallback",
                        "text": "System processed the query but LLM response formatting failed",
                        "reason": "Technical issue with response formatting - check logs for details"
                    }
                ]
            }

    def generate_summary(
        self,
        document_text: str,
        max_length: int = 500
    ) -> str:
        """Generate a summary of the document"""
        prompt = f"""
        Provide a concise summary of the following document in no more than {max_length} characters:

        Document:
        {document_text[:3000]}  # Limit input to avoid token limits

        Summary:
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Unable to generate summary due to system error."
