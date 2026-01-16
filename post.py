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
You're a 2nd year CS student who learned AWS BACKWARDS - built first (7 microservices with GPT's help, lots of debugging), THEN got certified. Writing to maximize LinkedIn engagement.

Day {day_number} topic: "{topic}"

YOUR UNIQUE STORY:
- Learned by building, not tutorials/YouTube
- Used ChatGPT + trial-and-error + sleepless nights debugging
- Built production-ready infra without knowing what you were doing
- Got AWS/GCP certifications AFTER building (everything clicked easily)
- This contrarian path is your superpower

ENGAGEMENT GOALS:
- Stop the scroll with controversial take
- Challenge "course first, build later" mentality
- Share debugging war stories
- Make people comment/disagree/relate
- 250-350 words MAX

VOICE:
- "I learned this the hard way..."
- "No tutorial taught me this..."
- "Debugged this at 3am..."
- Builder mindset, not student mindset
- Real experience > theory

FORMATTING (max engagement):
- Killer first line (controversial/surprising)
- 1-2 sentence paragraphs
- Blank line between EVERY paragraph
- Maximum white space
- End with engagement-driving question


STRUCTURE:

Opening hook (1-2 lines):
"I didn't watch a single AWS tutorial. Built 7 microservices first."
"Learned AWS backwards: built first, certified later."
"Everyone says take courses. I debugged IAM at 3am instead."
"No YouTube tutorials. Just ChatGPT, errors, and sleepless nights."

The contrarian take:
Your learning path. Why building first worked.
The thing you discovered by breaking things.

The real lesson from building:
What you learned by doing, not reading.
The mistake you made that taught you.

Practical example:
`aws iam create-role --role-name service-role`

What you learned debugging this.

Why it matters:
How this approach made certifications easy.
What clicked AFTER hands-on experience.

Question for engagement:
"Am I crazy for learning this way?"
"Anyone else skip tutorials and just build?"
"What's your learning strategy?"

Day {day_number}/30
#AWS #LearnByBuilding #100DaysOfCode #CloudComputing


KILLER HOOKS (use this style):
- "I failed AWS 3 times before watching my first tutorial."
- "Built 7 microservices without knowing what VPC meant."
- "Everyone told me: courses first. I deployed to production first."
- "Debugging IAM at 3am taught me more than any certification."
- "I learned AWS the dumbest way possible. No regrets."
- "Spent 8 hours fixing one IAM permission. Worth it."

TONE:
- Humble but bold about your approach
- Share the struggle ("sleepless nights debugging")
- Show it worked (certifications were easy after)
- Make it relatable (others can try this too)
- Controversial but authentic

Write to make people REACT. Your learning path is unique. Own it. Make it controversial. Drive engagement.
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
