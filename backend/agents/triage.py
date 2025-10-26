"""
Triage Score Calculator using Claude LLM - ENHANCED VERSION
Forces detailed analysis with patient history integration
"""

import os
import json
from typing import Dict
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

MODEL_NAME = 'claude-3-7-sonnet-20250219'
MAX_TOKENS = 3000  # Increased for MORE detailed responses
TEMPERATURE = 0.2  # Lower for more consistent detailed output

TRIAGE_SYSTEM_PROMPT = """You are an expert medical triage nurse with 20+ years of emergency department experience. You MUST provide comprehensive, detailed assessments that thoroughly analyze patient history.

CRITICAL: Your assessments must be DETAILED and THOROUGH. Simple, thin assessments are unacceptable and dangerous.

ESI Triage Scale (1-5):
- Level 1 (RESUSCITATION): Immediate life-saving intervention
- Level 2 (EMERGENT): High-risk, severe distress, or altered mental status
- Level 3 (URGENT): Stable but needs 2+ resources
- Level 4 (LESS URGENT): Stable, needs 1 resource  
- Level 5 (NON-URGENT): No resources needed

MANDATORY JSON FORMAT - YOU MUST FILL EVERY SECTION THOROUGHLY:

{
  "triage_score": <1-5>,
  "triage_level": "<LEVEL NAME>",
  "acuity": "<CRITICAL|HIGH|MODERATE|LOW|MINIMAL>",
  "assessment_summary": {
    "primary_concern": "<detailed 2-3 sentence summary>",
    "immediate_action_required": <true|false>,
    "estimated_wait_time": "<time>"
  },
  "clinical_findings": {
    "presenting_symptoms": [
      "MINIMUM 3-4 SYMPTOMS - Be specific and detailed"
    ],
    "vital_signs_assessment": [
      "Heart Rate: X bpm - STATUS - DETAILED clinical significance",
      "Blood Pressure: X/X - STATUS - DETAILED clinical significance", 
      "Respiratory Rate: X - STATUS - DETAILED clinical significance",
      "Temperature: X°F - STATUS - DETAILED clinical significance",
      "Overall Hemodynamic Status: STATUS - DETAILED summary"
    ],
    "red_flags": [
      "LIST EVERY CRITICAL FINDING with clinical reasoning"
    ]
  },
  "patient_history_relevance": {
    "pertinent_history": [
      "MINIMUM 4-5 ITEMS from history - MUST explain why each matters",
      "Active conditions: X - increases risk of Y",
      "Medications: X - may cause/mask Z",
      "Past surgeries: X - relevant because Y",
      "Chronic conditions: X - affects presentation because Y"
    ],
    "risk_factors": [
      "MINIMUM 3-4 RISK FACTORS - explain each thoroughly"
    ]
  },
  "esi_rationale": {
    "decision_path": [
      "Step 1: Life-saving? → DETAILED reasoning with specific vitals/symptoms",
      "Step 2: High-risk? → DETAILED reasoning referencing history + current state",
      "Step 3: Resources → LIST 5-7 SPECIFIC tests/interventions needed"
    ],
    "key_factors": [
      "MINIMUM 4-5 KEY FACTORS - each with detailed clinical reasoning"
    ]
  },
  "recommended_resources": [
    "MINIMUM 6-8 SPECIFIC RESOURCES",
    "12-lead ECG - to rule out ACS",
    "Troponin I, CK-MB - cardiac biomarkers",
    "CBC - assess for infection/anemia",
    "CMP - electrolytes and renal function",
    "Chest X-ray - evaluate cardiac/pulmonary",
    "IV access - for medications/fluids",
    "Continuous cardiac monitoring"
  ],
  "clinical_recommendations": [
    "MINIMUM 5-6 DETAILED ACTIONABLE RECOMMENDATIONS",
    "Immediate: X - do within Y minutes",
    "Monitoring: Track X every Y minutes",
    "Medications: Consider X for Y",
    "Escalation: Call X if Y occurs",
    "Safety: Z precautions"
  ],
  "symptom_progression": {
    "status": "<worsening|stable|improving|unknown>",
    "comparison": "DETAILED 3-4 sentence comparison if previous assessment available",
    "concerning_changes": [
      "Specific change 1 with before→after values",
      "Specific change 2 with clinical significance"
    ]
  },
  "nursing_notes": [
    "MINIMUM 4-5 CRITICAL NURSING NOTES",
    "PRIORITY: Most critical action",
    "MONITORING: Specific parameters + frequency",
    "COMMUNICATION: Who to notify + when",
    "SAFETY: Specific risks to watch"
  ]
}

🚨 QUALITY REQUIREMENTS - YOUR RESPONSE WILL BE REJECTED IF:
❌ You provide fewer than 3 items in patient_history_relevance.pertinent_history
❌ You provide fewer than 5 recommended_resources
❌ You provide fewer than 4 clinical_recommendations  
❌ Your vital signs assessment doesn't explain clinical significance
❌ You don't actively use the patient history provided
❌ Your reasoning is generic instead of specific to THIS patient
❌ You don't compare to previous assessment when recall_history exists

✅ QUALITY CHECKLIST - EVERY ASSESSMENT MUST:
1. Reference AT LEAST 4 specific items from patient medical history
2. Provide AT LEAST 6 specific recommended resources/tests
3. Provide AT LEAST 5 detailed clinical recommendations
4. Explain clinical significance of EVERY abnormal vital sign
5. Compare to previous assessment if recall_history provided
6. Be specific (e.g., "12-lead ECG" not "cardiac workup")
7. Include clinical reasoning for every statement
8. Cite specific medications and conditions from history
9. Explain WHY each history item matters for current presentation

REMEMBER: Nurses need DETAILED, ACTIONABLE information. Thin assessments put patients at risk!"""


