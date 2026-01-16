import os
import random
import requests
from datetime import date

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

topics = [
    "AWS IAM explained simply",
    "AWS S3 best practices",
    "AWS Lambda vs EC2",
    "AWS VPC basics",
    "AWS CloudWatch explained"
]

topic = random.choice(topics)

post_text = f"""{topic}

One concept. No fluff.

• What it is  
• Why it matters  
• One real-world use  

Learning AWS one step at a time.
"""

hashtags = "#AWS #Cloud #DevOps #LearningInPublic"

image_url = f"https://image.pollinations.ai/prompt/{topic} cloud computing minimal illustration"

data = {
    "parent": {"database_id": DATABASE_ID},
    "properties": {
        "Topic": {"title": [{"text": {"content": topic}}]},
        "Date": {"date": {"start": str(date.today())}},
        "Post": {"rich_text": [{"text": {"content": post_text}}]},
        "Hashtags": {"rich_text": [{"text": {"content": hashtags}}]},
        "Status": {"select": {"name": "Draft"}}
    },
    "children": [
        {
            "object": "block",
            "type": "image",
            "image": {"external": {"url": image_url}}
        }
    ]
}

response = requests.post(
    "https://api.notion.com/v1/pages",
    headers=headers,
    json=data
)

print(response.status_code, response.text)
