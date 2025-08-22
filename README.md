# 📉 PAR90 Manager Coaching Trainer

An **AI-powered interactive training module** designed to help branch managers learn about **PAR90**, practice **coaching CSRs**, receive **real-time feedback**, and generate a **SMART action plan** to reduce delinquent loans.

---

## 🚀 Features

- **Learn PAR90**: Understand what PAR90 is, why it matters, and how it affects branch performance.  
- **Coach a CSR**: Simulate realistic coaching conversations with an AI-powered resistant CSR.  
- **Real-Time Feedback**: Get immediate guidance on:
  - Connecting coaching to PAR90 outcomes  
  - Providing specific, actionable guidance  
  - Balancing support and accountability  
- **Generate Action Plan**: Automatically produce a SMART weekly plan based on the conversation.  
- **Interactive & Agentic**: Fully chat-based experience that adapts to manager inputs.  

---

## 🛠️ Tech Stack

- **Streamlit** – Interactive web UI  
- **Groq API** – LLM backend for AI responses  
- **Python 3.10+** – Core logic & utilities  

---

## ⚙️ Setup Instructions

1. **Clone the repo**

```bash
git clone <repo-url>
cd par90-coaching-trainer


2.**Install dependencies**
```bash
 pip install -r requirements.txt

3. **Set Groq API key**
```bash 
export XAI_API_KEY="your_groq_api_key_here"  # Linux/Mac
# OR for Windows PowerShell
setx XAI_API_KEY "your_groq_api_key_here"


3. **Run the app**
```bash 
streamlit run app.py

🧩 Usage

Learn Tab

Read about PAR90 and its impact.

Complete a quick check to reinforce learning.

Coach Tab

Chat with the AI CSR.

Receive real-time feedback on your coaching messages.

Chat is automatically disabled after reaching the turn limit.

Action Plan Tab

Click Generate Action Plan to create a SMART weekly plan.

Download the plan as Markdown for your branch.

⚠️ Notes

Compatible Groq models:

"llama-3.1-8b-instant"

"llama-3.3-70b-versatile"

"openai/gpt-oss-120b"

Groq Base URL: https://api.groq.com/openai/v1

Streamlit: Use st.rerun() instead of st.experimental_rerun.

Message content from LLM: use msg.content, not msg["content"].

📌 Tips

Ensure XAI_API_KEY is set before running.

Adjust turn_limit in the Coach tab slider to control session length.

Use the Reset Conversation button to restart training.

📝 License

This project is for demonstration purposes and internal use only.