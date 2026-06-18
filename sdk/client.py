import hashlib
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIFlagClient")

class AIFlagClient:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self._cache = {} 

    def _get_consistent_hash(self, flag_name: str, user_id: str) -> int:
        hash_key = f"{flag_name}-{user_id}"
        hash_int = int(hashlib.md5(hash_key.encode('utf-8')).hexdigest(), 16)
        return hash_int % 100

    def get_flag_config(self, flag_name: str):
        try:
            response = requests.get(f"{self.api_url}/flags/")
            response.raise_for_status()
            flags = response.json()
            for flag in flags:
                if flag["name"] == flag_name:
                    self._cache[flag_name] = flag 
                    return flag
        except requests.RequestException:
            pass
        return self._cache.get(flag_name)

    def evaluate(self, flag_name: str, user_id: str, default_fallback: dict):
        """Returns both the variant name AND the config."""
        flag = self.get_flag_config(flag_name)
        
        if not flag:
            return {"variant": "baseline", "config": default_fallback}

        is_active = flag.get("is_active", True)
        rollback_triggered = flag.get("rollback_triggered", False)

        if not is_active or rollback_triggered:
            return {"variant": "baseline", "config": flag.get("baseline_config", default_fallback)}

        user_hash = self._get_consistent_hash(flag_name, user_id)
        rollout_percent = flag.get("rollout_percentage", 0)
        
        if user_hash < rollout_percent:
            return {"variant": "experimental", "config": flag.get("experimental_config", default_fallback)}
        else:
            return {"variant": "baseline", "config": flag.get("baseline_config", default_fallback)}

    def log_interaction(self, flag_name: str, user_id: str, variant_served: str, user_input: str, ai_response: str):
        """Sends the AI interaction to the backend for asynchronous grading."""
        try:
            payload = {
                "flag_name": flag_name,
                "user_id": user_id,
                "variant_served": variant_served,
                "user_input": user_input,
                "ai_response": ai_response
            }
            response = requests.post(f"{self.api_url}/log_interaction/", json=payload, timeout=2)
            response.raise_for_status()
            logger.info(f"Interaction logged for {user_id}. Background grading started.")
        except requests.RequestException as e:
            logger.error(f"Failed to log interaction: {e}")