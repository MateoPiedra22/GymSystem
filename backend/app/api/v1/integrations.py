from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from ...core.auth import get_current_user, require_admin_access
from ...services.integration_service import (
    integration_service, IntegrationType, IntegrationStatus, RequestMethod, AuthType,
    IntegrationRequest, send_stripe_payment, send_twilio_sms, post_to_facebook
)
from ...models.user import User
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class IntegrationRequestModel(BaseModel):
    """Integration request model"""
    method: RequestMethod
    endpoint: str
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    files: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    correlation_id: Optional[str] = None

class IntegrationResponse(BaseModel):
    """Integration response model"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time: float
    success: bool
    error: Optional[str] = None
    correlation_id: Optional[str] = None

class WebhookRequest(BaseModel):
    """Webhook request model"""
    webhook_name: str
    payload: Any
    headers: Optional[Dict[str, str]] = None

class WebhookResponse(BaseModel):
    """Webhook response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None

class TestIntegrationResponse(BaseModel):
    """Test integration response model"""
    integration_name: str
    success: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    message: Optional[str] = None

class IntegrationLogResponse(BaseModel):
    """Integration log response model"""
    id: int
    integration_name: str
    integration_type: str
    method: str
    endpoint: str
    status_code: Optional[int]
    success: bool
    response_time_ms: Optional[float]
    error_message: Optional[str]
    retry_count: int
    correlation_id: Optional[str]
    created_at: str

class WebhookLogResponse(BaseModel):
    """Webhook log response model"""
    id: int
    webhook_name: str
    source_ip: Optional[str]
    method: str
    processed: bool
    processing_time_ms: Optional[float]
    response_status: Optional[int]
    error_message: Optional[str]
    signature_valid: Optional[bool]
    received_at: str
    processed_at: Optional[str]

