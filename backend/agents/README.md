# Patient Triage Monitoring Agent

An AI-powered medical triage agent built with Anthropic Claude and Fetch.ai's uAgents framework. This agent uses the **ESI (Emergency Severity Index)** methodology to assess patient symptoms and provide triage scores for remote healthcare monitoring.

## 🏥 Overview

The Patient Triage Monitor is an autonomous agent that:
- Receives patient symptom reports via Fetch.ai messaging protocol
- Analyzes symptoms using Claude 3.7 Sonnet AI
- Assigns ESI triage scores (1-5) based on acuity and resource needs
- Tracks patient history and symptom progression over time
- Detects if symptoms are worsening
- Provides structured medical triage assessments

## 🎯 Features

- **ESI-Based Triage**: Uses the evidence-based Emergency Severity Index methodology from AHRQ
- **AI-Powered Assessment**: Leverages Claude 3.7 Sonnet for intelligent symptom analysis
- **History Tracking**: Maintains patient conversation history for trend analysis
- **Symptom Progression**: Automatically detects if conditions are worsening
- **Persistent Storage**: Uses context storage to track up to 20 messages (10 exchanges) per patient
- **Real-time Processing**: Immediate triage assessment with acknowledgment system
- **Agentverse Ready**: Can be deployed to Fetch.ai Agentverse for production use

## 📊 ESI Triage Scale

The agent uses the 5-level Emergency Severity Index:

| Level | Category | Description | When to Use |
|-------|----------|-------------|-------------|
| **1** | RESUSCITATION | Immediate life-saving intervention required | Cardiac arrest, severe respiratory distress, unresponsive |
| **2** | EMERGENT | High-risk, confused/lethargic, or severe pain | Chest pain, altered mental status, severe pain (7-10/10) |
| **3** | URGENT | Stable but requires multiple resources (2+) | Moderate symptoms needing labs, imaging, IV fluids |
| **4** | LESS URGENT | Stable, requires one resource | Minor injuries, simple tests, mild symptoms |
| **5** | NON-URGENT | Stable, no resources needed | Very minor complaints, routine care |

### Example Interaction

**Input:**
```
"I have chest pain radiating to my left arm and shortness of breath for the past hour"
```

**Output:**
```
🏥 ESI TRIAGE ASSESSMENT

ESI Level: 2/5 - EMERGENT - High Risk/Severe Distress
Status: Stable or improved

REASONING:
Based on ESI criteria, this patient presents with high-risk symptoms 
(chest pain with radiation, respiratory symptoms). These symptoms suggest 
potential cardiac origin requiring immediate evaluation. Patient needs 
multiple resources (ECG, troponin, imaging) and should be seen urgently. 
Classified as ESI Level 2 - should not wait to be seen.
```

## 🔧 Architecture

### Components

1. **patient_agent.py** - Main agent implementation
   - Chat protocol handling
   - Message processing
   - History management
   - Integration with triage module

2. **triage.py** - Triage calculation engine
   - Claude API integration
   - ESI algorithm implementation
   - Response formatting

### Message Flow

```
User → ChatMessage → Patient Agent → Triage Module → Claude API
                                          ↓
User ← Formatted Response ← Assessment ← JSON Response
```

