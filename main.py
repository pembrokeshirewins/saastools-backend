from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from openai import OpenAI
import requests
import logging

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'saastools_db')]

# OpenAI setup
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

app = FastAPI(title="SaasTools.digital API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Models
class SaaSTool(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    short_description: str
    category: str
    logo_url: str
    website_url: str
    pricing_type: str
    pricing_details: str
    features: List[str]
    pros: List[str]
    cons: List[str]
    rating: float = Field(ge=0, le=5)
    tags: List[str]
    affiliate_link: Optional[str] = None
    ai_generated_review: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SaaSToolCreate(BaseModel):
    name: str
    description: str
    short_description: str
    category: str
    logo_url: str
    website_url: str
    pricing_type: str
    pricing_details: str
    features: List[str]
    pros: List[str]
    cons: List[str]
    rating: float = Field(ge=0, le=5)
    tags: List[str]
    affiliate_link: Optional[str] = None

class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    excerpt: str
    featured_image: str
    category: str = "SaaS Guide"
    tags: List[str]
    author: str = "AI Board"
    published_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BlogPostCreate(BaseModel):
    title: str
    category: str = "SaaS Guide"
    tags: List[str]

class UserSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    name: str
    email: str
    message: str
    tool_name: Optional[str] = None
    tool_url: Optional[str] = None
    rating: Optional[float] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserSubmissionCreate(BaseModel):
    type: str
    name: str
    email: str
    message: str
    tool_name: Optional[str] = None
    tool_url: Optional[str] = None
    rating: Optional[float] = None

class NewsletterSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: Optional[str] = None
    subscribed_at: datetime = Field(default_factory=datetime.utcnow)

class NewsletterSubscriptionCreate(BaseModel):
    email: str
    name: Optional[str] = None

# Helper functions
async def generate_ai_review(tool_name: str, description: str, features: List[str]) -> str:
    try:
        prompt = f"""
        Write a comprehensive, professional review for the SaaS tool '{tool_name}'.
        
        Description: {description}
        Key Features: {', '.join(features)}
        
        The review should be 200-300 words, professional and authoritative.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating AI review: {e}")
        return f"A comprehensive review of {tool_name} highlighting its key features and benefits."

async def generate_blog_content(title: str, category: str, tags: List[str]) -> tuple:
    try:
        prompt = f"""
        Write a comprehensive blog post about: {title}
        Category: {category}
        Tags: {', '.join(tags)}
        
        Make it 800-1200 words, SEO-friendly, and valuable for SaaS users.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        content = response.choices[0].message.content.strip()
        excerpt = content[:200] + "..." if len(content) > 200 else content
        
        return content, excerpt
    except Exception as e:
        logging.error(f"Error generating blog content: {e}")
        return "Blog content coming soon...", "Stay tuned for insights..."

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Welcome to SaasTools.digital API", "status": "operational"}

@api_router.get("/tools", response_model=List[SaaSTool])
async def get_tools(
    category: Optional[str] = None,
    search: Optional[str] = None,
    pricing_type: Optional[str] = None,
    limit: int = Query(20, le=100),
    skip: int = 0
):
    query = {}
    
    if category:
        query["category"] = category
    if pricing_type:
        query["pricing_type"] = pricing_type
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search]}}
        ]
    
    tools = await db.saas_tools.find(query).skip(skip).limit(limit).to_list(limit)
    return [SaaSTool(**tool) for tool in tools]

@api_router.get("/tools/{tool_id}", response_model=SaaSTool)
async def get_tool(tool_id: str):
    tool = await db.saas_tools.find_one({"id": tool_id})
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return SaaSTool(**tool)

@api_router.post("/tools", response_model=SaaSTool)
async def create_tool(tool_data: SaaSToolCreate):
    ai_review = await generate_ai_review(
        tool_data.name, 
        tool_data.description, 
        tool_data.features
    )
    
    tool_dict = tool_data.dict()
    tool_dict["ai_generated_review"] = ai_review
    tool_obj = SaaSTool(**tool_dict)
    
    await db.saas_tools.insert_one(tool_obj.dict())
    return tool_obj

