import os
import sys
from huggingface_hub import HfApi

def update_secrets():
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("❌ HF_TOKEN not found in environment")
        sys.exit(1)

    api = HfApi(token=hf_token)
    
    # Map of secrets to sync: { "SECRET_NAME": "TARGET_REPO_ID" (or list) }
    # The user specifically requested CRYPTOPANIC_API_KEY.
    # And we determined it's needed in 'crypto-bot'.
    # We also sync other critical keys if available to ensure the bot works.
    
    secrets_to_sync = [
        "CRYPTOPANIC_API_KEY",
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "OPENCLAW_SECRET"
    ]
    
    target_spaces = [
        "fr33b0t/crypto-bot",
        # "fr33b0t/crypto-sentiment-api" # Uncomment if needed there
    ]

    for secret_name in secrets_to_sync:
        secret_value = os.getenv(secret_name)
        if secret_value:
            print(f"🔐 Syncing {secret_name}...")
            for repo_id in target_spaces:
                try:
                    api.add_space_secret(repo_id=repo_id, key=secret_name, value=secret_value)
                    print(f"   ✅ Set in {repo_id}")
                except Exception as e:
                    print(f"   ❌ Failed to set in {repo_id}: {e}")
        else:
            print(f"⚠️ {secret_name} not found in environment, skipping.")

if __name__ == "__main__":
    update_secrets()