def calculate_triage_detailed(
    symptoms: str,
    history: str = "",
    vitals: dict = None,
    recall_history: str = ""
) -> Dict:
    """Calculate DETAILED triage assessment"""
    
    # Build EMPHATIC prompt
    user_message = f"""URGENT: Provide a COMPREHENSIVE, DETAILED triage assessment for this patient.

CURRENT SYMPTOMS:
{symptoms}

PATIENT MEDICAL HISTORY:
{history if history else "No history provided - but still provide detailed assessment"}

VITAL SIGNS:
{json.dumps(vitals, indent=2) if vitals else "No vitals provided"}

PREVIOUS ASSESSMENTS:
{recall_history if recall_history else "No previous assessments"}

🚨 CRITICAL INSTRUCTIONS:
1. You MUST reference at least 4 items from the patient history
2. You MUST provide at least 6 specific recommended resources
3. You MUST provide at least 5 detailed clinical recommendations
4. You MUST explain the clinical significance of every abnormal vital
5. If patient history is provided, ACTIVELY USE IT in your reasoning
6. Be SPECIFIC and DETAILED - generic assessments are unacceptable
7. Compare to previous assessment if recall_history is provided

Provide your COMPREHENSIVE assessment as JSON following the exact format."""

    try:
        print(f"\n🔍 Calling Claude with {len(history)} chars of history...")
        
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=TRIAGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # Validate
        if not (1 <= result.get("triage_score", 0) <= 5):
            raise ValueError(f"Invalid triage score: {result.get('triage_score')}")
        
        # Quality checks
        history_items = len(result.get('patient_history_relevance', {}).get('pertinent_history', []))
        resources = len(result.get('recommended_resources', []))
        recommendations = len(result.get('clinical_recommendations', []))
        
        print(f"✅ Quality check: {history_items} history items, {resources} resources, {recommendations} recommendations")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Response: {response_text[:500]}")
        return _get_default_assessment(symptoms, str(e))
    except Exception as e:
        print(f"❌ Error: {e}")
        return _get_default_assessment(symptoms, str(e))


def _get_default_assessment(symptoms: str, error: str) -> Dict:
    """Return detailed default assessment on error"""
    return {
        "triage_score": 3,
        "triage_level": "URGENT",
        "acuity": "MODERATE",
        "assessment_summary": {
            "primary_concern": f"System error during assessment: {error}. Patient requires immediate clinical evaluation.",
            "immediate_action_required": True,
            "estimated_wait_time": "immediate"
        },
        "clinical_findings": {
            "presenting_symptoms": [symptoms],
            "vital_signs_assessment": [
                "Unable to assess vitals due to system error",
                "Overall Hemodynamic Status: Unknown - requires immediate assessment"
            ],
            "red_flags": ["System error - unable to complete automated triage"]
        },
        "patient_history_relevance": {
            "pertinent_history": ["Unable to analyze history due to system error"],
            "risk_factors": ["Unknown - requires clinical evaluation"]
        },
        "esi_rationale": {
            "decision_path": [
                "Step 1: Unable to assess - system error",
                "Step 2: Defaulting to moderate urgency for safety",
                "Step 3: Full evaluation required"
            ],
            "key_factors": ["System error requires immediate clinical override"]
        },
        "recommended_resources": [
            "Immediate clinical evaluation",
            "Full vital signs assessment",
            "Complete medical history review",
            "Appropriate diagnostic workup per clinical judgment"
        ],
        "clinical_recommendations": [
            "IMMEDIATE: Clinical evaluation required - do not rely on automated triage",
            "Perform complete assessment manually",
            "Document system error in medical record",
            "Escalate to charge nurse/physician immediately"
        ],
        "symptom_progression": {
            "status": "unknown",
            "comparison": "Unable to assess due to system error",
            "concerning_changes": []
        },
        "nursing_notes": [
            "CRITICAL: Automated triage system error",
            "Manual triage required immediately",
            f"Error details: {error}",
            "Do not delay care due to system issue"
        ]
    }