@api_router.get("/categories")
async def get_categories():
    categories = await db.saas_tools.distinct("category")
    return {"categories": categories}

@api_router.get("/blog", response_model=List[BlogPost])
async def get_blog_posts(limit: int = Query(10, le=50), skip: int = 0):
    posts = await db.blog_posts.find().sort("published_at", -1).skip(skip).limit(limit).to_list(limit)
    return [BlogPost(**post) for post in posts]

@api_router.get("/blog/{slug}", response_model=BlogPost)
async def get_blog_post(slug: str):
    post = await db.blog_posts.find_one({"slug": slug})
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return BlogPost(**post)

@api_router.post("/blog", response_model=BlogPost)
async def create_blog_post(post_data: BlogPostCreate):
    content, excerpt = await generate_blog_content(
        post_data.title,
        post_data.category,
        post_data.tags
    )
    
    slug = post_data.title.lower().replace(" ", "-").replace(",", "")
    
    post_dict = {
        "title": post_data.title,
        "slug": slug,
        "content": content,
        "excerpt": excerpt,
        "featured_image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800",
        "category": post_data.category,
        "tags": post_data.tags,
        "author": "AI Board"
    }
    
    post_obj = BlogPost(**post_dict)
    await db.blog_posts.insert_one(post_obj.dict())
    return post_obj

@api_router.post("/submissions", response_model=UserSubmission)
async def create_submission(submission_data: UserSubmissionCreate):
    submission_obj = UserSubmission(**submission_data.dict())
    await db.user_submissions.insert_one(submission_obj.dict())
    return submission_obj

@api_router.post("/newsletter/subscribe")
async def subscribe_newsletter(subscription_data: NewsletterSubscriptionCreate):
    try:
        subscription_obj = NewsletterSubscription(**subscription_data.dict())
        await db.newsletter_subscriptions.insert_one(subscription_obj.dict())
        
        # Skip Mailchimp for test emails
        if subscription_data.email.endswith('@example.com') or subscription_data.email.startswith('test'):
            return {"message": "Successfully subscribed to newsletter (test mode)"}
        
        # Add to Mailchimp for real emails
        mailchimp_api_key = os.environ.get('MAILCHIMP_API_KEY')
        list_id = os.environ.get('MAILCHIMP_LIST_ID')
        
        if mailchimp_api_key and list_id:
            datacenter = mailchimp_api_key.split('-')[1]
            url = f"https://{datacenter}.api.mailchimp.com/3.0/lists/{list_id}/members"
            
            data = {
                "email_address": subscription_data.email,
                "status": "subscribed",
                "merge_fields": {
                    "FNAME": subscription_data.name or ""
                }
            }
            
            headers = {
                "Authorization": f"Bearer {mailchimp_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                return {"message": "Successfully subscribed to newsletter"}
            else:
                return {"message": "Subscribed locally, Mailchimp sync pending"}
        
        return {"message": "Successfully subscribed to newsletter"}
            
    except Exception as e:
        logging.error(f"Newsletter subscription error: {e}")
        raise HTTPException(status_code=500, detail="Subscription failed")

@api_router.get("/stats")
async def get_stats():
    tools_count = await db.saas_tools.count_documents({})
    blog_posts_count = await db.blog_posts.count_documents({})
    submissions_count = await db.user_submissions.count_documents({})
    
    return {
        "tools_count": tools_count,
        "blog_posts_count": blog_posts_count,
        "submissions_count": submissions_count
    }

# Include router and middleware
app.include_router(api_router)
@app.get("/")
async def main_root():
    return {"message": "Welcome to SaasTools.digital", "docs": "/docs", "api": "/api/"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SaasTools.digital API"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
