"""
Metadata Generator Module
Generates SEO-optimized titles, descriptions, and hashtags for YouTube Shorts.
"""
import random
import logging
from datetime import datetime
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
