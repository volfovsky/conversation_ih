import openai
import streamlit as st

# Set your OpenAI API key securely (e.g., from Streamlit Secrets).
# In Streamlit Cloud, go to Settings -> Secrets to add "OPENAI_API_KEY"
openai.api_key = st.secrets["OPENAI_API_KEY"]

# -- Helper Functions --

def get_assistant_message(conversation_history):
    """
    Takes a conversation history list of dicts:
      [ {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ... ]
    Returns the assistant's response from the ChatCompletion API.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        temperature=0.9,  # a bit of creativity
    )
    return response["choices"][0]["message"]["content"]

def analyze_humility(conversation_history):
    """
    After a certain number of user messages, we call GPT again to do
    an 'intellectual humility assessment' based on the entire conversation.
    """
    analysis_system_prompt = {
        "role": "system",
        "content": (
            "You are an expert psychologist asked to analyze a conversation. "
            "You will be given the entire conversation between the user and the assistant. "
            "Please produce an 'intellectual humility' assessment of the user, "
            "from 1 (low humility) to 10 (high humility), along with a short explanation."
        )
    }

    # We’ll feed the entire conversation as context, plus the system instruction above.
    # We'll turn the conversation into a single 'user' message so the model can see it in one shot.
    conversation_text = []
    for turn in conversation_history:
        # We'll label user vs. assistant to provide clarity
        speaker = turn["role"]
        content = turn["content"]
        conversation_text.append(f"{speaker.upper()}:\n{content}\n")

    full_conversation_string = "\n".join(conversation_text)
    user_message = {
        "role": "user",
        "content": f"Here is the conversation:\n\n{full_conversation_string}\n\nPlease provide your analysis now."
    }

    # Build the messages for the analysis request
    analysis_messages = [analysis_system_prompt, user_message]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=analysis_messages,
        temperature=0.0  # keep analysis deterministic
    )
    return response["choices"][0]["message"]["content"].strip()

# -- Streamlit App --

def main():
    st.title("Fun & Inquisitive Chatbot — Intellectual Humility Assessment")
    st.write("""
    This chatbot loves to ask fun, inquisitive questions about how you and your friends chat.
    After a short conversation (5–10 user messages), the bot will produce an
    'Intellectual Humility' assessment of you!
    """)

    # Initialize conversation in session state
    if "conversation_history" not in st.session_state:
        st.session_state["conversation_history"] = [
            {
                "role": "system",
                "content": (
                    "You are a fun, inquisitive chatbot. "
                    "Your personality is playful, curious, and friendly. "
                    "You love asking about what the user likes to talk about with friends, "
                    "how they react to disagreements on mundane topics (sports, art, restaurants) "
                    "and heavier topics (politics), etc. "
                    "After about 5–10 user messages, you will politely wrap up and attempt to end "
                    "the conversation so that an 'intellectual humility' analysis can be performed. "
                    "Try to keep the conversation going for at least 5 user messages before ending."
                )
            }
        ]

    # Show the chat history
    for turn in st.session_state["conversation_history"]:
        if turn["role"] == "assistant":
            st.markdown(f"**Chatbot**: {turn['content']}")
        elif turn["role"] == "user":
            st.markdown(f"**You**: {turn['content']}")

    user_input = st.text_input("Type your message here and press Enter:")

    if user_input:
        # Append user's message
        st.session_state["conversation_history"].append({"role": "user", "content": user_input})

        # Get assistant reply
        assistant_reply = get_assistant_message(st.session_state["conversation_history"])
        st.session_state["conversation_history"].append({"role": "assistant", "content": assistant_reply})

        # Re-render
        # st.experimental_rerun()
        st.cache_data.clear()

    # Check how many times the user has spoken
    user_turns = sum(1 for x in st.session_state["conversation_history"] if x["role"] == "user")

    # If the user has spoken at least 5 times and the assistant's last message
    # suggests it's time to wrap up, or user_turns > 10, do analysis
    if user_turns >= 5:
        # Provide a button to finalize
        st.write("---")
        if st.button("Get my Intellectual Humility assessment now!"):
            st.write("Analyzing your conversation for intellectual humility...")
            analysis = analyze_humility(st.session_state["conversation_history"])
            st.success("Analysis Complete!")
            st.markdown(f"**Your Intellectual Humility Assessment**:\n\n{analysis}")

            st.write("Thank you for chatting! If you'd like to start over, just reload the page.")

if __name__ == "__main__":
    main()
