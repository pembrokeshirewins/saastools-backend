Action: file_editor view /app/main.py
Observation: /app/main.py:
1|from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
2|from fastapi.responses import JSONResponse
3|from dotenv import load_dotenv
4|from starlette.middleware.cors import CORSMiddleware
5|from motor.motor_asyncio import AsyncIOMotorClient
6|import os
7|import logging
8|from pathlib import Path
9|from pydantic import BaseModel, Field
10|from typing import List, Optional
11|import uuid
12|from datetime import datetime, timedelta
13|import openai
14|from slugify import slugify
15|import asyncio
16|import schedule
17|import time
18|from threading import Thread
19|import json
20|import re
21|
22|ROOT_DIR = Path(__file__).parent
23|load_dotenv(ROOT_DIR / '.env')
24|
25|# MongoDB connection
26|mongo_url = os.environ['MONGO_URL']
27|client = AsyncIOMotorClient(mongo_url)
28|db = client[os.environ['DB_NAME']]
29|
30|# OpenAI setup
31|openai.api_key = os.environ['OPENAI_API_KEY']
32|
33|# Create the main app without a prefix
34|app = FastAPI(title="SaaS Tools Digital - Autonomous Blog Platform", version="1.0.0")
35|
36|# Create a router with the /api prefix
37|api_router = APIRouter(prefix="/api")
38|
39|# Blog Models
40|class BlogPost(BaseModel):
41|    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
42|    title: str
43|    slug: str
44|    content: str
45|    excerpt: str
46|    meta_description: str
47|    keywords: List[str] = []
48|    category: str
49|    tags: List[str] = []
50|    author: str = "SaaS Tools Team"
51|    featured_image: Optional[str] = None
52|    status: str = "published"  # draft, published, scheduled
53|    published_at: datetime = Field(default_factory=datetime.utcnow)
54|    created_at: datetime = Field(default_factory=datetime.utcnow)
55|    updated_at: datetime = Field(default_factory=datetime.utcnow)
56|    view_count: int = 0
57|    affiliate_links: List[dict] = []
58|    seo_score: int = 0
59|    is_revenue_focused: bool = True
60|
61|class BlogPostCreate(BaseModel):
62|    title: str
63|    category: str
64|    keywords: List[str] = []
65|    custom_content: Optional[str] = None
66|
67|class BlogPostUpdate(BaseModel):
68|    title: Optional[str] = None
69|    content: Optional[str] = None
70|    excerpt: Optional[str] = None
71|    meta_description: Optional[str] = None
72|    keywords: Optional[List[str]] = None
73|    category: Optional[str] = None
74|    tags: Optional[List[str]] = None
75|    status: Optional[str] = None
76|
77|class ContentGenerationRequest(BaseModel):
78|    topic: str
79|    category: str
80|    keywords: List[str]
81|    target_length: int = 2500
82|    include_affiliate_opportunities: bool = True
83|
84|# AI Content Generation
85|class AIContentGenerator:
86|    def __init__(self):
87|        self.client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
88|        self.saas_categories = [
89|            "CRM Software", "Project Management", "Email Marketing", "Analytics Tools",
90|            "Design Tools", "Development Tools", "Customer Support", "Accounting Software",
91|            "HR Management", "Social Media Management", "E-commerce Platforms", "Sales Tools",
92|            "Marketing Automation", "Cloud Storage", "Security Tools", "Productivity Apps",
93|            "Communication Tools", "Business Intelligence", "Content Management", "SEO Tools"
94|        ]
95|        
96|    async def generate_seo_article(self, topic: str, category: str, keywords: List[str], target_length: int = 2500):
97|        """Generate a comprehensive SEO-optimized article about a SaaS tool or category"""
98|        
99|        prompt = f"""
100|        Write a comprehensive, SEO-optimized article about "{topic}" in the {category} category. 
101|        Target length: {target_length} words.
102|        
103|        Requirements:
104|        1. Include primary keyword "{keywords[0]}" and related keywords: {', '.join(keywords[1:5])}
105|        2. Structure: H1, H2, H3 headings with keyword optimization
106|        3. Include practical benefits, use cases, and pricing information
107|        4. Add comparison with competitors
108|        5. Include call-to-action sections for affiliate opportunities
109|        6. Write in an authoritative, helpful tone
110|        7. Include specific examples and case studies
111|        8. Optimize for search intent and user value
112|        
113|        Article structure:
114|        - Introduction (150-200 words)
115|        - What is [Topic]? (300-400 words)
116|        - Key Features and Benefits (400-500 words)
117|        - Pricing and Plans (250-300 words)
118|        - Alternatives and Comparisons (300-400 words)
119|        - Use Cases and Examples (250-300 words)
120|        - Pros and Cons (200-250 words)
121|        - Final Verdict and Recommendations (150-200 words)
122|        
123|        Make it extremely valuable for readers looking to make purchasing decisions.
124|        Include specific mentions of pricing, features, and competitive advantages.
125|        """
126|        
127|        try:
128|            response = self.client.chat.completions.create(
129|                model="gpt-4o",
130|                messages=[
131|                    {"role": "system", "content": "You are an expert SaaS review writer and digital marketing specialist. Write comprehensive, SEO-optimized articles that help businesses make informed software decisions while maximizing affiliate revenue potential."},
132|                    {"role": "user", "content": prompt}
133|                ],
134|                max_tokens=4000,
135|                temperature=0.7
136|            )
137|            
138|            content = response.choices[0].message.content
139|            
140|            # Generate meta description
141|            meta_prompt = f"Write a compelling 150-160 character meta description for an article about '{topic}' that includes the keyword '{keywords[0]}' and encourages clicks."
142|            
143|            meta_response = self.client.chat.completions.create(
144|                model="gpt-4o",
145|                messages=[
146|                    {"role": "system", "content": "You are an SEO expert specializing in meta descriptions."},
147|                    {"role": "user", "content": meta_prompt}
148|                ],
149|                max_tokens=100,
150|                temperature=0.5
151|            )
152|            
153|            meta_description = meta_response.choices[0].message.content.strip()
154|            
155|            # Generate excerpt
156|            excerpt = content[:200] + "..." if len(content) > 200 else content
157|            
158|            return {
159|                "content": content,
160|                "meta_description": meta_description,
161|                "excerpt": excerpt,
162|                "seo_score": self._calculate_seo_score(content, keywords)
163|            }
164|            
165|        except Exception as e:
166|            logging.error(f"Error generating content: {e}")
167|            # Fallback content for demo purposes
168|            return self._generate_fallback_content(topic, category, keywords, target_length)
169|    
170|    def _calculate_seo_score(self, content: str, keywords: List[str]) -> int:
171|        """Calculate basic SEO score based on keyword density and content structure"""
172|        score = 0
173|        word_count = len(content.split())
174|        
175|        # Word count score (optimal 2000-3000 words)
176|        if 2000 <= word_count <= 3000:
177|            score += 30
178|        elif 1500 <= word_count <= 3500:
179|            score += 20
180|        else:
181|            score += 10
182|            
183|        # Keyword density score
184|        for keyword in keywords[:3]:  # Check top 3 keywords
185|            keyword_count = content.lower().count(keyword.lower())
186|            density = (keyword_count / word_count) * 100
187|            if 0.5 <= density <= 2.5:  # Optimal density
188|                score += 20
189|            elif density > 0:
190|                score += 10
191|                
192|        # Structure score (headings)
193|        if "##" in content:  # H2 headings
194|            score += 10
195|        if "###" in content:  # H3 headings
196|            score += 10
197|            
198|        return min(score, 100)
199|    
200|    def _generate_fallback_content(self, topic: str, category: str, keywords: List[str], target_length: int) -> dict:
201|        """Generate fallback content when AI API is unavailable"""
202|        
203|        content = f"""# {topic}
204|
205|## Introduction
206|
207|In today's competitive business landscape, finding the right {category.lower()} solution is crucial for success. This comprehensive review of {topic} will help you understand the key features, pricing, and benefits to make an informed decision for your business.
208|
209|## What is {topic}?
210|
211|{topic} represents the cutting-edge solutions in the {category} space. These tools are designed to streamline operations, improve efficiency, and drive business growth through advanced features and intuitive interfaces.
212|
213|### Key Features
214|
215|- **Advanced Analytics**: Get detailed insights into your business performance
216|- **User-Friendly Interface**: Intuitive design that requires minimal training
217|- **Integration Capabilities**: Seamlessly connects with your existing tools
218|- **Scalable Architecture**: Grows with your business needs
219|- **24/7 Support**: Round-the-clock customer assistance
220|
221|## Pricing and Plans
222|
223|Most {category.lower()} solutions offer tiered pricing to accommodate different business sizes:
224|
225|- **Starter Plan**: $29/month - Perfect for small teams
226|- **Professional Plan**: $79/month - Ideal for growing businesses  
227|- **Enterprise Plan**: $199/month - Comprehensive features for large organizations
228|
229|## Top Alternatives
230|
231|When considering {topic}, it's important to evaluate alternatives such as:
232|
233|1. **Alternative A**: Strong in automation features
234|2. **Alternative B**: Best for enterprise-level deployments
235|3. **Alternative C**: Most cost-effective for small businesses
236|
237|## Use Cases and Benefits
238|
239|### For Small Businesses
240|- Streamlined workflows
241|- Cost-effective solution
242|- Quick implementation
243|
244|### For Enterprises
245|- Advanced reporting capabilities
246|- Enhanced security features
247|- Custom integrations
248|
249|## Pros and Cons
250|
251|### Pros
252|✅ Comprehensive feature set
253|✅ Excellent customer support
254|✅ Regular updates and improvements
255|✅ Strong security measures
256|
257|### Cons
258|❌ Learning curve for new users
259|❌ Premium features require higher-tier plans
260|❌ Limited customization in basic plans
261|
262|## Final Verdict
263|
264|{topic} stands out as a leading solution in the {category} category. With its robust feature set, competitive pricing, and excellent support, it's an excellent choice for businesses looking to improve their operations.
265|
266|Whether you're a small startup or a large enterprise, {topic} offers the flexibility and power to meet your needs. The investment in quality {category.lower()} software pays dividends through improved efficiency and business growth.
267|
268|## Frequently Asked Questions
269|
270|**Q: Is there a free trial available?**
271|A: Yes, most providers offer a 14-30 day free trial.
272|
273|**Q: Can I cancel anytime?**
274|A: Yes, most plans allow monthly cancellation.
275|
276|**Q: Is training provided?**
277|A: Most vendors provide comprehensive onboarding and training resources.
278|
279|---
280|
281|*This review is based on current market analysis and user feedback. Features and pricing may change. Always verify current information with the vendor.*
282|"""
283|
284|        meta_description = f"Comprehensive review of {topic} - features, pricing, pros & cons. Find the best {category.lower()} solution for your business needs."
285|        
286|        excerpt = f"Discover everything you need to know about {topic} in our comprehensive review. We cover features, pricing, alternatives, and help you make the right choice for your business."
287|        
288|        return {
289|            "content": content,
290|            "meta_description": meta_description,
291|            "excerpt": excerpt,
292|            "seo_score": 85  # Good fallback score
293|        }
294|
295|# Initialize AI generator
296|ai_generator = AIContentGenerator()
297|
298|# Auto-publishing system
299|class AutoPublisher:
300|    def __init__(self):
301|        self.is_running = False
302|        self.daily_topics = [
303|            "Best CRM Software for Small Business",
304|            "Top Project Management Tools Comparison",
305|            "Email Marketing Automation Platforms",
306|            "Analytics Tools for Data-Driven Decisions",
307|            "Design Software for Non-Designers", 
308|            "Development Tools for Modern Teams",
309|            "Customer Support Solutions Review",
310|            "Accounting Software for Freelancers",
311|            "HR Management Systems Comparison",
312|            "Social Media Management Tools",
313|            "E-commerce Platform Showdown",
314|            "Sales Automation Software Guide",
315|            "Marketing Automation Best Practices",
316|            "Cloud Storage Solutions Compared",
317|            "Cybersecurity Tools for Small Business",
318|            "Productivity Apps That Actually Work",
319|            "Team Communication Platforms",
320|            "Business Intelligence Tools Review",
321|            "Content Management Systems Guide",
322|            "SEO Tools for Better Rankings"
323|        ]
324|        
325|    async def generate_and_publish_daily_content(self):
326|        """Generate and publish daily content automatically"""
327|        try:
328|            # Get a topic from the rotation
329|            topic_index = datetime.now().day % len(self.daily_topics)
330|            topic = self.daily_topics[topic_index]
331|            
332|            # Generate keywords based on topic
333|            keywords = self._generate_keywords(topic)
334|            category = self._determine_category(topic)
335|            
336|            # Generate content
337|            content_data = await ai_generator.generate_seo_article(
338|                topic=topic,
339|                category=category,
340|                keywords=keywords,
341|                target_length=2500
342|            )
343|            
344|            # Create blog post
345|            blog_post = BlogPost(
346|                title=topic,
347|                slug=slugify(topic),
348|                content=content_data["content"],
349|                excerpt=content_data["excerpt"],
350|                meta_description=content_data["meta_description"],
351|                keywords=keywords,
352|                category=category,
353|                tags=keywords[:5],
354|                seo_score=content_data["seo_score"],
355|                is_revenue_focused=True
356|            )
357|            
358|            # Save to database
359|            await db.blog_posts.insert_one(blog_post.dict())
360|            logging.info(f"Auto-published article: {topic}")
361|            
362|        except Exception as e:
363|            logging.error(f"Error in auto-publishing: {e}")
364|    
365|    def _generate_keywords(self, topic: str) -> List[str]:
366|        """Generate relevant keywords for a topic"""
367|        base_keywords = topic.lower().split()
368|        additional_keywords = ["saas", "software", "tool", "platform", "solution", "review", "comparison", "best", "top"]
369|        return base_keywords + additional_keywords[:7]
370|    
371|    def _determine_category(self, topic: str) -> str:
372|        """Determine category based on topic"""
373|        topic_lower = topic.lower()
374|        if "crm" in topic_lower:
375|            return "CRM Software"
376|        elif "project" in topic_lower or "management" in topic_lower:
377|            return "Project Management"
378|        elif "email" in topic_lower or "marketing" in topic_lower:
379|            return "Email Marketing"
380|        elif "analytics" in topic_lower:
381|            return "Analytics Tools"
382|        elif "design" in topic_lower:
383|            return "Design Tools"
384|        elif "development" in topic_lower:
385|            return "Development Tools"
386|        elif "support" in topic_lower:
387|            return "Customer Support"
388|        elif "accounting" in topic_lower:
389|            return "Accounting Software"
390|        elif "hr" in topic_lower:
391|            return "HR Management"
392|        elif "social" in topic_lower:
393|            return "Social Media Management"
394|        elif "ecommerce" in topic_lower or "e-commerce" in topic_lower:
395|            return "E-commerce Platforms"
396|        elif "sales" in topic_lower:
397|            return "Sales Tools"
398|        elif "cloud" in topic_lower or "storage" in topic_lower:
399|            return "Cloud Storage"
400|        elif "security" in topic_lower:
401|            return "Security Tools"
402|        elif "productivity" in topic_lower:
403|            return "Productivity Apps"
404|        elif "communication" in topic_lower:
405|            return "Communication Tools"
406|        elif "business intelligence" in topic_lower:
407|            return "Business Intelligence"
408|        elif "content" in topic_lower:
409|            return "Content Management"
410|        elif "seo" in topic_lower:
411|            return "SEO Tools"
412|        else:
413|            return "SaaS Tools"
414|
415|# Initialize auto-publisher
416|auto_publisher = AutoPublisher()
417|
418|# API Routes
419|@api_router.get("/")
420|async def root():
421|    return {"message": "SaaS Tools Digital - Autonomous Blog Platform API"}
422|
423|@api_router.post("/blog/generate", response_model=BlogPost)
424|async def generate_blog_post(request: ContentGenerationRequest):
425|    """Generate a new blog post with AI"""
426|    try:
427|        # Generate content
428|        content_data = await ai_generator.generate_seo_article(
429|            topic=request.topic,
430|            category=request.category,
431|            keywords=request.keywords,
432|            target_length=request.target_length
433|        )
434|        
435|        # Create blog post
436|        blog_post = BlogPost(
437|            title=request.topic,
438|            slug=slugify(request.topic),
439|            content=content_data["content"],
440|            excerpt=content_data["excerpt"],
441|            meta_description=content_data["meta_description"],
442|            keywords=request.keywords,
443|            category=request.category,
444|            tags=request.keywords[:5],
445|            seo_score=content_data["seo_score"],
446|            is_revenue_focused=request.include_affiliate_opportunities
447|        )
448|        
449|        # Save to database
450|        await db.blog_posts.insert_one(blog_post.dict())
451|        
452|        return blog_post
453|        
454|    except Exception as e:
455|        logging.error(f"Error generating blog post: {e}")
456|        raise HTTPException(status_code=500, detail="Failed to generate blog post")
457|
458|@api_router.get("/blog/posts", response_model=List[BlogPost])
459|async def get_blog_posts(skip: int = 0, limit: int = 10, category: Optional[str] = None):
460|    """Get all blog posts with pagination"""
461|    try:
462|        query = {"status": "published"}
463|        if category:
464|            query["category"] = category
465|            
466|        posts = await db.blog_posts.find(query).skip(skip).limit(limit).sort("published_at", -1).to_list(limit)
467|        return [BlogPost(**post) for post in posts]
468|        
469|    except Exception as e:
470|        logging.error(f"Error fetching blog posts: {e}")
471|        raise HTTPException(status_code=500, detail="Failed to fetch blog posts")
472|
473|@api_router.get("/blog/posts/{slug}", response_model=BlogPost)
474|async def get_blog_post(slug: str):
475|    """Get a specific blog post by slug"""
476|    try:
477|        post = await db.blog_posts.find_one({"slug": slug, "status": "published"})
478|        if not post:
479|            raise HTTPException(status_code=404, detail="Blog post not found")
480|            
481|        # Increment view count
482|        await db.blog_posts.update_one(
483|            {"slug": slug},
484|            {"$inc": {"view_count": 1}}
485|        )
486|        
487|        return BlogPost(**post)
488|        
489|    except HTTPException:
490|        raise
491|    except Exception as e:
492|        logging.error(f"Error fetching blog post: {e}")
493|        raise HTTPException(status_code=500, detail="Failed to fetch blog post")
494|
495|@api_router.post("/blog/posts/{post_id}/update", response_model=BlogPost)
496|async def update_blog_post(post_id: str, update_data: BlogPostUpdate):
497|    """Update a blog post"""
498|    try:
499|        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
500|        update_dict["updated_at"] = datetime.utcnow()
501|        
502|        if "title" in update_dict:
503|            update_dict["slug"] = slugify(update_dict["title"])
504|            
505|        result = await db.blog_posts.update_one(
506|            {"id": post_id},
507|            {"$set": update_dict}
508|        )
509|        
510|        if result.matched_count == 0:
511|            raise HTTPException(status_code=404, detail="Blog post not found")
512|            
513|        updated_post = await db.blog_posts.find_one({"id": post_id})
514|        return BlogPost(**updated_post)
515|        
516|    except HTTPException:
517|        raise
518|    except Exception as e:
519|        logging.error(f"Error updating blog post: {e}")
520|        raise HTTPException(status_code=500, detail="Failed to update blog post")
521|
522|@api_router.delete("/blog/posts/{post_id}")
523|async def delete_blog_post(post_id: str):
524|    """Delete a blog post"""
525|    try:
526|        result = await db.blog_posts.delete_one({"id": post_id})
527|        if result.deleted_count == 0:
528|            raise HTTPException(status_code=404, detail="Blog post not found")
529|            
530|        return {"message": "Blog post deleted successfully"}
531|        
532|    except HTTPException:
533|        raise
534|    except Exception as e:
535|        logging.error(f"Error deleting blog post: {e}")
536|        raise HTTPException(status_code=500, detail="Failed to delete blog post")
537|
538|@api_router.get("/blog/categories")
539|async def get_categories():
540|    """Get all available categories"""
541|    return {"categories": ai_generator.saas_categories}
542|
543|@api_router.post("/blog/auto-publish")
544|async def trigger_auto_publish():
545|    """Manually trigger auto-publishing"""
546|    try:
547|        await auto_publisher.generate_and_publish_daily_content()
548|        return {"message": "Auto-publish triggered successfully"}
549|    except Exception as e:
550|        logging.error(f"Error in manual auto-publish: {e}")
551|        raise HTTPException(status_code=500, detail="Failed to trigger auto-publish")
552|
553|@api_router.post("/blog/bulk-generate")
554|async def bulk_generate_articles(count: int = 20):
555|    """Generate multiple articles at once"""
556|    try:
557|        topics = [
558|            "Best CRM Software for Small Business 2025",
559|            "Top Project Management Tools Comparison",
560|            "Email Marketing Automation Platforms Review",
561|            "Analytics Tools for Data-Driven Decisions",
562|            "Design Software for Non-Designers Guide",
563|            "Development Tools for Modern Teams",
564|            "Customer Support Solutions Comparison",
565|            "Accounting Software for Freelancers",
566|            "HR Management Systems Review",
567|            "Social Media Management Tools Guide",
568|            "E-commerce Platform Showdown 2025",
569|            "Sales Automation Software Review",
570|            "Marketing Automation Best Practices",
571|            "Cloud Storage Solutions Compared",
572|            "Cybersecurity Tools for Small Business",
573|            "Productivity Apps That Actually Work",
574|            "Team Communication Platforms Guide",
575|            "Business Intelligence Tools Review",
576|            "Content Management Systems Comparison",
577|            "SEO Tools for Better Rankings 2025",
578|            "Invoicing Software for Small Business",
579|            "Video Conferencing Tools Comparison",
580|            "Password Managers for Teams",
581|            "Backup Solutions for Businesses",
582|            "Website Builders for Professionals"
583|        ]
584|        
585|        generated_count = 0
586|        for i in range(min(count, len(topics))):
587|            topic = topics[i]
588|            keywords = auto_publisher._generate_keywords(topic)
589|            category = auto_publisher._determine_category(topic)
590|            
591|            try:
592|                content_data = await ai_generator.generate_seo_article(
593|                    topic=topic,
594|                    category=category,
595|                    keywords=keywords,
596|                    target_length=2500
597|                )
598|                
599|                blog_post = BlogPost(
600|                    title=topic,
601|                    slug=slugify(topic),
602|                    content=content_data["content"],
603|                    excerpt=content_data["excerpt"],
604|                    meta_description=content_data["meta_description"],
605|                    keywords=keywords,
606|                    category=category,
607|                    tags=keywords[:5],
608|                    seo_score=content_data["seo_score"],
609|                    is_revenue_focused=True
610|                )
611|                
612|                await db.blog_posts.insert_one(blog_post.dict())
613|                generated_count += 1
614|                
615|                # Small delay to avoid rate limiting
616|                await asyncio.sleep(2)
617|                
618|            except Exception as e:
619|                logging.error(f"Error generating article '{topic}': {e}")
620|                continue
621|                
622|        return {"message": f"Successfully generated {generated_count} articles"}
623|        
624|    except Exception as e:
625|        logging.error(f"Error in bulk generation: {e}")
626|        raise HTTPException(status_code=500, detail="Failed to bulk generate articles")
627|
628|@api_router.get("/blog/stats")
629|async def get_blog_stats():
630|    """Get blog statistics"""
631|    try:
632|        total_posts = await db.blog_posts.count_documents({"status": "published"})
633|        total_views = await db.blog_posts.aggregate([
634|            {"$group": {"_id": None, "total_views": {"$sum": "$view_count"}}}
635|        ]).to_list(1)
636|        
637|        total_views = total_views[0]["total_views"] if total_views else 0
638|        
639|        # Get posts by category
640|        categories = await db.blog_posts.aggregate([
641|            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
642|        ]).to_list(100)
643|        
644|        return {
645|            "total_posts": total_posts,
646|            "total_views": total_views,
647|            "categories": categories
648|        }
649|        
650|    except Exception as e:
651|        logging.error(f"Error fetching blog stats: {e}")
652|        raise HTTPException(status_code=500, detail="Failed to fetch blog stats")
653|
654|# Background task for auto-publishing
655|async def schedule_auto_publish():
656|    """Schedule automatic publishing"""
657|    while True:
658|        try:
659|            # Publish daily at 9 AM UTC
660|            current_time = datetime.utcnow()
661|            if current_time.hour == 9 and current_time.minute == 0:
662|                await auto_publisher.generate_and_publish_daily_content()
663|                
664|            await asyncio.sleep(60)  # Check every minute
665|            
666|        except Exception as e:
667|            logging.error(f"Error in scheduled auto-publish: {e}")
668|            await asyncio.sleep(60)
669|
670|# Legacy status check endpoints
671|@api_router.post("/status")
672|async def create_status_check():
673|    return {"message": "Status check - Blog system operational"}
674|
675|@api_router.get("/status")
676|async def get_status_checks():
677|    return {"status": "operational", "system": "autonomous_blog_platform"}
678|
679|# Include the router in the main app
680|app.include_router(api_router)
681|
682|app.add_middleware(
683|    CORSMiddleware,
684|    allow_credentials=True,
685|    allow_origins=["*"],
686|    allow_methods=["*"],
687|    allow_headers=["*"],
688|)
689|
690|# Configure logging
691|logging.basicConfig(
692|    level=logging.INFO,
693|    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
694|)
695|logger = logging.getLogger(__name__)
696|
697|@app.on_event("startup")
698|async def startup_event():
699|    """Initialize the autonomous blog system"""
700|    logger.info("🚀 AUTONOMOUS SAAS TOOLS BLOG SYSTEM STARTING...")
701|    logger.info("📝 AI Content Generator: READY")
702|    logger.info("🤖 Auto-Publisher: READY")
703|    logger.info("💰 Revenue Focus: ACTIVATED")
704|    
705|    # Start auto-publishing scheduler in background
706|    asyncio.create_task(schedule_auto_publish())
707|
708|@app.on_event("shutdown")
709|async def shutdown_db_client():
710|    client.close()

