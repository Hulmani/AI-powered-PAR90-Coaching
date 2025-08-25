import os
import re
import streamlit as st
import json
from openai import OpenAI
from datetime import datetime

# -------------------- Config --------------------
st.set_page_config(page_title="PAR90 Coaching Trainer", page_icon="📉", layout="wide")

XAI_API_KEY = st.secrets.get("XAI_API_KEY", os.getenv("XAI_API_KEY", ""))  # Grok key
BASE_URL = "https://api.groq.com/openai/v1"
client = OpenAI(api_key=XAI_API_KEY, base_url=BASE_URL) if XAI_API_KEY else None

# -------------------- Content: Learn PAR90 --------------------
PAR_LEARN = """
### What is PAR90?
**PAR90 (Portfolio At Risk 1–90)** is the % of your active loan portfolio that is **past due 1–90 days**.

**Why it matters**
- High PAR90 → cash flow crunch, higher write-offs, lower bonus pool.
- Low PAR90 → stable cash, healthier portfolio, better customer retention.

**How managers move PAR90 (daily behaviors)**
1. **Proactive outreach** on 1–30 DPD (days past due) *before* they age.
2. **Empathy + options** on calls (split/partial payment, promise-to-pay date).
3. **Tight follow-up** (document commitment, confirm next contact time).
4. **Floor coaching** (listen to CSR calls, roleplay phrases, set daily targets).
5. **Same-day action on broken promises** (call back, reset plan).

**Example coaching micro-targets**
- “Every CSR completes **5 delinquency calls** before noon.”
- “Every call ends with **a specific next step** (amount + date).”
- “We log **every promise-to-pay** and follow up **same day** if missed.”
"""

# -------------------- Scenario (CSR role) --------------------
SCENARIO = {
    "name": "CSR mishandled a 45 DPD customer",
    "seed": (
        "You are a CSR who just spoke to a customer 45 days past due on a $600 loan with a $25 late fee. "
        "You told them to 'come back when you have money' and did not offer options. "
        "The user is your Branch Manager coaching you. "
        "Play a **resistant** CSR who makes excuses (busy lobby, customer was angry, etc.). "
        "Keep replies short (1–3 sentences), realistic, and slightly defensive."
    ),
    "context": "Store: Cash 4 You. Objective: improve coaching quality to reduce PAR90 via specific CSR behaviors."
}

# -------------------- System Prompt Builder --------------------
def build_system_prompt(turns_limit: int) -> str:
    return f"""
You are a training simulator for branch **managers coaching CSRs** to reduce PAR90.
- **Stay strictly in character as the CSR** (resistant, but coachable).
- Keep replies brief and natural (1–3 sentences).
- Push back realistically (time pressure, customer anger, 'it won't work').
- After exactly {turns_limit} assistant replies, STOP roleplay and output:
  1) A brief reflection as the CSR (what you'll do differently)
  2) Nothing else (the app will handle the manager-facing feedback)
Scenario: {SCENARIO['name']}
CSR Background: {SCENARIO['seed']}
Context: {SCENARIO['context']}
""".strip()

# -------------------- LLM Call --------------------
def llm_chat(messages, model="llama-3.1-8b-instant", temperature=0.6, max_tokens=1500):
    if not client:
        return {"role": "assistant", "content": "([Demo Mode] Add XAI_API_KEY to enable live conversation.)"}
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message

# -------------------- Rule-based Coaching Heuristics --------------------
EMPATHY_KWS = ["i hear", "i understand", "i’m sorry", "i am sorry", "that sounds", "thanks for", "appreciate"]
OPTIONS_KWS = ["split", "partial", "payment plan", "promise", "pay today", "pay by", "installment"]
PAR_KWS = ["par", "past due", "dpd", "days past due", "roll", "aging"]
FOLLOWUP_KWS = ["next call", "follow", "check in", "by [0-9]{1,2}/[0-9]{1,2}", "by (monday|tuesday|wednesday|thursday|friday)"]

def rb_score(text: str):
    t = text.lower()
    def hit_any(patterns):
        return any((re.search(p, t) if p.startswith("by ") or "[" in p else p in t) for p in patterns)
    s = {
        "Empathy": 1 if hit_any(EMPATHY_KWS) else 0,
        "Specific Options": 1 if hit_any(OPTIONS_KWS) else 0,
        "PAR Connection": 1 if hit_any(PAR_KWS) else 0,
        "Next-Step Clarity": 1 if hit_any(FOLLOWUP_KWS) else 0,
    }
    total = sum(s.values())
    return s, total

