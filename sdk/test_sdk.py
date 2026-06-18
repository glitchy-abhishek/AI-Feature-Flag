from client import AIFlagClient
import time

client = AIFlagClient()
user_input = "Write a python script to reverse a string."

print("--- 🚨 INITIATING DEGRADATION TEST 🚨 ---")
print("Simulating 3 bad experimental responses in a row...")

# We will simulate 3 different users who all magically got the experimental prompt
test_users = ["user_x", "user_y", "user_z"]

for user in test_users:
    # Simulating a catastrophic hallucination from the new GPT-4 prompt
    bad_ai_response = "Error 500: I refuse to answer this. It is too hard."
    
    print(f"\nLogging bad response for {user}...")
    client.log_interaction(
        flag_name="new-aggressive-prompt",
        user_id=user,
        variant_served="experimental", # Forcing experimental for the test
        user_input=user_input,
        ai_response=bad_ai_response
    )
    
    # Wait 2 seconds between logs to let the backend judge grade them
    time.sleep(2) 

print("\nFinished sending bad traffic.")
print("Now we will test what happens to the NEXT user who logs in...")
time.sleep(3) # Give the backend a moment to execute the rollback

# Now, a completely new user logs in. 
# Even if their hash says they SHOULD get the experimental prompt, 
# the kill switch should have triggered and forced them to Baseline.
new_user = "user_dave" # Dave got experimental in our very first test
result = client.evaluate("new-aggressive-prompt", new_user, {"system_prompt": "fallback"})

print(f"\nResult for {new_user} after rollback:")
print(f"Served Variant: {result['variant'].upper()}")