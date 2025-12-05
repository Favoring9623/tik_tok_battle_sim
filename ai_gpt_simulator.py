import streamlit as st
import random
import time
import openai

# --- Setup Page ---
st.set_page_config(page_title="AI Battle Simulator", layout="centered")
st.title("🤖 TikTok AI Battle Simulator - GPT Edition")

# --- Session State Setup ---
st.session_state.setdefault("ascended_bonus", False)
st.session_state.setdefault("vote_tally", {})
st.session_state.setdefault("battle_log", [])

# --- GPT-Enhanced AI Decision Making ---
def gpt_decide_action(prompt_context):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a dramatic TikTok battle strategist AI."},
                {"role": "user", "content": prompt_context}
            ]
        )
        action = response.choices[0].message['content'].strip()
        return action
    except Exception as e:
        return f"[GPT ERROR] {e}"

# --- Score Boost in Ascended Form ---
def apply_ascended_behavior(base_score):
    if st.session_state.get("ascended_bonus"):
        boosted = int(base_score * 2.0) + 250
        st.toast(f"🔥 Ascended boost applied: {boosted} points!")
        return boosted
    return base_score

# --- GPT-Driven Lore Narration ---
def generate_battle_lore(log):
    try:
        lore_prompt = "Generate a poetic lore summary of the following TikTok AI battle round log:\n" + "\n".join(log)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a battle chronicler AI that creates dramatic stories."},
                {"role": "user", "content": lore_prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"[LORE ERROR] {e}"

# --- Simulate Battle Round ---
def simulate_battle_round(round_number):
    st.subheader(f"🌀 Battle Round {round_number}")
    base_score = random.randint(100, 500)
    context = f"Round {round_number}. Choose the best action: Mega Gift, Protect Creator, Launch Emote Storm, Taunt Opponent. Base score: {base_score}. Ascended: {st.session_state['ascended_bonus']}"
    ai_action = gpt_decide_action(context)
    boosted_score = apply_ascended_behavior(base_score)

    round_log = f"Round {round_number}: Action={ai_action} | Base={base_score} | Final={boosted_score}"
    st.session_state.battle_log.append(round_log)

    st.write(f"**AI Action:** {ai_action}")
    st.write(f"**Base Score:** {base_score}")
    st.write(f"**Final Score:** {boosted_score}")

# --- Activate Ascension (for testing) ---
if st.button("🚀 Activate Ascended Form"):
    st.session_state["ascended_bonus"] = True
    st.success("AI has entered Ascended Form")

# --- Battle Simulation Loop ---
num_rounds = st.slider("Select Number of Rounds:", 1, 10, 3)
if st.button("▶️ Start Battle Simulation"):
    st.session_state["battle_log"] = []
    for i in range(1, num_rounds + 1):
        simulate_battle_round(i)
        time.sleep(0.5)

# --- Display GPT-Generated Lore ---
if st.session_state.get("battle_log"):
    st.divider()
    st.subheader("📖 Epic Battle Lore")
    lore = generate_battle_lore(st.session_state.battle_log)
    st.markdown(lore)

# --- OpenAI Key Reminder ---
st.info("To run GPT functions, ensure your OpenAI API key is set in your environment.")
