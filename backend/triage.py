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

TRIAGE_SYSTEM_PROMPT = """You are an expert medical triage assistant. Your role is to analyze patient symptoms and assign appropriate triage scores.

Triage Score Scale (1-5):
- Level 1 (Non-urgent): Minor issues, stable condition. Can wait, self-care appropriate.
  Examples: Minor cold, small bruise, mild headache
  
- Level 2 (Less urgent): Uncomfortable but stable. Should see doctor within days.
  Examples: Persistent cough, minor infections, non-urgent concerns
  
- Level 3 (Urgent): Needs attention soon, potentially serious. See doctor within 24 hours.
  Examples: High fever, moderate pain, concerning symptoms
  
- Level 4 (Very urgent): Serious condition, needs prompt care. Go to urgent care/ED soon.
  Examples: Severe pain, significant injury, worrying vital signs
  
- Level 5 (Emergency): Life-threatening, needs immediate emergency care. Call 911 or go to ED immediately.
  Examples: Chest pain, difficulty breathing, severe bleeding, stroke symptoms, altered consciousness

You must respond ONLY with a valid JSON object in this exact format:
{
  "triage_score": <integer 1-5>,
  "reasoning": "<brief explanation for the score>",
  "recommendation": "<specific medical recommendation>",
  "emergency_keywords": ["<list>", "<of>", "<critical>", "<symptoms>"],
  "worsened": <boolean true/false>
}

Consider:
- Severity of symptoms
- Potential for deterioration
- Vital signs if provided
- Patient history and temporal patterns
- Red flags and emergency keywords
- Comparison with previous symptoms if available

Always prioritize patient safety. When in doubt, assign a higher triage score."""


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

Provide your assessment as a JSON object with triage_score (1-5), reasoning, recommendation, emergency_keywords (list), and worsened (boolean)."""

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
            "recommendation": "Please consult medical professional for proper assessment.",
            "emergency_keywords": [],
            "worsened": False
        }
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        # Return default assessment
        return {
            "triage_score": 3,
            "reasoning": f"Error during triage assessment: {str(e)}",
            "recommendation": "Please consult medical professional for proper assessment.",
            "emergency_keywords": [],
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
    recommendation = assessment["recommendation"]
    emergency_keywords = assessment.get("emergency_keywords", [])
    worsened = assessment.get("worsened", False)
    
    urgency_labels = {
        1: "Non-urgent",
        2: "Less urgent",
        3: "Urgent",
        4: "Very urgent",
        5: "EMERGENCY"
    }
    
    response = f"""
🏥 TRIAGE ASSESSMENT

Triage Score: {score}/5 ({urgency_labels.get(score, "Unknown")})
Status: {"⚠️ Symptoms have worsened" if worsened else "Stable or improved"}

REASONING:
{reasoning}

RECOMMENDATION:
{recommendation}
"""
    
    if emergency_keywords:
        response += f"\n⚠️ Critical symptoms identified: {', '.join(emergency_keywords)}"
    
    return response.strip()
