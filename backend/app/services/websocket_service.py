from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import json
import asyncio
import uuid
from fastapi import WebSocket, WebSocketDisconnect
import logging
from collections import defaultdict
import jwt
from ..core.config import settings
from ..models.user import User
from ..models.employee import Employee
from sqlalchemy.orm import Session
from ..core.database import get_db
import redis
from typing import Union
import weakref

logger = logging.getLogger(__name__)

class MessageType(Enum):
    # System messages
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    
    # User notifications
    NOTIFICATION = "notification"
    PAYMENT_REMINDER = "payment_reminder"
    CLASS_REMINDER = "class_reminder"
    BIRTHDAY_GREETING = "birthday_greeting"
    
    # Real-time updates
    CLASS_UPDATE = "class_update"
    MEMBERSHIP_UPDATE = "membership_update"
    ROUTINE_UPDATE = "routine_update"
    EQUIPMENT_STATUS = "equipment_status"
    
    # Chat and communication
    CHAT_MESSAGE = "chat_message"
    TRAINER_MESSAGE = "trainer_message"
    ADMIN_BROADCAST = "admin_broadcast"
    
    # Live features
    LIVE_CLASS_JOIN = "live_class_join"
    LIVE_CLASS_LEAVE = "live_class_leave"
    LIVE_CLASS_UPDATE = "live_class_update"
    
    # Analytics and monitoring
    REAL_TIME_STATS = "real_time_stats"
    SYSTEM_ALERT = "system_alert"

class UserRole(Enum):
    MEMBER = "member"
    TRAINER = "trainer"
    ADMIN = "admin"
    GUEST = "guest"

