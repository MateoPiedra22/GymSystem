from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import aiohttp
import json
import logging
import hashlib
import hmac
import base64
from urllib.parse import urlencode, urlparse
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from ..core.database import Base, get_db
from ..core.config import settings
from .config_service import get_config_service
import xml.etree.ElementTree as ET
from xml.dom import minidom
import csv
import io
from jinja2 import Template

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Types of integrations"""
    REST_API = "rest_api"
    SOAP_API = "soap_api"
    WEBHOOK = "webhook"
    FTP = "ftp"
    SFTP = "sftp"
    EMAIL = "email"
    DATABASE = "database"
    FILE_SYNC = "file_sync"
    PAYMENT_GATEWAY = "payment_gateway"
    SMS_PROVIDER = "sms_provider"
    SOCIAL_MEDIA = "social_media"

class IntegrationStatus(Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"
    MAINTENANCE = "maintenance"

class RequestMethod(Enum):
    """HTTP request methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class AuthType(Enum):
    """Authentication types"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    CUSTOM_HEADER = "custom_header"
    HMAC_SIGNATURE = "hmac_signature"

@dataclass
class IntegrationConfig:
    """Integration configuration"""
    name: str
    integration_type: IntegrationType
    base_url: str
    auth_type: AuthType = AuthType.NONE
    auth_config: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1
    rate_limit: Optional[int] = None  # requests per minute
    enabled: bool = True
    webhook_secret: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IntegrationRequest:
    """Integration request data"""
    method: RequestMethod
    endpoint: str
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    files: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None

@dataclass
class IntegrationResponse:
    """Integration response data"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time: float
    success: bool
    error: Optional[str] = None

