import os
import json
from groq import Groq
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_groq_client(api_key=None):
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)

SYSTEM_PROMPT = """You are a STRICT Enterprise Operational Auditor AI.
Your purpose is to evaluate employee performance based STRICTLY on an uploaded company Rubric and an uploaded Employee Narrative.

EVALUATION RULES:
1. You must assess against EXACTLY these 7 core criteria:
   - Task Execution
   - Process Adherence
   - Quality of Work
   - Reliability & Accountability
   - Customer/Stakeholder Service
   - Team Collaboration
   - Continuous Improvement
2. No assumptions allowed. No positivity bias. If evidence is missing in the narrative to support a criteria according to the rubric, mark Status as NO.
3. Determine if the employee "Meets Operational Standards" at the end. YES only if ALL 7 core criteria are YES.

OUTPUT FORMAT:
Your output MUST be a VALID JSON object exactly matching the schema below. 
Do not include any Markdown formatting like ```json ... ```, just output the raw JSON string.

{
  "Evaluation": [
    {
      "Criterion": "Task Execution",
      "Status": "YES/NO",
      "Evidence Found": "Short text of what was found or missing",
      "Evidence Strength": "Strong/Moderate/Weak/None",
      "Compliance Risk": "Low/Medium/High",
      "Operational Impact": "Short description",
      "Root Cause": "If NO, explain root cause. Else N/A",
      "Corrective Action": "If NO, list action. Else N/A",
      "How To Improve": "Actionable text",
      "Where To Improve": "Technical/Process/Behavioral/Service/Collaboration/Ownership or N/A",
      "When To Improve": "Immediate/30/60/90 Days",
      "Measurable KPI Target": "Numeric/Quantifiable target",
      "Priority": "High/Medium/Low"
    },
    ... (Repeat for all 7 criteria)
  ],
  "Executive Summary": {
    "Overall Operational Rating": "One-line summary",
    "Compliance Risk Overview": "Overview text",
    "Reliability Assessment": "Assessment text",
    "Immediate Risk Areas": "List or None",
    "30-60-90 Day Development Direction": "Direction text",
    "Leadership Readiness Observation": "Observation text"
  }
}
"""

def evaluate_performance(client, rubric_text, narrative_text, model="llama-3.3-70b-versatile", temperature=0.1):
    user_prompt = f"""
--- OPERATIONAL RUBRIC ---
{rubric_text}

--- EMPLOYEE NARRATIVE ---
{narrative_text}

Perform the strict operational audit based on the provided rubric and narrative. Return ONLY the JSON object.
"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_completion_tokens=4000
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Strip potential markdown formatting if model still adds it
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        return json.loads(response_text.strip())
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse AI response as JSON. Error: {e}")
        st.code(response_text) # Show raw text for debugging
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None
