from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import urllib.parse
import uvicorn

# Import the ContentHealthAnalyzer from web.py
from web import ContentHealthAnalyzer

# Initialize FastAPI app
app = FastAPI(
    title="Content Health Analyzer API",
    description="API for analyzing content health and optimization for different social media platforms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize the analyzer
analyzer = ContentHealthAnalyzer()

# Response Models
class AnalysisResponse(BaseModel):
    """Response model for content analysis"""
    scores: Dict[str, float]
    metrics: Dict[str, Any]
    analysis: Dict[str, List[str]]
    
    class Config:
        schema_extra = {
            "example": {
                "scores": {
                    "readability": 85.5,
                    "engagement": 78.2,
                    "platform_optimization": 92.0,
                    "overall": 85.2
                },
                "metrics": {
                    "word_count": 42,
                    "character_count": 250,
                    "emoji_count": 2,
                    "hashtag_count": 3,
                    "cta_present": True,
                    "question_present": False
                },
                "analysis": {
                    "improvements": [
                        "Add more emojis for better engagement",
                        "Include a question to encourage comments"
                    ],
                    "warnings": [
                        "Content is longer than optimal for Instagram"
                    ],
                    "strengths": [
                        "Good use of hashtags",
                        "Clear call-to-action present"
                    ]
                }
            }
        }

# Helper Functions
def format_analysis_result(analysis_result) -> Dict[str, Any]:
    """Format the analysis result into a structured response"""
    return {
        "scores": {
            "readability": analysis_result.readability_score,
            "engagement": analysis_result.engagement_score,
            "platform_optimization": analysis_result.platform_score,
            "overall": analysis_result.overall_score
        },
        "metrics": {
            "word_count": analysis_result.word_count,
            "character_count": analysis_result.character_count,
            "emoji_count": analysis_result.emoji_count,
            "hashtag_count": analysis_result.hashtag_count,
            "cta_present": analysis_result.cta_present,
            "question_present": analysis_result.question_present
        },
        "analysis": {
            "improvements": analysis_result.improvements,
            "warnings": analysis_result.warnings,
            "strengths": analysis_result.strengths
        }
    }

# API Endpoints
@app.get("/analyze", response_model=AnalysisResponse, summary="Analyze content health (GET)")
async def analyze_content_get(
    content: str = Query(..., description="The text content to analyze (can be multiple paragraphs)"),
    platform: str = Query("instagram", description="Target platform (instagram, facebook, twitter, linkedin, tiktok)"),
    image_description: Optional[str] = Query(None, description="Optional description of any accompanying image")
):
    """
    Analyze the health and optimization of content for a specific platform using GET request.
    
    - **content**: The text content to analyze (can be multiple paragraphs)
    - **platform**: Target platform (instagram, facebook, twitter, linkedin, tiktok)
    - **image_description**: Optional description of any accompanying image
    """
    try:
        # URL decode the content in case it's encoded
        content = urllib.parse.unquote(content)
        
        # Validate platform
        if platform.lower() not in analyzer.platform_guidelines:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform. Choose from: {', '.join(analyzer.platform_guidelines.keys())}"
            )
            
        # Run the analysis
        analysis_result = analyzer.analyze_content(
            caption=content,
            image_description=image_description or "",
            platform=platform.lower()
        )
        
        # Format the response
        return format_analysis_result(analysis_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Keep the existing POST endpoint for backward compatibility
@app.post("/analyze", response_model=AnalysisResponse, summary="Analyze content health (POST)")
async def analyze_content_post(request: dict):
    """
    Analyze the health and optimization of content for a specific platform using POST request.
    
    - **content**: The text content to analyze (can be multiple paragraphs)
    - **platform**: Target platform (instagram, facebook, twitter, linkedin, tiktok)
    - **image_description**: Optional description of any accompanying image
    """
    try:
        content = request.get("content", "")
        platform = request.get("platform", "instagram")
        image_description = request.get("image_description", "")
        
        # Validate platform
        if platform.lower() not in analyzer.platform_guidelines:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform. Choose from: {', '.join(analyzer.platform_guidelines.keys())}"
            )
            
        # Run the analysis
        analysis_result = analyzer.analyze_content(
            caption=content,
            image_description=image_description,
            platform=platform.lower()
        )
        
        # Format the response
        return format_analysis_result(analysis_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/platforms", summary="Get supported platforms")
async def get_supported_platforms():
    """Get list of supported platforms and their specifications"""
    platforms = {}
    for platform, specs in analyzer.platform_guidelines.items():
        platforms[platform] = {
            "optimal_length": f"{specs['optimal_length'][0]}-{specs['optimal_length'][1]} characters",
            "max_hashtags": specs['max_hashtags'],
            "optimal_hashtags": f"{specs['optimal_hashtags'][0]}-{specs['optimal_hashtags'][1]}",
            "emoji_friendly": specs['emoji_friendly'],
            "questions_boost_engagement": specs['questions_boost'],
            "cta_important": specs['cta_important']
        }
    
    return {
        "supported_platforms": list(analyzer.platform_guidelines.keys()),
        "platform_specs": platforms
    }

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Content Health Analyzer API is running",
        "documentation": "/docs or /redoc",
        "endpoints": [
            {"path": "/analyze", "method": "GET", "description": "Analyze content health (GET with query params)"},
            {"path": "/analyze", "method": "POST", "description": "Analyze content health (POST with JSON body)"},
            {"path": "/platforms", "method": "GET", "description": "Get supported platforms"}
        ]
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Content Health Analyzer API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8002, help="Port to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "content_health_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1
    )