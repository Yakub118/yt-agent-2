"""
Pinterest Downloader Module
Downloads food-related videos from Pinterest using the API or web scraping.
"""
import os
import re
import json
import logging
from typing import List, Dict, Optional
import httpx
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PinterestDownloader:
    """Download videos from Pinterest."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.pinterest.com/v5"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def search_pins(self, query: str, page_size: int = 10) -> List[Dict]:
        """
        Search for pins with a specific query.
        
        Args:
            query: Search query (e.g., "food recipes")
            page_size: Number of results to return
            
        Returns:
            List of pin data dictionaries
        """
        pins = []
        try:
            # Note: Pinterest API v5 has limited search capabilities
            # This is a simplified implementation
            url = f"{self.base_url}/pins"
            params = {"page_size": page_size}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            pins = data.get("items", [])
            logger.info(f"Found {len(pins)} pins for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching pins: {e}")
            # Fallback to web scraping method
            pins = self._scrape_pinterest_search(query, page_size)
        
        return pins

    def _scrape_pinterest_search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Scrape Pinterest search results for video pins.
        This is a fallback method when API is not available.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of pin data dictionaries
        """
        pins = []
        try:
            # Use Pinterest search URL
            search_url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            # Extract video URLs from the page
            # This is a simplified extraction - real implementation would need proper parsing
            video_urls = re.findall(r'https://[^\s"\']+\.(mp4|mov|avi)[^\s"\']*', response.text)
            
            for url in video_urls[:max_results]:
                pins.append({
                    "id": f"scraped_{len(pins)}",
                    "media": {"videos": [{"url": url}]},
                    "title": query,
                    "description": f"Food video: {query}",
                })
            
            logger.info(f"Scraped {len(pins)} video pins for query: {query}")
            
        except Exception as e:
            logger.error(f"Error scraping Pinterest: {e}")
        
        return pins

    def download_video(self, pin_data: Dict, save_path: str) -> Optional[str]:
        """
        Download a video from a pin.
        
        Args:
            pin_data: Pin data dictionary
            save_path: Path to save the video
            
        Returns:
            Path to downloaded video or None if failed
        """
        try:
            # Extract video URL from pin data
            media = pin_data.get("media", {})
            videos = media.get("videos", [])
            
            if not videos:
                # Try alternative extraction for scraped data
                video_url = pin_data.get("video_url") or pin_data.get("url")
                if not video_url:
                    logger.warning("No video URL found in pin data")
                    return None
            else:
                # Get the best quality video
                video_url = videos[-1].get("url")  # Last is usually highest quality
            
            if not video_url:
                logger.warning("No video URL found")
                return None
            
            # Download the video
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded successfully: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None

    def get_food_videos(self, count: int = 3) -> List[str]:
        """
        Get food-related video URLs from Pinterest.
        
        Args:
            count: Number of videos to retrieve
            
        Returns:
            List of paths to downloaded videos
        """
        from config.settings import FOOD_KEYWORDS, DOWNLOADED_VIDEOS_DIR
        
        downloaded_paths = []
        keywords_used = []
        
        # Rotate through keywords to get variety
        for keyword in FOOD_KEYWORDS:
            if len(downloaded_paths) >= count:
                break
            
            logger.info(f"Searching for: {keyword}")
            pins = self.search_pins(keyword, page_size=5)
            
            for pin in pins:
                if len(downloaded_paths) >= count:
                    break
                
                # Create unique filename
                filename = f"{keyword.replace(' ', '_')}_{pin.get('id', 'unknown')}.mp4"
                save_path = os.path.join(DOWNLOADED_VIDEOS_DIR, filename)
                
                # Skip if already downloaded
                if os.path.exists(save_path):
                    logger.info(f"Video already exists: {save_path}")
                    downloaded_paths.append(save_path)
                    continue
                
                # Download video
                video_path = self.download_video(pin, save_path)
                if video_path:
                    downloaded_paths.append(video_path)
                    keywords_used.append(keyword)
        
        logger.info(f"Downloaded {len(downloaded_paths)} videos")
        return downloaded_paths


if __name__ == "__main__":
    # Test the downloader
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    access_token = os.getenv("PINTEREST_ACCESS_TOKEN", "")
    
    if access_token:
        downloader = PinterestDownloader(access_token)
        videos = downloader.get_food_videos(count=3)
        print(f"Downloaded videos: {videos}")
    else:
        print("Please set PINTEREST_ACCESS_TOKEN environment variable")