class IntegrationStatisticsResponse(BaseModel):
    """Integration statistics response model"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_response_time_ms: float
    recent_requests_24h: int
    integration_usage: Dict[str, int]
    total_webhooks: int
    processed_webhooks: int
    active_integrations: int

class IntegrationConfigResponse(BaseModel):
    """Integration configuration response model"""
    name: str
    integration_type: str
    base_url: str
    auth_type: str
    enabled: bool
    timeout: int
    retry_attempts: int
    retry_delay: int
    rate_limit: Optional[int]
    has_webhook_secret: bool

class StripePaymentRequest(BaseModel):
    """Stripe payment request model"""
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    description: Optional[str] = Field(None, description="Payment description")

class TwilioSMSRequest(BaseModel):
    """Twilio SMS request model"""
    to: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="SMS message content")
    from_number: Optional[str] = Field(None, description="Sender phone number")

class FacebookPostRequest(BaseModel):
    """Facebook post request model"""
    message: str = Field(..., description="Post message content")
    page_id: Optional[str] = Field(None, description="Facebook page ID")
    link: Optional[str] = Field(None, description="Link to include in post")

# API Routes
@router.post("/request/{integration_name}", response_model=IntegrationResponse)
async def make_integration_request(
    integration_name: str,
    request_data: IntegrationRequestModel,
    current_user: User = Depends(get_current_user)
):
    """Make a request to an external integration"""
    try:
        # Generate correlation ID if not provided
        correlation_id = request_data.correlation_id or str(uuid.uuid4())
        
        # Create integration request
        integration_request = IntegrationRequest(
            method=request_data.method,
            endpoint=request_data.endpoint,
            data=request_data.data,
            params=request_data.params,
            headers=request_data.headers,
            files=request_data.files,
            timeout=request_data.timeout
        )
        
        # Make request
        response = await integration_service.make_request(
            integration_name, integration_request, current_user.id, correlation_id
        )
        
        return IntegrationResponse(
            status_code=response.status_code,
            data=response.data,
            headers=response.headers,
            response_time=response.response_time,
            success=response.success,
            error=response.error,
            correlation_id=correlation_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Integration request failed: {e}")
        raise HTTPException(status_code=500, detail="Integration request failed")

@router.post("/webhook/{webhook_name}", response_model=WebhookResponse)
async def process_webhook(
    webhook_name: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Process incoming webhook (public endpoint)"""
    try:
        # Get request details
        method = request.method
        headers = dict(request.headers)
        
        # Get client IP
        source_ip = request.client.host if request.client else None
        
        # Get payload
        content_type = headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
        elif "application/x-www-form-urlencoded" in content_type:
            form_data = await request.form()
            payload = dict(form_data)
        else:
            payload = await request.body()
            payload = payload.decode() if isinstance(payload, bytes) else payload
        
        start_time = datetime.utcnow()
        
        # Process webhook
        result = await integration_service.process_webhook(
            webhook_name, method, headers, payload, source_ip
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return WebhookResponse(
            success=True,
            message="Webhook processed successfully",
            data=result,
            processing_time_ms=processing_time
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.get("/test/{integration_name}", response_model=TestIntegrationResponse)
async def test_integration(
    integration_name: str,
    current_user: User = Depends(require_admin_access)
):
    """Test an integration connection"""
    try:
        result = await integration_service.test_integration(integration_name)
        
        return TestIntegrationResponse(
            integration_name=integration_name,
            success=result["success"],
            status_code=result.get("status_code"),
            response_time=result.get("response_time"),
            error=result.get("error"),
            message=result.get("message")
        )
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise HTTPException(status_code=500, detail="Integration test failed")

@router.get("/logs", response_model=List[IntegrationLogResponse])
async def get_integration_logs(
    integration_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    current_user: User = Depends(require_admin_access)
):
    """Get integration logs"""
    try:
        logs = await integration_service.get_integration_logs(
            integration_name, start_date, end_date, limit
        )
        
        return [
            IntegrationLogResponse(**log)
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"Failed to get integration logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration logs")

@router.get("/webhook-logs", response_model=List[WebhookLogResponse])
async def get_webhook_logs(
    webhook_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    current_user: User = Depends(require_admin_access)
):
    """Get webhook logs"""
    try:
        logs = await integration_service.get_webhook_logs(
            webhook_name, start_date, end_date, limit
        )
        
        return [
            WebhookLogResponse(**log)
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"Failed to get webhook logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get webhook logs")

@router.get("/statistics", response_model=IntegrationStatisticsResponse)
async def get_integration_statistics(
    current_user: User = Depends(require_admin_access)
):
    """Get integration usage statistics"""
    try:
        stats = await integration_service.get_integration_statistics()
        return IntegrationStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get integration statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration statistics")

@router.get("/config", response_model=List[IntegrationConfigResponse])
async def get_integration_configurations(
    current_user: User = Depends(require_admin_access)
):
    """Get integration configurations"""
    try:
        configs = []
        for name, config in integration_service.integrations.items():
            configs.append(IntegrationConfigResponse(
                name=config.name,
                integration_type=config.integration_type.value,
                base_url=config.base_url,
                auth_type=config.auth_type.value,
                enabled=config.enabled,
                timeout=config.timeout,
                retry_attempts=config.retry_attempts,
                retry_delay=config.retry_delay,
                rate_limit=config.rate_limit,
                has_webhook_secret=bool(config.webhook_secret)
            ))
        
        return configs
        
    except Exception as e:
        logger.error(f"Failed to get integration configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration configurations")

@router.get("/available-types")
async def get_available_integration_types():
    """Get available integration types and enums"""
    return {
        "integration_types": [t.value for t in IntegrationType],
        "request_methods": [m.value for m in RequestMethod],
        "auth_types": [a.value for a in AuthType],
        "integration_status": [s.value for s in IntegrationStatus]
    }

# Specific integration endpoints
@router.post("/stripe/payment")
async def create_stripe_payment(
    payment_request: StripePaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a Stripe payment"""
    try:
        result = await send_stripe_payment(
            amount=payment_request.amount,
            currency=payment_request.currency,
            customer_id=payment_request.customer_id
        )
        
        return {
            "success": True,
            "payment_id": result.get("id"),
            "status": result.get("status"),
            "amount": result.get("amount"),
            "currency": result.get("currency")
        }
        
    except Exception as e:
        logger.error(f"Stripe payment failed: {e}")
        raise HTTPException(status_code=500, detail="Payment processing failed")

@router.post("/twilio/sms")
async def send_sms(
    sms_request: TwilioSMSRequest,
    current_user: User = Depends(get_current_user)
):
    """Send SMS via Twilio"""
    try:
        result = await send_twilio_sms(
            to=sms_request.to,
            message=sms_request.message,
            from_number=sms_request.from_number
        )
        
        return {
            "success": True,
            "message_sid": result.get("sid"),
            "status": result.get("status"),
            "to": result.get("to"),
            "from": result.get("from")
        }
        
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        raise HTTPException(status_code=500, detail="SMS sending failed")

@router.post("/facebook/post")
async def create_facebook_post(
    post_request: FacebookPostRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a Facebook post"""
    try:
        result = await post_to_facebook(
            message=post_request.message,
            page_id=post_request.page_id
        )
        
        return {
            "success": True,
            "post_id": result.get("id"),
            "message": "Post created successfully"
        }
        
    except Exception as e:
        logger.error(f"Facebook post failed: {e}")
        raise HTTPException(status_code=500, detail="Facebook post failed")

@router.post("/test-webhook/{webhook_name}")
async def test_webhook(
    webhook_name: str,
    test_payload: Dict[str, Any],
    current_user: User = Depends(require_admin_access)
):
    """Test webhook processing with sample data"""
    try:
        result = await integration_service.process_webhook(
            webhook_name, "POST", {"Content-Type": "application/json"}, test_payload
        )
        
        return {
            "success": True,
            "message": "Webhook test completed",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Webhook test failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook test failed")

@router.get("/health")
async def integration_health_check():
    """Check integration service health"""
    try:
        active_integrations = len([i for i in integration_service.integrations.values() if i.enabled])
        
        return {
            "status": "healthy",
            "active_integrations": active_integrations,
            "total_integrations": len(integration_service.integrations),
            "webhook_handlers": len(integration_service.webhook_handlers),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Integration health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")