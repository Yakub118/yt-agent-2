"""
Metadata Generator Module
Generates SEO-optimized titles, descriptions, and hashtags for YouTube Shorts.
Includes viral audio engine for trending music discovery.
"""
import random
import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendingAudioEngine:
    """Scrape and manage trending audio from YouTube Shorts and TikTok."""
    
    def __init__(self):
        self.trending_audio_cache = []
        self.cache_expiry = None
        self.cache_duration_hours = 24
        
        # Fallback trending audio tracks (copyright-free options)
        self.fallback_tracks = [
            {"name": "Upbeat Cooking", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"},
            {"name": "Kitchen Vibes", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"},
            {"name": "Food Beat", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"},
            {"name": "Recipe Rhythm", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"},
            {"name": "Cooking Flow", "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3"},
        ]
    
    def get_trending_audio(self, count: int = 10) -> List[Dict]:
        """
        Get top trending audio tracks from YouTube Shorts/TikTok.
        
        Args:
            count: Number of tracks to return
            
        Returns:
            List of trending audio track info
        """
        # Check if cache is still valid
        if self.cache_expiry and datetime.now() < self.cache_expiry:
            logger.info("Using cached trending audio")
            return self.trending_audio_cache[:count]
        
        # Try to scrape from TikTok Creative Center
        tracks = self._scrape_tiktok_trending()
        
        # If scraping fails, use fallback tracks
        if not tracks:
            logger.warning("Could not scrape trending audio, using fallback tracks")
            tracks = self.fallback_tracks
        
        # Update cache
        self.trending_audio_cache = tracks
        from datetime import timedelta
        self.cache_expiry = datetime.now() + timedelta(hours=self.cache_duration_hours)
        
        logger.info(f"Retrieved {len(tracks)} trending audio tracks")
        return tracks[:count]
    
    def _scrape_tiktok_trending(self) -> List[Dict]:
        """
        Scrape TikTok Creative Center for trending songs.
        
        Returns:
            List of trending audio track info
        """
        try:
            # TikTok Creative Center API endpoint (public data)
            url = "https://creative-api.tiktokapis.com/creative/v1/music/trending"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            
            # Note: This is a simplified implementation
            # Real implementation would need proper API authentication
            response = httpx.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            tracks = []
            
            for item in data.get("music_list", [])[:10]:
                tracks.append({
                    "name": item.get("title", "Unknown"),
                    "artist": item.get("author", "Unknown"),
                    "url": item.get("play_url", ""),
                    "duration": item.get("duration", 30),
                    "trend_score": item.get("popularity_score", 0),
                })
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error scraping TikTok trending: {e}")
            return []
    
    def _scrape_youtube_trending(self) -> List[Dict]:
        """
        Scrape YouTube Shorts trending audio page.
        
        Returns:
            List of trending audio track info
        """
        try:
            # YouTube doesn't have a public API for trending audio
            # This would require web scraping or using third-party services
            # For now, we'll use a placeholder implementation
            
            url = "https://music.youtube.com/browse/trending"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            }
            
            response = httpx.get(url, headers=headers, timeout=10)
            
            # Parse HTML to extract trending songs
            # This is a simplified extraction
            tracks = []
            
            # In production, you'd use BeautifulSoup or similar to parse the HTML
            # and extract actual trending song data
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error scraping YouTube trending: {e}")
            return []
    
    def download_trending_audio(self, save_dir: str, count: int = 5) -> List[str]:
        """
        Download top trending audio tracks.
        
        Args:
            save_dir: Directory to save audio files
            count: Number of tracks to download
            
        Returns:
            List of paths to downloaded audio files
        """
        os.makedirs(save_dir, exist_ok=True)
        
        tracks = self.get_trending_audio(count)
        downloaded_paths = []
        
        for i, track in enumerate(tracks):
            try:
                if not track.get("url"):
                    continue
                
                # Generate filename
                safe_name = track["name"].replace(" ", "_").replace("/", "_")[:50]
                filename = f"trending_{i+1}_{safe_name}.mp3"
                filepath = os.path.join(save_dir, filename)
                
                # Skip if already exists
                if os.path.exists(filepath):
                    downloaded_paths.append(filepath)
                    continue
                
                # Download the audio
                response = httpx.get(track["url"], timeout=30)
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                downloaded_paths.append(filepath)
                logger.info(f"Downloaded: {track['name']}")
                
            except Exception as e:
                logger.error(f"Error downloading {track['name']}: {e}")
        
        logger.info(f"Downloaded {len(downloaded_paths)} trending audio tracks")
        return downloaded_paths
    
    def get_best_track_for_food(self) -> Dict:
        """
        Get the best trending audio track for food content.
        
        Returns:
            Best matching track info
        """
        tracks = self.get_trending_audio(10)
        
        # Prioritize upbeat, energetic tracks for food content
        food_keywords = ["upbeat", "energetic", "happy", "cooking", "kitchen", "food"]
        
        for track in tracks:
            name_lower = track.get("name", "").lower()
            for keyword in food_keywords:
                if keyword in name_lower:
                    logger.info(f"Selected food-friendly track: {track['name']}")
                    return track
        
        # Return the most popular track if no match
        if tracks:
            return max(tracks, key=lambda t: t.get("trend_score", 0))
        
        # Fallback
        return random.choice(self.fallback_tracks)


class MetadataGenerator:
    """Generate metadata for YouTube Shorts."""

    def __init__(self):
        from config.settings import DEFAULT_HASHTAGS
        
        self.default_hashtags = DEFAULT_HASHTAGS
        
        # Title templates for food content
        self.title_templates = [
            "🍕 {dish} - Easy Recipe in 60 Seconds! #shorts",
            "😋 You NEED to Try This {dish} Recipe! #food",
            "🔥 Viral {dish} Recipe That Everyone's Making!",
            "✨ The Secret to Perfect {dish} Revealed!",
            "👨‍🍳 How to Make Amazing {dish} at Home",
            "💯 Best {dish} Recipe You'll Ever See!",
            "🎯 Quick & Easy {dish} for Busy Days",
            "🌟 Restaurant-Quality {dish} at Home!",
            "😍 This {dish} Recipe Will Blow Your Mind!",
            "🚀 5-Minute {dish} Hack You Need to Know!",
        ]
        
        # Food dish names for title generation
        self.dish_names = [
            "Pasta", "Pizza", "Cake", "Cookies", "Smoothie",
            "Salad", "Sandwich", "Tacos", "Burger", "Fries",
            "Chicken", "Steak", "Fish", "Rice Bowl", "Noodles",
            "Soup", "Bread", "Muffins", "Pancakes", "Waffles",
        ]

    def generate_title(self, keyword: str = None) -> str:
        """
        Generate an engaging title for a YouTube Short.
        
        Args:
            keyword: Optional keyword/topic for the video
            
        Returns:
            Generated title string
        """
        template = random.choice(self.title_templates)
        
        if keyword:
            # Extract dish name from keyword or use generic
            dish = self._extract_dish_name(keyword)
        else:
            dish = random.choice(self.dish_names)
        
        title = template.format(dish=dish)
        
        # Ensure title is under 100 characters (YouTube limit)
        if len(title) > 100:
            title = title[:97] + "..."
        
        logger.info(f"Generated title: {title}")
        return title

    def _extract_dish_name(self, keyword: str) -> str:
        """
        Extract a dish name from a keyword.
        
        Args:
            keyword: Input keyword
            
        Returns:
            Extracted or generated dish name
        """
        # Simple extraction - look for common food words
        food_words = ["pasta", "pizza", "cake", "chicken", "beef", "fish", 
                     "salad", "soup", "bread", "rice", "noodles", "tacos"]
        
        keyword_lower = keyword.lower()
        for word in food_words:
            if word in keyword_lower:
                return word.capitalize()
        
        # If no match, return a random dish
        return random.choice(self.dish_names)

    def generate_description(self, keyword: str = None, title: str = None) -> str:
        """
        Generate an SEO-optimized description for a YouTube Short.
        
        Args:
            keyword: Optional keyword/topic for the video
            title: Optional title of the video
            
        Returns:
            Generated description string
        """
        # Base description templates
        descriptions = [
            "Try this amazing recipe! Perfect for quick meals and busy days. "
            "Don't forget to like and subscribe for more delicious recipes! 🍴",
            
            "Watch till the end for the secret ingredient! 😋 "
            "Subscribe for daily food content and cooking tips!",
            
            "This recipe will change your life! Super easy and incredibly tasty. "
            "Hit that subscribe button for more! 🔥",
            
            "Perfect for beginners! Follow along and make this at home today. "
            "Like and subscribe for weekly recipes! ✨",
            
            "The easiest recipe you'll ever make! Save this for later and "
            "subscribe for more food inspiration! 💯",
        ]
        
        description = random.choice(descriptions)
        
        # Add relevant hashtags
        hashtags = self.generate_hashtags(keyword)
        hashtag_string = " ".join(hashtags[:10])  # Use top 10 hashtags
        
        full_description = f"{description}\n\n{hashtag_string}"
        
        logger.info(f"Generated description (length: {len(full_description)})")
        return full_description

    def generate_hashtags(self, keyword: str = None) -> List[str]:
        """
        Generate relevant hashtags for the video.
        
        Args:
            keyword: Optional keyword/topic for the video
            
        Returns:
            List of hashtags
        """
        hashtags = list(self.default_hashtags)  # Start with defaults
        
        # Add keyword-specific hashtags
        if keyword:
            keyword_tags = [
                f"#{keyword.replace(' ', '')}",
                f"#{keyword.replace(' ', '_')}",
            ]
            hashtags = keyword_tags + hashtags
        
        # Add trending food hashtags
        trending_tags = [
            "#foodtiktok",
            "#recipetok",
            "#cookingathome",
            "#foodreels",
            "#viralfood",
            "#trending",
            "#fyp",
            "#shortsvideo",
            "#youtubeshorts",
        ]
        
        # Mix in some trending tags
        hashtags.extend(random.sample(trending_tags, 5))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            if tag not in seen:
                seen.add(tag)
                unique_hashtags.append(tag)
        
        # Return top 15 hashtags (YouTube allows up to 15 in description)
        return unique_hashtags[:15]

    def generate_tags(self, keyword: str = None) -> List[str]:
        """
        Generate YouTube tags for better discoverability.
        
        Args:
            keyword: Optional keyword/topic for the video
            
        Returns:
            List of tags
        """
        base_tags = [
            "food",
            "recipe",
            "cooking",
            "easy recipe",
            "quick recipe",
            "food shorts",
            "youtube shorts",
            "cooking tutorial",
            "food video",
            "recipe video",
        ]
        
        if keyword:
            base_tags.insert(0, keyword)
            base_tags.insert(1, f"{keyword} recipe")
            base_tags.insert(2, f"{keyword} cooking")
        
        # Add category-specific tags
        category_tags = [
            "how to cook",
            "best recipes",
            "homemade",
            "delicious",
            "tasty",
            "food lover",
            "cooking hacks",
            "kitchen tips",
        ]
        
        base_tags.extend(random.sample(category_tags, 5))
        
        return base_tags

    def generate_full_metadata(self, keyword: str = None) -> Dict:
        """
        Generate complete metadata for a YouTube Short.
        
        Args:
            keyword: Optional keyword/topic for the video
            
        Returns:
            Dictionary with all metadata fields
        """
        title = self.generate_title(keyword)
        description = self.generate_description(keyword, title)
        tags = self.generate_tags(keyword)
        hashtags = self.generate_hashtags(keyword)
        
        metadata = {
            "title": title,
            "description": description,
            "tags": tags,
            "hashtags": hashtags,
            "category_id": "26",  # Pets & Animals - but we'll use Food category
            "privacy_status": "public",
        }
        
        logger.info(f"Generated complete metadata for keyword: {keyword}")
        return metadata


if __name__ == "__main__":
    # Test the metadata generator
    generator = MetadataGenerator()
    
    # Test with different keywords
    keywords = ["pasta recipe", "chicken dishes", "dessert ideas", None]
    
    for keyword in keywords:
        print(f"\n=== Keyword: {keyword} ===")
        metadata = generator.generate_full_metadata(keyword)
        print(f"Title: {metadata['title']}")
        print(f"Description: {metadata['description'][:100]}...")
        print(f"Tags: {metadata['tags'][:5]}...")
        print(f"Hashtags: {metadata['hashtags'][:5]}...")
