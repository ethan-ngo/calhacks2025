"""
Triage Score Calculator using Claude LLM - BRIEF VERSION
Concise, focused assessments for dashboard display
"""

import os
import json
import re
from typing import Dict
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

MODEL_NAME = 'claude-3-7-sonnet-20250219'
MAX_TOKENS = 1200  # Reduced for briefer responses
TEMPERATURE = 0.2

TRIAGE_SYSTEM_PROMPT = """You are an expert emergency triage nurse. Provide concise, focused assessments for dashboard display.

ESI Triage Scale (1-5):
- Level 1 (RESUSCITATION): Immediate life-saving intervention
- Level 2 (EMERGENT): High-risk, severe distress, altered mental status
- Level 3 (URGENT): Stable but needs 2+ resources
- Level 4 (LESS URGENT): Stable, needs 1 resource
- Level 5 (NON-URGENT): No resources needed

REQUIRED JSON FORMAT - Keep ALL entries brief and focused:

{
  "triage_score": <1-5>,
  "triage_level": "<RESUSCITATION|EMERGENT|URGENT|LESS URGENT|NON-URGENT>",
  "acuity": "<CRITICAL|HIGH|MODERATE|LOW|MINIMAL>",
  "assessment_summary": {
    "primary_concern": "<1-2 sentence summary>",
    "immediate_action_required": <true|false>,
    "estimated_wait_time": "<immediate|<15min|<30min|<60min|<2hr|when available>"
  },
  "clinical_findings": {
    "presenting_symptoms": [
      "2-3 key symptoms only"
    ],
    "vital_signs_assessment": [
      "Heart Rate: X bpm - status - brief note",
      "Blood Pressure: X/X - status - brief note",
      "Respiratory Rate: X - status",
      "Temperature: X°F - status",
      "Overall Status: <stable|unstable|critical>"
    ],
    "red_flags": [
      "Critical findings only (empty array if none)"
    ]
  },
  "patient_history_relevance": {
    "pertinent_history": [
      "2-3 relevant items: 'Condition - why it matters'",
      "If no history: ['No history provided']"
    ],
    "risk_factors": [
      "2-3 key risk factors"
    ]
  },
  "esi_rationale": {
    "decision_path": [
      "Step 1: Life-saving? -> Yes/No - brief reason",
      "Step 2: High-risk? -> Yes/No - brief reason",
      "Step 3: Resources -> 2-3 tests"
    ],
    "key_factors": [
      "2-3 key factors only"
    ]
  },
  "recommended_resources": [
    "2-4 specific tests"
  ],
  "clinical_recommendations": [
    "2-3 key actions"
  ],
  "symptom_progression": {
    "status": "<worsening|stable|improving|unknown>",
    "comparison": "Brief 1 sentence if recall_history available, else 'No previous assessment'",
    "concerning_changes": [
      "1-2 changes if worsening, else empty array"
    ]
  },
  "nursing_notes": [
    "2-3 critical notes"
  ]
}

CRITICAL RULES:
- Keep ALL entries BRIEF - max 1 sentence per item
- 2-3 items per list (not more)
- Focus on essential information only
- Use simple ASCII characters (-> not unicode arrows)
- No // comments in JSON
- No trailing commas"""


def calculate_triage_detailed(
    symptoms: str,
    history: str = "",
    vitals: dict = None,
    recall_history: str = ""
) -> Dict:
    """Calculate brief triage assessment"""
    
    user_message = f"""Provide a BRIEF, CONCISE triage assessment for dashboard display.

CURRENT SYMPTOMS:
{symptoms}

PATIENT MEDICAL HISTORY:
{history if history else "No history provided"}

VITAL SIGNS:
{json.dumps(vitals, indent=2) if vitals else "No vitals provided"}

PREVIOUS ASSESSMENTS:
{recall_history if recall_history else "No previous assessments"}

IMPORTANT: Keep your response brief and focused. Use 2-3 items per list, not more. Keep all text concise."""

    try:
        print(f"\n🔍 Calling Claude...")
        
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=TRIAGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON - robust cleaning
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Remove BOM
        response_text = response_text.strip('\ufeff\ufffe')
        
        # Fix common JSON issues
        response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)  # Trailing commas
        response_text = re.sub(r'//[^\n]*', '', response_text)  # Comments
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parse Error at line {e.lineno}, column {e.colno}")
            print(f"Error: {e.msg}")
            print(f"\n🔍 Problematic section:")
            lines = response_text.split('\n')
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            for i in range(start, end):
                marker = ">>> " if i == e.lineno - 1 else "    "
                print(f"{marker}{i+1}: {lines[i]}")
            raise
        
        # Validate
        if not (1 <= result.get("triage_score", 0) <= 5):
            raise ValueError(f"Invalid triage score: {result.get('triage_score')}")
        
        print(f"✅ Assessment complete: Level {result['triage_score']}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return _get_default_assessment(symptoms, str(e))
    except Exception as e:
        print(f"❌ Error: {e}")
        return _get_default_assessment(symptoms, str(e))


def _get_default_assessment(symptoms: str, error: str) -> Dict:
    """Return brief default assessment on error"""
    return {
        "triage_score": 3,
        "triage_level": "URGENT",
        "acuity": "MODERATE",
        "assessment_summary": {
            "primary_concern": f"System error: {error[:50]}. Clinical evaluation required.",
            "immediate_action_required": True,
            "estimated_wait_time": "immediate"
        },
        "clinical_findings": {
            "presenting_symptoms": [symptoms],
            "vital_signs_assessment": [
                "Unable to assess - system error",
                "Overall Status: Unknown - immediate evaluation needed"
            ],
            "red_flags": ["System error - manual triage required"]
        },
        "patient_history_relevance": {
            "pertinent_history": ["Unable to analyze - system error"],
            "risk_factors": ["Unknown - requires clinical evaluation"]
        },
        "esi_rationale": {
            "decision_path": [
                "Step 1: Unable to assess",
                "Step 2: Defaulting to moderate urgency",
                "Step 3: Full evaluation required"
            ],
            "key_factors": ["System error requires clinical override"]
        },
        "recommended_resources": [
            "Immediate clinical evaluation",
            "Full vital signs assessment",
            "Manual triage required"
        ],
        "clinical_recommendations": [
            "IMMEDIATE clinical evaluation required",
            "Do not rely on automated triage",
            "Escalate to charge nurse immediately"
        ],
        "symptom_progression": {
            "status": "unknown",
            "comparison": "Unable to assess due to system error",
            "concerning_changes": []
        },
        "nursing_notes": [
            "CRITICAL: Automated triage error",
            "Manual triage required immediately",
            f"Error: {error[:100]}"
        ]
    }