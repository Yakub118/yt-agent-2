"""
Main Agent Module
Orchestrates the entire Pinterest to YouTube Shorts automation workflow.
"""
import os
import sys
import json
import requests
import logging
from datetime import datetime
from typing import List, Dict

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Duplicate prevention - prevents uploading same video multiple times
HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "upload_history.json")


class PinterestToYouTubeAgent:
    """
    Main agent that orchestrates the complete workflow:
    1. Download food videos from Pinterest
    2. Process videos for YouTube Shorts format
    3. Generate SEO-optimized metadata
    4. Upload to YouTube at optimal times
    """

    def __init__(self):
        """Initialize all components of the agent."""
        logger.info("Initializing Pinterest to YouTube Agent...")
        
        # Import and initialize components
        from src.pinterest_downloader import PinterestDownloader
        from src.video_processor import VideoProcessor
        from src.metadata_generator import MetadataGenerator
        from src.youtube_uploader import create_youtube_uploader_from_env
        from src.scheduler import UploadScheduler
        
        # Initialize downloader
        pinterest_token = os.getenv("PINTEREST_ACCESS_TOKEN", "")
        self.downloader = PinterestDownloader(pinterest_token) if pinterest_token else None
        
        # Initialize processor
        self.processor = VideoProcessor()
        
        # Initialize metadata generator
        self.metadata_gen = MetadataGenerator()
        
        # Initialize uploader (requires credentials)
        try:
            self.uploader = create_youtube_uploader_from_env()
        except Exception as e:
            logger.warning(f"YouTube uploader not initialized: {e}")
            self.uploader = None
        
        # Initialize scheduler
        timezone = os.getenv("TIMEZONE", "America/New_York")
        self.scheduler = UploadScheduler(timezone)
        
        logger.info("Agent initialization complete!")

    def run_daily_workflow(self, force_upload: bool = False) -> Dict:
        """
        Run the complete daily workflow.
        
        Args:
            force_upload: If True, upload immediately regardless of schedule
            
        Returns:
            Workflow execution results
        """
        logger.info("=" * 60)
        logger.info("Starting Daily Pinterest to YouTube Workflow")
        logger.info("=" * 60)
        
        results = {
            "success": False,
            "videos_downloaded": 0,
            "videos_processed": 0,
            "videos_uploaded": 0,
            "errors": [],
            "uploaded_videos": [],
        }
        
        try:
            # Step 1: Check if we should upload now
            if not force_upload:
                should_upload = self.scheduler.should_upload_now()
                if not should_upload:
                    next_upload = self.scheduler.get_next_upload_time()
                    logger.info(f"Not within upload window. Next upload: {next_upload}")
                    results["success"] = True
                    results["message"] = f"Waiting for scheduled time: {next_upload}"
                    return results
            
            # Load upload history to prevent duplicate uploads
            history = []
            if os.path.exists(HISTORY_FILE):
                try:
                    with open(HISTORY_FILE, 'r') as f:
                        history = json.load(f)
                except Exception:
                    history = []
            logger.info(f"Loaded upload history: {len(history)} videos")
            
            # Step 2: Download videos from Pinterest
            if self.downloader:
                logger.info("\n📥 Step 1: Downloading videos from Pinterest...")
                downloaded_videos = self.downloader.get_food_videos(count=3)
                results["videos_downloaded"] = len(downloaded_videos)
                logger.info(f"Downloaded {len(downloaded_videos)} videos")
            else:
                logger.warning("Pinterest downloader not configured")
                downloaded_videos = []
            
            if not downloaded_videos:
                results["errors"].append("No videos downloaded")
                return results
            
            # Filter out duplicates using Pinterest pin IDs
            unique_videos = []
            for video_path in downloaded_videos:
                filename = os.path.basename(video_path)
                parts = filename.replace('.mp4', '').split('_')
                pin_id = parts[-1] if len(parts) > 1 else filename
                
                if pin_id in history:
                    logger.info(f"Skipping duplicate video: {pin_id}")
                    continue
                
                unique_videos.append(video_path)
                history.append(pin_id)
            
            downloaded_videos = unique_videos
            logger.info(f"Filtered to {len(downloaded_videos)} unique videos after duplicate check")
            
            if not downloaded_videos:
                results["message"] = "All downloaded videos were duplicates"
                results["success"] = True
                # Save history anyway
                with open(HISTORY_FILE, 'w') as f:
                    json.dump(history, f, indent=2)
                return results

            # Step 3: Process videos for YouTube Shorts
            logger.info("\n✂️ Step 2: Processing videos for YouTube Shorts...")
            processed_videos = []
            
            from config.settings import PROCESSED_VIDEOS_DIR
            
            # Initialize trending audio engine and download top track
            from src.metadata_generator import TrendingAudioEngine
            
            audio_engine = TrendingAudioEngine()
            trending_tracks = audio_engine.get_trending_audio(1)
            
            trending_audio_file = None
            if trending_tracks and trending_tracks[0].get('url'):
                audio_url = trending_tracks[0]['url']
                trending_audio_file = "/tmp/trending_audio.mp3"
                try:
                    r = requests.get(audio_url, timeout=15)
                    with open(trending_audio_file, 'wb') as f:
                        f.write(r.content)
                    logger.info(f"Downloaded trending audio: {trending_audio_file}")
                except Exception as e:
                    logger.warning(f"Failed to download trending audio: {e}")
                    trending_audio_file = None
            
            for video_path in downloaded_videos:
                filename = os.path.basename(video_path)
                output_path = os.path.join(PROCESSED_VIDEOS_DIR, f"processed_{filename}")
                voiceover_path = "/tmp/voiceover.mp3"
                
                # Generate metadata & script
                keyword = filename.split("_")[0]
                
                # Create a 15-second script for the AI to read
                ai_script = f"Here is the easiest {keyword} recipe you will ever see. Watch closely, because this will change how you cook forever. Don't forget to subscribe for more daily hacks!"
                
                # Generate voiceover using Edge-TTS
                self.processor._generate_edge_voiceover(ai_script, voiceover_path)
                
                # Process video with trending audio and voiceover
                processed_path = self.processor.process_video(
                    video_path, 
                    output_path, 
                    trending_audio_path=trending_audio_file,
                    voiceover_path=voiceover_path if os.path.exists(voiceover_path) else None
                )
                
                if processed_path:
                    # Validate the processed video
                    is_valid = self.processor.validate_video(processed_path)
                    if is_valid:
                        processed_videos.append({
                            "path": processed_path,
                            "keyword": keyword,
                        })
                        logger.info(f"✓ Processed: {filename}")
                    else:
                        logger.warning(f"Invalid video after processing: {filename}")
                else:
                    logger.error(f"Failed to process: {filename}")
            
            results["videos_processed"] = len(processed_videos)
            
            if not processed_videos:
                results["errors"].append("No videos successfully processed")
                # Save history anyway
                with open(HISTORY_FILE, 'w') as f:
                    json.dump(history, f, indent=2)
                return results
            
            # Step 4: Generate metadata and upload to YouTube
            if self.uploader:
                logger.info("\n📤 Step 3: Uploading videos to YouTube...")
                
                for video_info in processed_videos:
                    video_path = video_info["path"]
                    keyword = video_info.get("keyword", "food recipe")
                    
                    # Generate metadata
                    metadata = self.metadata_gen.generate_full_metadata(keyword)
                    
                    # Upload video
                    upload_result = self.uploader.upload_video(
                        video_path=video_path,
                        title=metadata["title"],
                        description=metadata["description"],
                        tags=metadata["tags"],
                        category_id="26",  # Howto & Style (includes cooking)
                        privacy_status="public",
                    )
                    
                    if upload_result and upload_result.get("success"):
                        results["videos_uploaded"] += 1
                        results["uploaded_videos"].append(upload_result)
                        logger.info(f"✓ Uploaded: {metadata['title']}")
                        logger.info(f"  URL: {upload_result.get('url')}")
                    else:
                        error_msg = upload_result.get("error", "Unknown error") if upload_result else "Upload failed"
                        results["errors"].append(f"Failed to upload {video_path}: {error_msg}")
                        logger.error(f"✗ Upload failed: {error_msg}")
            else:
                logger.warning("YouTube uploader not configured - skipping upload step")
                results["message"] = "Videos processed but not uploaded (no YouTube credentials)"
            
            # Step 5: Summary
            logger.info("\n" + "=" * 60)
            logger.info("Workflow Complete!")
            logger.info("=" * 60)
            logger.info(f"Videos Downloaded: {results['videos_downloaded']}")
            logger.info(f"Videos Processed: {results['videos_processed']}")
            logger.info(f"Videos Uploaded: {results['videos_uploaded']}")
            
            if results["errors"]:
                logger.warning(f"Errors: {len(results['errors'])}")
                for error in results["errors"]:
                    logger.warning(f"  - {error}")
            
            results["success"] = results["videos_uploaded"] > 0 or not self.uploader
            
            # Save upload history to prevent future duplicates
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
            logger.info(f"Saved upload history: {len(history)} videos")
            
            return results
            
        except Exception as e:
            logger.error(f"Workflow failed with error: {e}")
            results["errors"].append(str(e))
            return results

    def check_channel_status(self) -> Dict:
        """
        Check YouTube channel status and monetization progress.
        
        Returns:
            Channel status information
        """
        if not self.uploader:
            return {"error": "YouTube uploader not configured"}
        
        return self.uploader.check_channel_status()

    def print_schedule(self):
        """Print the upload schedule."""
        print("\n" + self.scheduler.format_upload_schedule())


def main():
    """Main entry point for the agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pinterest to YouTube Shorts Agent")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force upload immediately, ignoring schedule",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Print upload schedule and exit",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check YouTube channel status",
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = PinterestToYouTubeAgent()
    
    if args.schedule:
        agent.print_schedule()
        return
    
    if args.status:
        status = agent.check_channel_status()
        print("\nChannel Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return
    
    # Run workflow
    results = agent.run_daily_workflow(force_upload=args.force)
    
    # Exit with appropriate code
    if results.get("success"):
        print("\n✅ Workflow completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Workflow completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
