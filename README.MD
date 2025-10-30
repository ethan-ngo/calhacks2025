# 🏥 TriageFlow

> AI-powered triage system that empowers nurses with instant, expert-level assistance on ESI assessments using Fetch.AI to manage Claude and ChromaDB, ensuring critical patients never wait while reducing burnout.

**[🌐 Live App](https://calhacks2025-nine.vercel.app/)** | **[📋 Devpost Submission](https://devpost.com/software/triageflow?ref_content=user-portfolio&ref_feature=in_progress)**

---

## ✨ Inspiration

One of our teammates went to the ER with a broken arm and waited almost 6 hours. In busy emergency rooms like his, even the smallest inefficiencies can add up. We were inspired by the idea that digital tools and automation can support nursing staff, not replace them, by monitoring evolving conditions, surfacing early warnings, and giving transparent, actionable recommendations.

---

## 🎯 What It Does

- **🎯 Triage Score Determination**: Calculates ESI (Emergency Severity Index) priority levels based on current symptoms, history, images of injuries, and patient comments following established medical guidelines.
- **📋 Patient Records Retrieval (HL7 FHIR)**: Retrieves prior visits, known conditions, and reason for visit so nurses and the system have full context.
- **🎤 Voice & Text Patient Intake**: Patients can speak or type their current symptoms and comments. The system uses AI to extract structured data and prompts for clarifying details.
- **👩‍⚕️ Nurse Dashboard**: Presents a real-time queue, allows manual add/remove of patients, queue re-ordering, and re-running of triage logic.
- **🚨 Smart Alert System**: If a patient's condition changes during chatbot conversations (ESI increases/decreases), the system triggers an alert to the nurse with the new recommendation and rationale.
- **📱 Patient View**: Unique links for each patient sent via SMS, allowing patients to update their symptoms in real-time through a chatbot interface.

---

## 🛠️ Tech Stack

### Frontend
- **React** - UI framework
- **Vite** - Build tool
- **React Router** - Navigation
- **Browser Web Speech API** - Voice recognition
- **Vercel** - Hosting

### Backend
- **Python** - Core language
- **Flask** - Web framework
- **Gunicorn** - Production server
- **Render** - Backend hosting

### AI & Agents
- **Claude 3 Haiku (Anthropic)** - Triage assessment and structured data extraction
- **Fetch.AI UAgents** - Smart agent orchestration for data flow
- **ChromaDB** - Vector database for semantic search of patient medical records (HL7 FHIR)

### Integrations
- **Twilio** - SMS communication for patient links and updates

---

## 📁 Project Structure

```
calhacks2025/
├── nurse-ui/              # Frontend React application
│   ├── src/
│   │   ├── pages/        # Page components (Queue, Nurse Form, Patient Chat, etc.)
│   │   ├── components/   # Reusable UI components
│   │   └── utils/        # Utility functions (queue management)
│   └── package.json
│
├── backend/               # Flask backend API
│   ├── app.py            # Main Flask application
│   ├── agents/           # AI agent implementations
│   │   ├── triage.py     # ESI triage logic and prompts
│   │   ├── nurse_agent.py
│   │   └── patient_agent.py
│   └── requirements.txt
│
├── Chromadb_rag/         # ChromaDB integration for patient records
│
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.11 or higher)
- **Anthropic API Key** - Get one at [console.anthropic.com](https://console.anthropic.com)
- **Twilio Account** (for SMS features) - Sign up at [twilio.com](https://www.twilio.com)
- **ChromaDB** (local or cloud instance)

### Frontend Setup

```bash
# Navigate to frontend directory
cd nurse-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_sid_here
TWILIO_AUTH_TOKEN=your_twilio_token_here
TWILIO_PHONE_NUMBER=your_twilio_number_here
CHROMADB_URL=your_chromadb_url_here
EOF

# Run the Flask server
python app.py
```

The backend will be available at `http://localhost:5000`

### Configuration

Update the API base URL in `nurse-ui/src/config.js` if running locally:

```javascript
export const API_BASE_URL = 'http://localhost:5000'  // Local
// or
export const API_BASE_URL = 'https://calhacks2025-ncoi.onrender.com'  // Production
```

---

## 🎮 Usage

### For Nurses

1. **Navigate to Queue Page**: View all patients and their current ESI scores
2. **Add Patient**: Click "Add Patient" to register a new patient
3. **Fill Triage Form**: Enter vitals, symptoms, pain level, and comments
   - **Voice Input**: Click the microphone icon to speak patient information - AI will automatically fill the form
4. **View Dashboard**: See triage assessment results with ESI score and rationale
5. **Respond to Alerts**: When patient conditions change, review and accept/reject ESI updates

### For Patients

1. Receive SMS link with unique patient ID
2. Click link to access patient waiting page
3. Chat with AI assistant to update symptoms
4. View estimated wait time and queue position
5. Receive notifications if triage level changes

---

## 🔍 Key Features Explained

### ESI Triage Scale
The Emergency Severity Index (ESI) is a 5-level triage algorithm:
- **ESI 1**: Resuscitation - Immediate life-saving intervention needed
- **ESI 2**: Emergency - High risk situation, should be seen immediately
- **ESI 3**: Urgent - Multiple resources needed, complex workup
- **ESI 4**: Less Urgent - One resource needed, simple workup
- **ESI 5**: Non-Urgent - No resources needed, simple treatment

### Real-time Alert System
The system continuously monitors patient chatbot conversations. When symptoms change significantly (e.g., pain increases from 3/10 to 9/10), the AI re-evaluates the ESI score and sends an alert to the nurse with:
- Current ESI vs. Suggested ESI
- Brief summary of the change
- Option to accept or reject the update

---

## 🏆 Accomplishments

- ✅ **Fully custom priority queue system** that supports real-time triage reordering
- ✅ **Consistent AI-generated feedback** using advanced prompt engineering and model tuning
- ✅ **Successful integration** of all components (backend, agent, triage logic, frontend) into a cohesive working prototype
- ✅ **Voice-to-form automation** using Claude for structured data extraction
- ✅ **Real-time alert system** for dynamic triage updates

---

## 🧠 Challenges We Faced

- **LiveKit Integration Issues**: Managing rooms, sessions, and audio streaming was complex. We pivoted to Browser Web Speech API for more reliable voice input.
- **Custom Priority Queue**: Ensuring triage scoring and patient order dynamically updated in real-time required careful state management.
- **Prompt Engineering**: Tuning prompts so the AI agent produced stable, actionable outputs each time required extensive iteration.
- **Working with AI Agents**: Learning how to manage message flow, context retention, and error recovery in multi-agent systems.

---

## 🚧 Future Improvements

- [ ] Deploy backend and agent services on secure, scalable cloud infrastructure
- [ ] Integrate live hospital databases to access authentic patient records
- [ ] Fine-tune waiting time predictions using queue length and patient flow analytics
- [ ] Refine chatbot prompts for more empathetic, context-aware responses
- [ ] Expand multilingual and accessibility support
- [ ] Add monitoring dashboards for hospital administrators
- [ ] Implement WebSocket connections for real-time updates (eliminate polling)

---

## 👥 Team

Created for **Cal Hacks 12.0**

- **Maor Barzilay**
- **Hritika Arjunwadkar**
- **Samuel Araya**
- **Ethan Ngo**

---

## 📝 License

This project was created for Cal Hacks 12.0 hackathon. All rights reserved.

---

## 🔗 Links

- **[Live Application](https://calhacks2025-nine.vercel.app/)**
- **[Devpost Submission](https://devpost.com/software/triageflow?ref_content=user-portfolio&ref_feature=in_progress)**
- **Backend API**: `https://calhacks2025-ncoi.onrender.com`

---

**Built with ❤️ at Cal Hacks 12.0**