@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    sender_id: Optional[str] = None
    recipient_id: Optional[str] = None
    room_id: Optional[str] = None
    message_id: str = None
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'room_id': self.room_id,
            'message_id': self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        return cls(
            type=MessageType(data['type']),
            data=data['data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            sender_id=data.get('sender_id'),
            recipient_id=data.get('recipient_id'),
            room_id=data.get('room_id'),
            message_id=data.get('message_id')
        )

@dataclass
class ConnectedClient:
    """Connected client information"""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[str]
    user_role: UserRole
    connected_at: datetime
    last_heartbeat: datetime
    rooms: Set[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not self.rooms:
            self.rooms = set()
        if not self.metadata:
            self.metadata = {}

class WebSocketManager:
    """WebSocket connection and message management"""
    
    def __init__(self):
        # Active connections
        self.connections: Dict[str, ConnectedClient] = {}
        
        # Room management
        self.rooms: Dict[str, Set[str]] = defaultdict(set)  # room_id -> connection_ids
        
        # User to connection mapping
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        
        # Redis for scaling (optional)
        self.redis_client = None
        try:
            if hasattr(settings, 'REDIS_URL'):
                self.redis_client = redis.from_url(settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Start background services
        self._start_background_services()
    
    def _start_background_services(self):
        """Start background services"""
        # Heartbeat checker
        task = asyncio.create_task(self._heartbeat_checker())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Connection cleaner
        task = asyncio.create_task(self._connection_cleaner())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> str:
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        user_role = UserRole.GUEST
        
        # Authenticate user if token provided
        if token:
            try:
                user_data = await self._authenticate_token(token)
                if user_data:
                    user_id = user_data['user_id']
                    user_role = UserRole(user_data.get('role', 'member'))
            except Exception as e:
                logger.warning(f"Authentication failed: {e}")
        
        # Create client connection
        client = ConnectedClient(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            user_role=user_role,
            connected_at=datetime.now(),
            last_heartbeat=datetime.now(),
            rooms=set(),
            metadata={}
        )
        
        # Store connection
        self.connections[connection_id] = client
        
        # Map user to connection
        if user_id:
            self.user_connections[user_id].add(connection_id)
        
        # Send connection confirmation
        await self.send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.CONNECT,
                data={
                    'connection_id': connection_id,
                    'user_id': user_id,
                    'role': user_role.value,
                    'server_time': datetime.now().isoformat()
                },
                timestamp=datetime.now()
            )
        )
        
        # Join default rooms based on role
        await self._join_default_rooms(connection_id, user_role)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id}, role: {user_role.value})")
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect WebSocket connection"""
        if connection_id not in self.connections:
            return
        
        client = self.connections[connection_id]
        
        # Leave all rooms
        for room_id in list(client.rooms):
            await self.leave_room(connection_id, room_id)
        
        # Remove from user mapping
        if client.user_id:
            self.user_connections[client.user_id].discard(connection_id)
            if not self.user_connections[client.user_id]:
                del self.user_connections[client.user_id]
        
        # Remove connection
        del self.connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def _authenticate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Authenticate JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            user_id = payload.get('sub')
            if not user_id:
                return None
            
            # Get user from database
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return None
            
            # Determine role
            role = 'member'
            if user.can_access_admin:
                role = 'admin'
            else:
                # Check if user is an employee
                employee = db.query(Employee).filter(Employee.user_id == user_id).first()
                if employee:
                    role = 'trainer'
            
            return {
                'user_id': str(user_id),
                'role': role,
                'email': user.email,
                'name': user.full_name
            }
            
        except Exception as e:
            logger.error(f"Token authentication error: {e}")
            return None
    
    async def _join_default_rooms(self, connection_id: str, user_role: UserRole):
        """Join default rooms based on user role"""
        # All users join general notifications room
        await self.join_room(connection_id, "notifications")
        
        # Role-specific rooms
        if user_role == UserRole.ADMIN:
            await self.join_room(connection_id, "admin")
            await self.join_room(connection_id, "system_alerts")
        elif user_role == UserRole.TRAINER:
            await self.join_room(connection_id, "trainers")
        elif user_role == UserRole.MEMBER:
            await self.join_room(connection_id, "members")
    
    async def join_room(self, connection_id: str, room_id: str):
        """Join a room"""
        if connection_id not in self.connections:
            return
        
        client = self.connections[connection_id]
        client.rooms.add(room_id)
        self.rooms[room_id].add(connection_id)
        
        # Notify client
        await self.send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.NOTIFICATION,
                data={
                    'action': 'joined_room',
                    'room_id': room_id
                },
                timestamp=datetime.now()
            )
        )
        
        logger.debug(f"Connection {connection_id} joined room {room_id}")
    
    async def leave_room(self, connection_id: str, room_id: str):
        """Leave a room"""
        if connection_id not in self.connections:
            return
        
        client = self.connections[connection_id]
        client.rooms.discard(room_id)
        self.rooms[room_id].discard(connection_id)
        
        # Clean up empty rooms
        if not self.rooms[room_id]:
            del self.rooms[room_id]
        
        logger.debug(f"Connection {connection_id} left room {room_id}")
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return False
        
        client = self.connections[connection_id]
        
        try:
            await client.websocket.send_text(json.dumps(message.to_dict()))
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            # Connection is probably dead, remove it
            await self.disconnect(connection_id)
            return False
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send message to all connections of a user"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        connection_ids = list(self.user_connections[user_id])  # Copy to avoid modification during iteration
        
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_room(self, room_id: str, message: WebSocketMessage, exclude_connection: Optional[str] = None):
        """Send message to all connections in a room"""
        if room_id not in self.rooms:
            return 0
        
        sent_count = 0
        connection_ids = list(self.rooms[room_id])  # Copy to avoid modification during iteration
        
        for connection_id in connection_ids:
            if connection_id != exclude_connection:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: WebSocketMessage, exclude_connection: Optional[str] = None):
        """Broadcast message to all connections"""
        sent_count = 0
        connection_ids = list(self.connections.keys())  # Copy to avoid modification during iteration
        
        for connection_id in connection_ids:
            if connection_id != exclude_connection:
                if await self.send_to_connection(connection_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def handle_message(self, connection_id: str, raw_message: str):
        """Handle incoming message from client"""
        try:
            message_data = json.loads(raw_message)
            message = WebSocketMessage.from_dict(message_data)
            
            # Update heartbeat
            if connection_id in self.connections:
                self.connections[connection_id].last_heartbeat = datetime.now()
            
            # Handle specific message types
            if message.type == MessageType.HEARTBEAT:
                await self._handle_heartbeat(connection_id, message)
            elif message.type == MessageType.CHAT_MESSAGE:
                await self._handle_chat_message(connection_id, message)
            elif message.type == MessageType.LIVE_CLASS_JOIN:
                await self._handle_live_class_join(connection_id, message)
            elif message.type == MessageType.LIVE_CLASS_LEAVE:
                await self._handle_live_class_leave(connection_id, message)
            else:
                # Call registered handlers
                for handler in self.message_handlers[message.type]:
                    try:
                        await handler(connection_id, message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
            
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await self.send_to_connection(
                connection_id,
                WebSocketMessage(
                    type=MessageType.ERROR,
                    data={'error': 'Invalid message format'},
                    timestamp=datetime.now()
                )
            )
    
    async def _handle_heartbeat(self, connection_id: str, message: WebSocketMessage):
        """Handle heartbeat message"""
        await self.send_to_connection(
            connection_id,
            WebSocketMessage(
                type=MessageType.HEARTBEAT,
                data={'status': 'alive', 'server_time': datetime.now().isoformat()},
                timestamp=datetime.now()
            )
        )
    
    async def _handle_chat_message(self, connection_id: str, message: WebSocketMessage):
        """Handle chat message"""
        if connection_id not in self.connections:
            return
        
        client = self.connections[connection_id]
        
        # Add sender information
        message.sender_id = client.user_id
        message.data['sender_name'] = client.metadata.get('name', 'Unknown')
        message.data['sender_role'] = client.user_role.value
        
        # Send to room or specific user
        if message.room_id:
            await self.send_to_room(message.room_id, message, exclude_connection=connection_id)
        elif message.recipient_id:
            await self.send_to_user(message.recipient_id, message)
    
    async def _handle_live_class_join(self, connection_id: str, message: WebSocketMessage):
        """Handle live class join"""
        class_id = message.data.get('class_id')
        if not class_id:
            return
        
        room_id = f"live_class_{class_id}"
        await self.join_room(connection_id, room_id)
        
        # Notify others in the class
        client = self.connections.get(connection_id)
        if client:
            notification = WebSocketMessage(
                type=MessageType.LIVE_CLASS_UPDATE,
                data={
                    'action': 'user_joined',
                    'class_id': class_id,
                    'user_id': client.user_id,
                    'user_name': client.metadata.get('name', 'Unknown')
                },
                timestamp=datetime.now()
            )
            await self.send_to_room(room_id, notification, exclude_connection=connection_id)
    
    async def _handle_live_class_leave(self, connection_id: str, message: WebSocketMessage):
        """Handle live class leave"""
        class_id = message.data.get('class_id')
        if not class_id:
            return
        
        room_id = f"live_class_{class_id}"
        
        # Notify others before leaving
        client = self.connections.get(connection_id)
        if client:
            notification = WebSocketMessage(
                type=MessageType.LIVE_CLASS_UPDATE,
                data={
                    'action': 'user_left',
                    'class_id': class_id,
                    'user_id': client.user_id,
                    'user_name': client.metadata.get('name', 'Unknown')
                },
                timestamp=datetime.now()
            )
            await self.send_to_room(room_id, notification, exclude_connection=connection_id)
        
        await self.leave_room(connection_id, room_id)
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type].append(handler)
    
    async def _heartbeat_checker(self):
        """Background task to check for dead connections"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                current_time = datetime.now()
                dead_connections = []
                
                for connection_id, client in self.connections.items():
                    # Consider connection dead if no heartbeat for 2 minutes
                    if (current_time - client.last_heartbeat).total_seconds() > 120:
                        dead_connections.append(connection_id)
                
                # Remove dead connections
                for connection_id in dead_connections:
                    logger.info(f"Removing dead connection: {connection_id}")
                    await self.disconnect(connection_id)
                    
            except Exception as e:
                logger.error(f"Error in heartbeat checker: {e}")
    
    async def _connection_cleaner(self):
        """Background task to clean up resources"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean every 5 minutes
                
                # Clean up empty rooms
                empty_rooms = [room_id for room_id, connections in self.rooms.items() if not connections]
                for room_id in empty_rooms:
                    del self.rooms[room_id]
                
                # Clean up empty user mappings
                empty_users = [user_id for user_id, connections in self.user_connections.items() if not connections]
                for user_id in empty_users:
                    del self.user_connections[user_id]
                
                logger.debug(f"Cleaned up {len(empty_rooms)} empty rooms and {len(empty_users)} empty user mappings")
                
            except Exception as e:
                logger.error(f"Error in connection cleaner: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        stats = {
            'total_connections': len(self.connections),
            'authenticated_connections': len([c for c in self.connections.values() if c.user_id]),
            'guest_connections': len([c for c in self.connections.values() if not c.user_id]),
            'total_rooms': len(self.rooms),
            'connections_by_role': {},
            'active_rooms': list(self.rooms.keys()),
            'uptime_seconds': 0  # Would track actual uptime
        }
        
        # Count by role
        for client in self.connections.values():
            role = client.user_role.value
            stats['connections_by_role'][role] = stats['connections_by_role'].get(role, 0) + 1
        
        return stats
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ):
        """Send notification to user"""
        notification_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                'title': title,
                'message': message,
                'type': notification_type,
                'data': data or {}
            },
            timestamp=datetime.now(),
            recipient_id=user_id
        )
        
        return await self.send_to_user(user_id, notification_message)
    
    async def send_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info",
        target_roles: Optional[List[UserRole]] = None
    ):
        """Send system alert to specific roles"""
        alert_message = WebSocketMessage(
            type=MessageType.SYSTEM_ALERT,
            data={
                'alert_type': alert_type,
                'message': message,
                'severity': severity
            },
            timestamp=datetime.now()
        )
        
        if target_roles:
            sent_count = 0
            for connection_id, client in self.connections.items():
                if client.user_role in target_roles:
                    if await self.send_to_connection(connection_id, alert_message):
                        sent_count += 1
            return sent_count
        else:
            return await self.broadcast(alert_message)
    
    async def update_real_time_stats(self, stats: Dict[str, Any]):
        """Send real-time statistics to admin users"""
        stats_message = WebSocketMessage(
            type=MessageType.REAL_TIME_STATS,
            data=stats,
            timestamp=datetime.now()
        )
        
        return await self.send_to_room("admin", stats_message)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

# WebSocket service class for easier integration
class WebSocketService:
    """High-level WebSocket service"""
    
    def __init__(self):
        self.manager = websocket_manager
    
    async def notify_payment_reminder(self, user_id: str, amount: float, due_date: str):
        """Send payment reminder notification"""
        return await self.manager.send_notification(
            user_id=user_id,
            title="Payment Reminder",
            message=f"Your payment of ${amount:.2f} is due on {due_date}",
            notification_type="warning",
            data={
                'amount': amount,
                'due_date': due_date,
                'action_url': '/payments'
            }
        )
    
    async def notify_class_reminder(self, user_id: str, class_name: str, start_time: str):
        """Send class reminder notification"""
        return await self.manager.send_notification(
            user_id=user_id,
            title="Class Reminder",
            message=f"Your {class_name} class starts at {start_time}",
            notification_type="info",
            data={
                'class_name': class_name,
                'start_time': start_time,
                'action_url': '/classes'
            }
        )
    
    async def notify_class_cancelled(self, user_ids: List[str], class_name: str, reason: str):
        """Notify users about class cancellation"""
        sent_count = 0
        for user_id in user_ids:
            count = await self.manager.send_notification(
                user_id=user_id,
                title="Class Cancelled",
                message=f"Your {class_name} class has been cancelled. Reason: {reason}",
                notification_type="error",
                data={
                    'class_name': class_name,
                    'reason': reason,
                    'action_url': '/classes'
                }
            )
            sent_count += count
        return sent_count
    
    async def broadcast_maintenance_alert(self, message: str, start_time: str, duration: str):
        """Broadcast maintenance alert"""
        return await self.manager.send_system_alert(
            alert_type="maintenance",
            message=f"Scheduled maintenance: {message}. Start: {start_time}, Duration: {duration}",
            severity="warning",
            target_roles=[UserRole.ADMIN, UserRole.TRAINER]
        )
    
    async def update_equipment_status(self, equipment_id: str, status: str, location: str):
        """Update equipment status in real-time"""
        message = WebSocketMessage(
            type=MessageType.EQUIPMENT_STATUS,
            data={
                'equipment_id': equipment_id,
                'status': status,
                'location': location,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )
        
        return await self.manager.send_to_room("trainers", message)
    
    async def send_birthday_greeting(self, user_id: str, name: str):
        """Send birthday greeting"""
        return await self.manager.send_notification(
            user_id=user_id,
            title="Happy Birthday! 🎉",
            message=f"Happy Birthday, {name}! Enjoy your special day and your complimentary workout session!",
            notification_type="success",
            data={
                'special_offer': 'free_session',
                'action_url': '/profile'
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket service statistics"""
        return self.manager.get_connection_stats()

# Global service instance
websocket_service = WebSocketService()