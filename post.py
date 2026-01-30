import os
import random
import requests
from datetime import date

# ================== ENV ==================
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

GROQ_HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# ================== CONTENT ENGINE CONFIG ==================
TOPIC_BANK = {
    "AWS/Cloud": [
        "IAM policies that look right but still fail",
        "VPC route tables: the one line that breaks everything",
        "Security Groups vs NACLs: what actually blocks traffic",
        "S3 lifecycle rules that actually save money",
        "RDS connection limits and why apps crash",
        "CloudFront cache invalidation gotchas",
        "ALB health checks: why instances look healthy but aren't",
        "ECS task networking pitfalls (awsvpc vs bridge)",
        "Lambda timeouts and hidden cold start causes",
        "CloudWatch alarms that saved me from silent failures"
    ],
    "Microservices/Backend": [
        "Why I split one service into three (and when not to)",
        "API gateway rate limits that broke my mobile app",
        "Idempotency keys: small detail, huge impact",
        "Retries vs timeouts: the failure mode nobody expects",
        "Schema migration strategy that didn't break production",
        "Message queues: when async actually makes things worse"
    ],
    "DevOps/Infra": [
        "CI caching: the 1-line change that cut build time",
        "Secrets in CI: safer than env vars (if you do this)",
        "Docker build layers: why your image is huge",
        "Health checks: what to probe and what NOT to",
        "Blue/green deploys: the simple way without fancy tools"
    ],
    "Tools & Tips": [
        "3 AWS CLI flags I use every day",
        "My default CloudWatch dashboard setup",
        "Naming conventions that keep infra sane",
        "The one logging mistake that hides real errors",
        "How I document architecture so future me survives"
    ]
}

VOICES = [
    {
        "name": "The Analyst",
        "instruction": "Calm and structured. Focus on clarity and trade-offs."
    },
    {
        "name": "The Builder",
        "instruction": "Hands-on and practical. Focus on what worked in real setups."
    },
    {
        "name": "The Skeptic",
        "instruction": "Question common advice. Use a respectful contrarian angle."
    },
    {
        "name": "The Debugger",
        "instruction": "Focused on fixing real issues. Explain the root cause."
    }
]

STRUCTURES = [
    "Story: Hook -> Context -> Insight -> Example -> Tip",
    "List: Hook -> 3 bullets -> Practical tip",
    "Comparison: A vs B -> When to use -> Tip",
    "Myth-bust: Common belief -> Reality -> Example -> Tip",
    "Problem/Solution: Problem -> Fix -> Why it works -> Tip"
]

category = random.choice(list(TOPIC_BANK.keys()))
topic = random.choice(TOPIC_BANK[category])
voice = random.choice(VOICES)
structure = random.choice(STRUCTURES)

print(f"Generating:\n- Category: {category}\n- Topic: {topic}\n- Voice: {voice['name']}\n- Structure: {structure}")

# ================== LLM PROMPT ==================
prompt = f"""
Write a technical LinkedIn post about: "{topic}" (Category: {category}).

VOICE/TONE: {voice['name']} -> {voice['instruction']}
STRUCTURE: {structure}

STORYTELLING (light, not personal):
- Include a short technical scenario (1-2 sentences max)
- No personal life details or emotions
- Avoid repetitive phrases like "I was confused" or "spent hours"
- Keep it professional and focused on the technical lesson

CONTENT (200-300 words):
- Hook that feels fresh (varied style)
- One non-obvious technical insight or gotcha
- Practical example (CLI command, config snippet, or architecture choice)
- Why it matters in real systems
- One actionable tip

FORMATTING:
- Short paragraphs
- Blank line between paragraphs
- Use bullets if listing (max 3)
- Code block for commands

HOOK IDEAS (rotate styles):
- Technical scenario: "While configuring X, this broke..."
- Before/after: "I used to do X. Now I do Y."
- Common mistake: "Most people get X wrong. Here's why."
- Discovery: "Found out Y when testing Z."
- Comparison: "X vs Y. Here's the practical difference."

Avoid fluff. Keep it technical, readable, and lightly story-driven.
"""

# ================== GROQ API CALL ==================
groq_payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": "You write concise, technical posts for developers. Avoid fluff and personal life details."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7
}

try:
    groq_response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=GROQ_HEADERS,
        json=groq_payload,
        timeout=30
    )
    
    # Log response details if error
    if groq_response.status_code != 200:
        print(f"Groq API error details: {groq_response.text}")
    
    groq_response.raise_for_status()
    
    response_data = groq_response.json()
    
    # Validate response structure
    if "choices" not in response_data or len(response_data["choices"]) == 0:
        print(f"Error: Groq API returned invalid structure: {response_data}")
        exit(1)
    
    generated_post = response_data["choices"][0]["message"]["content"]
    
    # Validate content quality
    word_count = len(generated_post.split())
    
    if word_count < 150:
        print(f"Warning: Generated post is short ({word_count} words)")
    if word_count > 400:
        print(f"Warning: Generated post is long ({word_count} words)")
    
    print(f"✓ Content generated successfully ({word_count} words)")
    
except requests.exceptions.Timeout:
    print("Error: Groq API request timed out")
    exit(1)
except requests.exceptions.RequestException as e:
    print(f"Error: Groq API request failed: {e}")
    exit(1)
except (KeyError, IndexError) as e:
    print(f"Error: Failed to parse Groq response: {e}")
    exit(1)

# ================== IMAGE URL ==================
# Use shields.io badges by category for clean, consistent visuals
badge_colors = {
    "AWS/Cloud": "232F3E",
    "Microservices/Backend": "4B7BEC",
    "DevOps/Infra": "20BF6B",
    "Tools & Tips": "F39C12"
}

color = badge_colors.get(category, "4B7BEC")
sanitized_category = category.replace(" ", "%20").replace("&", "%26").replace("/", "%2F")
image_url = f"https://img.shields.io/badge/{sanitized_category}-Tech-{color}?style=for-the-badge&logo=github&logoColor=white"
print(f"✓ Using badge for category: {category}")

# ================== PUSH TO NOTION ==================
# Notion rich_text has 2000 char limit per block, split if needed
post_chunks = [generated_post[i:i+1900] for i in range(0, len(generated_post), 1900)]
post_rich_text = [{"text": {"content": chunk}} for chunk in post_chunks]

payload = {
    "parent": {"database_id": DATABASE_ID},
    "properties": {
        "Topic": {"title": [{"text": {"content": topic}}]},
        "Date": {"date": {"start": str(date.today())}},
        "Post": {"rich_text": post_rich_text},
        "Hashtags": {"rich_text": [{"text": {"content": "#AWS #CloudComputing #DevOps #LearningInPublic"}}]},
        "Image": {"url": image_url},
        "Status": {"select": {"name": "Draft"}}
    }
}

try:
    notion_response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=10
    )
    notion_response.raise_for_status()
    
    response_json = notion_response.json()
    page_url = response_json.get("url")
    page_id = response_json.get("id")
    
    print(f"✓ Post successfully pushed to Notion: {topic}")
    print(f"Status: {notion_response.status_code}")
    if page_url:
        print(f"Page URL: {page_url}")
    if page_id:
        print(f"Page ID: {page_id}")
    
except requests.exceptions.RequestException as e:
    print(f"Error pushing to Notion: {e}")
    print(f"Response: {notion_response.text if 'notion_response' in locals() else 'No response'}")
    exit(1)
