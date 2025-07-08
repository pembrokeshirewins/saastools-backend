from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import logging
import asyncio

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'saastools_db')]

# OpenAI setup - with fallback
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    AI_ENABLED = True
except Exception as e:
    logging.warning(f"OpenAI not available: {e}")
    AI_ENABLED = False

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

# Affiliate link generator
def get_affiliate_links(category: str, tool_name: str = "") -> dict:
    """Generate affiliate links based on category and tool"""
    
    # Common affiliate programs (replace with real affiliate IDs)
    affiliate_links = {
        "CRM Software": {
            "primary": "https://hubspot.sjv.io/c/5416786/1999432/12893",  # HubSpot
            "secondary": "https://salesforce.partners/affiliate-link",
            "text": "Get started with HubSpot CRM (Free Forever)"
        },
        "Project Management": {
            "primary": "https://try.monday.com/?utm_medium=affiliate&utm_source=saastools",
            "secondary": "https://asana.com/?ref=saastools",
            "text": "Try Monday.com - 14 Day Free Trial"
        },
        "Email Marketing": {
            "primary": "https://www.mailmodo.com/?fpr=adrian55",  # Your Mailmodo affiliate
            "secondary": "https://convertkit.com/?ref=saastools",
            "text": "Start with Mailmodo - Interactive Email Platform"
        },
        "Analytics Tools": {
            "primary": "https://analytics.google.com/analytics/web/",
            "secondary": "https://mixpanel.com/?ref=saastools",
            "text": "Get Google Analytics (Free)"
        },
        "Design Tools": {
            "primary": "https://partner.canva.com/c/5416786/647168/10068",
            "secondary": "https://figma.com/?ref=saastools",
            "text": "Try Canva Pro - 30 Day Free Trial"
        },
        "default": {
            "primary": "https://www.mailmodo.com/?fpr=adrian55",
            "secondary": "https://cj.affiliate.com/link",
            "text": "Learn More"
        }
    }
    
    return affiliate_links.get(category, affiliate_links["default"])

