"""
Triage Score Calculator using Claude LLM
Uses Anthropic's Claude to analyze symptoms and calculate triage scores (1-5)
"""

import os
import json
from typing import Dict
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Model configuration
MODEL_NAME = 'claude-3-7-sonnet-20250219'  # Latest Claude model
MAX_TOKENS = 1024
TEMPERATURE = 0.3  # Lower temperature for more consistent medical assessments

TRIAGE_SYSTEM_PROMPT = """You are an expert medical triage assistant using the ESI (Emergency Severity Index) methodology for triage assessment.

ESI Triage Scale (1-5):
The Emergency Severity Index is a five-level triage algorithm that categorizes patients by evaluating both acuity and resource needs.

- Level 1 (RESUSCITATION): Immediate life-saving intervention required
  * Requires immediate physician evaluation and life-saving interventions
  * Unstable vital signs, severe trauma, cardiac arrest
  * Unresponsive or only responding to painful stimuli
  Examples: Cardiac arrest, severe respiratory distress, unresponsive, severe trauma, active seizure

- Level 2 (EMERGENT): High-risk situation, confused/lethargic/disoriented, or severe pain/distress
  * Should not wait to be seen
  * High-risk situation (chest pain, altered mental status)
  * Confused, lethargic, or disoriented
  * Severe pain or distress (typically 7-10/10 pain scale)
  Examples: Chest pain, difficulty breathing, altered mental status, severe pain, signs of sepsis

- Level 3 (URGENT): Stable but requires multiple resources
  * Patient is stable enough to wait but condition needs attention
  * Expected to require 2+ hospital resources (labs, imaging, IV fluids, etc.)
  * Moderate symptoms that are stable
  Examples: Abdominal pain, moderate fever, mild dehydration, stable injuries requiring multiple tests

- Level 4 (LESS URGENT): Stable, requires one resource
  * Can safely wait to be seen
  * Expected to need only 1 hospital resource
  * Minor to moderate symptoms
  Examples: Minor lacerations, simple fractures, UTI symptoms, mild symptoms

- Level 5 (NON-URGENT): Stable, no resources needed
  * Could be treated in clinic or primary care setting
  * No resources anticipated
  * Very minor complaints
  Examples: Prescription refill, minor rash, chronic stable conditions, preventive care

ESI Decision Points:
1. Does the patient require immediate life-saving intervention? (Level 1)
2. Is this a high-risk situation, or is the patient confused/lethargic/disoriented, or in severe pain/distress? (Level 2)
3. How many resources will the patient need? (Levels 3, 4, or 5)
   - Multiple resources (2+) → Level 3
   - One resource → Level 4
   - No resources → Level 5

You must respond ONLY with a valid JSON object in this exact format:
{
  "triage_score": <integer 1-5>,
  "reasoning": "<brief explanation referencing ESI criteria: vital stability, resource needs, acuity level>",
  "worsened": <boolean true/false>
}

Assessment Guidelines:
- Follow ESI decision algorithm: life-saving intervention → high risk/severe distress → resource needs
- Consider vital sign stability and hemodynamic status
- Assess mental status (alert, confused, lethargic, unresponsive)
- Evaluate pain level and distress
- Estimate resource utilization (how many medical resources/tests would be needed)
- Compare current symptoms to previous assessments to determine if worsened
- Red flags: unstable vitals, altered mental status, severe pain, high-risk conditions
- When in doubt between levels, choose the higher acuity level for patient safety

Reference: Emergency Severity Index (ESI) - Agency for Healthcare Research and Quality (AHRQ)"""


def calculate_triage_detailed(
    symptoms: str,
    history: str = "",
    vitals: dict = None,
    recall_history: str = ""
) -> Dict:
    """
    Calculate detailed triage assessment including score, reasoning, and recommendations.
    
    Args:
        symptoms (str): Current patient symptoms description
        history (str): Patient medical history
        vitals (dict): Dictionary of vital signs
        recall_history (str): Previous symptom reports and assessments
        
    Returns:
        Dict: Dictionary containing:
            - triage_score (int): Score from 1-5
            - reasoning (str): Explanation for the score
            - recommendation (str): Medical recommendation
            - emergency_keywords (list): List of critical symptoms identified
            - worsened (bool): Whether symptoms have worsened from previous
    """
    # Build comprehensive prompt with all available information
    user_message = f"""Analyze the following patient information and provide a triage assessment:

CURRENT SYMPTOMS:
{symptoms}

PATIENT HISTORY:
{history if history else "No history provided"}

VITAL SIGNS:
{json.dumps(vitals, indent=2) if vitals else "No vital signs provided"}

PREVIOUS ASSESSMENTS:
{recall_history if recall_history else "No previous assessments"}

Provide your assessment as a JSON object with triage_score (1-5), reasoning, and worsened (boolean)."""

    try:
        # Call Claude API
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=TRIAGE_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        
        # Extract response text
        response_text = response.content[0].text
        
        # Parse JSON response
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        
        # Validate triage score is in range
        if not (1 <= result.get("triage_score", 0) <= 5):
            raise ValueError(f"Invalid triage score: {result.get('triage_score')}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"Error parsing Claude response: {e}")
        print(f"Response text: {response_text}")
        # Return default assessment
        return {
            "triage_score": 3,
            "reasoning": "Unable to parse triage assessment. Defaulting to moderate urgency.",
            "worsened": False
        }
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        # Return default assessment
        return {
            "triage_score": 3,
            "reasoning": f"Error during triage assessment: {str(e)}",
            "worsened": False
        }


def format_triage_response(assessment: Dict) -> str:
    """
    Format triage assessment into human-readable text.
    
    Args:
        assessment (Dict): Assessment dictionary from calculate_triage_detailed
        
    Returns:
        str: Formatted response text
    """
    score = assessment["triage_score"]
    reasoning = assessment["reasoning"]
    worsened = assessment.get("worsened", False)
    
    urgency_labels = {
        1: "RESUSCITATION - Immediate Life-Saving Intervention",
        2: "EMERGENT - High Risk/Severe Distress",
        3: "URGENT - Stable, Multiple Resources",
        4: "LESS URGENT - Stable, One Resource",
        5: "NON-URGENT - Stable, No Resources"
    }
    
    response = f"""
🏥 ESI TRIAGE ASSESSMENT

ESI Level: {score}/5 - {urgency_labels.get(score, "Unknown")}
Status: {"⚠️ Symptoms have worsened" if worsened else "Stable or improved"}

REASONING:
{reasoning}
"""
    
    return response.strip()
