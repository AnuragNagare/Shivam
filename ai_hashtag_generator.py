from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uvicorn
import random
from datetime import datetime

app = FastAPI(
    title="🤖 Social Media Content Generator API",
    description="Generate captions and hashtags for social media posts",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContentRequest(BaseModel):
    topic: str = "travel"
    style: str = "casual"  # casual, professional, funny, inspirational
    platform: str = "instagram"  # instagram, twitter, facebook, tiktok
    include_hashtags: bool = True
    include_emoji: bool = True

class ContentResponse(BaseModel):
    success: bool = True
    message: str = "Content generated successfully"
    data: Dict[str, Any]

class ContentGenerator:
    def __init__(self):
        # Hashtag components
        self.modifiers = [
            "", "love", "daily", "life", "post", "gram", "world", "time", 
            "best", "addict", "inspiration", "motivation", "vibes"
        ]
        
        # Caption templates
        self.caption_templates = {
            "casual": [
                "Living my best {topic} life! {emoji}",
                "Can't get enough of {topic}! {emoji}",
                "Just another day loving {topic} {emoji}",
                "Hello from {topic}! {emoji}",
                "Living for these {topic} moments {emoji}"
            ],
            "professional": [
                "Exploring the world of {topic}. #ProfessionalVibes",
                "Engaging with {topic} on a whole new level.",
                "The art of {topic} never fails to inspire.",
                "Diving deep into the realm of {topic}.",
                "Mastering the craft of {topic}."
            ],
            "funny": [
                "Me pretending to know about {topic} like... {emoji}",
                "When someone says they don't like {topic}... {emoji}",
                "Me and {topic}? It's complicated. {emoji}",
                "No {topic}, no life! {emoji}",
                "I put the 'pro' in {topic}. Just kidding! {emoji}"
            ],
            "inspirational": [
                "Chasing {topic}, finding myself. {emoji}",
                "In a world full of trends, I choose {topic}. {emoji}",
                "The journey of a thousand miles begins with {topic}. {emoji}",
                "Dream it. Wish it. {topic.capitalize()} it. {emoji}",
                "Be the change you want to see in {topic}. {emoji}"
            ]
        }
        
        # Platform-specific adjustments
        self.platform_emojis = {
            "instagram": ["✨", "🌟", "💫", "🔥", "💯", "👑", "💖", "👏", "🙌", "🎯"],
            "twitter": ["🚀", "💡", "🔥", "⚡", "🎯", "💯", "🧵", "📈", "🌊", "✅"],
            "facebook": ["👍", "❤️", "😊", "🎉", "🌟", "💙", "🤝", "👪", "🏡", "🎯"],
            "tiktok": ["🎵", "💃", "🕺", "🔥", "✨", "🎉", "💯", "🤳", "🌟", "⚡"]
        }

    def _get_emoji(self, platform: str) -> str:
        return random.choice(self.platform_emojis.get(platform.lower(), ["✨"]))

    def generate_caption(self, topic: str, style: str = "casual", platform: str = "instagram") -> str:
        """Generate a caption based on the topic and style"""
        try:
            emoji = self._get_emoji(platform)
            template = random.choice(self.caption_templates.get(style, self.caption_templates["casual"]))
            return template.format(topic=topic, emoji=emoji)
        except:
            return f"Enjoying {topic}! {self._get_emoji(platform)}"

    def generate_hashtags(self, topic: str, count: int = 10) -> List[str]:
        """Generate relevant hashtags based on the topic"""
        try:
            topic = topic.lower().strip()
            base = topic.replace(" ", "")
            
            # Generate variations
            variations = {f"#{base}"}
            variations.add(f"#{base}s")
            
            # Add modified versions
            for mod in random.sample(self.modifiers, min(5, len(self.modifiers))):
                if mod:
                    variations.add(f"#{base}{mod}")
            
            # Add some generic popular ones
            popular = {
                "#viral", "#trending", "#explore", 
                "#instagood", "#photooftheday", "#love"
            }
            
            # Combine and randomize
            all_tags = list(variations.union(popular))
            random.shuffle(all_tags)
            
            return all_tags[:min(count, 30)]
            
        except:
            return [f"#{topic.replace(' ', '')}", "#viral", "#trending"]

# Initialize the generator
content_generator = ContentGenerator()

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "🚀 Social Media Content Generator API is running!",
        "endpoints": {
            "GET /generate": "Generate content (query params)",
            "POST /generate": "Generate content (JSON body)",
            "/docs": "Interactive API documentation"
        }
    }

@app.get("/generate", response_model=ContentResponse)
async def generate_content(
    topic: str = Query(..., description="Main topic for the content"),
    style: str = Query("casual", description="Content style: casual, professional, funny, inspirational"),
    platform: str = Query("instagram", description="Target platform: instagram, twitter, facebook, tiktok"),
    include_hashtags: bool = Query(True, description="Include hashtags in the response"),
    include_emoji: bool = Query(True, description="Include emojis in the caption")
):
    """Generate social media content with a single API call"""
    try:
        # Generate caption
        caption = content_generator.generate_caption(topic, style, platform)
        
        # Generate hashtags if requested
        hashtags = []
        if include_hashtags:
            hashtags = content_generator.generate_hashtags(topic, count=15)
        
        return {
            "success": True,
            "message": "Content generated successfully",
            "data": {
                "caption": caption,
                "hashtags": hashtags,
                "topic": topic,
                "style": style,
                "platform": platform,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate", response_model=ContentResponse)
async def generate_content_post(request: ContentRequest):
    """Generate social media content with a POST request"""
    try:
        # Generate caption
        caption = content_generator.generate_caption(
            request.topic, 
            request.style, 
            request.platform
        )
        
        # Generate hashtags if requested
        hashtags = []
        if request.include_hashtags:
            hashtags = content_generator.generate_hashtags(request.topic, count=15)
        
        return {
            "success": True,
            "message": "Content generated successfully",
            "data": {
                "caption": caption,
                "hashtags": hashtags,
                "topic": request.topic,
                "style": request.style,
                "platform": request.platform,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Social Media Content Generator API...")
    print(f"🌐 Access the API at: http://localhost:8000")
    print(f"📚 API Documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "ai_hashtag_generator:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    start_server()