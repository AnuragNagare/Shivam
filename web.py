import streamlit as st
import re
import math
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
from dataclasses import dataclass
import plotly.graph_objects as go
import plotly.express as px
from urllib.parse import urlparse

# Set page config
st.set_page_config(
    page_title="Content Health Score Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .score-excellent {
        color: #4CAF50;
        font-weight: bold;
        font-size: 24px;
    }
    .score-good {
        color: #FF9800;
        font-weight: bold;
        font-size: 24px;
    }
    .score-poor {
        color: #f44336;
        font-weight: bold;
        font-size: 24px;
    }
    .improvement-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
    }
    .warning-box {
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #FF9800;
    }
    .success-box {
        background-color: #e8f5e8;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class SocialPost:
    platform: str
    content: str
    hashtags: str
    character_count: int
    post_type: str
    tips: List[str]

@dataclass
class ContentAnalysis:
    readability_score: float
    engagement_score: float
    platform_score: float
    overall_score: float
    word_count: int
    character_count: int
    emoji_count: int
    hashtag_count: int
    cta_present: bool
    question_present: bool
    improvements: List[str]
    warnings: List[str]
    strengths: List[str]

class BlogToSocialConverter:
    def __init__(self):
        self.platform_specs = {
            'instagram': {
                'max_chars': 2200,
                'optimal_chars': (150, 300),
                'hashtag_limit': 30,
                'optimal_hashtags': (10, 20),
                'emoji_friendly': True,
                'post_types': ['single_post', 'carousel', 'story']
            },
            'facebook': {
                'max_chars': 63206,
                'optimal_chars': (100, 400),
                'hashtag_limit': 5,
                'optimal_hashtags': (1, 3),
                'emoji_friendly': True,
                'post_types': ['single_post', 'long_form']
            },
            'twitter': {
                'max_chars': 280,
                'optimal_chars': (71, 240),
                'hashtag_limit': 3,
                'optimal_hashtags': (1, 2),
                'emoji_friendly': True,
                'post_types': ['single_tweet', 'thread']
            },
            'linkedin': {
                'max_chars': 3000,
                'optimal_chars': (200, 600),
                'hashtag_limit': 10,
                'optimal_hashtags': (3, 5),
                'emoji_friendly': False,
                'post_types': ['single_post', 'article_promo']
            },
            'tiktok': {
                'max_chars': 150,
                'optimal_chars': (50, 120),
                'hashtag_limit': 10,
                'optimal_hashtags': (3, 7),
                'emoji_friendly': True,
                'post_types': ['video_caption']
            }
        }
        
        # Brand voice templates
        self.voice_templates = {
            'professional': {
                'intro_phrases': ["Exploring", "Diving into", "Understanding", "Analyzing"],
                'transition_phrases': ["Furthermore", "Additionally", "Moreover", "Key insight:"],
                'conclusion_phrases': ["In conclusion", "The bottom line", "Key takeaway", "To summarize"],
                'cta_phrases': ["Share your thoughts", "What's your experience?", "Connect with me", "Learn more"]
            },
            'casual': {
                'intro_phrases': ["So I've been thinking about", "Let's talk about", "Here's the thing about", "You know what's interesting?"],
                'transition_phrases': ["And here's the cool part", "But wait, there's more", "Plot twist", "Here's what's crazy"],
                'conclusion_phrases': ["So yeah", "Bottom line", "Long story short", "Here's the deal"],
                'cta_phrases': ["Let me know what you think!", "Drop a comment", "Tag a friend", "What do you think?"]
            },
            'educational': {
                'intro_phrases': ["Today we're exploring", "Let's break down", "Understanding", "Did you know"],
                'transition_phrases': ["Step 1:", "Next,", "Important note:", "Here's why this matters:"],
                'conclusion_phrases': ["Remember:", "Key learning:", "Takeaway:", "To recap:"],
                'cta_phrases': ["Save this for later", "Share to help others", "Questions? Comment below", "Want to learn more?"]
            },
            'inspirational': {
                'intro_phrases': ["Imagine if", "What if I told you", "Here's a powerful truth", "Success story:"],
                'transition_phrases': ["But here's the magic", "The transformation happens when", "This is where it gets exciting", "The secret is"],
                'conclusion_phrases': ["You have the power to", "Your journey starts now", "Believe in yourself", "The time is now"],
                'cta_phrases': ["Tag someone who needs this", "Share if this inspired you", "What's your next step?", "Ready to take action?"]
            }
        }

    def extract_content_from_url(self, url: str) -> Dict[str, str]:
        """Extract content from blog URL"""
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {"error": "Invalid URL format"}
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()
            
            # Extract main content
            content_selectors = [
                'article', '.post-content', '.entry-content', '.content',
                '.post-body', 'main', '.article-body', '[role="main"]'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text()
                    break
            
            # Fallback to body if no specific content found
            if not content:
                content = soup.get_text()
            
            # Clean up content
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Extract key sections
            paragraphs = [p.strip() for p in content.split('\n') if len(p.strip()) > 50]
            
            return {
                "title": title,
                "content": content,
                "paragraphs": paragraphs[:10],  # Limit to first 10 paragraphs
                "word_count": len(content.split()),
                "char_count": len(content)
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch URL: {str(e)}"}
        except Exception as e:
            return {"error": f"Error processing content: {str(e)}"}

    def extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """Extract key points from long-form content"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Score sentences based on keywords and position
        scored_sentences = []
        
        # Important keywords that indicate key points
        key_indicators = [
            'important', 'key', 'essential', 'crucial', 'significant', 'main', 'primary',
            'first', 'second', 'third', 'finally', 'conclusion', 'result', 'benefit',
            'advantage', 'solution', 'tip', 'strategy', 'method', 'approach'
        ]
        
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_lower = sentence.lower()
            
            # Keyword scoring
            for keyword in key_indicators:
                if keyword in sentence_lower:
                    score += 2
            
            # Length scoring (prefer medium-length sentences)
            word_count = len(sentence.split())
            if 10 <= word_count <= 25:
                score += 1
            
            # Position scoring (beginning and end are important)
            if i < len(sentences) * 0.2:  # First 20%
                score += 1
            elif i > len(sentences) * 0.8:  # Last 20%
                score += 1
            
            # Numbers and lists are often key points
            if re.search(r'\d+', sentence):
                score += 1
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and return top points
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        return [sentence for score, sentence in scored_sentences[:max_points]]

    def create_platform_post(self, key_points: List[str], title: str, platform: str, 
                           voice: str = "professional", post_type: str = "single_post") -> SocialPost:
        """Create platform-specific social media post"""
        
        specs = self.platform_specs[platform]
        voice_template = self.voice_templates[voice]
        
        if platform == 'twitter' and post_type == 'thread':
            return self._create_twitter_thread(key_points, title, voice_template)
        elif platform == 'instagram' and post_type == 'carousel':
            return self._create_instagram_carousel(key_points, title, voice_template)
        else:
            return self._create_single_post(key_points, title, platform, voice_template, post_type)

    def _create_single_post(self, key_points: List[str], title: str, platform: str, voice_template: Dict, post_type: str = "single_post") -> SocialPost:
        """Create a single social media post"""
        import random
        
        specs = self.platform_specs[platform]
        optimal_min, optimal_max = specs['optimal_chars']
        
        # Build post content
        intro = random.choice(voice_template['intro_phrases'])
        conclusion = random.choice(voice_template['conclusion_phrases'])
        cta = random.choice(voice_template['cta_phrases'])
        
        # Start with title/intro
        content = f"{intro} {title.lower() if title else 'this topic'}.\n\n"
        
        # Add key points
        for i, point in enumerate(key_points[:3], 1):
            # Shorten point if needed
            if len(point) > 100:
                point = point[:97] + "..."
            
            if platform == 'linkedin':
                content += f"🔹 {point}\n\n"
            else:
                content += f"{i}. {point}\n\n"
        
        # Add conclusion and CTA
        content += f"{conclusion}: {key_points[0] if key_points else 'Quality content drives results.'}\n\n"
        content += f"{cta}"
        
        # Trim if too long
        if len(content) > optimal_max:
            # Remove points until it fits
            while len(content) > optimal_max and '\n\n' in content:
                lines = content.split('\n\n')
                if len(lines) > 3:
                    lines.pop(-3)  # Remove a middle point
                    content = '\n\n'.join(lines)
                else:
                    break
        
        # Generate hashtags
        hashtags = self._generate_hashtags(title + " " + " ".join(key_points), platform)
        
        # Platform-specific tips
        tips = []
        if platform == 'instagram':
            tips = ["Add a relevant image", "Use Stories to drive traffic", "Engage with comments quickly"]
        elif platform == 'linkedin':
            tips = ["Post during business hours", "Tag relevant connections", "Share industry insights"]
        elif platform == 'twitter':
            tips = ["Tweet during peak hours", "Use trending hashtags", "Engage with replies"]
        elif platform == 'facebook':
            tips = ["Ask questions to boost engagement", "Share to relevant groups", "Use Facebook Insights"]
        elif platform == 'tiktok':
            tips = ["Create engaging video content", "Use trending sounds", "Add text overlays"]
        
        return SocialPost(
            platform=platform.title(),
            content=content,
            hashtags=hashtags,
            character_count=len(content),
            post_type=post_type,
            tips=tips
        )

    def _create_twitter_thread(self, key_points: List[str], title: str, voice_template: Dict) -> SocialPost:
        """Create a Twitter thread"""
        import random
        
        intro = random.choice(voice_template['intro_phrases'])
        cta = random.choice(voice_template['cta_phrases'])
        
        thread_content = f"🧵 THREAD: {intro} {title.lower() if title else 'this important topic'}\n\n"
        
        # Add numbered tweets
        for i, point in enumerate(key_points[:7], 2):  # Start from 2/ since 1/ is intro
            if len(point) > 200:
                point = point[:197] + "..."
            thread_content += f"{i}/ {point}\n\n"
        
        # Add conclusion tweet
        thread_content += f"{len(key_points)+2}/ {cta}\n\n"
        thread_content += "♻️ Retweet the first tweet if this was helpful!"
        
        hashtags = self._generate_hashtags(title + " " + " ".join(key_points), 'twitter')
        
        return SocialPost(
            platform="Twitter",
            content=thread_content,
            hashtags=hashtags,
            character_count=len(thread_content),
            post_type="thread",
            tips=["Pin the thread to your profile", "Engage with replies", "Share insights in comments"]
        )

    def _create_instagram_carousel(self, key_points: List[str], title: str, voice_template: Dict) -> SocialPost:
        """Create Instagram carousel post"""
        import random
        
        intro = random.choice(voice_template['intro_phrases'])
        cta = random.choice(voice_template['cta_phrases'])
        
        carousel_content = f"📸 CAROUSEL POST: {intro} {title.lower() if title else 'this topic'}\n\n"
        carousel_content += "Swipe for the complete breakdown! ➡️\n\n"
        
        # Slide breakdown
        carousel_content += "SLIDE 1: Cover/Title\n"
        carousel_content += f"SLIDE 2-{min(len(key_points)+1, 10)}: Key points\n"
        
        for i, point in enumerate(key_points[:8], 1):
            if len(point) > 80:
                point = point[:77] + "..."
            carousel_content += f"• Slide {i+1}: {point}\n"
        
        carousel_content += f"\nLAST SLIDE: {cta}\n"
        
        hashtags = self._generate_hashtags(title + " " + " ".join(key_points), 'instagram')
        
        return SocialPost(
            platform="Instagram",
            content=carousel_content,
            hashtags=hashtags,
            character_count=len(carousel_content),
            post_type="carousel",
            tips=["Design visually appealing slides", "Use consistent colors/fonts", "Include your branding"]
        )

    def _generate_hashtags(self, content: str, platform: str) -> str:
        """Generate relevant hashtags from content"""
        specs = self.platform_specs[platform]
        
        # Extract potential hashtag words
        words = re.findall(r'\b\w{4,}\b', content.lower())
        
        # Common hashtag mappings
        hashtag_map = {
            'business': ['#business', '#entrepreneur', '#success', '#growth'],
            'marketing': ['#marketing', '#digitalmarketing', '#socialmedia', '#branding'],
            'technology': ['#technology', '#tech', '#innovation', '#digital'],
            'lifestyle': ['#lifestyle', '#motivation', '#inspiration', '#life'],
            'education': ['#education', '#learning', '#knowledge', '#tips'],
            'health': ['#health', '#wellness', '#fitness', '#selfcare'],
            'finance': ['#finance', '#money', '#investing', '#wealth'],
            'productivity': ['#productivity', '#efficiency', '#timemanagement', '#success']
        }
        
        # Generate hashtags based on content
        hashtags = set()
        
        for word in words:
            for key, tags in hashtag_map.items():
                if key in word or word in key:
                    hashtags.update(tags[:2])
        
        # Add generic high-performing hashtags
        generic_hashtags = {
            'instagram': ['#instagood', '#photooftheday', '#motivation'],
            'twitter': ['#trending', '#tips', '#mondaymotivation'],
            'linkedin': ['#leadership', '#professional', '#networking'],
            'facebook': ['#inspiration', '#community', '#sharing'],
            'tiktok': ['#fyp', '#viral', '#tips']
        }
        
        hashtags.update(generic_hashtags.get(platform, [])[:2])
        
        # Limit to platform specifications
        hashtag_list = list(hashtags)[:specs['optimal_hashtags'][1]]
        
        return ' '.join(hashtag_list)

class ContentHealthAnalyzer:
    def __init__(self):
        # Platform-specific guidelines
        self.platform_guidelines = {
            'instagram': {
                'optimal_length': (100, 300),
                'max_hashtags': 30,
                'optimal_hashtags': (10, 20),
                'emoji_friendly': True,
                'questions_boost': True,
                'cta_important': True
            },
            'facebook': {
                'optimal_length': (40, 200),
                'max_hashtags': 5,
                'optimal_hashtags': (1, 3),
                'emoji_friendly': True,
                'questions_boost': True,
                'cta_important': True
            },
            'twitter': {
                'optimal_length': (71, 240),
                'max_hashtags': 3,
                'optimal_hashtags': (1, 2),
                'emoji_friendly': True,
                'questions_boost': True,
                'cta_important': False
            },
            'linkedin': {
                'optimal_length': (150, 400),
                'max_hashtags': 10,
                'optimal_hashtags': (3, 5),
                'emoji_friendly': False,
                'questions_boost': True,
                'cta_important': True
            },
            'tiktok': {
                'optimal_length': (50, 150),
                'max_hashtags': 10,
                'optimal_hashtags': (3, 7),
                'emoji_friendly': True,
                'questions_boost': True,
                'cta_important': True
            }
        }
        
        # Engagement trigger words
        self.engagement_words = {
            'high': ['amazing', 'incredible', 'awesome', 'fantastic', 'perfect', 'love', 'beautiful', 'stunning'],
            'medium': ['great', 'good', 'nice', 'cool', 'interesting', 'wonderful', 'excellent'],
            'cta': ['comment', 'share', 'like', 'follow', 'subscribe', 'save', 'tag', 'dm', 'click', 'swipe']
        }
        
        # Common readability issues
        self.readability_patterns = {
            'long_sentences': r'[.!?]+',
            'complex_words': r'\b\w{12,}\b',
            'caps_abuse': r'\b[A-Z]{3,}\b',
            'excessive_punctuation': r'[!?]{2,}'
        }

    def extract_features(self, text: str) -> Dict:
        """Extract basic features from text"""
        features = {
            'word_count': len(text.split()),
            'character_count': len(text),
            'sentence_count': len(re.findall(r'[.!?]+', text)),
            'emoji_count': len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text)),
            'hashtag_count': len(re.findall(r'#\w+', text)),
            'mention_count': len(re.findall(r'@\w+', text)),
            'url_count': len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)),
            'question_marks': len(re.findall(r'\?', text)),
            'exclamation_marks': len(re.findall(r'!', text))
        }
        
        # Check for CTA presence
        cta_words = ['comment', 'share', 'like', 'follow', 'subscribe', 'save', 'tag', 'dm', 'click', 'swipe', 'link in bio']
        features['cta_present'] = any(word in text.lower() for word in cta_words)
        features['question_present'] = '?' in text
        
        return features

    def calculate_readability_score(self, text: str, features: Dict) -> Tuple[float, List[str], List[str]]:
        """Calculate readability score based on text complexity"""
        score = 100.0
        issues = []
        strengths = []
        
        # Average sentence length
        if features['sentence_count'] > 0:
            avg_sentence_length = features['word_count'] / features['sentence_count']
            if avg_sentence_length > 20:
                score -= 15
                issues.append("Sentences are too long. Aim for 15-20 words per sentence.")
            elif avg_sentence_length <= 15:
                strengths.append("Good sentence length for readability")
        
        # Complex words
        complex_words = len(re.findall(r'\b\w{12,}\b', text))
        if complex_words > 2:
            score -= 10
            issues.append("Too many complex words. Use simpler alternatives.")
        
        # ALL CAPS abuse
        caps_words = len(re.findall(r'\b[A-Z]{3,}\b', text))
        if caps_words > 1:
            score -= 20
            issues.append("Avoid excessive ALL CAPS - it appears aggressive")
        elif caps_words == 0:
            strengths.append("Good use of capitalization")
        
        # Excessive punctuation
        excessive_punct = len(re.findall(r'[!?]{3,}', text))
        if excessive_punct > 0:
            score -= 15
            issues.append("Avoid excessive punctuation (!!!, ???)")
        
        # Line breaks and structure
        lines = text.split('\n')
        if len(lines) > 1:
            strengths.append("Good use of line breaks for structure")
            score += 5
        
        return max(0, score), issues, strengths

    def calculate_engagement_score(self, text: str, features: Dict, image_description: str = "") -> Tuple[float, List[str], List[str]]:
        """Calculate engagement potential score"""
        score = 0.0
        issues = []
        strengths = []
        
        # Emotional words
        text_lower = text.lower()
        high_emotion_count = sum(1 for word in self.engagement_words['high'] if word in text_lower)
        medium_emotion_count = sum(1 for word in self.engagement_words['medium'] if word in text_lower)
        
        emotion_score = (high_emotion_count * 10) + (medium_emotion_count * 5)
        score += min(emotion_score, 30)
        
        if high_emotion_count > 0:
            strengths.append(f"Uses {high_emotion_count} high-impact emotional words")
        elif medium_emotion_count == 0 and high_emotion_count == 0:
            issues.append("Add emotional words to increase engagement")
        
        # Questions boost engagement
        if features['question_present']:
            score += 15
            strengths.append("Includes question to boost engagement")
        else:
            issues.append("Consider adding a question to encourage comments")
        
        # Call-to-action
        if features['cta_present']:
            score += 20
            strengths.append("Includes clear call-to-action")
        else:
            issues.append("Add a call-to-action (like, share, comment)")
        
        # Emoji usage
        if features['emoji_count'] > 0 and features['emoji_count'] <= 5:
            score += 10
            strengths.append("Good emoji usage for visual appeal")
        elif features['emoji_count'] > 5:
            score -= 5
            issues.append("Too many emojis - use 3-5 for best results")
        else:
            issues.append("Add 2-3 relevant emojis for visual appeal")
        
        # Image-text synergy
        if image_description:
            # Simple keyword matching between text and image
            text_words = set(text_lower.split())
            image_words = set(image_description.lower().split())
            common_words = len(text_words.intersection(image_words))
            
            if common_words >= 2:
                score += 15
                strengths.append("Good text-image alignment")
            else:
                issues.append("Ensure text relates to the image content")
        
        return min(score, 100), issues, strengths

    def calculate_platform_score(self, text: str, features: Dict, platform: str) -> Tuple[float, List[str], List[str]]:
        """Calculate platform-specific optimization score"""
        score = 100.0
        issues = []
        strengths = []
        
        guidelines = self.platform_guidelines.get(platform.lower(), self.platform_guidelines['instagram'])
        
        # Length optimization
        optimal_min, optimal_max = guidelines['optimal_length']
        char_count = features['character_count']
        
        if optimal_min <= char_count <= optimal_max:
            strengths.append(f"Perfect length for {platform} ({char_count} characters)")
        elif char_count < optimal_min:
            score -= 15
            issues.append(f"Too short for {platform}. Aim for {optimal_min}-{optimal_max} characters")
        else:
            score -= 10
            issues.append(f"Too long for {platform}. Aim for {optimal_min}-{optimal_max} characters")
        
        # Hashtag optimization
        hashtag_count = features['hashtag_count']
        optimal_hashtag_min, optimal_hashtag_max = guidelines['optimal_hashtags']
        
        if optimal_hashtag_min <= hashtag_count <= optimal_hashtag_max:
            strengths.append(f"Good hashtag count for {platform}")
        elif hashtag_count < optimal_hashtag_min:
            score -= 10
            issues.append(f"Add more hashtags. Use {optimal_hashtag_min}-{optimal_hashtag_max} for {platform}")
        elif hashtag_count > guidelines['max_hashtags']:
            score -= 20
            issues.append(f"Too many hashtags for {platform}. Maximum: {guidelines['max_hashtags']}")
        
        # Platform-specific features
        if not guidelines['emoji_friendly'] and features['emoji_count'] > 2:
            score -= 10
            issues.append(f"Limit emojis for {platform} - use sparingly")
        
        if guidelines['cta_important'] and not features['cta_present']:
            score -= 15
            issues.append(f"Add call-to-action - important for {platform}")
        
        return max(0, score), issues, strengths

    def analyze_content(self, caption: str, image_description: str = "", platform: str = "instagram") -> ContentAnalysis:
        """Perform complete content analysis"""
        
        # Extract features
        features = self.extract_features(caption)
        
        # Calculate individual scores
        readability_score, read_issues, read_strengths = self.calculate_readability_score(caption, features)
        engagement_score, eng_issues, eng_strengths = self.calculate_engagement_score(caption, features, image_description)
        platform_score, plat_issues, plat_strengths = self.calculate_platform_score(caption, features, platform)
        
        # Calculate overall score (weighted average)
        overall_score = (readability_score * 0.3 + engagement_score * 0.4 + platform_score * 0.3)
        
        # Combine all feedback
        all_issues = read_issues + eng_issues + plat_issues
        all_strengths = read_strengths + eng_strengths + plat_strengths
        
        return ContentAnalysis(
            readability_score=readability_score,
            engagement_score=engagement_score,
            platform_score=platform_score,
            overall_score=overall_score,
            word_count=features['word_count'],
            character_count=features['character_count'],
            emoji_count=features['emoji_count'],
            hashtag_count=features['hashtag_count'],
            cta_present=features['cta_present'],
            question_present=features['question_present'],
            improvements=all_issues,
            warnings=[],  # We'll add critical warnings separately
            strengths=all_strengths
        )

def get_score_color_class(score: float) -> str:
    """Get CSS class based on score"""
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    else:
        return "score-poor"

def get_score_emoji(score: float) -> str:
    """Get emoji based on score"""
    if score >= 90:
        return "🎯"
    elif score >= 80:
        return "🔥"
    elif score >= 70:
        return "✅"
    elif score >= 60:
        return "⚠️"
    else:
        return "❌"

def create_score_gauge(score: float, title: str) -> go.Figure:
    """Create a gauge chart for scores"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'converted_posts' not in st.session_state:
    st.session_state.converted_posts = []
if 'blog_content' not in st.session_state:
    st.session_state.blog_content = None

# Main App
def main():
    st.title("🎯 Content Health Score Analyzer")
    st.markdown("**Analyze your content quality and convert blogs to social posts**")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Analysis Settings")
        
        platform = st.selectbox(
            "Target Platform",
            ["Instagram", "Facebook", "Twitter", "LinkedIn", "TikTok"],
            help="Choose the platform you're optimizing for"
        )
        
        st.markdown("---")
        st.markdown("### 🎯 Scoring Criteria")
        st.markdown("- **Readability (30%)**: Text clarity and structure")
        st.markdown("- **Engagement (40%)**: Potential to drive interactions") 
        st.markdown("- **Platform Fit (30%)**: Platform-specific optimization")
        
        st.markdown("---")
        st.markdown("### 📈 Score Guide")
        st.markdown("- 🎯 **90-100**: Excellent")
        st.markdown("- 🔥 **80-89**: Very Good") 
        st.markdown("- ✅ **70-79**: Good")
        st.markdown("- ⚠️ **60-69**: Needs Improvement")
        st.markdown("- ❌ **Below 60**: Poor")
        
        st.markdown("---")
        st.markdown("### 🔄 Blog Converter")
        st.markdown("- Extract key points from blogs")
        st.markdown("- Generate platform-specific posts")
        st.markdown("- Maintain brand voice")
        st.markdown("- Multiple post formats")
    
    # Create main tabs
    tab1, tab2 = st.tabs(["🎯 Content Health Analyzer", "🔄 Blog to Social Converter"])
    
    with tab1:
        # Original Content Health Analyzer
        col1, col2 = st.columns([1.2, 0.8])
        
        with col1:
            st.header("📝 Content Input")
            
            # Caption input
            caption = st.text_area(
                "Enter your caption:",
                placeholder="Paste your social media caption here...",
                height=150,
                help="Enter the complete caption including hashtags"
            )
            
            # Image description input
            image_description = st.text_area(
                "Describe your image (optional):",
                placeholder="e.g., Person drinking coffee in a cozy cafe, product shot of new sneakers, etc.",
                height=80,
                help="Describe what's in your image to analyze text-image alignment"
            )
            
            # Analyze button
            analyze_btn = st.button("🔍 Analyze Content Health", type="primary", use_container_width=True)
            
            if analyze_btn:
                if not caption.strip():
                    st.error("Please enter a caption to analyze!")
                else:
                    with st.spinner("🤖 Analyzing your content..."):
                        analyzer = ContentHealthAnalyzer()
                        analysis = analyzer.analyze_content(caption, image_description, platform)
                        st.session_state.analysis_result = analysis
        
        with col2:
            st.header("📊 Quick Stats")
            
            if caption:
                # Real-time stats
                word_count = len(caption.split())
                char_count = len(caption)
                emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', caption))
                hashtag_count = len(re.findall(r'#\w+', caption))
                
                st.metric("Word Count", word_count)
                st.metric("Character Count", char_count)
                st.metric("Emojis", emoji_count)
                st.metric("Hashtags", hashtag_count)
            else:
                st.info("Enter caption to see live stats")
        
        # Display analysis results
        if st.session_state.analysis_result:
            analysis = st.session_state.analysis_result
            
            st.markdown("---")
            st.header("📈 Content Health Analysis")
            
            # Overall score display
            col_score1, col_score2, col_score3 = st.columns(3)
            
            with col_score1:
                score_emoji = get_score_emoji(analysis.overall_score)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🎯 Overall Health Score</h3>
                    <div class="{get_score_color_class(analysis.overall_score)}">
                        {score_emoji} {analysis.overall_score:.1f}/100
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_score2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📖 Readability</h3>
                    <div class="{get_score_color_class(analysis.readability_score)}">
                        {analysis.readability_score:.1f}/100
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_score3:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🚀 Engagement Potential</h3>
                    <div class="{get_score_color_class(analysis.engagement_score)}">
                        {analysis.engagement_score:.1f}/100
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Detailed analysis tabs
            analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["📊 Score Breakdown", "💡 Improvements", "✅ Strengths"])
            
            with analysis_tab1:
                # Gauge charts
                col_gauge1, col_gauge2, col_gauge3 = st.columns(3)
                
                with col_gauge1:
                    fig1 = create_score_gauge(analysis.readability_score, "Readability")
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col_gauge2:
                    fig2 = create_score_gauge(analysis.engagement_score, "Engagement")
                    st.plotly_chart(fig2, use_container_width=True)
                
                with col_gauge3:
                    fig3 = create_score_gauge(analysis.platform_score, f"{platform} Optimization")
                    st.plotly_chart(fig3, use_container_width=True)
                
                # Content metrics
                st.subheader("📋 Content Metrics")
                
                col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                
                with col_met1:
                    st.metric("Words", analysis.word_count)
                with col_met2:
                    st.metric("Characters", analysis.character_count) 
                with col_met3:
                    st.metric("Emojis", analysis.emoji_count)
                with col_met4:
                    st.metric("Hashtags", analysis.hashtag_count)
            
            with analysis_tab2:
                st.subheader("🔧 Improvement Suggestions")
                
                if analysis.improvements:
                    for i, improvement in enumerate(analysis.improvements, 1):
                        st.markdown(f"""
                        <div class="improvement-box">
                            <strong>{i}.</strong> {improvement}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="success-box">
                        🎉 <strong>Excellent!</strong> No major improvements needed. Your content is well-optimized!
                    </div>
                    """, unsafe_allow_html=True)
            
            with analysis_tab3:
                st.subheader("💪 Content Strengths")
                
                if analysis.strengths:
                    for i, strength in enumerate(analysis.strengths, 1):
                        st.markdown(f"""
                        <div class="success-box">
                            ✅ <strong>{i}.</strong> {strength}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Keep working on your content to build up its strengths!")
            
            # Action items
            st.markdown("---")
            st.subheader("🎯 Next Steps")
            
            if analysis.overall_score >= 80:
                st.success("🎉 Your content is performing well! Consider A/B testing small variations.")
            elif analysis.overall_score >= 60:
                st.warning("⚠️ Good foundation! Focus on the top 2-3 improvement suggestions.")
            else:
                st.error("❌ Significant improvements needed. Start with readability and engagement basics.")
    
    with tab2:
        # Blog to Social Converter
        st.header("🔄 Blog to Social Media Converter")
        st.markdown("Transform your long-form content into engaging social media posts")
        
        # Input section
        input_col1, input_col2 = st.columns([2, 1])
        
        with input_col1:
            st.subheader("📝 Content Input")
            
            # Input method selection
            input_method = st.radio(
                "Choose input method:",
                ["Blog URL", "Paste Text"],
                horizontal=True
            )
            
            if input_method == "Blog URL":
                blog_url = st.text_input(
                    "Enter blog post URL:",
                    placeholder="https://example.com/blog-post",
                    help="Enter the URL of your blog post"
                )
                
                if st.button("📥 Extract Content", use_container_width=True):
                    if blog_url:
                        with st.spinner("🔍 Extracting content from URL..."):
                            converter = BlogToSocialConverter()
                            extracted_content = converter.extract_content_from_url(blog_url)
                            
                            if "error" in extracted_content:
                                st.error(f"❌ {extracted_content['error']}")
                            else:
                                st.session_state.blog_content = extracted_content
                                st.success("✅ Content extracted successfully!")
                    else:
                        st.error("Please enter a valid URL")
            
            else:  # Paste Text
                blog_text = st.text_area(
                    "Paste your blog content:",
                    placeholder="Paste your long-form content here...",
                    height=200,
                    help="Paste the main content of your blog post"
                )
                
                blog_title = st.text_input(
                    "Blog title (optional):",
                    placeholder="Enter your blog post title"
                )
                
                if st.button("📝 Process Text", use_container_width=True):
                    if blog_text:
                        st.session_state.blog_content = {
                            "title": blog_title or "Blog Post",
                            "content": blog_text,
                            "word_count": len(blog_text.split()),
                            "char_count": len(blog_text)
                        }
                        st.success("✅ Text processed successfully!")
                    else:
                        st.error("Please enter some text to process")
        
        with input_col2:
            st.subheader("⚙️ Conversion Settings")
            
            # Brand voice selection
            brand_voice = st.selectbox(
                "Brand Voice:",
                ["Professional", "Casual", "Educational", "Inspirational"],
                help="Choose the tone for your social media posts"
            )
            
            # Platform selection for conversion
            target_platforms = st.multiselect(
                "Target Platforms:",
                ["Instagram", "Facebook", "Twitter", "LinkedIn", "TikTok"],
                default=["Instagram", "Twitter"],
                help="Select platforms to generate posts for"
            )
            
            # Post types
            st.markdown("**Post Types:**")
            include_threads = st.checkbox("Twitter Threads", value=True)
            include_carousels = st.checkbox("Instagram Carousels", value=True)
            
            # Convert button
            convert_btn = st.button("🚀 Convert to Social Posts", type="primary", use_container_width=True)
        
        # Display extracted content
        if st.session_state.blog_content:
            with st.expander("📄 Extracted Content Preview", expanded=False):
                content = st.session_state.blog_content
                st.write(f"**Title:** {content.get('title', 'N/A')}")
                st.write(f"**Word Count:** {content.get('word_count', 0)}")
                st.write(f"**Character Count:** {content.get('char_count', 0)}")
                
                if 'content' in content:
                    preview = content['content'][:500] + "..." if len(content['content']) > 500 else content['content']
                    st.text_area("Content Preview:", preview, height=150, disabled=True)
        
        # Convert content to social posts
        if convert_btn:
            if not st.session_state.blog_content:
                st.error("Please extract or input content first!")
            elif not target_platforms:
                st.error("Please select at least one target platform!")
            else:
                with st.spinner("🔄 Converting content to social media posts..."):
                    converter = BlogToSocialConverter()
                    content = st.session_state.blog_content
                    
                    # Extract key points
                    key_points = converter.extract_key_points(content['content'])
                    
                    # Generate posts for each platform
                    converted_posts = []
                    
                    for platform in target_platforms:
                        platform_lower = platform.lower()
                        
                        # Generate regular post
                        regular_post = converter.create_platform_post(
                            key_points, 
                            content['title'], 
                            platform_lower, 
                            brand_voice.lower(), 
                            'single_post'
                        )
                        converted_posts.append(regular_post)
                        
                        # Generate special post types
                        if platform == "Twitter" and include_threads:
                            thread_post = converter.create_platform_post(
                                key_points, 
                                content['title'], 
                                platform_lower, 
                                brand_voice.lower(), 
                                'thread'
                            )
                            converted_posts.append(thread_post)
                        
                        if platform == "Instagram" and include_carousels:
                            carousel_post = converter.create_platform_post(
                                key_points, 
                                content['title'], 
                                platform_lower, 
                                brand_voice.lower(), 
                                'carousel'
                            )
                            converted_posts.append(carousel_post)
                    
                    st.session_state.converted_posts = converted_posts
                    st.success(f"✅ Generated {len(converted_posts)} social media posts!")
        
        # Display converted posts
        if st.session_state.converted_posts:
            st.markdown("---")
            st.header("📱 Generated Social Media Posts")
            
            for i, post in enumerate(st.session_state.converted_posts):
                with st.expander(f"📝 {post.platform} - {post.post_type.replace('_', ' ').title()}", expanded=True):
                    
                    # Post metrics
                    col_metric1, col_metric2, col_metric3 = st.columns(3)
                    
                    with col_metric1:
                        st.metric("Platform", post.platform)
                    with col_metric2:
                        st.metric("Characters", post.character_count)
                    with col_metric3:
                        st.metric("Type", post.post_type.replace('_', ' ').title())
                    
                    # Post content
                    st.markdown("**📝 Post Content:**")
                    st.text_area(
                        f"Content for {post.platform}:",
                        post.content,
                        height=200,
                        key=f"content_{i}",
                        help="Copy this content to use on the platform"
                    )
                    
                    # Hashtags
                    if post.hashtags:
                        st.markdown("**#️⃣ Hashtags:**")
                        st.code(post.hashtags)
                    
                    # Platform-specific tips
                    if post.tips:
                        st.markdown("**💡 Platform Tips:**")
                        for tip in post.tips:
                            st.write(f"• {tip}")
                    
                    # Copy buttons
                    col_copy1, col_copy2 = st.columns(2)
                    
                    with col_copy1:
                        if st.button(f"📋 Copy Content", key=f"copy_content_{i}"):
                            st.code(post.content)
                            st.success("Content copied!")
                    
                    with col_copy2:
                        if st.button(f"📋 Copy with Hashtags", key=f"copy_all_{i}"):
                            full_post = f"{post.content}\n\n{post.hashtags}" if post.hashtags else post.content
                            st.code(full_post)
                            st.success("Full post copied!")
            
            # Bulk actions
            st.markdown("---")
            st.subheader("🔄 Bulk Actions")
            
            col_bulk1, col_bulk2, col_bulk3 = st.columns(3)
            
            with col_bulk1:
                if st.button("📄 Export All Posts"):
                    # Create downloadable content
                    export_content = ""
                    for post in st.session_state.converted_posts:
                        export_content += f"=== {post.platform} - {post.post_type.replace('_', ' ').title()} ===\n"
                        export_content += f"Characters: {post.character_count}\n\n"
                        export_content += f"{post.content}\n\n"
                        if post.hashtags:
                            export_content += f"Hashtags: {post.hashtags}\n\n"
                        export_content += f"Tips: {', '.join(post.tips)}\n\n"
                        export_content += "="*50 + "\n\n"
                    
                    st.download_button(
                        label="💾 Download All Posts",
                        data=export_content,
                        file_name="social_media_posts.txt",
                        mime="text/plain"
                    )
            
            with col_bulk2:
                if st.button("🔄 Regenerate All"):
                    st.rerun()
            
            with col_bulk3:
                if st.button("🗑️ Clear All"):
                    st.session_state.converted_posts = []
                    st.session_state.blog_content = None
                    st.rerun()

if __name__ == "__main__":
    main()