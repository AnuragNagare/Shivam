from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uvicorn
from datetime import datetime
from enum import Enum

app = FastAPI(
    title="📜 Social Media Script Generator API",
    description="Generate engaging social media scripts based on topic, audience, and content type",
    version="1.0.0",
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

# Enums for validation
class Audience(str, Enum):
    GENERAL = "general"
    CREATORS = "creators"
    BUSINESS = "business"
    STUDENTS = "students"
    PROFESSIONALS = "professionals"

class ContentType(str, Enum):
    VIDEO = "video"
    CAROUSEL = "carousel"
    REEL = "reel"
    STORY = "story"
    TUTORIAL = "tutorial"
    THREAD = "thread"

class ScriptRequest(BaseModel):
    topic: str = Field(..., description="Main topic for the script")
    audience: Audience = Field(Audience.GENERAL, description="Target audience for the content")
    content_type: ContentType = Field(ContentType.VIDEO, description="Type of content to generate")
    include_hashtags: bool = Field(True, description="Include relevant hashtags in the response")
    max_length: int = Field(500, ge=100, le=2000, description="Maximum length of the script in characters")

class ScriptResponse(BaseModel):
    success: bool = True
    message: str = "Script generated successfully"
    data: Dict[str, Any]

class ScriptGenerator:
    def __init__(self):
        # Script templates for different content types and audiences
        self.templates = {
            "video": {
                "general": "Create a {length}-second video about {topic} that appeals to a wide audience. Start with an engaging hook, then explain the main points clearly.",
                "creators": "Make a {length}-second video for content creators about {topic}. Share practical tips and real-world examples they can apply.",
                "business": "Produce a professional {length}-second video about {topic} for business professionals. Focus on ROI, strategies, and actionable insights.",
                "students": "Create an educational {length}-second video about {topic} for students. Make it engaging and easy to understand with clear examples.",
                "professionals": "Develop a concise {length}-second video about {topic} for industry professionals. Include expert insights and practical applications."
            },
            "carousel": {
                "general": "Create a {length}-word carousel post about {topic} with 5-7 engaging slides. Each slide should have a clear heading and concise text.",
                "creators": "Design a {length}-word carousel for creators about {topic}. Each slide should offer practical tips or resources they can use.",
                "business": "Develop a {length}-word business-focused carousel about {topic}. Include statistics, case studies, and actionable insights.",
                "students": "Make an educational {length}-word carousel about {topic} for students. Use simple language and clear visuals.",
                "professionals": "Create a professional {length}-word carousel about {topic}. Focus on industry insights and advanced concepts."
            },
            "reel": {
                "general": "Script a {length}-character reel about {topic} that's engaging in the first 3 seconds. Keep it fun and easy to understand.",
                "creators": "Write a {length}-character reel script for creators about {topic}. Make it shareable and full of quick tips.",
                "business": "Create a {length}-character business reel about {topic}. Focus on quick, valuable insights professionals will love.",
                "students": "Draft a {length}-character educational reel about {topic}. Make it engaging and easy to remember.",
                "professionals": "Script a {length}-character professional reel about {topic}. Keep it concise and packed with value."
            },
            "story": {
                "general": "Write a {length}-character story about {topic} that will keep viewers engaged. Make it relatable and easy to follow.",
                "creators": "Create a {length}-character story for creators about {topic}. Share a personal experience or case study.",
                "business": "Develop a {length}-character business story about {topic}. Focus on challenges, solutions, and results.",
                "students": "Tell a {length}-character educational story about {topic}. Make it engaging and informative.",
                "professionals": "Craft a {length}-character professional story about {topic}. Include industry insights and lessons learned."
            },
            "tutorial": {
                "general": "Create a step-by-step tutorial about {topic} in {length} words. Start with an introduction, list materials if needed, then explain each step clearly.",
                "creators": "Write a detailed {length}-word tutorial for creators about {topic}. Include pro tips and common mistakes to avoid.",
                "business": "Develop a professional {length}-word tutorial about {topic}. Focus on practical applications and business benefits.",
                "students": "Create an easy-to-follow {length}-word tutorial about {topic} for students. Break it down into simple steps.",
                "professionals": "Write an advanced {length}-word tutorial about {topic} for professionals. Include technical details and best practices."
            },
            "thread": {
                "general": "Create a Twitter thread about {topic} with 5-7 tweets. Start with a hook, then build on each tweet. Total around {length} characters.",
                "creators": "Write a Twitter thread for creators about {topic}. Share valuable insights in {length} characters across 5-7 tweets.",
                "business": "Develop a professional Twitter thread about {topic}. Keep it under {length} characters across 5-7 insightful tweets.",
                "students": "Create an educational Twitter thread about {topic}. Make it engaging and informative in {length} characters.",
                "professionals": "Write a professional Twitter thread about {topic}. Share expert insights in {length} characters across 5-7 tweets."
            }
        }
        
        # Hashtag collections for different audiences
        self.audience_hashtags = {
            "general": ["#trending", "#viral", "#explore"],
            "creators": ["#creator", "#contentcreator", "#digitalcreator"],
            "business": ["#business", "#entrepreneur", "#startup"],
            "students": ["#student", "#education", "#learning"],
            "professionals": ["#professional", "#career", "#industry"]
        }
        
        # Content type specific hashtags
        self.content_hashtags = {
            "video": ["#video", "#videocontent", "#videoproduction"],
            "carousel": ["#carousel", "#slideshow", "#presentation"],
            "reel": ["#reel", "#reels", "#reelit"],
            "story": ["#story", "#stories", "#storytime"],
            "tutorial": ["#tutorial", "#howto", "#diy"],
            "thread": ["#thread", "#tweettorial", "#twitterthread"]
        }

    def _estimate_word_count(self, char_count: int) -> int:
        """Estimate word count from character count"""
        return max(1, char_count // 5)

    def _generate_hashtags(self, topic: str, audience: str, content_type: str, count: int = 5) -> List[str]:
        """Generate relevant hashtags"""
        # Clean the topic for hashtag
        base_hashtag = topic.lower().replace(" ", "")
        
        # Combine audience and content type hashtags
        hashtags = set()
        hashtags.update(self.audience_hashtags.get(audience, []))
        hashtags.update(self.content_hashtags.get(content_type, []))
        
        # Add topic variations
        hashtags.add(f"#{base_hashtag}")
        hashtags.add(f"#{base_hashtag}{content_type}")
        
        # Convert to list and limit count
        return list(hashtags)[:count]

    def generate_script(self, request: ScriptRequest) -> Dict[str, Any]:
        """Generate a script based on the request parameters"""
        try:
            # Get the appropriate template
            template = self.templates[request.content_type.value].get(
                request.audience.value,
                self.templates[request.content_type.value]["general"]
            )
            
            # Calculate length parameters
            word_count = self._estimate_word_count(request.max_length)
            char_count = request.max_length
            
            # Format the prompt
            prompt = template.format(
                topic=request.topic,
                length=word_count if request.content_type in ["tutorial", "carousel"] else char_count
            )
            
            # Generate hashtags if requested
            hashtags = []
            if request.include_hashtags:
                hashtags = self._generate_hashtags(
                    request.topic,
                    request.audience.value,
                    request.content_type.value
                )
            
            return {
                "script": prompt,
                "topic": request.topic,
                "audience": request.audience.value,
                "content_type": request.content_type.value,
                "word_count": word_count,
                "character_count": char_count,
                "hashtags": hashtags,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating script: {str(e)}")

# Initialize the generator
script_generator = ScriptGenerator()

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "🚀 Social Media Script Generator API is running!",
        "endpoints": {
            "GET /generate": "Generate script (query params)",
            "POST /generate": "Generate script (JSON body)",
            "/docs": "Interactive API documentation"
        },
        "audience_types": [e.value for e in Audience],
        "content_types": [e.value for e in ContentType]
    }

@app.get("/generate", response_model=ScriptResponse)
async def generate_script(
    topic: str = Query(..., description="Main topic for the script"),
    audience: Audience = Query(Audience.GENERAL, description="Target audience for the content"),
    content_type: ContentType = Query(ContentType.VIDEO, description="Type of content to generate"),
    include_hashtags: bool = Query(True, description="Include relevant hashtags in the response"),
    max_length: int = Query(500, ge=100, le=2000, description="Maximum length of the script in characters")
):
    """
    Generate a social media script using GET request with query parameters
    """
    request = ScriptRequest(
        topic=topic,
        audience=audience,
        content_type=content_type,
        include_hashtags=include_hashtags,
        max_length=max_length
    )
    
    result = script_generator.generate_script(request)
    return {
        "success": True,
        "message": f"Successfully generated {content_type.value} script",
        "data": result
    }

@app.post("/generate", response_model=ScriptResponse)
async def generate_script_post(request: ScriptRequest):
    """
    Generate a social media script using POST request with JSON body
    """
    result = script_generator.generate_script(request)
    return {
        "success": True,
        "message": f"Successfully generated {request.content_type.value} script",
        "data": result
    }

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Script Generator API...")
    print(f"🌐 Access the API at: http://localhost:8001")
    print(f"📚 API Documentation: http://localhost:8001/docs")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "script_generator:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )

if __name__ == "__main__":
    start_server()