# FIXED: HTML content generation with affiliate links
def generate_html_content_with_affiliates(title: str, category: str, tags: List[str]) -> tuple:
    """Generate HTML content with proper formatting and affiliate links"""
    
    # Get affiliate links for this category
    affiliate_data = get_affiliate_links(category, title)
    
    # Create comprehensive HTML content with affiliate integration
    content = f"""
<div class="blog-content">
    <h1>{title}</h1>

    <div class="intro-section">
        <h2>Introduction</h2>
        <p>In today's competitive business landscape, finding the right <strong>{category.lower()}</strong> solution is crucial for success. This comprehensive guide to <strong>{title}</strong> will help you understand the key features, benefits, pricing, and use cases to make an informed decision for your business.</p>
        
        <div class="cta-box" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #007bff;">
            <p><strong>🚀 Quick Start:</strong> <a href="{affiliate_data['primary']}" target="_blank" rel="noopener" style="color: #007bff; font-weight: bold;">{affiliate_data['text']}</a></p>
        </div>
    </div>

    <div class="overview-section">
        <h2>What is {title}?</h2>
        <p><strong>{title}</strong> represents cutting-edge solutions in the <strong>{category}</strong> space. These tools are designed to streamline operations, improve efficiency, and drive business growth through advanced features and intuitive interfaces.</p>
        
        <p>Whether you're a small startup looking to optimize your workflows or a large enterprise seeking to scale your operations, the right {category.lower()} solution can transform how your business operates.</p>
    </div>

    <div class="features-section">
        <h2>Key Features and Benefits</h2>
        
        <h3>🎯 Advanced Functionality</h3>
        <ul>
            <li><strong>Professional-grade capabilities</strong> that meet enterprise standards</li>
            <li><strong>User-friendly interface</strong> with intuitive design and minimal learning curve</li>
            <li><strong>Comprehensive feature set</strong> covering all essential business needs</li>
            <li><strong>Excellent customer support</strong> with 24/7 availability and expert assistance</li>
        </ul>

        <h3>💼 Business Impact</h3>
        <ul>
            <li><strong>Increased Productivity:</strong> Streamline workflows and eliminate manual processes</li>
            <li><strong>Better Collaboration:</strong> Enable seamless teamwork across departments</li>
            <li><strong>Cost Efficiency:</strong> Reduce operational costs while improving output quality</li>
            <li><strong>Scalable Growth:</strong> Solutions that grow with your business needs</li>
        </ul>
        
        <div class="affiliate-banner" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 10px; margin: 30px 0; text-align: center;">
            <h4 style="margin: 0 0 15px 0; color: white;">⭐ Recommended Solution</h4>
            <p style="margin: 0 0 15px 0; font-size: 16px;">Get started with the top-rated {category.lower()} platform trusted by thousands of businesses.</p>
            <a href="{affiliate_data['primary']}" target="_blank" rel="noopener" style="background: white; color: #667eea; padding: 12px 25px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">Start Free Trial →</a>
        </div>
    </div>

    <div class="pricing-section">
        <h2>💰 Pricing and Plans</h2>
        <p>Most <strong>{category.lower()}</strong> solutions offer flexible pricing tiers to accommodate different business sizes:</p>

        <div class="pricing-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 25px 0;">
            <div style="border: 1px solid #e9ecef; border-radius: 8px; padding: 20px;">
                <h3 style="color: #28a745;">💡 Starter Plan</h3>
                <p><strong>Price:</strong> Starting at $29/month</p>
                <p><strong>Best For:</strong> Small teams and startups</p>
                <p><strong>Features:</strong> Core functionality with essential features</p>
            </div>
            
            <div style="border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; border-color: #007bff; border-width: 2px;">
                <h3 style="color: #007bff;">🚀 Professional Plan</h3>
                <p><strong>Price:</strong> Starting at $79/month</p>
                <p><strong>Best For:</strong> Growing businesses and medium teams</p>
                <p><strong>Features:</strong> Advanced features with enhanced capabilities</p>
                <div style="margin-top: 15px;">
                    <a href="{affiliate_data['primary']}" target="_blank" rel="noopener" style="background: #007bff; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-size: 14px;">Most Popular →</a>
                </div>
            </div>
            
            <div style="border: 1px solid #e9ecef; border-radius: 8px; padding: 20px;">
                <h3 style="color: #6c757d;">🏢 Enterprise Plan</h3>
                <p><strong>Price:</strong> Starting at $199/month</p>
                <p><strong>Best For:</strong> Large organizations with complex needs</p>
                <p><strong>Features:</strong> Full feature access with premium support</p>
            </div>
        </div>
    </div>

    <div class="comparison-section">
        <h2>📊 Competitive Analysis</h2>
        <p>When evaluating <strong>{title}</strong>, consider these key differentiators:</p>

        <h3>✅ Strengths</h3>
        <ul>
            <li><strong>Comprehensive feature set</strong> that covers all business needs</li>
            <li><strong>Excellent user experience</strong> with intuitive design</li>
            <li><strong>Strong customer support</strong> with responsive service team</li>
            <li><strong>Regular updates</strong> and continuous feature improvements</li>
            <li><strong>Competitive pricing</strong> with transparent cost structure</li>
        </ul>

        <h3>⚠️ Considerations</h3>
        <ul>
            <li><strong>Learning curve</strong> for advanced features may require training</li>
            <li><strong>Premium features</strong> may require higher-tier subscription plans</li>
            <li><strong>Customization options</strong> might be limited in basic plans</li>
        </ul>
    </div>

    <div class="use-cases-section">
        <h2>🎯 Use Cases and Applications</h2>

        <h3>For Small Businesses</h3>
        <ul>
            <li>Streamlined operations with automated workflows</li>
            <li>Cost-effective solution that grows with your business</li>
            <li>Quick implementation with minimal setup requirements</li>
            <li>Essential features without unnecessary complexity</li>
        </ul>

        <h3>For Enterprise Organizations</h3>
        <ul>
            <li>Advanced reporting and analytics capabilities</li>
            <li>Enhanced security features and compliance tools</li>
            <li>Custom integrations with existing business systems</li>
            <li>Dedicated support and account management</li>
        </ul>
    </div>

    <div class="implementation-section">
        <h2>🚀 Implementation and Getting Started</h2>
        
        <h3>Step 1: Assessment</h3>
        <p>Evaluate your current {category.lower()} needs and identify key requirements for your business.</p>

        <h3>Step 2: Trial Period</h3>
        <p>Take advantage of free trials to test functionality and user experience with your team.</p>
        
        <div class="trial-cta" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <p><strong>Ready to try it yourself?</strong></p>
            <a href="{affiliate_data['primary']}" target="_blank" rel="noopener" style="background: #28a745; color: white; padding: 12px 25px; border-radius: 6px; text-decoration: none; font-weight: bold;">Start Your Free Trial Today →</a>
        </div>

        <h3>Step 3: Migration Planning</h3>
        <p>Develop a comprehensive plan for transitioning from existing solutions to minimize disruption.</p>

        <h3>Step 4: Training and Adoption</h3>
        <p>Ensure proper training for your team to maximize the value of your new {category.lower()} solution.</p>
    </div>

    <div class="roi-section">
        <h2>💹 ROI and Business Impact</h2>
        <p>Investing in quality <strong>{category.lower()}</strong> software typically delivers:</p>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
            <div style="background: #e8f5e8; padding: 15px; border-radius: 6px; text-align: center;">
                <h4 style="color: #28a745; margin: 0;">25-40%</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Improvement in operational efficiency</p>
            </div>
            <div style="background: #e3f2fd; padding: 15px; border-radius: 6px; text-align: center;">
                <h4 style="color: #1976d2; margin: 0;">10-15 hours</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Saved per week per employee</p>
            </div>
            <div style="background: #fff3e0; padding: 15px; border-radius: 6px; text-align: center;">
                <h4 style="color: #f57c00; margin: 0;">Better</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Decision making through data visibility</p>
            </div>
            <div style="background: #fce4ec; padding: 15px; border-radius: 6px; text-align: center;">
                <h4 style="color: #c2185b; margin: 0;">Enhanced</h4>
                <p style="margin: 5px 0 0 0; font-size: 14px;">Customer satisfaction</p>
            </div>
        </div>
    </div>

    <div class="conclusion-section">
        <h2>🎯 Final Recommendation</h2>
        <p><strong>{title}</strong> stands out as a leading solution in the <strong>{category}</strong> space. With its robust feature set, competitive pricing, and excellent support, it's an excellent choice for businesses looking to improve their operations and drive growth.</p>

        <p>Whether you're a small startup or a large enterprise, <strong>{title}</strong> offers the flexibility and power to meet your specific needs. The investment in quality {category.lower()} software pays dividends through improved efficiency, better collaboration, and enhanced business outcomes.</p>
        
        <div class="final-cta" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); color: white; padding: 30px; border-radius: 10px; margin: 30px 0; text-align: center;">
            <h3 style="margin: 0 0 15px 0; color: white;">🎉 Special Offer Available</h3>
            <p style="margin: 0 0 20px 0; font-size: 18px;">Get started today and join thousands of businesses already benefiting from this solution.</p>
            <a href="{affiliate_data['primary']}" target="_blank" rel="noopener" style="background: white; color: #ff6b6b; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; display: inline-block;">Claim Your Free Trial →</a>
            <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.9;">No credit card required • Cancel anytime</p>
        </div>
    </div>

    <div class="next-steps-section">
        <h2>🚀 Next Steps</h2>
        <p>Ready to get started with <strong>{title}</strong>? Here's what to do next:</p>

        <ol>
            <li><strong><a href="{affiliate_data['primary']}" target="_blank" rel="noopener">Sign up for a free trial</a></strong> to test the features</li>
            <li><strong>Schedule a demo</strong> with their sales team for personalized guidance</li>
            <li><strong>Compare pricing plans</strong> to find the best fit for your budget</li>
            <li><strong>Read customer reviews</strong> to understand real-world experiences</li>
            <li><strong>Contact their support team</strong> with any questions</li>
        </ol>

        <p>For more information about <strong>{title}</strong> and other {category.lower()} solutions, explore our comprehensive reviews and comparison guides.</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
            <p><strong>💡 Pro Tip:</strong> Many {category.lower()} tools offer free trials or freemium plans. Take advantage of these to test multiple solutions before making your final decision.</p>
        </div>
    </div>

    <div class="disclaimer-section" style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 14px;">
        <p><em>This review is based on current market analysis and feature comparisons. Pricing and features may change. Always verify current information with the vendor before making purchasing decisions. Some links in this article are affiliate links, which means we may earn a commission if you make a purchase through them at no additional cost to you.</em></p>
    </div>
</div>
"""

    excerpt = f"Comprehensive guide to {title} covering features, pricing, benefits, and use cases. Find out if this {category.lower()} solution is right for your business needs. Includes exclusive trial offers and pricing comparisons."
    
    return content, excerpt

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "SaaS Tools Digital API", "status": "operational", "ai_enabled": AI_ENABLED}

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

