import os
import time
from supabase import create_client, Client
from dotenv import load_dotenv
import anthropic

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
CLAUDE_API_KEY = os.environ["ANTHROPIC_API_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# ---------------------------------------------------------------------
# AI Summarization Function
# ---------------------------------------------------------------------

def summarize_text(text: str, name: str) -> str:
    prompt = f"""
    You are creating a compelling investment pitch for "{name}" in a Tinder-style investing app.

    Write a punchy, engaging 100-word summary that makes investors want to swipe right. 

    Focus on:
    - What they do (in simple terms)
    - Why they matter (market position, competitive edge)
    - The opportunity (growth potential, sector trends)

    Style guidelines:
    - Start with a hook that captures attention
    - Use active, confident language
    - Make it scannable (2-3 short paragraphs or clear sentences)
    - Avoid jargon - write like you're explaining to a smart friend
    - End with momentum/forward-looking statement

    Company: {name}
    Raw Description:
    {text}
    """
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    
    return response.content[0].text.strip()

# ---------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------

def summarize_missing_stocks():
    print("Fetching stocks with missing AI summaries...")
    
    data = (
        supabase.table("stocks")
        .select("id, name, description")
        .is_("summary_ai", "null")
        .execute()
    ).data

    print(f"Found {len(data)} stocks to summarize.")

    for stock in data:
        desc = stock["description"]
        name = stock["name"]

        if not desc:
            print(f"Skipping {name} — no description found.")
            continue

        print(f"Summarizing: {name}...")
        try:
            summary = summarize_text(desc, name)
            supabase.table("stocks").update({"summary_ai": summary}).eq("id", stock["id"]).execute()
            print(f"✅ Saved summary for {name}")
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")
            continue

        # Rate limit: wait 1 second between API calls to avoid hitting rate limits
        time.sleep(1)

    print("✨ Done updating all summaries!")

if __name__ == "__main__":
    summarize_missing_stocks()
