import os
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

# ================== 30-DAY AWS ROADMAP ==================
AWS_TOPICS = [
    # Week 1: AWS Fundamentals
    "AWS account setup and security best practices from day one",
    "AWS regions, availability zones, and how to choose the right one",
    "IAM: users, roles, and policies explained with real examples",
    "Common IAM security mistakes that expose your AWS account",
    "AWS shared responsibility model: what you own vs what AWS owns",
    "AWS Free Tier: what's actually free and the hidden costs",
    "AWS pricing models: On-Demand, Reserved, Spot explained",

    # Week 2: Compute Services
    "What really happens when you launch an EC2 instance",
    "EC2 instance types: how to pick between T2, M5, C5, R5",
    "AWS Lambda fundamentals: when serverless makes sense",
    "Lambda cold starts: why they happen and when they matter",
    "Auto Scaling Groups: scaling based on actual traffic patterns",
    "ECS vs EKS vs Fargate: choosing containers on AWS",
    "EC2 vs Lambda vs Fargate: decision framework",

    # Week 3: Networking
    "VPC explained from scratch: subnets, CIDR, and isolation",
    "Public vs private subnets: the routing difference",
    "Internet Gateway vs NAT Gateway: when to use each",
    "Security Groups vs NACLs: stateful vs stateless filtering",
    "Application Load Balancer vs Network Load Balancer",
    "Route53 basics: DNS routing policies explained",
    "CloudFront CDN: when caching at the edge matters",

    # Week 4: Storage & Databases
    "S3 storage classes: Standard vs IA vs Glacier vs Deep Archive",
    "EBS vs EFS vs S3: choosing the right storage type",
    "RDS fundamentals: managed databases on AWS",
    "DynamoDB mental model: when NoSQL beats SQL",
    "Database backups and point-in-time recovery on AWS",
    "Secrets Manager vs Parameter Store: storing credentials safely",

    # Week 5: Architecture & Best Practices
    "CloudWatch: monitoring, alarms, and logs in one place",
    "Simple 3-tier web app architecture on AWS",
    "Deploying your first production-ready app on AWS"
]

# ================== FIND NEXT DAY ==================
try:
    query = requests.post(
        f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
        headers=NOTION_HEADERS,
        timeout=10
    )
    query.raise_for_status()
    
    # Handle pagination (Notion returns max 100 results by default)
    results = query.json().get("results", [])
    has_more = query.json().get("has_more", False)
    
    if has_more:
        print("Warning: More than 100 posts exist. Pagination needed.")
    
    existing_posts = len(results)
except requests.exceptions.RequestException as e:
    print(f"Error querying Notion database: {e}")
    exit(1)

if existing_posts >= len(AWS_TOPICS):
    print(f"All {len(AWS_TOPICS)} AWS posts already generated.")
    exit(0)

topic = AWS_TOPICS[existing_posts]
day_number = existing_posts + 1
print(f"Generating Day {day_number}: {topic}")

# ================== LLM PROMPT ==================
prompt = f"""
You are a 2nd year student learning AWS in public. You're documenting your learning journey on LinkedIn.

Day {day_number} topic: "{topic}"

VOICE & TONE (CRITICAL):
- Write as a STUDENT who just learned something cool
- Learning in public, sharing discoveries
- Relatable struggles: "I was confused about X until..."
- Excited but humble: "Just figured this out..."
- No expert posturing - you're learning too
- Show the learning process, not just the result
- Be real about what's hard or confusing

CONTENT REQUIREMENTS:
- 300-400 words
- Start with your confusion or "before/after" moment
- Include 1 AWS CLI command or console screenshot reference
- Explain like you're helping a classmate
- Share what finally made it click for you
- End with what you're trying next

FORMATTING (LinkedIn):
- Short paragraphs (1-3 sentences)
- Blank line between each paragraph
- Use bullets for lists (-)
- Natural, conversational flow
- No formal section headers


STRUCTURE (natural flow, hide these labels):

Hook - Your "before" moment:
"I spent 2 hours confused about..."
"Tried to set up X, got this error..."
"Everyone talks about X but nobody explains..."


What confused you / The struggle:
Be honest about what was hard. Other students relate to this.


The breakthrough / What you learned:
What finally clicked? What helped you understand?


How you actually did it (with example):
Show the command or steps you used:

`aws iam create-user --user-name myuser`

Share what worked for YOU.


What you'd tell yourself yesterday:
The one thing you wish you knew before starting.


What's next for you:
What you're going to try tomorrow. Keep it real.


Day {day_number}/30 - Learning AWS
#LearningInPublic #AWS #CloudComputing #StudentDeveloper


EXAMPLE HOOKS FOR STUDENTS:
- "Spent 3 hours debugging IAM permissions today. Here's what I learned..."
- "I thought AWS would be easy. Then I saw my first bill."
- "No one tells you this when you start learning AWS..."
- "Made my first mistake on AWS today. Here's what happened..."

Write like you're explaining to a friend in your study group. Be authentic. Share the struggle AND the win.
"""

# ================== GROQ API CALL ==================
groq_payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": "You write high-quality technical explanations."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.4
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
    if word_count < 250:
        print(f"Error: Generated post too short ({word_count} words, minimum 250)")
        exit(1)
    
    if word_count > 450:
        print(f"Warning: Generated post is long ({word_count} words)")
    
    # Check if required sections are present
    required_terms = ["TL;DR", f"Day {day_number}/30"]
    for term in required_terms:
        if term not in generated_post:
            print(f"Warning: Generated post missing '{term}'")
    
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
# AWS blocks hotlinking their icons, so using simple SVG badges via shields.io
# Clean, professional, no API needed, always works

# Map to relevant AWS service names for badges
aws_services = [
    "IAM", "Regions", "IAM", "Security", "AWS", "Free-Tier", "Pricing",
    "EC2", "EC2", "Lambda", "Lambda", "Auto-Scaling", "ECS", "Fargate",
    "VPC", "VPC", "Gateway", "Security-Groups", "ELB", "Route53", "CloudFront",
    "S3", "EBS", "RDS", "DynamoDB", "Backup", "Secrets-Manager",
    "CloudWatch", "Architecture", "Production"
]

service_name = aws_services[existing_posts] if existing_posts < len(aws_services) else "AWS"

# Use shields.io for clean, simple badges (always works, no auth needed)
image_url = f"https://img.shields.io/badge/AWS-{service_name}-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white"
print(f"✓ Using badge for: {service_name}")

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
    
    print(f"✓ Day {day_number} successfully pushed to Notion")
    print(f"Status: {notion_response.status_code}")
    
except requests.exceptions.RequestException as e:
    print(f"Error pushing to Notion: {e}")
    print(f"Response: {notion_response.text if 'notion_response' in locals() else 'No response'}")
    exit(1)