@api_router.get("/blog", response_model=List[BlogPost])
async def get_blog_posts(limit: int = Query(10, le=50), skip: int = 0):
    """FIXED: Non-blocking blog post retrieval"""
    try:
        posts = await db.blog_posts.find().sort("published_at", -1).skip(skip).limit(limit).to_list(limit)
        return [BlogPost(**post) for post in posts]
    except Exception as e:
        logging.error(f"Error fetching posts: {e}")
        return []

@api_router.get("/blog/{slug}", response_model=BlogPost)
async def get_blog_post(slug: str):
    try:
        post = await db.blog_posts.find_one({"slug": slug})
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        return BlogPost(**post)
    except Exception as e:
        logging.error(f"Error fetching post: {e}")
        raise HTTPException(status_code=404, detail="Blog post not found")

@api_router.post("/blog/bulk-generate")
async def bulk_generate_blog_posts():
    """Generate initial blog posts for the platform"""
    
    try:
        # Sample blog post topics with categories
        blog_topics = [
            {"title": "Best CRM Software for Small Business 2025", "category": "CRM Software", "tags": ["crm", "small-business", "2025"]},
            {"title": "Top Project Management Tools That Actually Work", "category": "Project Management", "tags": ["project-management", "productivity", "collaboration"]},
            {"title": "Email Marketing Platforms: Complete ROI Analysis", "category": "Email Marketing", "tags": ["email", "marketing", "automation", "roi"]},
            {"title": "Analytics Tools Every Business Needs in 2025", "category": "Analytics Tools", "tags": ["analytics", "data", "insights", "business-intelligence"]},
            {"title": "Design Software for Non-Designers: Complete Guide", "category": "Design Tools", "tags": ["design", "ui-ux", "beginner-friendly", "graphics"]},
            {"title": "Customer Support Software That Reduces Churn", "category": "Customer Support", "tags": ["support", "customer-service", "retention", "helpdesk"]},
            {"title": "Accounting Software for Growing SaaS Companies", "category": "Finance", "tags": ["accounting", "finance", "saas", "bookkeeping"]},
            {"title": "HR Management Tools: Streamline Your People Operations", "category": "HR Software", "tags": ["hr", "management", "employees", "recruitment"]},
            {"title": "Social Media Management: Tools That Generate ROI", "category": "Social Media", "tags": ["social-media", "marketing", "roi", "automation"]},
            {"title": "E-commerce Platforms: Which One Maximizes Revenue?", "category": "E-commerce", "tags": ["ecommerce", "sales", "revenue", "online-store"]},
            {"title": "Video Conferencing Solutions: Performance vs Price", "category": "Communication", "tags": ["video-conferencing", "remote-work", "communication", "meetings"]},
            {"title": "Password Management: Security Tools Your Team Needs", "category": "Security", "tags": ["password-manager", "security", "cybersecurity", "team-tools"]},
            {"title": "Backup Solutions: Protect Your Business Data", "category": "Security", "tags": ["backup", "data-protection", "cloud-storage", "disaster-recovery"]},
            {"title": "Lead Generation Tools That Actually Work in 2025", "category": "Marketing", "tags": ["lead-generation", "marketing", "sales", "conversion"]},
            {"title": "Automation Tools: Reduce Manual Work, Increase Profits", "category": "Productivity", "tags": ["automation", "productivity", "efficiency", "workflow"]},
            {"title": "Customer Feedback Tools: Turn Opinions into Revenue", "category": "Customer Support", "tags": ["feedback", "survey", "customer-experience", "improvement"]},
            {"title": "Invoicing Software: Get Paid Faster, Work Less", "category": "Finance", "tags": ["invoicing", "billing", "payments", "cash-flow"]},
            {"title": "Team Collaboration Tools for Remote-First Companies", "category": "Productivity", "tags": ["collaboration", "remote-work", "team-communication", "productivity"]},
            {"title": "SEO Tools That Deliver Measurable Traffic Growth", "category": "Marketing", "tags": ["seo", "traffic", "search-optimization", "digital-marketing"]},
            {"title": "Live Chat Software: Convert Visitors to Customers", "category": "Customer Support", "tags": ["live-chat", "conversion", "customer-service", "website-tools"]},
        ]
        
        created_posts = []
        
        for topic in blog_topics:
            try:
                # Generate slug from title
                slug = topic["title"].lower()
                slug = slug.replace(" ", "-").replace(":", "").replace("?", "").replace(",", "").replace("(", "").replace(")", "")
                slug = "".join(c for c in slug if c.isalnum() or c == "-")
                
                # Check if post already exists
                existing_post = await db.blog_posts.find_one({"slug": slug})
                if existing_post:
                    continue
                
                # Generate content using existing function
                content, excerpt = generate_html_content_with_affiliates(
                    topic["title"], 
                    topic["category"], 
                    topic["tags"]
                )
                
                # Create blog post
                blog_post = BlogPost(
                    title=topic["title"],
                    slug=slug,
                    content=content,
                    excerpt=excerpt,
                    category=topic["category"],
                    tags=topic["tags"],
                    featured_image="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=400&fit=crop",
                    author="SaaS Tools Team"
                )
                
                await db.blog_posts.insert_one(blog_post.dict())
                created_posts.append(blog_post)
                
                # Small delay to avoid overwhelming the database
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error creating post '{topic['title']}': {e}")
                continue
        
        return {
            "message": f"Successfully generated {len(created_posts)} blog posts with affiliate links!",
            "posts": [{"title": post.title, "slug": post.slug, "category": post.category} for post in created_posts]
        }
        
    except Exception as e:
        logging.error(f"Error in bulk generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate posts: {str(e)}")

