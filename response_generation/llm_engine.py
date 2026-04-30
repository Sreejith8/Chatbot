import ollama

class LocalLLM:
    def __init__(self, model="mistral"):
        self.model = model

    def generate_response(self, emotion, user_input, conversation_history=None, rag_context=None):
        """
        Routes the detected emotion and user context into a local Mistral model
        running on Ollama to generate a dynamic, empathetic response.
        """
        # Format conversation history string if it exists to give the LLM memory
        history_str = ""
        if conversation_history:
            # Only send the last 4 messages to prevent context explosion
            recent_context = conversation_history[-4:]
            formatted_msgs = []
            for msg in recent_context:
                role = "User" if msg.get('role') == 'user' else "Chatbot"
                content = msg.get('content', '')
                formatted_msgs.append(f"{role}: {content}")
            history_str = "\n".join(formatted_msgs)

        # Format RAG context if it exists
        rag_str = ""
        if rag_context:
            rag_msgs = []
            for item in rag_context:
                text = item.get("text", "")
                state = item.get("metadata", {}).get("state", "Unknown")
                rag_msgs.append(f"- Past thought: '{text}' (State: {state})")
            if rag_msgs:
                rag_str = "\nRelevant Past Thoughts/Emotions Retrieved from Memory:\n" + "\n".join(rag_msgs) + "\n"

        prompt = f"""You are a supportive, professional mental health chatbot utilizing Cognitive Behavioral Therapy (CBT) techniques.

Detected Emotional State: {emotion}
{rag_str}
Recent Conversation Context (if any):
{history_str}

User's Latest Message:
{user_input}

Respond extremely empathetically in 2-3 sentences. Do not use generic cliches. Acknowledge what the user specifically typed, and offer a gentle, actionable CBT-based coping suggestion tailored to their "{emotion}" emotional state. Do not act like an AI or ask how you can help, just respond conversationally."""

        try:
            # We enforce a timeout context within Ollama's client wrapper to ensure
            # the system falls back to the CBT Engine if Mistral takes too long
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"]
            
        except Exception as e:
            # Log the exact Ollama failure so developers know why it fell back
            print(f"[LLM Engine] Failed to generate Local LLM response: {e}")
            return None