class IntegrationLogModel(Base):
    """Integration log database model"""
    __tablename__ = "integration_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    integration_name = Column(String(100), nullable=False, index=True)
    integration_type = Column(String(20), nullable=False, index=True)
    
    # Request details
    method = Column(String(10), nullable=False)
    endpoint = Column(String(500), nullable=False)
    request_data = Column(JSON, nullable=True)
    request_headers = Column(JSON, nullable=True)
    
    # Response details
    status_code = Column(Integer, nullable=True)
    response_data = Column(JSON, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    
    # Status and error handling
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    user_id = Column(Integer, nullable=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WebhookLogModel(Base):
    """Webhook log database model"""
    __tablename__ = "webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_name = Column(String(100), nullable=False, index=True)
    source_ip = Column(String(45), nullable=True)
    
    # Request details
    method = Column(String(10), nullable=False)
    headers = Column(JSON, nullable=True)
    payload = Column(JSON, nullable=True)
    raw_payload = Column(Text, nullable=True)
    
    # Processing details
    processed = Column(Boolean, default=False)
    processing_time_ms = Column(Float, nullable=True)
    response_status = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Security
    signature_valid = Column(Boolean, nullable=True)
    
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)

class IntegrationService:
    """Comprehensive integration service for external APIs and services"""
    
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.webhook_handlers: Dict[str, Callable] = {}
        self.rate_limiters: Dict[str, List[datetime]] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        self._load_integrations()
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _load_integrations(self):
        """Load integration configurations"""
        try:
            # Load from configuration service
            integration_configs = get_config_service().get_category_configs("integrations")
            
            for name, config in integration_configs.items():
                if config.get("enabled", False):
                    self.integrations[name] = IntegrationConfig(
                        name=name,
                        integration_type=IntegrationType(config.get("type", "rest_api")),
                        base_url=config.get("base_url", ""),
                        auth_type=AuthType(config.get("auth_type", "none")),
                        auth_config=config.get("auth_config", {}),
                        headers=config.get("headers", {}),
                        timeout=config.get("timeout", 30),
                        retry_attempts=config.get("retry_attempts", 3),
                        retry_delay=config.get("retry_delay", 1),
                        rate_limit=config.get("rate_limit"),
                        enabled=config.get("enabled", True),
                        webhook_secret=config.get("webhook_secret"),
                        custom_settings=config.get("custom_settings", {})
                    )
            
            # Add default integrations
            self._add_default_integrations()
            
        except Exception as e:
            logger.error(f"Failed to load integrations: {e}")
    
    def _add_default_integrations(self):
        """Add default integration configurations"""
        # Payment gateway integrations
        if "stripe" not in self.integrations:
            self.integrations["stripe"] = IntegrationConfig(
                name="stripe",
                integration_type=IntegrationType.REST_API,
                base_url="https://api.stripe.com/v1",
                auth_type=AuthType.BEARER_TOKEN,
                auth_config={"token_key": "stripe_secret_key"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                enabled=False
            )
        
        # SMS provider integrations
        if "twilio" not in self.integrations:
            self.integrations["twilio"] = IntegrationConfig(
                name="twilio",
                integration_type=IntegrationType.REST_API,
                base_url="https://api.twilio.com/2010-04-01",
                auth_type=AuthType.BASIC_AUTH,
                auth_config={"username_key": "twilio_account_sid", "password_key": "twilio_auth_token"},
                enabled=False
            )
        
        # Social media integrations
        if "facebook" not in self.integrations:
            self.integrations["facebook"] = IntegrationConfig(
                name="facebook",
                integration_type=IntegrationType.REST_API,
                base_url="https://graph.facebook.com/v18.0",
                auth_type=AuthType.API_KEY,
                auth_config={"key_param": "access_token", "key_name": "facebook_access_token"},
                enabled=False
            )
    
    async def make_request(self, integration_name: str, request: IntegrationRequest,
                          user_id: Optional[int] = None,
                          correlation_id: Optional[str] = None) -> IntegrationResponse:
        """Make an API request to an integration"""
        if integration_name not in self.integrations:
            raise ValueError(f"Integration '{integration_name}' not found")
        
        config = self.integrations[integration_name]
        
        if not config.enabled:
            raise ValueError(f"Integration '{integration_name}' is disabled")
        
        # Check rate limiting
        if not self._check_rate_limit(integration_name, config.rate_limit):
            raise ValueError(f"Rate limit exceeded for integration '{integration_name}'")
        
        start_time = datetime.utcnow()
        
        try:
            # Prepare request
            url = f"{config.base_url.rstrip('/')}/{request.endpoint.lstrip('/')}"
            headers = {**config.headers, **(request.headers or {})}
            timeout = request.timeout or config.timeout
            
            # Add authentication
            headers, params, data = self._add_authentication(
                config, headers, request.params or {}, request.data
            )
            
            # Merge params
            if request.params:
                params.update(request.params)
            
            # Make request with retries
            response = await self._make_request_with_retry(
                config, request.method, url, headers, params, 
                data or request.data, request.files, timeout
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Parse response
            response_data = await self._parse_response(response)
            
            integration_response = IntegrationResponse(
                status_code=response.status,
                data=response_data,
                headers=dict(response.headers),
                response_time=response_time,
                success=200 <= response.status < 300
            )
            
            # Log request
            await self._log_integration_request(
                integration_name, config.integration_type, request,
                integration_response, user_id, correlation_id
            )
            
            return integration_response
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            error_response = IntegrationResponse(
                status_code=0,
                data=None,
                headers={},
                response_time=response_time,
                success=False,
                error=str(e)
            )
            
            # Log error
            await self._log_integration_request(
                integration_name, config.integration_type, request,
                error_response, user_id, correlation_id
            )
            
            raise
    
    async def process_webhook(self, webhook_name: str, method: str, headers: Dict[str, str],
                            payload: Any, source_ip: Optional[str] = None) -> Dict[str, Any]:
        """Process incoming webhook"""
        start_time = datetime.utcnow()
        
        try:
            # Validate webhook signature if configured
            if webhook_name in self.integrations:
                config = self.integrations[webhook_name]
                if config.webhook_secret:
                    if not self._validate_webhook_signature(
                        config.webhook_secret, headers, payload
                    ):
                        raise ValueError("Invalid webhook signature")
            
            # Process webhook
            if webhook_name in self.webhook_handlers:
                handler = self.webhook_handlers[webhook_name]
                result = await handler(payload, headers)
            else:
                result = {"message": "Webhook received but no handler configured"}
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log webhook
            await self._log_webhook(
                webhook_name, method, headers, payload, source_ip,
                True, processing_time, 200, None, True
            )
            
            return result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log webhook error
            await self._log_webhook(
                webhook_name, method, headers, payload, source_ip,
                False, processing_time, 500, str(e), False
            )
            
            raise
    
    def register_webhook_handler(self, webhook_name: str, handler: Callable):
        """Register a webhook handler function"""
        self.webhook_handlers[webhook_name] = handler
    
    async def test_integration(self, integration_name: str) -> Dict[str, Any]:
        """Test an integration connection"""
        if integration_name not in self.integrations:
            return {"success": False, "error": "Integration not found"}
        
        config = self.integrations[integration_name]
        
        try:
            # Simple health check request
            if config.integration_type == IntegrationType.REST_API:
                request = IntegrationRequest(
                    method=RequestMethod.GET,
                    endpoint="",  # Root endpoint
                    timeout=10
                )
                
                response = await self.make_request(integration_name, request)
                
                return {
                    "success": response.success,
                    "status_code": response.status_code,
                    "response_time": response.response_time,
                    "error": response.error
                }
            else:
                return {"success": True, "message": "Integration type not testable"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_integration_logs(self, integration_name: Optional[str] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Get integration logs"""
        try:
            db = next(get_db())
            
            query = db.query(IntegrationLogModel)
            
            if integration_name:
                query = query.filter(IntegrationLogModel.integration_name == integration_name)
            if start_date:
                query = query.filter(IntegrationLogModel.created_at >= start_date)
            if end_date:
                query = query.filter(IntegrationLogModel.created_at <= end_date)
            
            logs = query.order_by(IntegrationLogModel.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": log.id,
                    "integration_name": log.integration_name,
                    "integration_type": log.integration_type,
                    "method": log.method,
                    "endpoint": log.endpoint,
                    "status_code": log.status_code,
                    "success": log.success,
                    "response_time_ms": log.response_time_ms,
                    "error_message": log.error_message,
                    "retry_count": log.retry_count,
                    "correlation_id": log.correlation_id,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get integration logs: {e}")
            return []
        finally:
            db.close()
    
    async def get_webhook_logs(self, webhook_name: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Get webhook logs"""
        try:
            db = next(get_db())
            
            query = db.query(WebhookLogModel)
            
            if webhook_name:
                query = query.filter(WebhookLogModel.webhook_name == webhook_name)
            if start_date:
                query = query.filter(WebhookLogModel.received_at >= start_date)
            if end_date:
                query = query.filter(WebhookLogModel.received_at <= end_date)
            
            logs = query.order_by(WebhookLogModel.received_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": log.id,
                    "webhook_name": log.webhook_name,
                    "source_ip": log.source_ip,
                    "method": log.method,
                    "processed": log.processed,
                    "processing_time_ms": log.processing_time_ms,
                    "response_status": log.response_status,
                    "error_message": log.error_message,
                    "signature_valid": log.signature_valid,
                    "received_at": log.received_at.isoformat(),
                    "processed_at": log.processed_at.isoformat() if log.processed_at else None
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get webhook logs: {e}")
            return []
        finally:
            db.close()
    
    async def get_integration_statistics(self) -> Dict[str, Any]:
        """Get integration usage statistics"""
        try:
            db = next(get_db())
            
            # Total requests
            total_requests = db.query(IntegrationLogModel).count()
            
            # Successful requests
            successful_requests = db.query(IntegrationLogModel).filter(
                IntegrationLogModel.success == True
            ).count()
            
            # Failed requests
            failed_requests = total_requests - successful_requests
            
            # Success rate
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Average response time
            avg_response_time = db.query(IntegrationLogModel).filter(
                IntegrationLogModel.response_time_ms.isnot(None)
            ).with_entities(IntegrationLogModel.response_time_ms).all()
            
            avg_time = sum(time[0] for time in avg_response_time if time[0]) / len(avg_response_time) if avg_response_time else 0
            
            # Requests by integration
            integration_stats = {}
            for integration_name in self.integrations.keys():
                count = db.query(IntegrationLogModel).filter(
                    IntegrationLogModel.integration_name == integration_name
                ).count()
                if count > 0:
                    integration_stats[integration_name] = count
            
            # Recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_requests = db.query(IntegrationLogModel).filter(
                IntegrationLogModel.created_at >= yesterday
            ).count()
            
            # Webhook statistics
            total_webhooks = db.query(WebhookLogModel).count()
            processed_webhooks = db.query(WebhookLogModel).filter(
                WebhookLogModel.processed == True
            ).count()
            
            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": round(success_rate, 2),
                "average_response_time_ms": round(avg_time, 2),
                "recent_requests_24h": recent_requests,
                "integration_usage": integration_stats,
                "total_webhooks": total_webhooks,
                "processed_webhooks": processed_webhooks,
                "active_integrations": len([i for i in self.integrations.values() if i.enabled])
            }
            
        except Exception as e:
            logger.error(f"Failed to get integration statistics: {e}")
            return {}
        finally:
            db.close()
    
    def _check_rate_limit(self, integration_name: str, rate_limit: Optional[int]) -> bool:
        """Check if request is within rate limit"""
        if not rate_limit:
            return True
        
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Initialize or clean old requests
        if integration_name not in self.rate_limiters:
            self.rate_limiters[integration_name] = []
        
        # Remove old requests
        self.rate_limiters[integration_name] = [
            req_time for req_time in self.rate_limiters[integration_name]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.rate_limiters[integration_name]) >= rate_limit:
            return False
        
        # Add current request
        self.rate_limiters[integration_name].append(now)
        return True
    
    def _add_authentication(self, config: IntegrationConfig, headers: Dict[str, str],
                          params: Dict[str, str], data: Any) -> tuple:
        """Add authentication to request"""
        if config.auth_type == AuthType.API_KEY:
            key_param = config.auth_config.get("key_param", "api_key")
            key_value = get_config_service().get_config(config.auth_config.get("key_name", "api_key"))
            if key_value:
                if config.auth_config.get("in_header", False):
                    headers[key_param] = key_value
                else:
                    params[key_param] = key_value
        
        elif config.auth_type == AuthType.BEARER_TOKEN:
            token_value = get_config_service().get_config(config.auth_config.get("token_key", "bearer_token"))
            if token_value:
                headers["Authorization"] = f"Bearer {token_value}"
        
        elif config.auth_type == AuthType.BASIC_AUTH:
            username = get_config_service().get_config(config.auth_config.get("username_key", "username"))
            password = get_config_service().get_config(config.auth_config.get("password_key", "password"))
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        elif config.auth_type == AuthType.CUSTOM_HEADER:
            header_name = config.auth_config.get("header_name")
            header_value = get_config_service().get_config(config.auth_config.get("header_key"))
            if header_name and header_value:
                headers[header_name] = header_value
        
        elif config.auth_type == AuthType.HMAC_SIGNATURE:
            # HMAC signature authentication
            secret = get_config_service().get_config(config.auth_config.get("secret_key"))
            if secret and data:
                payload = json.dumps(data) if isinstance(data, dict) else str(data)
                signature = hmac.new(
                    secret.encode(), payload.encode(), hashlib.sha256
                ).hexdigest()
                headers[config.auth_config.get("signature_header", "X-Signature")] = signature
        
        return headers, params, data
    
    async def _make_request_with_retry(self, config: IntegrationConfig, method: RequestMethod,
                                     url: str, headers: Dict[str, str], params: Dict[str, str],
                                     data: Any, files: Any, timeout: int):
        """Make request with retry logic"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        last_exception = None
        
        for attempt in range(config.retry_attempts):
            try:
                # Prepare request data
                request_kwargs = {
                    "headers": headers,
                    "params": params,
                    "timeout": aiohttp.ClientTimeout(total=timeout)
                }
                
                if method in [RequestMethod.POST, RequestMethod.PUT, RequestMethod.PATCH]:
                    if files:
                        # Multipart form data
                        form_data = aiohttp.FormData()
                        if data:
                            for key, value in data.items():
                                form_data.add_field(key, str(value))
                        for key, file_data in files.items():
                            form_data.add_field(key, file_data)
                        request_kwargs["data"] = form_data
                    elif data:
                        if headers.get("Content-Type") == "application/json":
                            request_kwargs["json"] = data
                        elif headers.get("Content-Type") == "application/x-www-form-urlencoded":
                            request_kwargs["data"] = urlencode(data)
                        else:
                            request_kwargs["json"] = data
                
                async with self.session.request(method.value, url, **request_kwargs) as response:
                    return response
                
            except Exception as e:
                last_exception = e
                if attempt < config.retry_attempts - 1:
                    await asyncio.sleep(config.retry_delay * (attempt + 1))
                    continue
                else:
                    raise last_exception
    
    async def _parse_response(self, response) -> Any:
        """Parse response data"""
        content_type = response.headers.get("Content-Type", "")
        
        try:
            if "application/json" in content_type:
                return await response.json()
            elif "application/xml" in content_type or "text/xml" in content_type:
                text = await response.text()
                return self._parse_xml(text)
            elif "text/csv" in content_type:
                text = await response.text()
                return self._parse_csv(text)
            else:
                return await response.text()
        except Exception as e:
            logger.warning(f"Failed to parse response: {e}")
            return await response.text()
    
    def _parse_xml(self, xml_text: str) -> Dict[str, Any]:
        """Parse XML response to dictionary"""
        try:
            root = ET.fromstring(xml_text)
            return self._xml_to_dict(root)
        except Exception as e:
            logger.warning(f"Failed to parse XML: {e}")
            return {"raw_xml": xml_text}
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result["@attributes"] = element.attrib
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result["#text"] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _parse_csv(self, csv_text: str) -> List[Dict[str, Any]]:
        """Parse CSV response to list of dictionaries"""
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            return list(reader)
        except Exception as e:
            logger.warning(f"Failed to parse CSV: {e}")
            return [{"raw_csv": csv_text}]
    
    def _validate_webhook_signature(self, secret: str, headers: Dict[str, str], payload: Any) -> bool:
        """Validate webhook signature"""
        try:
            # Common signature headers
            signature_headers = [
                "X-Hub-Signature-256", "X-Signature", "X-Webhook-Signature",
                "Stripe-Signature", "X-GitHub-Signature"
            ]
            
            signature = None
            for header in signature_headers:
                if header in headers:
                    signature = headers[header]
                    break
            
            if not signature:
                return False
            
            # Prepare payload
            if isinstance(payload, dict):
                payload_str = json.dumps(payload, separators=(',', ':'))
            else:
                payload_str = str(payload)
            
            # Calculate expected signature
            expected = hmac.new(
                secret.encode(), payload_str.encode(), hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if signature.startswith("sha256="):
                signature = signature[7:]
            
            return hmac.compare_digest(signature, expected)
            
        except Exception as e:
            logger.warning(f"Failed to validate webhook signature: {e}")
            return False
    
    async def _log_integration_request(self, integration_name: str, integration_type: IntegrationType,
                                     request: IntegrationRequest, response: IntegrationResponse,
                                     user_id: Optional[int], correlation_id: Optional[str]):
        """Log integration request to database"""
        try:
            db = next(get_db())
            
            log_entry = IntegrationLogModel(
                integration_name=integration_name,
                integration_type=integration_type.value,
                method=request.method.value,
                endpoint=request.endpoint,
                request_data=request.data,
                request_headers=request.headers,
                status_code=response.status_code,
                response_data=response.data if response.status_code != 0 else None,
                response_headers=response.headers,
                response_time_ms=response.response_time,
                success=response.success,
                error_message=response.error,
                user_id=user_id,
                correlation_id=correlation_id
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log integration request: {e}")
        finally:
            db.close()
    
    async def _log_webhook(self, webhook_name: str, method: str, headers: Dict[str, str],
                         payload: Any, source_ip: Optional[str], processed: bool,
                         processing_time: float, response_status: int,
                         error_message: Optional[str], signature_valid: Optional[bool]):
        """Log webhook to database"""
        try:
            db = next(get_db())
            
            log_entry = WebhookLogModel(
                webhook_name=webhook_name,
                source_ip=source_ip,
                method=method,
                headers=headers,
                payload=payload if isinstance(payload, dict) else None,
                raw_payload=str(payload) if not isinstance(payload, dict) else None,
                processed=processed,
                processing_time_ms=processing_time,
                response_status=response_status,
                error_message=error_message,
                signature_valid=signature_valid,
                processed_at=datetime.utcnow() if processed else None
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log webhook: {e}")
        finally:
            db.close()

# Global integration service instance
integration_service = IntegrationService()

# Convenience functions for common integrations
async def send_stripe_payment(amount: int, currency: str = "usd", 
                            customer_id: Optional[str] = None) -> Dict[str, Any]:
    """Send payment request to Stripe"""
    request = IntegrationRequest(
        method=RequestMethod.POST,
        endpoint="charges",
        data={
            "amount": amount,
            "currency": currency,
            "customer": customer_id
        }
    )
    
    response = await integration_service.make_request("stripe", request)
    return response.data

async def send_twilio_sms(to: str, message: str, from_number: Optional[str] = None) -> Dict[str, Any]:
    """Send SMS via Twilio"""
    account_sid = get_config_service().get_config("twilio_account_sid")
    
    request = IntegrationRequest(
        method=RequestMethod.POST,
        endpoint=f"Accounts/{account_sid}/Messages.json",
        data={
            "To": to,
            "Body": message,
            "From": from_number or get_config_service().get_config("twilio_phone_number")
        }
    )
    
    response = await integration_service.make_request("twilio", request)
    return response.data

async def post_to_facebook(message: str, page_id: Optional[str] = None) -> Dict[str, Any]:
    """Post message to Facebook page"""
    page_id = page_id or get_config_service().get_config("facebook_page_id")
    
    request = IntegrationRequest(
        method=RequestMethod.POST,
        endpoint=f"{page_id}/feed",
        data={"message": message}
    )
    
    response = await integration_service.make_request("facebook", request)
    return response.data