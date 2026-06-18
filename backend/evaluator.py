import time
import random

def evaluate_ai_response(user_input: str, ai_response: str) -> dict:
    """
    Simulates an LLM-as-a-Judge. 
    In production, this would send the input/response to GPT-4 
    and ask it to grade the quality from 1 to 5.
    """
    print(f"🔍 LLM Judge analyzing response to: '{user_input}'...")
    
    # Simulate the network delay of an LLM API call
    time.sleep(1) 
    
    # Simple mock logic to simulate a real judge:
    # If the AI gives a lazy/short answer or an error, it gets a bad score.
    if len(ai_response) < 15 or "error" in ai_response.lower() or "i don't know" in ai_response.lower():
        score = random.uniform(1.0, 2.5)
        reason = "Response was unhelpful, too brief, or indicated failure."
    else:
        # Otherwise, it gets a passing grade
        score = random.uniform(3.8, 5.0)
        reason = "Response was detailed, relevant, and helpful."

    rounded_score = round(score, 1)
    print(f"✅ Judge awarded score: {rounded_score}/5.0")
    
    return {
        "score": rounded_score,
        "reasoning": reason
    }