@api_router.post("/blog/update-content")
async def update_existing_content(count: int = 20):
    """FIXED: Update existing posts with HTML content and affiliate links"""
    
    try:
        # Get existing posts with old content
        posts = await db.blog_posts.find().limit(count).to_list(count)
        updated_count = 0
        
        for post in posts:
            try:
                # Generate new HTML content with affiliate links
                content, excerpt = generate_html_content_with_affiliates(
                    post['title'], 
                    post.get('category', 'SaaS Tools'), 
                    post.get('tags', [])
                )
                
                # Update the post
                await db.blog_posts.update_one(
                    {"_id": post["_id"]},
                    {"$set": {
                        "content": content,
                        "excerpt": excerpt,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                updated_count += 1
                
            except Exception as e:
                logging.error(f"Error updating post '{post.get('title', 'unknown')}': {e}")
                continue
        
        return {
            "message": f"Successfully updated {updated_count} posts with HTML content and affiliate links!",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logging.error(f"Error in content update: {e}")
        raise HTTPException(status_code=500, detail="Failed to update content")

@api_router.get("/stats")
async def get_stats():
    try:
        tools_count = await db.saas_tools.count_documents({})
        blog_posts_count = await db.blog_posts.count_documents({})
        
        return {
            "tools_count": tools_count,
            "blog_posts_count": blog_posts_count,
            "ai_enabled": AI_ENABLED
        }
    except Exception as e:
        logging.error(f"Error fetching stats: {e}")
        return {"tools_count": 0, "blog_posts_count": 0, "ai_enabled": AI_ENABLED}

@api_router.post("/newsletter/subscribe")
async def subscribe_newsletter(email: str, name: Optional[str] = None):
    """Subscribe to newsletter"""
    try:
        # Simple email validation
        if "@" not in email or "." not in email:
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        # Check if already subscribed
        existing = await db.newsletter_subscriptions.find_one({"email": email})
        if existing:
            return {"message": "Email already subscribed"}
        
        # Add subscription
        subscription = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": name,
            "subscribed_at": datetime.utcnow(),
            "active": True
        }
        
        await db.newsletter_subscriptions.insert_one(subscription)
        return {"message": "Successfully subscribed to newsletter"}
        
    except Exception as e:
        logging.error(f"Newsletter subscription error: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")

# Include router and middleware
app.include_router(api_router)

@app.get("/")
async def main_root():
    return {"message": "SaaS Tools Digital", "status": "operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SaaS Tools Digital API"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
