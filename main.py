from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio
from openai import OpenAI
from slugify import slugify
import json
import re
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client - Updated to handle API key properly
openai_client = None
AI_ENABLED = False
if os.environ.get('OPENAI_API_KEY'):
    try:
        openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        AI_ENABLED = True
    except Exception as e:
        logging.error(f"OpenAI initialization failed: {e}")
        AI_ENABLED = False

# Create the main app
app = FastAPI(
    title="SaaS Tools Digital API",
    description="AI-powered SaaS tools discovery and content platform",
    version="1.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# Data Models
class SaaSTool(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    description: str
    pricing: str
    features: List[str]
    pros: List[str]
    cons: List[str]
    rating: float
    affiliate_link: str
    logo_url: str
    website_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    excerpt: str
    category: str
    tags: List[str]
    featured_image: str
    meta_title: str
    meta_description: str
    author: str = "SaaS Tools Team"
    published: bool = True
    featured: bool = False
    views: int = 0
    affiliate_links: List[Dict[str, str]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NewsletterSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: Optional[str] = None
    subscribed_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

class BlogPostCreate(BaseModel):
    title: str
    category: str
    tags: List[str] = []
    generate_content: bool = True

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    published: Optional[bool] = None
    featured: Optional[bool] = None

# Affiliate link generator
def get_affiliate_links(category: str, tool_name: str = "") -> dict:
    """Generate affiliate links based on category and tool"""
    base_links = {
        "mailmodo": "https://www.mailmodo.com/?fpr=adrian55",
        "cj_affiliate": "https://www.cj.com/advertiser-signup"
    }
    
    # Category-specific affiliate opportunities
    category_links = {
        "Marketing": {
            "mailchimp": "https://mailchimp.com/pricing/",
            "hubspot": "https://www.hubspot.com/pricing",
            "convertkit": "https://convertkit.com/pricing"
        },
        "Sales": {
            "salesforce": "https://www.salesforce.com/pricing/",
            "pipedrive": "https://www.pipedrive.com/pricing",
            "hubspot_crm": "https://www.hubspot.com/pricing/crm"
        },
        "Productivity": {
            "asana": "https://asana.com/pricing",
            "monday": "https://monday.com/pricing",
            "notion": "https://www.notion.so/pricing"
        }
    }
    
    links = base_links.copy()
    if category in category_links:
        links.update(category_links[category])
    
    return links

# Enhanced content generation with affiliate links
def generate_html_content_with_affiliates(title: str, category: str, tags: List[str]) -> tuple:
    """Generate rich HTML content with integrated affiliate links"""
    
    affiliate_links = get_affiliate_links(category)
    
    # Generate unique, category-specific content
    category_data = {
        "Marketing": {
            "pain_points": "low conversion rates, poor lead quality, ineffective email campaigns",
            "solutions": ["email marketing automation", "lead scoring", "A/B testing", "customer segmentation"],
            "roi_metrics": "300% increase in lead conversion, 45% reduction in CAC",
            "tools": ["Mailmodo", "HubSpot", "Mailchimp", "ConvertKit"],
            "price_range": "$29-$299/month"
        },
        "Sales": {
            "pain_points": "lost leads, poor pipeline visibility, manual data entry",
            "solutions": ["CRM automation", "pipeline management", "lead tracking", "sales forecasting"],
            "roi_metrics": "40% increase in sales velocity, 60% improvement in close rates",
            "tools": ["Salesforce", "Pipedrive", "HubSpot CRM", "Zoho CRM"],
            "price_range": "$25-$150/month"
        },
        "Productivity": {
            "pain_points": "missed deadlines, poor team coordination, scattered workflows",
            "solutions": ["project management", "task automation", "team collaboration", "time tracking"],
            "roi_metrics": "35% improvement in project delivery, 50% reduction in missed deadlines",
            "tools": ["Asana", "Monday.com", "Notion", "ClickUp"],
            "price_range": "$8-$24/month"
        }
    }
    
    # Get category-specific data or use default
    data = category_data.get(category, {
        "pain_points": "operational inefficiencies, high costs, poor scalability",
        "solutions": ["automation", "integration", "analytics", "optimization"],
        "roi_metrics": "250% ROI improvement, 40% cost reduction",
        "tools": ["Premium Solution", "Business Pro", "Enterprise Suite"],
        "price_range": "$50-$200/month"
    })
    
    # Generate comprehensive HTML content
    html_content = f"""
    <article class="blog-content">
        <h1>{title}</h1>
        
        <div class="intro-section">
            <p>In 2025, businesses struggling with <strong>{data['pain_points']}</strong> are losing millions in potential revenue. This comprehensive guide reveals the top {category.lower()} solutions that deliver measurable results and maximum ROI.</p>
        </div>
        
        <h2>The Business Impact of {category} Tools</h2>
        <p>Companies using advanced {category.lower()} platforms report <strong>{data['roi_metrics']}</strong>. The right solution can transform your operations and drive sustainable growth.</p>
        
        <div class="cta-box">
            <h3>🚀 Ready to Transform Your {category} Strategy?</h3>
            <p>Start with <a href="{affiliate_links['mailmodo']}" target="_blank" rel="noopener sponsored">Mailmodo's powerful platform</a> and see immediate improvements in your metrics. <strong>Try free for 21 days!</strong></p>
        </div>
        
        <h2>Top {category} Solutions: Complete Analysis</h2>
        <div class="comparison-table">
            <table>
                <thead>
                    <tr>
                        <th>Solution</th>
                        <th>Best For</th>
                        <th>Pricing</th>
                        <th>ROI Potential</th>
                        <th>Rating</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>{data['tools'][0]}</strong></td>
                        <td>Enterprise Teams</td>
                        <td>{data['price_range']}</td>
                        <td>450% ROI</td>
                        <td>⭐⭐⭐⭐⭐ (4.8/5)</td>
                    </tr>
                    <tr>
                        <td><strong>{data['tools'][1]}</strong></td>
                        <td>Growing Businesses</td>
                        <td>{data['price_range']}</td>
                        <td>380% ROI</td>
                        <td>⭐⭐⭐⭐⭐ (4.7/5)</td>
                    </tr>
                    <tr>
                        <td><strong>{data['tools'][2]}</strong></td>
                        <td>Small Teams</td>
                        <td>{data['price_range']}</td>
                        <td>320% ROI</td>
                        <td>⭐⭐⭐⭐ (4.5/5)</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <h2>Key Features That Drive Results</h2>
        <ul>
            <li><strong>{data['solutions'][0].title()}</strong> - Essential for scalable operations</li>
            <li><strong>{data['solutions'][1].title()}</strong> - Critical for ROI optimization</li>
            <li><strong>{data['solutions'][2].title()}</strong> - Key for competitive advantage</li>
            <li><strong>{data['solutions'][3].title()}</strong> - Vital for long-term success</li>
        </ul>
        
        <h2>Implementation Strategy</h2>
        <ol>
            <li><strong>Assessment:</strong> Evaluate current {category.lower()} processes</li>
            <li><strong>Selection:</strong> Choose based on ROI potential and scalability</li>
            <li><strong>Pilot:</strong> Test with a small team first</li>
            <li><strong>Training:</strong> Ensure proper team adoption</li>
            <li><strong>Optimization:</strong> Monitor and refine for best results</li>
        </ol>
        
        <div class="affiliate-banner">
            <h3>💰 Maximize Your Investment</h3>
            <p>Join 50,000+ businesses achieving breakthrough results. <a href="{affiliate_links['cj_affiliate']}" target="_blank" rel="noopener sponsored">Explore premium solutions</a> and start your transformation today!</p>
        </div>
        
        <h2>ROI Analysis: Real Numbers</h2>
        <div class="pricing-grid">
            <div class="price-card">
                <h4>Small Business</h4>
                <div class="price">$15K - $50K</div>
                <p class="savings">Annual Value Creation</p>
                <ul>
                    <li>Time savings: 25-35 hours/week</li>
                    <li>Error reduction: 65%</li>
                    <li>Efficiency gain: +50%</li>
                </ul>
            </div>
            <div class="price-card featured">
                <h4>Enterprise</h4>
                <div class="price">$500K - $2M</div>
                <p class="savings">Annual Impact</p>
                <ul>
                    <li>Revenue increase: 35-50%</li>
                    <li>Cost reduction: 40%</li>
                    <li>Productivity: +75%</li>
                </ul>
            </div>
        </div>
        
        <div class="final-cta">
            <h3>🎯 Start Your Transformation Today</h3>
            <p>Don't let competitors gain the advantage. <a href="{affiliate_links['mailmodo']}" target="_blank" rel="noopener sponsored">Begin with Mailmodo's proven platform</a> and join thousands of businesses already achieving breakthrough results!</p>
        </div>
    </article>
    """
    
    # Generate excerpt and meta description
    excerpt = f"Discover the top {category.lower()} tools that deliver {data['roi_metrics']}. Complete analysis of features, pricing, and ROI potential."
    meta_description = f"Compare the best {category.lower()} tools for 2025. Features, pricing, ROI analysis, and expert recommendations to maximize your investment."
    
    # Prepare affiliate links for database
    affiliate_data = [
        {"name": "Mailmodo", "url": affiliate_links['mailmodo']},
        {"name": "CJ Affiliate", "url": affiliate_links['cj_affiliate']}
    ]
    
    return html_content, excerpt, meta_description, affiliate_data

# AI Content Generation with fallback
async def generate_ai_content(title: str, category: str, tags: List[str] = None) -> Dict[str, Any]:
    """Generate AI-powered blog content with affiliate links and SEO optimization"""
    
    if not AI_ENABLED or not openai_client:
        # Use enhanced fallback with affiliate links
        content, excerpt, meta_description, affiliate_links = generate_html_content_with_affiliates(title, category, tags or [])
        return {
            "content": content,
            "excerpt": excerpt,
            "meta_description": meta_description,
            "affiliate_links": affiliate_links
        }
    
    try:
        affiliate_links = get_affiliate_links(category)
        
        prompt = f"""
        Write a comprehensive, SEO-optimized blog post about "{title}" in the {category} category.
        
        Requirements:
        - 2000-3000 words with HTML formatting
        - Include strategic affiliate links: {affiliate_links['mailmodo']} and {affiliate_links['cj_affiliate']}
        - Use proper headings (h1, h2, h3)
        - Include profit-focused content with monetization opportunities
        - Add call-to-action boxes with affiliate links
        - Include pricing information and comparison tables
        - Focus on high-value tools that generate revenue
        - Use persuasive copywriting to drive conversions
        - Add sections for pros/cons, pricing, and alternatives
        - Include specific ROI metrics and case studies
        
        Structure:
        1. Compelling introduction with business impact
        2. Problem identification and cost of inaction
        3. Solution analysis with affiliate recommendations
        4. Comparison table with pricing and ROI
        5. Implementation strategy
        6. Call-to-action sections with affiliate links
        7. Conclusion with final CTA
        
        Make it highly profitable and conversion-focused while remaining valuable and ethical.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert SaaS content writer focused on creating profitable, high-converting blog content with strategic affiliate marketing."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Generate meta description
        meta_prompt = f"Write a compelling 150-character meta description for a blog post titled '{title}' in the {category} category. Focus on SEO and conversion optimization."
        
        meta_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an SEO expert who writes compelling meta descriptions for maximum click-through rates."},
                {"role": "user", "content": meta_prompt}
            ],
            max_tokens=100,
            temperature=0.5
        )
        
        meta_description = meta_response.choices[0].message.content.strip()
        excerpt = content[:200] + "..." if len(content) > 200 else content
        
        return {
            "content": content,
            "meta_description": meta_description,
            "excerpt": excerpt,
            "affiliate_links": [
                {"name": "Mailmodo", "url": affiliate_links["mailmodo"]},
                {"name": "CJ Affiliate", "url": affiliate_links["cj_affiliate"]}
            ]
        }
        
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        # Fall back to enhanced content generation
        content, excerpt, meta_description, affiliate_links = generate_html_content_with_affiliates(title, category, tags or [])
        return {
            "content": content,
            "excerpt": excerpt,
            "meta_description": meta_description,
            "affiliate_links": affiliate_links
        }

# API Endpoints - FIXED ROUTING ORDER
@api_router.get("/")
async def root():
    return {"message": "SaaS Tools Digital API", "status": "operational", "ai_enabled": AI_ENABLED}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SaaS Tools Digital API"}

@api_router.get("/tools", response_model=List[SaaSTool])
async def get_tools(
    category: Optional[str] = None,
    search: Optional[str] = None,
    pricing_type: Optional[str] = None,
    limit: int = Query(20, le=100),
    skip: int = 0
):
    """Get SaaS tools with optional filtering"""
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    if search:
        filter_dict["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if pricing_type:
        filter_dict["pricing"] = {"$regex": pricing_type, "$options": "i"}
    
    tools = await db.saas_tools.find(filter_dict).sort("rating", -1).skip(skip).limit(limit).to_list(length=limit)
    return [SaaSTool(**tool) for tool in tools]

@api_router.get("/blog", response_model=List[BlogPost])
async def get_blog_posts(limit: int = Query(10, le=50), skip: int = 0):
    """Get blog posts"""
    posts = await db.blog_posts.find().sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    return [BlogPost(**post) for post in posts]

# CRITICAL: Specific endpoints BEFORE generic slug endpoint
@api_router.post("/blog/bulk-generate")
async def bulk_generate_blog_posts():
    """Generate multiple blog posts for initial content"""
    
    blog_topics = [
        {"title": "Best CRM Software for Small Business 2025", "category": "Sales"},
        {"title": "Top Project Management Tools That Actually Work", "category": "Productivity"},
        {"title": "Email Marketing Platforms: Complete ROI Analysis", "category": "Marketing"},
        {"title": "Analytics Tools Every Business Needs in 2025", "category": "Analytics"},
        {"title": "Design Software for Non-Designers: Complete Guide", "category": "Design"},
        {"title": "Customer Support Software That Reduces Churn", "category": "Support"},
        {"title": "Accounting Software for Growing SaaS Companies", "category": "Finance"},
        {"title": "HR Management Tools: Streamline Your People Operations", "category": "HR"},
        {"title": "Social Media Management: Tools That Generate ROI", "category": "Marketing"},
        {"title": "E-commerce Platforms: Which One Maximizes Revenue?", "category": "E-commerce"},
        {"title": "Video Conferencing Solutions: Performance vs Price", "category": "Communication"},
        {"title": "Password Management: Security Tools Your Team Needs", "category": "Security"},
        {"title": "Backup Solutions: Protect Your Business Data", "category": "Security"},
        {"title": "Lead Generation Tools That Actually Work in 2025", "category": "Marketing"},
        {"title": "Automation Tools: Reduce Manual Work, Increase Profits", "category": "Productivity"},
        {"title": "Customer Feedback Tools: Turn Opinions into Revenue", "category": "Support"},
        {"title": "Invoicing Software: Get Paid Faster, Work Less", "category": "Finance"},
        {"title": "Team Collaboration Tools for Remote-First Companies", "category": "Productivity"},
        {"title": "SEO Tools That Deliver Measurable Traffic Growth", "category": "Marketing"},
        {"title": "Live Chat Software: Convert Visitors to Customers", "category": "Support"}
    ]
    
    created_posts = []
    
    for topic in blog_topics:
        try:
            # Check if post already exists
            existing_post = await db.blog_posts.find_one({"title": topic["title"]})
            if existing_post:
                continue
            
            # Generate slug
            slug = slugify(topic["title"])
            existing_slug = await db.blog_posts.find_one({"slug": slug})
            if existing_slug:
                slug = f"{slug}-{str(uuid.uuid4())[:8]}"
            
            # Generate AI content
            ai_content = await generate_ai_content(topic["title"], topic["category"], ["saas", "tools", "business"])
            
            # Create blog post
            blog_post = BlogPost(
                title=topic["title"],
                slug=slug,
                content=ai_content["content"],
                excerpt=ai_content["excerpt"],
                category=topic["category"],
                tags=["saas", "tools", "business", "productivity"],
                featured_image="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=400&fit=crop",
                meta_title=topic["title"],
                meta_description=ai_content["meta_description"],
                affiliate_links=ai_content["affiliate_links"],
                featured=len(created_posts) < 5  # First 5 posts are featured
            )
            
            await db.blog_posts.insert_one(blog_post.dict())
            created_posts.append(blog_post)
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logging.error(f"Error creating post '{topic['title']}': {e}")
            continue
    
    return {
        "message": f"Successfully generated {len(created_posts)} blog posts with affiliate links!",
        "posts": [{"title": post.title, "slug": post.slug, "category": post.category} for post in created_posts]
    }

@api_router.post("/blog/update-content")
async def update_existing_content(count: int = 20):
    """Update existing blog posts with enhanced content"""
    try:
        # Get existing posts
        existing_posts = await db.blog_posts.find().limit(count).to_list(length=count)
        updated_count = 0
        
        for post in existing_posts:
            try:
                # Generate new enhanced content
                ai_content = await generate_ai_content(post["title"], post["category"], post.get("tags", []))
                
                # Update the post
                await db.blog_posts.update_one(
                    {"_id": post["_id"]},
                    {"$set": {
                        "content": ai_content["content"],
                        "excerpt": ai_content["excerpt"],
                        "meta_description": ai_content["meta_description"],
                        "affiliate_links": ai_content["affiliate_links"],
                        "updated_at": datetime.utcnow()
                    }}
                )
                updated_count += 1
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error updating post '{post['title']}': {e}")
                continue
        
        return {
            "message": f"Successfully updated {updated_count} blog posts",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logging.error(f"Error updating content: {e}")
        return {"error": str(e)}

@api_router.get("/stats")
async def get_stats():
    """Get platform statistics"""
    try:
        total_posts = await db.blog_posts.count_documents({})
        published_posts = await db.blog_posts.count_documents({"published": True})
        featured_posts = await db.blog_posts.count_documents({"featured": True})
        
        return {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "featured_posts": featured_posts,
            "ai_enabled": AI_ENABLED
        }
    except Exception as e:
        logging.error(f"Error getting stats: {e}")
        return {"error": str(e)}

@api_router.post("/newsletter/subscribe")
async def subscribe_newsletter(email: str, name: Optional[str] = None):
    """Subscribe to newsletter"""
    try:
        existing_sub = await db.newsletter_subscriptions.find_one({"email": email})
        if existing_sub:
            return {"message": "Already subscribed to newsletter"}
        
        subscription = NewsletterSubscription(email=email, name=name)
        await db.newsletter_subscriptions.insert_one(subscription.dict())
        return {"message": "Successfully subscribed to newsletter"}
    except Exception as e:
        logging.error(f"Error subscribing to newsletter: {e}")
        return {"error": str(e)}

# Generic slug endpoint MUST come last
@api_router.get("/blog/{slug}", response_model=BlogPost)
async def get_blog_post(slug: str):
    """Get a specific blog post by slug"""
    try:
        post = await db.blog_posts.find_one({"slug": slug})
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Increment view count
        await db.blog_posts.update_one(
            {"slug": slug},
            {"$inc": {"views": 1}}
        )
        
        return BlogPost(**post)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting blog post: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Include router
app.include_router(api_router)

@app.get("/")
async def main_root():
    return {"message": "SaaS Tools Digital", "status": "operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SaaS Tools Digital API"}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
