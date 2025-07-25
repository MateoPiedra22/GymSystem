from typing import Optional, List, Dict, Any
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes
from ..core.config import settings
from ..models.configuration import Configuration
from ..core.database import get_db
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
import asyncio
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class InstagramService:
    """Instagram integration service for gym social media management"""
    
    def __init__(self):
        self.client = None
        self.session_file = Path("instagram_session.json")
        self.is_authenticated = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Instagram client"""
        try:
            self.client = Client()
            
            # Load existing session if available
            if self.session_file.exists():
                self.client.load_settings(str(self.session_file))
                self.is_authenticated = True
                logger.info("Instagram session loaded successfully")
            else:
                logger.info("No Instagram session found")
                
        except Exception as e:
            logger.error(f"Failed to initialize Instagram client: {e}")
    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with Instagram"""
        if not self.client:
            return False
        
        try:
            self.client.login(username, password)
            
            # Save session
            self.client.dump_settings(str(self.session_file))
            self.is_authenticated = True
            
            logger.info(f"Successfully authenticated Instagram account: {username}")
            return True
            
        except LoginRequired as e:
            logger.error(f"Instagram login required: {e}")
            return False
        except PleaseWaitFewMinutes as e:
            logger.error(f"Instagram rate limit: {e}")
            return False
        except Exception as e:
            logger.error(f"Instagram authentication failed: {e}")
            return False
    
    async def get_recent_posts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from authenticated account"""
        if not self.is_authenticated or not self.client:
            logger.error("Instagram not authenticated")
            return []
        
        try:
            user_id = self.client.user_id
            medias = self.client.user_medias(user_id, count)
            
            posts = []
            for media in medias:
                post_data = {
                    "id": media.id,
                    "code": media.code,
                    "caption": media.caption_text or "",
                    "media_type": media.media_type,
                    "image_url": str(media.thumbnail_url) if media.thumbnail_url else None,
                    "video_url": str(media.video_url) if media.video_url else None,
                    "like_count": media.like_count,
                    "comment_count": media.comment_count,
                    "taken_at": media.taken_at.isoformat() if media.taken_at else None,
                    "permalink": f"https://www.instagram.com/p/{media.code}/"
                }
                posts.append(post_data)
            
            logger.info(f"Retrieved {len(posts)} Instagram posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching Instagram posts: {e}")
            return []
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if not self.is_authenticated or not self.client:
            return None
        
        try:
            user_info = self.client.account_info()
            
            return {
                "username": user_info.username,
                "full_name": user_info.full_name,
                "biography": user_info.biography,
                "follower_count": user_info.follower_count,
                "following_count": user_info.following_count,
                "media_count": user_info.media_count,
                "profile_pic_url": str(user_info.profile_pic_url) if user_info.profile_pic_url else None,
                "is_verified": user_info.is_verified,
                "is_business": user_info.is_business
            }
            
        except Exception as e:
            logger.error(f"Error fetching Instagram account info: {e}")
            return None
    
    async def post_image(
        self,
        image_path: str,
        caption: str,
        hashtags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Post an image to Instagram"""
        if not self.is_authenticated or not self.client:
            logger.error("Instagram not authenticated")
            return None
        
        try:
            # Prepare caption with hashtags
            full_caption = caption
            if hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                full_caption = f"{caption}\n\n{hashtag_text}"
            
            # Upload photo
            media = self.client.photo_upload(
                path=image_path,
                caption=full_caption
            )
            
            logger.info(f"Successfully posted image to Instagram: {media.code}")
            return media.code
            
        except Exception as e:
            logger.error(f"Error posting image to Instagram: {e}")
            return None
    
    async def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Post a video to Instagram"""
        if not self.is_authenticated or not self.client:
            logger.error("Instagram not authenticated")
            return None
        
        try:
            # Prepare caption with hashtags
            full_caption = caption
            if hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                full_caption = f"{caption}\n\n{hashtag_text}"
            
            # Upload video
            media = self.client.video_upload(
                path=video_path,
                caption=full_caption
            )
            
            logger.info(f"Successfully posted video to Instagram: {media.code}")
            return media.code
            
        except Exception as e:
            logger.error(f"Error posting video to Instagram: {e}")
            return None
    
    async def get_post_insights(self, media_code: str) -> Optional[Dict[str, Any]]:
        """Get insights for a specific post"""
        if not self.is_authenticated or not self.client:
            return None
        
        try:
            media_id = self.client.media_id(media_code)
            media_info = self.client.media_info(media_id)
            
            return {
                "like_count": media_info.like_count,
                "comment_count": media_info.comment_count,
                "view_count": getattr(media_info, 'view_count', 0),
                "reach": getattr(media_info, 'reach', 0),
                "impressions": getattr(media_info, 'impressions', 0)
            }
            
        except Exception as e:
            logger.error(f"Error fetching post insights: {e}")
            return None
    
    async def schedule_post(
        self,
        content_type: str,
        file_path: str,
        caption: str,
        hashtags: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Schedule a post for later (stored in database for processing)"""
        try:
            # For now, we'll store scheduled posts in the database
            # and process them with a background task
            
            scheduled_post = {
                "content_type": content_type,
                "file_path": file_path,
                "caption": caption,
                "hashtags": hashtags or [],
                "scheduled_time": scheduled_time or datetime.now(),
                "status": "scheduled",
                "created_at": datetime.now()
            }
            
            # TODO: Store in database
            logger.info(f"Post scheduled for {scheduled_time}")
            
            return {
                "success": True,
                "message": "Post scheduled successfully",
                "scheduled_time": scheduled_time
            }
            
        except Exception as e:
            logger.error(f"Error scheduling post: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def get_hashtag_suggestions(self, base_hashtags: List[str]) -> List[str]:
        """Get hashtag suggestions based on gym content"""
        # Predefined hashtag suggestions for gym content
        gym_hashtags = [
            "fitness", "gym", "workout", "training", "health",
            "bodybuilding", "cardio", "strength", "muscle", "fit",
            "exercise", "wellness", "lifestyle", "motivation", "goals",
            "transformation", "progress", "dedication", "discipline", "results",
            "crossfit", "yoga", "pilates", "zumba", "spinning",
            "personaltrainer", "coach", "nutrition", "protein", "supplements"
        ]
        
        # Combine with base hashtags and remove duplicates
        all_hashtags = list(set(base_hashtags + gym_hashtags))
        
        # Return top suggestions (limit to 30 for Instagram)
        return all_hashtags[:30]
    
    async def analyze_best_posting_times(self) -> Dict[str, Any]:
        """Analyze best times to post based on account activity"""
        try:
            # This would require Instagram Insights API for business accounts
            # For now, return general best practices for gym content
            
            return {
                "best_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
                "best_times": {
                    "morning": "06:00-09:00",
                    "lunch": "12:00-13:00",
                    "evening": "17:00-20:00"
                },
                "recommendations": [
                    "Post workout motivation on Monday mornings",
                    "Share transformation photos on Wednesday",
                    "Post class schedules on Sunday evenings",
                    "Share nutrition tips during lunch hours"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing posting times: {e}")
            return {}
    
    async def disconnect(self):
        """Disconnect from Instagram and clear session"""
        try:
            if self.session_file.exists():
                os.remove(self.session_file)
            
            self.is_authenticated = False
            self.client = None
            
            logger.info("Instagram service disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting Instagram service: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            "connected": self.is_authenticated,
            "client_initialized": self.client is not None,
            "session_file_exists": self.session_file.exists()
        }

# Global instance
instagram_service = InstagramService()