# -------------------- LLM Coaching Feedback --------------------
def llm_feedback(convo, last_manager_msg):
    prompt = [
        {"role": "system", "content": "You are a collections performance coach. Be concise, specific, and actionable."},
        {"role": "user", "content":
            f"""
Evaluate the MANAGER's last coaching message to a CSR in a PAR90 context.
Conversation so far (JSON-ish): {convo}
Manager's last message: {last_manager_msg}

Score 0–10 on:
- PAR Connection (did they link behavior -> PAR90 impact?)
- Specificity (did they give concrete behaviors/phrases to use?)
- Coaching Tone (support + accountability)
- Next-Step Clarity (specific amount/date/next action)

Return JSON with fields:
par_connection, specificity, coaching_tone, next_step_clarity, summary, tips (3 bullet tips).
Keep it under 120 words.
"""
        }
    ]
    if not client:
        return {
            "par_connection": 5, "specificity": 5, "coaching_tone": 5, "next_step_clarity": 5,
            "summary": "([Demo Mode]) Add XAI_API_KEY for LLM feedback.", "tips": [
                "Acknowledge the CSR’s effort, then pivot to behaviors.",
                "Offer a concrete script for offering split payments.",
                "Close with a specific next step and time."]
        }
    resp = client.chat.completions.create(model="llama-3.1-8b-instant", messages=prompt, temperature=0.4, max_tokens=1500)
    txt = resp.choices[0].message.content
    # Best-effort JSON scrape
    import json
    try:
        return json.loads(txt)
    except Exception:
        # Fallback: heuristic parse
        return {
            "par_connection": 6, "specificity": 6, "coaching_tone": 6, "next_step_clarity": 6,
            "summary": txt[:1500],
            "tips": ["Link behavior to PAR90.", "Give exact words to try.", "Set a specific next step."]
        }

# -------------------- Action Plan --------------------
def generate_action_plan(convo):
    prompt = [
        {"role": "system", "content": "You are a branch operations coach. Output a concise action plan only."},
        {"role": "user", "content":
            f"""
From this manager↔CSR coaching conversation, produce a 5-step SMART action plan for reducing PAR90 **this week**.
Each step should be concrete, measurable, and time-bound. Keep it under 120 words.
Conversation: {convo}
"""
        }
    ]
    with st.spinner("Waiting for CSR response..."):
        msg = llm_chat(prompt, temperature=0.4, max_tokens=1500)
    return msg.content

# -------------------- State --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []   # chat history
if "assistant_count" not in st.session_state:
    st.session_state.assistant_count = 0
if "feedback_blocks" not in st.session_state:
    st.session_state.feedback_blocks = []  # list of (timestamp, rb, rb_total, llm_json)
if "action_plan" not in st.session_state:
    st.session_state.action_plan = None

# -------------------- UI --------------------
st.title("📉 PAR90 Manager Coaching Trainer")
st.caption("Teach managers what PAR90 is, simulate coaching, give feedback, and produce a branch action plan.")

tab_learn, tab_coach, tab_plan = st.tabs(["📘 Learn PAR90", "🗣️ Coach a CSR", "📝 Action Plan"])

# ---- Learn Tab ----
with tab_learn:
    st.markdown(PAR_LEARN)
    with st.expander("Quick Check: Can you spot the PAR mover?", expanded=False):
        st.write("A CSR finishes a call with a 38 DPD customer and schedules a generic 'follow up next week'. What’s missing?")
        a = st.radio("Pick one", ["Empathy", "Specific option (amount/date)", "Coaching tone", "Nothing missing"], index=1)
        if st.button("Check"):
            if a == "Specific option (amount/date)":
                st.success("Correct: without a concrete amount/date, there’s no commitment to move PAR.")
            else:
                st.warning("Not quite. The biggest gap is the lack of a concrete amount/date commitment.")

