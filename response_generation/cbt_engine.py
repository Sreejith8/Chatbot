import random
import re

class CBTEngine:
    def __init__(self):
        # 1. Richer Templates categorized by 'Strategy'
        self.templates = {
            "Depression": {
                "Validation": [
                    "It sounds like you're carrying a very heavy burden right now.",
                    "It is completely understandable that you feel drained. Depression can be exhausting.",
                    "I hear meaningful pain in your words. You are not alone in this.",
                ],
                "Questioning": [
                    "When you feel this low, what does your inner voice tend to say to you?",
                    "Have you felt this way before? If so, what helped you get through it then?",
                    "Is there one small thing, no matter how tiny, that you can control right now?",
                ],
                "Coping": [
                    "Sometimes, just getting through the next hour is enough. Let's focus on that.",
                    "Let's try a 'micro-step'. What is one simple act of self-care you can do in the next 5 minutes?",
                    "Physical movement can sometimes shift mental states. Could you try stretching for 30 seconds?",
                ]
            },
            "Anxiety": {
                "Validation": [
                    "It sounds like your mind is racing right now.",
                    "That feeling of impending worry is so tough to sit with. I'm here with you.",
                    "It makes sense that you're anxious given the uncertainty.",
                ],
                "Questioning": [
                    "What is the 'worst case' story your anxiety is telling you right now?",
                    "If a friend felt this way, what comforting words would you offer them?",
                    "Is this worry about something happening right now, or something in the future?",
                ],
                "Coping": [
                    "Let's try the 5-4-3-2-1 technique. Can you name 5 things you can see?",
                    "Take a deep breath. Inhale for 4, hold for 7, exhale for 8. Let's do it together.",
                    "Try to 'ground' yourself. Feel your feet on the floor. You are safe in this moment.",
                ]
            },
            "Sadness": {
                "Validation": [
                    "It feels really heavy right now, doesn't it?",
                    "Sorrow is a valid and human emotion. You don't have to 'fix' it immediately.",
                    "I'm really sorry you're going through this. It sounds painful.",
                ],
                "Questioning": [
                    "What do you think is at the heart of this sadness today?",
                    "Does this sadness feel like it's about a specific event, or a general feeling?",
                ],
                "Coping": [
                    "Being kind to yourself is vital now. Can you wrap yourself in a warm blanket?",
                    "Sometimes a good cry is exactly what the body needs to release stress.",
                ]
            },
            "Stress": {
                "Validation": [
                    "It sounds like you have an immense amount of pressure on you.",
                    "That sounds incredibly draining. No wonder you are feeling stressed.",
                ],
                "Questioning": [
                    "If you could take just one task off your plate today, which one would it be?",
                    "What is the most pressing thing causing this stress right now?",
                ],
                "Coping": [
                    "Let's just pause. Take one deep breath. The world can wait for 30 seconds.",
                    "Breaking things down helps. What is the very first, smallest step you can take?",
                ]
            },
             "Normal": {
                "Validation": [
                    "I'm glad to hear you're doing okay!", 
                    "It sounds like things are relatively stable for you right now."
                ],
                "Questioning": [
                    "What's been the highlight of your day so far?",
                    "Is there anything on your mind you'd like to explore?"
                ],
                "Coping": []
            },
             "High_Risk": {
                "Validation": [
                    "I am very concerned about what you're sharing.",
                    "Your safety is the most important thing to me right now."
                ],
                "Questioning": [],
                "Coping": [
                    "Please reach out to a professional immediately. Here is a helpline: 988.",
                    "Please contact emergency services or a trusted person right now."
                ]
            }
        }
        
        # 2. Keyword Triggers for specific topics
        self.topics = {
            r"\b(exam|test|study|grade|fail)\b": "It sounds like academic pressure is weighing on you. Remember, a grade does not define your worth.",
            r"\b(job|work|boss|career)\b": "Work stress can be all-consuming. Are you able to set any boundaries today?",
            r"\b(lonely|alone|isolated)\b": "Loneliness is a universal human feeling, but it hurts deeply. Connection starts with small steps.",
            r"\b(sleep|tired|insomnia)\b": "Rest is foundational to mental health. Have you been sleeping okay lately?",
            r"\b(breakup|ex|relationship|sad)\b": "Heartbreak is a unique kind of grief. Be gentle with yourself.",
            r"\b(die|kill|suicide|end it)\b": "RISK_TRIGGER"
        }

    def get_cbt_response(self, state, risk_level, conversation_history=None, user_input=None):
        """
        Sophisticated Rule-Based Response Generation
        """
        # 1. Immediate Safety Override
        if risk_level == "High":
             return random.choice(self.templates["High_Risk"]["Validation"] + self.templates["High_Risk"]["Coping"])
             
        # 2. Topic/Keyword Reflection (Simulated Empathy)
        if user_input:
            user_input_lower = user_input.lower()
            for pattern, topic_response in self.topics.items():
                if re.search(pattern, user_input_lower):
                    if topic_response == "RISK_TRIGGER":
                        return random.choice(self.templates["High_Risk"]["Coping"])
                    return f"{topic_response} {random.choice(self.templates.get(state, self.templates['Normal'])['Questioning'])}"

        # 3. State-Based Selection Strategy
        # If we have history, we can try to vary the strategy (Validation -> Questioning -> Coping)
        strategy = "Validation" # Default start
        
        if conversation_history and len(conversation_history) > 0:
            # Check length of conversation about this state
            # Simple heuristic: longer convo -> move to Coping
            if len(conversation_history) > 4:
                strategy = "Coping"
            elif len(conversation_history) > 2:
                strategy = "Questioning"
                
        # Fallback if specific lists empty
        try:
            choices = self.templates.get(state, self.templates["Normal"]).get(strategy)
            if not choices:
                # Fallback to Validation if Coping/Questioning empty
                choices = self.templates.get(state, self.templates["Normal"]).get("Validation")
            if not choices:
                 # Absolute fallback
                 return "I'm here for you. How can I help?"
                 
            base_response = random.choice(choices)
            
            # Add lightweight reflection if possible?
            # "It sounds like you're anxious."
            return base_response
            
        except Exception as e:
            print(f"CBT Error: {e}")
            return "I am listening. Please go on."
