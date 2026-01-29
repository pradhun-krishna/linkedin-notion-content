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
Write a technical AWS post for Day {day_number} about: "{topic}"

You're a builder who learned AWS by building a 7-microservice system. Mix technical insights with brief context, but vary the storytelling style.

CONTENT (250-350 words):
- Hook with varied approach (see examples below)
- Technical insight or non-obvious gotcha
- Practical AWS CLI command or pattern
- Why it matters in production
- Actionable tip

STORYTELLING VARIETY (rotate between these):
1. Technical scenario: "When setting up IAM for microservices..."
2. Before/after: "I used to do X. Now I do Y. Here's why."
3. Common mistake: "Most people configure X wrong. Here's what breaks."
4. Discovery: "Found out Y the hard way. Here's what happened."
5. Comparison: "X vs Y. Here's which one actually matters."
6. Myth-busting: "Everyone says X. Reality is Y."

STYLE:
- Brief context (1-2 lines max), then straight to tech
- Show don't tell: "The IAM policy failed" not "I spent hours debugging"
- Vary the hook style each post
- Keep storytelling minimal but engaging
- Focus on the technical lesson

FORMATTING:
- Short paragraphs
- Blank line between paragraphs
- Code blocks for commands
- Scannable


STRUCTURE:

Hook (vary the style):
Quick context or scenario that sets up the technical point.
Make it interesting but brief.

The technical insight:
The core lesson about this AWS service.
What actually matters in production.

Practical example:
```
aws [command] --flag value
```
Real code or architecture decision.

The gotcha/lesson:
What breaks. What to watch for.
Technical detail that matters.

Actionable tip:
One thing they can apply today.

Day {day_number}/30
#AWS #CloudComputing #DevOps


VARIED HOOK EXAMPLES (rotate styles):
- "IAM policies work differently than you'd expect. Here's why."
- "Migrating 7 services to ECS taught me this about container networking."
- "Security Groups vs NACLs. Most tutorials explain this wrong."
- "S3 buckets got expensive fast. Found the issue in CloudWatch logs."
- "Lambda cold starts: 100ms vs 5s. Here's what causes the difference."
- "RDS backup strategy: learned this after almost losing data."

Keep it TECHNICAL but use brief context to make it engaging. Vary the storytelling approach - don't repeat the same narrative pattern.
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
    
    # Shorter is better for LinkedIn engagement - no minimum
    if word_count > 500:
        print(f"Warning: Generated post is quite long ({word_count} words)")
    
    # Check if Day marker is present
    if f"Day {day_number}/30" not in generated_post:
        print(f"Warning: Generated post missing 'Day {day_number}/30'")
    
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