# ---- Coach Tab ----
with tab_coach:
    left, right = st.columns([0.6, 0.4])

    with left:
        st.subheader("Roleplay: You are the Branch Manager (AI is the CSR)")
        turn_limit = st.slider("Assistant replies before CSR reflection", 3, 7, 5, 1)
        model_name = st.selectbox("Model", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"], index=0)
        if st.button("🔄 Reset Conversation"):
            st.session_state.messages = []
            st.session_state.assistant_count = 0
            st.session_state.feedback_blocks = []
            st.session_state.action_plan = None
            st.rerun()

        # Ensure system prompt present
        if not any(m for m in st.session_state.messages if m["role"] == "system"):
            st.session_state.messages.insert(0, {"role": "system", "content": build_system_prompt(turn_limit)})

        # Render chat
        chat_box = st.container()
        with chat_box:
            for m in st.session_state.messages:
                if m["role"] == "user":
                    with st.chat_message("user"): st.markdown(m["content"])
                elif m["role"] == "assistant":
                    with st.chat_message("assistant"): st.markdown(m["content"])

        user_input = st.chat_input("Coach your CSR… (e.g., acknowledge, offer options, set next step)")
        if user_input:
            # Append manager message
            st.session_state.messages.append({"role": "user", "content": user_input})

            # --- Real-time rule-based feedback on the manager message ---
            rb_detail, rb_total = rb_score(user_input)

            # --- LLM qualitative scoring/feedback (manager-facing) ---
            convo_snapshot = st.session_state.messages[-10:]  # keep short
            fb = llm_feedback(convo_snapshot, user_input)
            st.session_state.feedback_blocks.append(
                (datetime.now().isoformat(), rb_detail, rb_total, fb)
            )

            # Continue roleplay or force CSR reflection
            if st.session_state.assistant_count >= turn_limit - 1:
                st.session_state.messages.append({"role": "user", "content": "CSR: Please provide your brief reflection now."})
            with st.spinner("Waiting for CSR response..."):
                msg = llm_chat(st.session_state.messages, model=model_name)
            st.session_state.messages.append({"role": "assistant", "content": msg.content})
            st.session_state.assistant_count += 1
            st.rerun()

    with right:
        st.subheader("Real-time Feedback")
        if not st.session_state.feedback_blocks:
            st.info("Your coaching feedback will appear here after you send a message.")
        else:
            for ts, rb, rb_total, fb in reversed(st.session_state.feedback_blocks[-5:]):
                st.markdown(f"**Assessment at {ts.split('T')[1][:8]}**")
                cols = st.columns(4)
                cols[0].metric("Empathy", "✅" if rb["Empathy"] else "—")
                cols[1].metric("Specific Options", "✅" if rb["Specific Options"] else "—")
                cols[2].metric("PAR Connection", "✅" if rb["PAR Connection"] else "—")
                cols[3].metric("Next-Step Clarity", "✅" if rb["Next-Step Clarity"] else "—")
                st.progress(rb_total / 4.0)
                try:
                    cols2 = st.columns(4)
                    cols2[0].metric("PAR Conn (0-10)", fb.get("par_connection", 0))
                    cols2[1].metric("Specificity", fb.get("specificity", 0))
                    cols2[2].metric("Tone", fb.get("coaching_tone", 0))
                    cols2[3].metric("Next Step", fb.get("next_step_clarity", 0))
                except Exception:
                    pass
            
                raw_summary = fb.get("summary", "")
                tips = fb.get("tips", [])
                try:
                    # Clean up markdown code blocks if present
                    clean_summary = raw_summary.strip()
                    if clean_summary.startswith("```json"):
                        clean_summary = clean_summary[7:]  # Remove ```json
                    if clean_summary.startswith("```"):
                        clean_summary = clean_summary[3:]   # Remove ```
                    if clean_summary.endswith("```"):
                        clean_summary = clean_summary[:-3]  # Remove trailing ```
                    clean_summary = clean_summary.strip()
                    
                    parsed = json.loads(clean_summary)
                    summary_text = parsed.get("summary", raw_summary)
                    tips = parsed.get("tips", tips)  # Also extract tips from JSON
                except Exception as e:
                    print(f"JSON parsing error: {e}")  # Debug
                    summary_text = "Parsing error from server response. Please check the input format."

                if summary_text:
                    st.markdown(f"**Summary:** {summary_text}")
                if tips and isinstance(tips, list):
                    st.markdown("**Tips:**")
                    for tip in tips:
                        st.markdown(f"- {tip}")
                st.markdown("---")


        # Generate Action Plan Button
        if st.button("📝 Generate Action Plan from Conversation"):
            convo_snapshot = st.session_state.messages
            st.session_state.action_plan = generate_action_plan(convo_snapshot)
            st.success("Action plan generated. Check the Action Plan tab.")

# ---- Action Plan Tab ----
with tab_plan:
    st.subheader("Branch Action Plan (SMART)")
    if st.session_state.action_plan:
        st.markdown(st.session_state.action_plan)
        md = f"# PAR90 Weekly Action Plan\n\nGenerated: {datetime.now().isoformat()}\n\n{st.session_state.action_plan}\n"
        st.download_button("⬇️ Download as Markdown", md, file_name="PAR90_Action_Plan.md")
    else:
        st.info("Generate an action plan from the Coach tab after a short conversation.")
