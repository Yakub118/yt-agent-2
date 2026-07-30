"""
YouTube Uploader Module
Uploads videos to YouTube Shorts with proper metadata and authentication.
"""
import os
import logging
from typing import Optional, Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeUploader:
    """Upload videos to YouTube Shorts."""

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.youtube = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with YouTube API using OAuth2."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            
            # Create credentials from refresh token
            credentials = Credentials(
                None,  # No access token initially
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=["https://www.googleapis.com/auth/youtube.upload"],
            )
            
            # Refresh the token to get access token
            credentials.refresh(Request())
            
            # Build YouTube API client
            self.youtube = build("youtube", "v3", credentials=credentials)
            
            logger.info("Successfully authenticated with YouTube API")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        category_id: str = "26",
        privacy_status: str = "public",
    ) -> Optional[Dict]:
        """
        Upload a video to YouTube Shorts.
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (26 = Howto & Style for food)
            privacy_status: Privacy setting (public, private, unlisted)
            
        Returns:
            Upload result dictionary or None if failed
        """
        try:
            from googleapiclient.http import MediaFileUpload
            from googleapiclient.errors import ResumableUploadError
            
            if not self.youtube:
                logger.error("YouTube API client not initialized")
                return None
            
            logger.info(f"Uploading video: {video_path}")
            logger.info(f"Title: {title}")
            
            # Prepare video metadata
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category_id,
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "madeForKids": False,
                    "selfDeclaredMadeForKids": False,
                },
            }
            
            # Prepare media file
            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=1024 * 1024,  # 1MB chunks
            )
            
            # Upload video
            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
            
            logger.info(f"Upload successful! Video ID: {response.get('id')}")
            
            return {
                "success": True,
                "video_id": response.get("id"),
                "title": response.get("snippet", {}).get("title"),
                "url": f"https://www.youtube.com/shorts/{response.get('id')}",
            }
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {"success": False, "error": str(e)}

    def check_channel_status(self) -> Dict:
        """
        Check YouTube channel status and statistics.
        
        Returns:
            Channel status dictionary
        """
        try:
            if not self.youtube:
                return {"error": "Not authenticated"}
            
            # Get channel details
            request = self.youtube.channels().list(
                part="snippet,statistics,status",
                mine=True,
            )
            
            response = request.execute()
            
            if response.get("items"):
                channel = response["items"][0]
                return {
                    "channel_name": channel["snippet"]["title"],
                    "subscribers": channel["statistics"].get("subscriberCount", "0"),
                    "total_views": channel["statistics"].get("viewCount", "0"),
                    "video_count": channel["statistics"].get("videoCount", "0"),
                    "privacy_status": channel["status"]["privacyStatus"],
                    "made_for_kids": channel["status"].get("madeForKids", False),
                }
            
            return {"error": "Channel not found"}
            
        except Exception as e:
            logger.error(f"Error checking channel status: {e}")
            return {"error": str(e)}


def create_youtube_uploader_from_env() -> YouTubeUploader:
    """
    Create YouTubeUploader instance from environment variables.
    
    Returns:
        YouTubeUploader instance
    """
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing YouTube credentials. Please set YOUTUBE_CLIENT_ID, "
            "YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN environment variables."
        )
    
    return YouTubeUploader(client_id, client_secret, refresh_token)


if __name__ == "__main__":
    # Test the uploader
    try:
        uploader = create_youtube_uploader_from_env()
        
        # Check channel status
        status = uploader.check_channel_status()
        print(f"Channel Status: {status}")
        
        # Note: Actual upload test requires a valid video file
        # result = uploader.upload_video(
        #     video_path="/path/to/video.mp4",
        #     title="Test Video",
        #     description="Test description",
        #     tags=["test", "food"],
        # )
        # print(f"Upload result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set YouTube credentials in environment variables")
