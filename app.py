import streamlit as st
import requests
import json
import time
from typing import List, Dict

# Set page config
st.set_page_config(
    page_title="AI Content Creation Suite",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .caption-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .platform-badge {
        display: inline-block;
        padding: 5px 10px;
        background-color: #007bff;
        color: white;
        border-radius: 15px;
        font-size: 12px;
        margin: 2px;
    }
    .tone-badge {
        display: inline-block;
        padding: 5px 10px;
        background-color: #28a745;
        color: white;
        border-radius: 15px;
        font-size: 12px;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Hugging Face API Configuration
class HuggingFaceAPI:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    def generate_text(self, model: str, prompt: str, max_length: int = 100) -> str:
        """Generate text using Hugging Face API"""
        url = f"{self.base_url}/{model}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 50,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    if 'generated_text' in result[0]:
                        text = result[0]['generated_text']
                        # Remove the original prompt if it's included
                        if prompt in text:
                            text = text.replace(prompt, "").strip()
                        return text if text else "Generated caption about the topic"
                    elif 'text' in result[0]:
                        return result[0]['text'].strip()
                
                # If no proper response, return a fallback
                return "Generated caption about the topic"
                
            elif response.status_code == 503:
                return "Model is loading, try again in a moment"
            else:
                return f"API Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Request timed out, try again"
        except Exception as e:
            return f"Connection error: {str(e)}"

# Script Generator Class
class ScriptGenerator:
    def __init__(self, hf_api: HuggingFaceAPI):
        self.hf_api = hf_api
        
        # Script templates for different content types
        self.script_templates = {
            'video': {
                'structure': ['Hook', 'Introduction', 'Main Content', 'Call to Action'],
                'hooks': [
                    "Wait until you see what happens next...",
                    "This one trick changed everything for me",
                    "You won't believe what I discovered about {topic}",
                    "Everyone gets this wrong about {topic}",
                    "The truth about {topic} that nobody tells you"
                ]
            },
            'carousel': {
                'structure': ['Title Slide', 'Problem', 'Solution Steps', 'Results', 'CTA'],
                'hooks': [
                    "🚨 Stop scrolling! This {topic} guide will change your life",
                    "✨ The ultimate {topic} breakdown in 5 slides",
                    "💡 Everything you need to know about {topic}",
                    "🔥 {topic} secrets that actually work"
                ]
            },
            'reel': {
                'structure': ['Hook (3s)', 'Quick Tips', 'Visual Demo', 'Strong CTA'],
                'hooks': [
                    "POV: You finally understand {topic}",
                    "That girl who mastered {topic}:",
                    "Plot twist: {topic} is actually easy",
                    "When you realize {topic} can change everything:"
                ]
            },
            'story': {
                'structure': ['Hook', 'Build Up', 'Climax/Lesson', 'Reflection', 'CTA'],
                'hooks': [
                    "This story about {topic} will shock you",
                    "I never expected {topic} to teach me this",
                    "The day {topic} changed my perspective forever"
                ]
            },
            'tutorial': {
                'structure': ['Introduction', 'Materials/Setup', 'Step-by-Step', 'Final Result', 'Tips & CTA'],
                'hooks': [
                    "Master {topic} in under 5 minutes",
                    "The easiest way to learn {topic}",
                    "Follow along to become a {topic} pro"
                ]
            },
            'thread': {
                'structure': ['Hook Tweet', 'Context Setup', 'Main Points (3-5)', 'Conclusion', 'CTA Tweet'],
                'hooks': [
                    "🧵 Everything I learned about {topic} in one thread:",
                    "A thread on {topic} that will save you years of mistakes:",
                    "The {topic} framework that changed my life:"
                ]
            }
        }
        
        # CTA templates by audience
        self.cta_templates = {
            'creators': [
                "💡 Save this for your next {topic} content!",
                "🔄 Share if this helped you with {topic}",
                "📩 DM me for more {topic} tips",
                "👇 Drop your {topic} questions below"
            ],
            'business': [
                "📈 Ready to implement {topic} in your business?",
                "💼 Book a consultation to discuss {topic} strategy",
                "🔗 Link in bio for our {topic} course",
                "📊 Download our free {topic} template"
            ],
            'students': [
                "📚 Study this for your {topic} exam",
                "✅ Practice these {topic} techniques daily",
                "👥 Share with study partners",
                "📝 Comment your {topic} progress"
            ],
            'general': [
                "❤️ Like if this {topic} tip helped you",
                "🔄 Share to help others with {topic}",
                "💬 What's your experience with {topic}?",
                "🔔 Follow for more {topic} content"
            ]
        }
    
    def get_content_specs(self, content_type: str) -> dict:
        """Get specifications for different content types"""
        specs = {
            'video': {'duration': '60-90 seconds', 'word_count': '150-200 words', 'focus': 'Visual storytelling'},
            'carousel': {'slides': '5-10 slides', 'word_count': '20-30 words per slide', 'focus': 'Step-by-step breakdown'},
            'reel': {'duration': '15-30 seconds', 'word_count': '50-80 words', 'focus': 'Quick, punchy content'},
            'story': {'duration': '30-60 seconds', 'word_count': '100-150 words', 'focus': 'Narrative arc'},
            'tutorial': {'duration': '90-180 seconds', 'word_count': '200-300 words', 'focus': 'Educational value'},
            'thread': {'tweets': '5-10 tweets', 'word_count': '280 chars per tweet', 'focus': 'Valuable insights'}
        }
        return specs.get(content_type, specs['video'])
    
    def create_script_prompt(self, topic: str, audience: str, content_type: str) -> str:
        """Create optimized prompt for script generation"""
        
        template = self.script_templates.get(content_type, self.script_templates['video'])
        specs = self.get_content_specs(content_type)
        
        prompt = f"""Create a {content_type} script about {topic} for {audience} audience.

Script Requirements:
- Structure: {' → '.join(template['structure'])}
- Duration/Length: {specs['duration']} ({specs['word_count']})
- Focus: {specs['focus']}
- Include engaging hook, valuable content, and strong call-to-action
- Make it conversational and engaging
- Target audience: {audience}

Topic: {topic}
Content Type: {content_type}

Script:"""
        
        return prompt

    def generate_script_with_ai(self, topic: str, audience: str, content_type: str) -> str:
        """Generate script using AI with fallback"""
        
        prompt = self.create_script_prompt(topic, audience, content_type)
        
        try:
            # Try AI generation
            script = self.hf_api.generate_text("gpt2", prompt, max_length=200)
            
            if script and not any(error in script.lower() for error in ['error', 'timeout', 'loading']):
                # Clean up the script
                script = script.replace(prompt, "").strip()
                if len(script) > 50:
                    return script
            
            # Fallback to template if AI fails
            return self.generate_template_script(topic, audience, content_type)
            
        except Exception as e:
            return self.generate_template_script(topic, audience, content_type)
    
    def generate_template_script(self, topic: str, audience: str, content_type: str) -> str:
        """Generate script using templates as fallback"""
        
        template = self.script_templates.get(content_type, self.script_templates['video'])
        import random
        
        # Select random hook and customize it
        hook = random.choice(template['hooks']).format(topic=topic)
        
        # Generate script based on content type
        if content_type == 'video':
            script = f"""🎬 VIDEO SCRIPT: {topic.title()}

🪝 HOOK (0-3s):
{hook}

📍 INTRODUCTION (3-10s):
Hey everyone! Today we're diving deep into {topic}. If you've been struggling with this, you're in the right place.

🎯 MAIN CONTENT (10-45s):
Here's what you need to know about {topic}:

1. The first key point about {topic} is understanding its foundation
2. Next, consider how {topic} impacts your daily routine
3. Finally, implement these {topic} strategies consistently

💡 VALUE DELIVERY (45-55s):
The biggest mistake people make with {topic} is rushing the process. Take your time and focus on quality over quantity.

📢 CALL TO ACTION (55-60s):
{random.choice(self.cta_templates.get(audience, self.cta_templates['general'])).format(topic=topic)}

🎬 END SCREEN: Subscribe for more {topic} content!"""

        elif content_type == 'carousel':
            script = f"""📱 CAROUSEL SCRIPT: {topic.title()}

SLIDE 1 - TITLE:
{hook}
Swipe for the complete guide →

SLIDE 2 - PROBLEM:
The Challenge with {topic}:
Most people struggle because they don't have a clear system

SLIDE 3 - SOLUTION STEP 1:
Step 1: Foundation
Start by understanding the basics of {topic}

SLIDE 4 - SOLUTION STEP 2:
Step 2: Implementation
Apply {topic} principles to your specific situation

SLIDE 5 - SOLUTION STEP 3:
Step 3: Optimization
Fine-tune your {topic} approach based on results

SLIDE 6 - RESULTS:
What You'll Achieve:
✅ Better understanding of {topic}
✅ Practical skills you can use immediately
✅ Confidence in your {topic} knowledge

SLIDE 7 - CTA:
{random.choice(self.cta_templates.get(audience, self.cta_templates['general'])).format(topic=topic)}"""

        elif content_type == 'reel':
            script = f"""🎬 REEL SCRIPT: {topic.title()}

🪝 HOOK (0-2s):
{hook}

⚡ QUICK TIPS (2-15s):
✨ Tip 1: Master the basics of {topic}
🔥 Tip 2: Practice {topic} daily
💡 Tip 3: Track your {topic} progress

📱 VISUAL DEMO (15-25s):
[Show practical example of {topic} in action]

📢 CTA (25-30s):
{random.choice(self.cta_templates.get(audience, self.cta_templates['general'])).format(topic=topic)}"""

        elif content_type == 'thread':
            script = f"""🐦 TWITTER THREAD: {topic.title()}

TWEET 1 - HOOK:
{random.choice(self.script_templates['thread']['hooks']).format(topic=topic)}

TWEET 2 - CONTEXT:
Here's why {topic} matters more than you think...

TWEET 3 - POINT 1:
1/ The foundation of {topic} starts with understanding its core principles

TWEET 4 - POINT 2:
2/ Most people fail at {topic} because they skip the basics

TWEET 5 - POINT 3:
3/ The secret to mastering {topic} is consistent daily practice

TWEET 6 - POINT 4:
4/ Advanced {topic} techniques only work when you have solid fundamentals

TWEET 7 - CONCLUSION:
Remember: {topic} is a journey, not a destination. Start small, stay consistent.

TWEET 8 - CTA:
{random.choice(self.cta_templates.get(audience, self.cta_templates['general'])).format(topic=topic)}

🔄 Retweet the first tweet if this thread helped you!"""

        else:  # Default to tutorial
            script = f"""📚 TUTORIAL SCRIPT: {topic.title()}

🎯 INTRODUCTION (0-15s):
Welcome to this {topic} tutorial! By the end of this video, you'll have everything you need to get started.

🛠️ WHAT YOU'LL NEED (15-30s):
Materials for {topic}:
- Basic understanding of the concept
- Willingness to practice
- Notebook for tracking progress

📋 STEP-BY-STEP (30-120s):
Step 1: Set up your {topic} foundation
Step 2: Learn the core techniques
Step 3: Practice with real examples
Step 4: Troubleshoot common issues

🎉 FINAL RESULT (120-150s):
Now you have a complete understanding of {topic} and can apply it immediately!

💡 BONUS TIPS (150-170s):
Pro tips for {topic} success:
- Start simple and build complexity
- Track your progress daily
- Join communities for support

📢 CTA (170-180s):
{random.choice(self.cta_templates.get(audience, self.cta_templates['general'])).format(topic=topic)}"""
        
        return script
    
    def generate_script(self, topic: str, audience: str, content_type: str) -> dict:
        """Generate complete script with metadata"""
        
        # Generate the main script
        script_content = self.generate_script_with_ai(topic, audience, content_type)
        
        # Get content specifications
        specs = self.get_content_specs(content_type)
        
        # Estimate metrics
        word_count = len(script_content.split())
        estimated_duration = word_count * 0.4  # ~0.4 seconds per word
        
        return {
            'script': script_content,
            'content_type': content_type,
            'target_audience': audience,
            'topic': topic,
            'word_count': word_count,
            'estimated_duration': f"{estimated_duration:.0f} seconds",
            'specifications': specs,
            'structure': self.script_templates.get(content_type, {}).get('structure', [])
        }

# Hashtag Generator Class
class HashtagGenerator:
    def __init__(self):
        # Comprehensive hashtag database organized by niche and popularity
        self.hashtag_db = {
            'food': {
                'high': ['#food', '#foodie', '#delicious', '#yummy', '#tasty', '#foodporn', '#eating', '#instafood'],
                'medium': ['#foodstagram', '#foodlover', '#homemade', '#cooking', '#recipe', '#chef', '#kitchen', '#meal'],
                'niche': ['#foodblogger', '#foodphotography', '#healthy', '#organic', '#vegan', '#glutenfree', '#local', '#fresh']
            },
            'fitness': {
                'high': ['#fitness', '#workout', '#gym', '#health', '#fit', '#training', '#exercise', '#motivation'],
                'medium': ['#fitlife', '#healthy', '#strong', '#muscle', '#cardio', '#strength', '#wellness', '#active'],
                'niche': ['#fitnessmotivation', '#gymlife', '#personaltrainer', '#nutrition', '#bodybuilding', '#crossfit', '#yoga', '#running']
            },
            'business': {
                'high': ['#business', '#entrepreneur', '#success', '#motivation', '#leadership', '#growth', '#innovation', '#startup'],
                'medium': ['#hustle', '#goals', '#mindset', '#productivity', '#strategy', '#networking', '#career', '#professional'],
                'niche': ['#businessowner', '#smallbusiness', '#digitalmarketing', '#sales', '#consulting', '#finance', '#investment', '#ecommerce']
            },
            'lifestyle': {
                'high': ['#lifestyle', '#life', '#love', '#happy', '#beautiful', '#style', '#fashion', '#travel'],
                'medium': ['#inspiration', '#positivity', '#wellness', '#selfcare', '#mindfulness', '#gratitude', '#joy', '#peace'],
                'niche': ['#lifestyleblogger', '#minimalism', '#sustainability', '#mindful', '#authentic', '#balance', '#growth', '#intentional']
            },
            'tech': {
                'high': ['#technology', '#tech', '#innovation', '#digital', '#future', '#AI', '#software', '#coding'],
                'medium': ['#programming', '#developer', '#startup', '#gadgets', '#automation', '#data', '#cybersecurity', '#mobile'],
                'niche': ['#artificialintelligence', '#machinelearning', '#blockchain', '#cloudcomputing', '#webdev', '#python', '#javascript', '#opensource']
            },
            'beauty': {
                'high': ['#beauty', '#makeup', '#skincare', '#beautiful', '#style', '#fashion', '#selfie', '#love'],
                'medium': ['#cosmetics', '#glam', '#makeupartist', '#skincareroutine', '#natural', '#glow', '#confidence', '#selfcare'],
                'niche': ['#beautyinfluencer', '#makeuptutorial', '#skincareproducts', '#beautytips', '#crueltyfree', '#organic', '#antiaging', '#beautyblogger']
            },
            'travel': {
                'high': ['#travel', '#vacation', '#explore', '#adventure', '#wanderlust', '#trip', '#holiday', '#beautiful'],
                'medium': ['#traveling', '#tourism', '#destination', '#culture', '#nature', '#photography', '#journey', '#discovery'],
                'niche': ['#travelblogger', '#solotravel', '#backpacking', '#luxurytravel', '#sustainabletravel', '#roadtrip', '#citybreak', '#beachlife']
            },
            'education': {
                'high': ['#education', '#learning', '#knowledge', '#study', '#school', '#student', '#teacher', '#growth'],
                'medium': ['#academic', '#research', '#university', '#college', '#training', '#development', '#skills', '#wisdom'],
                'niche': ['#onlinelearning', '#elearning', '#studytips', '#education', '#scholarship', '#academiclife', '#lifelong', '#educational']
            }
        }
        
        # Trending and evergreen hashtags
        self.trending_hashtags = ['#viral', '#trending', '#fyp', '#reels', '#explore', '#instagood', '#photooftheday', '#like4like']
        self.seasonal_hashtags = {
            'general': ['#monday', '#weekend', '#summer', '#winter', '#spring', '#fall', '#morning', '#night'],
            'monthly': ['#january', '#february', '#march', '#april', '#may', '#june', '#july', '#august', '#september', '#october', '#november', '#december']
        }

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from caption text"""
        import re
        
        # Clean text and extract meaningful words
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Common stop words to filter out
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        words = text.split()
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return keywords[:10]  # Return top 10 keywords

    def get_niche_hashtags(self, niche: str, count: int = 20) -> List[str]:
        """Get hashtags for specific niche"""
        niche = niche.lower()
        hashtags = []
        
        # Find matching niche or closest match
        for key in self.hashtag_db.keys():
            if key in niche or niche in key:
                niche_data = self.hashtag_db[key]
                # Mix high, medium, and niche popularity
                hashtags.extend(niche_data['high'][:4])
                hashtags.extend(niche_data['medium'][:8])
                hashtags.extend(niche_data['niche'][:8])
                break
        
        # If no specific niche found, use general popular tags
        if not hashtags:
            hashtags = ['#content', '#social', '#post', '#share', '#community', '#engagement', '#creative', '#inspiration']
        
        return hashtags[:count]

    def generate_custom_hashtags(self, keywords: List[str]) -> List[str]:
        """Generate custom hashtags from keywords"""
        custom_tags = []
        
        for keyword in keywords:
            # Create hashtag variations
            if len(keyword) > 2:
                custom_tags.append(f"#{keyword}")
                
                # Add variations
                if len(keyword) > 5:
                    custom_tags.append(f"#{keyword}life")
                    custom_tags.append(f"#{keyword}love")
        
        return custom_tags[:8]

    def generate_hashtags(self, caption: str, niche: str, platform: str = 'instagram', count: int = 20) -> Dict:
        """Generate comprehensive hashtag strategy"""
        
        # Extract keywords from caption
        keywords = self.extract_keywords(caption)
        
        # Get niche-specific hashtags
        niche_hashtags = self.get_niche_hashtags(niche, count // 2)
        
        # Generate custom hashtags from keywords
        custom_hashtags = self.generate_custom_hashtags(keywords)
        
        # Add trending hashtags (2-3)
        trending = self.trending_hashtags[:3]
        
        # Combine all hashtags
        all_hashtags = niche_hashtags + custom_hashtags + trending
        
        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in all_hashtags:
            if tag not in seen:
                seen.add(tag)
                unique_hashtags.append(tag)
        
        # Limit to requested count
        final_hashtags = unique_hashtags[:count]
        
        # Organize by category for better presentation
        return {
            'all_hashtags': final_hashtags,
            'niche_specific': niche_hashtags[:10],
            'content_based': custom_hashtags,
            'trending': trending,
            'total_count': len(final_hashtags)
        }


# Caption Generator Class
class CaptionGenerator:
    def __init__(self, hf_api: HuggingFaceAPI):
        self.hf_api = hf_api
        self.emojis = {
            'instagram': ['📸', '✨', '💫', '🌟', '💝', '🔥', '💯', '🙌', '👏', '💪'],
            'facebook': ['👍', '❤️', '😊', '🎉', '🌟', '💙', '🤝', '👪', '🏡', '🎯'],
            'twitter': ['🚀', '💡', '🔥', '⚡', '🎯', '💯', '🧵', '📈', '🌊', '✅'],
            'linkedin': ['💼', '🚀', '📈', '💡', '🎯', '🤝', '🏆', '💪', '🌟', '📊'],
            'tiktok': ['🎵', '💃', '🕺', '🔥', '✨', '🎉', '💯', '🤳', '🌟', '⚡']
        }
    
    def get_platform_specs(self, platform: str) -> Dict:
        """Get platform-specific specifications"""
        specs = {
            'instagram': {'max_chars': 2200, 'hashtags': True, 'emojis': True},
            'facebook': {'max_chars': 63206, 'hashtags': False, 'emojis': True},
            'twitter': {'max_chars': 280, 'hashtags': True, 'emojis': True},
            'linkedin': {'max_chars': 3000, 'hashtags': True, 'emojis': False},
            'tiktok': {'max_chars': 150, 'hashtags': True, 'emojis': True}
        }
        return specs.get(platform.lower(), specs['instagram'])
    
    def create_prompt(self, topic: str, tone: str, platform: str) -> str:
        """Create optimized prompt for caption generation"""
        platform_specs = self.get_platform_specs(platform)
        
        prompt = f"""Write a {tone} {platform} caption about {topic}.

Requirements:
- Keep it under {platform_specs['max_chars']} characters
- Use {tone} tone
- Make it engaging and shareable"""
        
        if platform_specs['emojis']:
            prompt += "\n- Include relevant emojis"
        
        if platform_specs['hashtags']:
            prompt += "\n- Add 3-5 relevant hashtags"
        
        prompt += f"\n\nCaption:"
        
        return prompt
    
    def add_emojis(self, text: str, platform: str) -> str:
        """Add platform-appropriate emojis to text"""
        import random
        
        platform_emojis = self.emojis.get(platform.lower(), self.emojis['instagram'])
        selected_emojis = random.sample(platform_emojis, min(3, len(platform_emojis)))
        
        # Add emojis at the beginning or end
        if random.choice([True, False]):
            return f"{' '.join(selected_emojis)} {text}"
        else:
            return f"{text} {' '.join(selected_emojis)}"
    
    def generate_captions(self, topic: str, tone: str, platform: str, count: int = 3) -> List[str]:
        """Generate multiple caption variations"""
        captions = []
        
        # Predefined templates as fallback
        templates = {
            'casual': [
                f"Just discovered {topic}! 😍 What's your favorite thing about this?",
                f"Loving this {topic} vibe today ✨ Who else is obsessed?",
                f"{topic} hits different when you really appreciate it 💫"
            ],
            'professional': [
                f"Exploring the impact of {topic} in today's landscape. Thoughts?",
                f"Key insights about {topic} that are worth considering today.",
                f"The importance of {topic} cannot be overstated. Here's why:"
            ],
            'funny': [
                f"Me trying to explain {topic} to my friends 😂",
                f"When {topic} is life but nobody understands 🤷‍♀️",
                f"POV: You're obsessed with {topic} and it shows 😅"
            ],
            'inspirational': [
                f"Let {topic} remind you that great things come to those who believe ✨",
                f"Every moment with {topic} is a chance to grow and learn 🌟",
                f"Finding beauty in {topic} - sometimes the simple things matter most 💫"
            ],
            'educational': [
                f"Did you know? {topic} has some fascinating aspects worth exploring.",
                f"Breaking down {topic}: Here's what you need to know today.",
                f"Quick facts about {topic} that might surprise you:"
            ],
            'excited': [
                f"OMG YES! {topic} is absolutely EVERYTHING right now! 🔥",
                f"Can't contain my excitement about {topic}! Who's with me? 🙌",
                f"THIS is why I love {topic} so much! Pure magic ✨"
            ]
        }
        
        for i in range(count):
            try:
                # Try AI generation first
                variations = [
                    f"Write a {tone} social media caption about {topic}",
                    f"Create an engaging {platform} post about {topic} in {tone} style",
                    f"Generate a {tone} caption for {topic}"
                ]
                
                prompt = variations[i % len(variations)]
                
                # Generate caption with AI
                caption = self.hf_api.generate_text("gpt2", prompt, max_length=80)
                
                # Check if AI generation was successful
                if caption and not any(error in caption.lower() for error in ['error', 'timeout', 'loading']):
                    # Clean up the caption
                    caption = caption.replace(prompt, "").strip()
                    
                    # Ensure it's not empty after cleanup
                    if len(caption) > 10:
                        # Add emojis if platform supports them
                        platform_specs = self.get_platform_specs(platform)
                        if platform_specs['emojis']:
                            caption = self.add_emojis(caption, platform)
                        
                        captions.append(caption)
                        continue
                
                # Fallback to templates if AI fails
                template_captions = templates.get(tone.lower(), templates['casual'])
                fallback_caption = template_captions[i % len(template_captions)]
                
                # Add platform-specific emojis
                platform_specs = self.get_platform_specs(platform)
                if platform_specs['emojis']:
                    fallback_caption = self.add_emojis(fallback_caption, platform)
                
                captions.append(fallback_caption)
                
            except Exception as e:
                # Ultimate fallback
                captions.append(f"Check out this amazing {topic}! What do you think? ✨")
        
        return captions

        # Initialize session state
if 'captions' not in st.session_state:
    st.session_state.captions = []
if 'hashtags' not in st.session_state:
    st.session_state.hashtags = {}
if 'selected_caption' not in st.session_state:
    st.session_state.selected_caption = ""
if 'generated_script' not in st.session_state:
    st.session_state.generated_script = {}

# Main App
def main():
    st.title("🚀 AI Content Creation Suite")
    st.markdown("Generate captions, hashtags & full scripts with AI - **Free to use!**")
    
    # Sidebar for API key (optional)
    with st.sidebar:
        st.header("⚙️ Settings")
        api_key = st.text_input(
            "Hugging Face API Key (Optional)", 
            type="password",
            help="Get your free API key from huggingface.co/settings/tokens"
        )
        
        if not api_key:
            st.info("💡 **Free Mode**: Using public Hugging Face API (limited requests)")
            st.markdown("[Get Free API Key](https://huggingface.co/settings/tokens)")
        else:
            st.success("✅ Using your API key")
        
        st.markdown("---")
        st.markdown("### 📊 Features")
        st.markdown("- ✅ Free to use")
        st.markdown("- 🎯 Platform optimization")
        st.markdown("- 😊 Multiple tones")
        st.markdown("- 📱 3 caption variants")
        st.markdown("- 🔄 Emoji integration")
        st.markdown("- #️⃣ Smart hashtag generation")
        st.markdown("- 🎪 Niche-specific tags")
        st.markdown("- 📝 Full script generation")
        st.markdown("- 🎬 Multiple content types")
    
    # Create tabs for different features
    tab1, tab2, tab3 = st.tabs(["📱 Captions & Hashtags", "🎬 Script Generator", "📊 Analytics"])
    
    with tab1:
        # Main content area for captions
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("🎯 Caption Settings")
            
            # Topic input
            topic = st.text_input(
                "What's your post about?",
                placeholder="e.g., Morning coffee, new product launch, weekend vibes",
                help="Describe your post topic or theme"
            )
            
            # Platform selection
            platform = st.selectbox(
                "Choose Platform",
                ["Instagram", "Facebook", "Twitter", "LinkedIn", "TikTok"],
                help="Each platform has different optimization"
            )
            
            # Tone selection
            tone = st.selectbox(
                "Select Tone",
                ["Casual", "Professional", "Funny", "Inspirational", "Educational", "Excited"],
                help="Choose the mood for your caption"
            )
            
            # NEW: Niche selection for hashtags
            st.markdown("---")
            st.subheader("🏷️ Hashtag Settings")
            
            niche = st.selectbox(
                "Select Your Niche",
                ["Food & Cooking", "Fitness & Health", "Business & Entrepreneurship", 
                 "Lifestyle & Wellness", "Technology & Innovation", "Beauty & Fashion", 
                 "Travel & Adventure", "Education & Learning"],
                help="Choose your content niche for targeted hashtags"
            )
            
            hashtag_count = st.slider(
                "Number of Hashtags",
                min_value=10,
                max_value=30,
                value=20,
                help="Choose how many hashtags to generate"
            )
            
            # Generate button
            generate_btn = st.button("🎨 Generate Captions & Hashtags", type="primary", use_container_width=True)
        
        with col2:
            st.header("📝 Generated Content")
            
            if generate_btn:
                if not topic:
                    st.error("Please enter a topic for your post!")
                else:
                    with st.spinner("🤖 AI is crafting your captions & hashtags..."):
                        # Initialize APIs and generators
                        hf_api = HuggingFaceAPI(api_key)
                        caption_generator = CaptionGenerator(hf_api)
                        hashtag_generator = HashtagGenerator()
                        
                        # Generate captions
                        captions = caption_generator.generate_captions(topic, tone, platform)
                        st.session_state.captions = captions
                        
                        # Generate hashtags for the first caption
                        if captions and captions[0]:
                            # Clean niche name for processing
                            niche_clean = niche.split(" & ")[0].lower()  # "Food & Cooking" -> "food"
                            
                            hashtag_data = hashtag_generator.generate_hashtags(
                                captions[0], 
                                niche_clean, 
                                platform.lower(), 
                                hashtag_count
                            )
                            st.session_state.hashtags = hashtag_data
                        
                        # Small delay for better UX
                        time.sleep(1)
            
            # Display captions with hashtag integration
            if st.session_state.captions:
                st.success(f"✨ Generated {len(st.session_state.captions)} captions + hashtags!")
                
                # Tabs for better organization
                sub_tab1, sub_tab2 = st.tabs(["📝 Captions", "#️⃣ Hashtags"])
                
                with sub_tab1:
                    for i, caption in enumerate(st.session_state.captions, 1):
                        st.markdown(f"""
                        <div class="caption-box">
                            <h4>Caption {i}</h4>
                            <p>{caption}</p>
                            <div>
                                <span class="platform-badge">{platform}</span>
                                <span class="tone-badge">{tone}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Copy button with hashtags
                        col_copy, col_hashtag = st.columns([1, 1])
                        
                        with col_copy:
                            if st.button(f"📋 Copy Caption {i}", key=f"copy_{i}"):
                                full_content = caption
                                if st.session_state.hashtags:
                                    hashtags_str = " ".join(st.session_state.hashtags['all_hashtags'])
                                    full_content += f"\n\n{hashtags_str}"
                                st.code(full_content)
                                st.success(f"Caption {i} + hashtags ready to copy!")
                        
                        with col_hashtag:
                            if st.button(f"#️⃣ Use for Hashtags", key=f"hashtag_{i}"):
                                # Regenerate hashtags for this specific caption
                                hashtag_generator = HashtagGenerator()
                                niche_clean = niche.split(" & ")[0].lower()
                                
                                hashtag_data = hashtag_generator.generate_hashtags(
                                    caption, 
                                    niche_clean, 
                                    platform.lower(), 
                                    hashtag_count
                                )
                                st.session_state.hashtags = hashtag_data
                                st.success(f"Hashtags updated for Caption {i}!")
                
                with sub_tab2:
                    if st.session_state.hashtags:
                        hashtag_data = st.session_state.hashtags
                        
                        st.markdown(f"### 🎯 Hashtag Strategy ({hashtag_data['total_count']} tags)")
                        
                        # Display hashtags in different categories
                        col_h1, col_h2 = st.columns([1, 1])
                        
                        with col_h1:
                            st.markdown("**🏷️ All Hashtags**")
                            hashtags_text = " ".join(hashtag_data['all_hashtags'])
                            st.text_area("Copy all hashtags:", hashtags_text, height=100)
                            
                            if st.button("📋 Copy All Hashtags"):
                                st.code(hashtags_text)
                                st.success("All hashtags ready to copy!")
                        
                        with col_h2:
                            st.markdown("**📊 By Category**")
                            
                            st.markdown("*Niche-Specific:*")
                            st.write(" ".join(hashtag_data['niche_specific'][:5]))
                            
                            st.markdown("*Content-Based:*")
                            st.write(" ".join(hashtag_data['content_based'][:5]))
                            
                            st.markdown("*Trending:*")
                            st.write(" ".join(hashtag_data['trending']))
                            
                            # Hashtag analytics
                            st.markdown("**📈 Strategy Mix**")
                            st.write(f"• Niche hashtags: {len(hashtag_data['niche_specific'])}")
                            st.write(f"• Content hashtags: {len(hashtag_data['content_based'])}")
                            st.write(f"• Trending hashtags: {len(hashtag_data['trending'])}")
                    else:
                        st.info("Generate captions first to see hashtag strategy!")

                with tab2:
                    
                    # Script Generator Tab
                    st.header("🎬 AI Script Generator")
                    st.markdown("Create full-length scripts for videos, carousels, tutorials, and more!")
                    
                    col1_script, col2_script = st.columns([1, 1])
                    
                    with col1_script:
                        st.subheader("📋 Script Settings")
                        
                        # Script topic
                        script_topic = st.text_input(
                            "Script Topic",
                            placeholder="e.g., How to start a morning routine, Python basics for beginners",
                            help="What is your script about?"
                        )
                        
                        # Target audience
                        target_audience = st.selectbox(
                            "Target Audience",
                            ["General", "Creators", "Business", "Students", "Professionals"],
                            help="Who is your content for?"
                        )
                        
                        # Content type
                        content_type = st.selectbox(
                            "Content Type",
                            ["Video", "Carousel", "Reel", "Story", "Tutorial", "Thread"],
                            help="What type of content are you creating?"
                        )
                        
                        # Generate script button
                        generate_script_btn = st.button("🎬 Generate Full Script", type="primary", use_container_width=True)
                        
                        # Content type info
                        if content_type:
                            st.markdown("---")
                            st.markdown("### 📊 Content Specifications")
                            
                            specs_info = {
                                'Video': "📺 Duration: 60-90s | Focus: Visual storytelling",
                                'Carousel': "📱 5-10 slides | Focus: Step-by-step breakdown", 
                                'Reel': "⚡ Duration: 15-30s | Focus: Quick, punchy content",
                                'Story': "📖 Duration: 30-60s | Focus: Narrative arc",
                                'Tutorial': "📚 Duration: 90-180s | Focus: Educational value",
                                'Thread': "🐦 5-10 tweets | Focus: Valuable insights"
                            }
                            
                            st.info(specs_info.get(content_type, ""))
                    
                    with col2_script:
                        st.subheader("📝 Generated Script")
                        
                        if generate_script_btn:
                            if not script_topic:
                                st.error("Please enter a topic for your script!")
                            else:
                                with st.spinner("🤖 AI is creating your full script..."):
                                    # Initialize script generator
                                    hf_api = HuggingFaceAPI(api_key)
                                    script_generator = ScriptGenerator(hf_api)
                                    
                                    # Generate script
                                    script_data = script_generator.generate_script(
                                        script_topic, 
                                        target_audience.lower(), 
                                        content_type.lower()
                                    )
                                    st.session_state.generated_script = script_data
                                    
                                    time.sleep(1)
                        
                        # Display generated script
                        if st.session_state.generated_script:
                            script_data = st.session_state.generated_script
                            
                            st.success("✨ Script generated successfully!")
                            
                            # Script metadata
                            col_meta1, col_meta2 = st.columns([1, 1])
                            with col_meta1:
                                st.metric("Word Count", script_data['word_count'])
                                st.metric("Content Type", script_data['content_type'].title())
                            
                            with col_meta2:
                                st.metric("Est. Duration", script_data['estimated_duration'])
                                st.metric("Target Audience", script_data['target_audience'].title())
                            
                            # Script content
                            st.markdown("### 📄 Your Script")
                            st.text_area(
                                "Full Script Content:",
                                script_data['script'],
                                height=400,
                                help="Copy this script to use in your content creation"
                            )
                            
                            # Copy script button
                            if st.button("📋 Copy Complete Script"):
                                st.code(script_data['script'])
                                st.success("Script ready to copy!")
                            
                            # Script structure breakdown
                            st.markdown("### 🏗️ Script Structure")
                            structure = script_data.get('structure', [])
                            if structure:
                                for i, section in enumerate(structure, 1):
                                    st.write(f"{i}. **{section}**")
                
    
                with tab3:
                    # Analytics/Tips Tab
                    st.header("📊 Content Analytics & Tips")
                    st.markdown("Performance insights and optimization tips for your content")
                    
                    col_analytics1, col_analytics2 = st.columns([1, 1])
                    
                    with col_analytics1:
                        st.subheader("📈 Content Performance Tips")
                        
                        st.markdown("""
                        **🎯 Caption Optimization:**
                        - First 125 characters are crucial for Instagram
                        - Use line breaks for better readability
                        - Include clear call-to-action
                        - Ask questions to boost engagement
                        
                        **#️⃣ Hashtag Strategy:**
                        - Mix of popular (1M+ posts) and niche (10K-100K posts)
                        - Use 20-30 hashtags on Instagram
                        - Research competitor hashtags
                        - Create branded hashtags
                        
                        **🎬 Script Writing:**
                        - Hook viewers in first 3 seconds
                        - Deliver value quickly
                        - Include visual cues and transitions
                        - End with strong call-to-action
                        """)
                    
                    with col_analytics2:
                        st.subheader("⏰ Best Posting Times")
                        
                        st.markdown("""
                        **📱 Platform Timing:**
                        - **Instagram:** 11am-1pm, 7pm-9pm
                        - **Facebook:** 1pm-3pm weekdays
                        - **Twitter:** 8am-10am, 7pm-9pm
                        - **LinkedIn:** 8am-10am, 12pm-2pm weekdays
                        - **TikTok:** 6am-10am, 7pm-9pm
                        
                        **📊 Content Mix (80/20 Rule):**
                        - 80% value/entertainment content
                        - 20% promotional content
                        
                        **🔄 Posting Frequency:**
                        - Instagram: 1-2 posts/day
                        - Stories: 3-5/day
                        - Reels: 3-5/week
                        - Carousels: 2-3/week
                        """)
                    
                    # Content calendar suggestion
                    st.markdown("---")
                    st.subheader("📅 Weekly Content Planner")
                    
                    if st.session_state.captions or st.session_state.generated_script:
                        st.success("🎉 You have generated content! Here's how to use it:")
                        
                        if st.session_state.captions:
                            st.markdown("**📱 Your Generated Captions:**")
                            st.markdown("- Use for daily posts across platforms")
                            st.markdown("- Adapt tone for different audiences")
                            st.markdown("- A/B test different caption styles")
                        
                        if st.session_state.generated_script:
                            script_type = st.session_state.generated_script.get('content_type', 'content')
                            st.markdown(f"**🎬 Your Generated {script_type.title()} Script:**")
                            st.markdown(f"- Perfect for {script_type} content creation")
                            st.markdown("- Use as framework for multiple pieces")
                            st.markdown("- Adapt for different platforms")
                    else:
                        st.info("Generate some content first to see personalized planning tips!")

    # Footer
    st.markdown("---")
    st.markdown("### 🚀 How to get better results:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        **📝 Topic Tips**
        - Be specific
        - Include context
        - Mention key details
        """)
    
    with col2:
        st.markdown("""
        **🎯 Platform Tips**
        - Instagram: Visual focus
        - LinkedIn: Professional
        - Twitter: Concise & punchy
        """)
    
    with col3:
        st.markdown("""
        **💡 Tone Tips**
        - Match your brand voice
        - Consider your audience
        - Test different tones
        """)
    
    with col4:
        st.markdown("""
        **#️⃣ Hashtag Tips**
        - Mix popular & niche tags
        - Match your content niche
        - Use 10-30 hashtags max
        """)

if __name__ == "__main__":
    main()

    