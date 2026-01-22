import os
from dotenv import load_dotenv

def load_gemini_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Authentication Error: Please set the GOOGLE_API_KEY environment variable."
        )
    return api_key


if __name__ == "__main__":
    try:
        load_gemini_api_key()
        print("✅ Gemini API key setup complete.")
    except Exception as exc:
        print(
            "🔑 Authentication Error: Please make sure you have set the "
            f"GOOGLE_API_KEY environment variable. Details: {exc}"
        )
