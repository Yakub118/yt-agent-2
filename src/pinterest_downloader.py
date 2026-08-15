"""
Pinterest Downloader Module
Downloads food-related videos from Pinterest using the official API.
"""
import os
import logging
from typing import List, Dict, Optional
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PinterestDownloader:
    """Download videos from Pinterest with smart viral content sourcing."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.pinterest.com/v5"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        self.min_repins_for_viral = 1000
        self.min_likes_for_viral = 500
        self.days_lookback = 30

    def search_pins(self, query: str, page_size: int = 20) -> List[Dict]:
        """Search for public pins using the correct Pinterest v5 Search API."""
        pins = []
        try:
            # CORRECT ENDPOINT for public search
            url = f"{self.base_url}/search/pins"
            params = {
                "query": query,
                "page_size": page_size
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            raw_pins = data.get("items", [])
            
            # Filter strictly for VIDEO pins (Images don't work for Shorts)
            for pin in raw_pins:
                media = pin.get("media", {})
                if media.get("media_type") == "video":
                    pins.append(pin)
            
            logger.info(f"Found {len(pins)} VIDEO pins for query: {query}")
            return pins
            
        except Exception as e:
            logger.error(f"Error searching Pinterest API: {e}")
            return []

    def get_viral_pins(self, query: str, max_results: int = 10) -> List[Dict]:
        """Get viral pins (relies on Pinterest search relevance)."""
        logger.info(f"Searching for viral content: {query}")
        pins = self.search_pins(query, page_size=max_results * 2)
        
        viral_pins = []
        cutoff_date = datetime.now() - timedelta(days=self.days_lookback)
        
        for pin in pins:
            media = pin.get("media", {})
            if media.get("media_type") != "video":
                continue
            
            created_at = pin.get("created_at", "")
            try:
                if created_at:
                    pin_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    is_recent = pin_date.replace(tzinfo=None) >= cutoff_date
                else:
                    is_recent = True
            except:
                is_recent = True
            
            if is_recent:
                viral_pins.append(pin)
            
            if len(viral_pins) >= max_results:
                break
        
        if len(viral_pins) < max_results:
            viral_pins = pins[:max_results]
            
        logger.info(f"Found {len(viral_pins)} viral/high-engagement pins")
        return viral_pins

    def download_video(self, pin_data: Dict, save_path: str) -> Optional[str]:
        """Download a video from a pin."""
        try:
            media = pin_data.get("media", {})
            videos = media.get("video_list", {}) or media.get("videos", [])
            
            # Try to get highest quality
            video_url = None
            if isinstance(videos, dict) and videos:
                video_url = videos.get("V_HLSV4", {}).get("url") or videos.get("V_HLSV3", {}).get("url") or list(videos.values())[-1].get("url")
            elif isinstance(videos, list) and videos:
                video_url = videos[-1].get("url")
                
            if not video_url:
                video_url = media.get("url")

            if not video_url:
                logger.warning("No video URL found in pin data")
                return None
            
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

    def get_food_videos(self, count: int = 3, use_viral_sourcing: bool = True) -> List[str]:
        """Get food-related video paths from Pinterest."""
        from config.settings import FOOD_KEYWORDS, DOWNLOADED_VIDEOS_DIR
        
        downloaded_paths = []
        
        for keyword in FOOD_KEYWORDS:
            if len(downloaded_paths) >= count:
                break
            
            logger.info(f"Searching for: {keyword}")
            
            if use_viral_sourcing:
                pins = self.get_viral_pins(keyword, max_results=5)
            else:
                pins = self.search_pins(keyword, page_size=5)
            
            for pin in pins:
                if len(downloaded_paths) >= count:
                    break
                
                filename = f"{keyword.replace(' ', '_')}_{pin.get('id', 'unknown')}.mp4"
                save_path = os.path.join(DOWNLOADED_VIDEOS_DIR, filename)
                
                if os.path.exists(save_path):
                    downloaded_paths.append(save_path)
                    continue
                
                video_path = self.download_video(pin, save_path)
                if video_path:
                    downloaded_paths.append(video_path)
        
        logger.info(f"Downloaded {len(downloaded_paths)} videos")
        return downloaded_paths

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    access_token = os.getenv("PINTEREST_ACCESS_TOKEN", "")
    if access_token:
        downloader = PinterestDownloader(access_token)
        videos = downloader.get_food_videos(count=3)
        print(f"Downloaded videos: {videos}")
    else:
        print("Please set PINTEREST_ACCESS_TOKEN environment variable")
