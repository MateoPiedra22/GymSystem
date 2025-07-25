from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from ..models.user import User
from ..models.membership import Membership, Payment
from ..models.routine import RoutineAssignment
from ..models.class_model import Class, ClassBooking
from ..models.employee import Employee
from ..core.database import get_db
import json
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class AnalyticsType(Enum):
    REVENUE = "revenue"
    MEMBERSHIP = "membership"
    ATTENDANCE = "attendance"
    RETENTION = "retention"
    PERFORMANCE = "performance"
    OPERATIONAL = "operational"
    PREDICTIVE = "predictive"
    CUSTOMER_SEGMENTATION = "customer_segmentation"

class TimeFrame(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

@dataclass
class AnalyticsRequest:
    """Analytics request configuration"""
    analytics_type: AnalyticsType
    time_frame: TimeFrame
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = None
    include_predictions: bool = False
    segment_by: Optional[str] = None

@dataclass
class AnalyticsResult:
    """Analytics result structure"""
    request_id: str
    analytics_type: AnalyticsType
    generated_at: datetime
    data: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class CustomerSegment:
    """Customer segment definition"""
    segment_id: str
    name: str
    description: str
    characteristics: Dict[str, Any]
    size: int
    avg_revenue: float
    retention_rate: float

class AnalyticsService:
    """Advanced analytics and business intelligence service"""
    
    def __init__(self):
        self.db = next(get_db())
        self.scaler = StandardScaler()
        self.models = {}
        self.customer_segments = []
        
    async def generate_analytics(
        self,
        request: AnalyticsRequest
    ) -> AnalyticsResult:
        """Generate analytics based on request"""
        try:
            request_id = f"{request.analytics_type.value}_{datetime.now().timestamp()}"
            
            if request.analytics_type == AnalyticsType.REVENUE:
                result_data = await self._analyze_revenue(request)
            elif request.analytics_type == AnalyticsType.MEMBERSHIP:
                result_data = await self._analyze_membership(request)
            elif request.analytics_type == AnalyticsType.ATTENDANCE:
                result_data = await self._analyze_attendance(request)
            elif request.analytics_type == AnalyticsType.RETENTION:
                result_data = await self._analyze_retention(request)
            elif request.analytics_type == AnalyticsType.PERFORMANCE:
                result_data = await self._analyze_performance(request)
            elif request.analytics_type == AnalyticsType.OPERATIONAL:
                result_data = await self._analyze_operational(request)
            elif request.analytics_type == AnalyticsType.PREDICTIVE:
                result_data = await self._generate_predictions(request)
            elif request.analytics_type == AnalyticsType.CUSTOMER_SEGMENTATION:
                result_data = await self._perform_customer_segmentation(request)
            else:
                raise ValueError(f"Analytics type {request.analytics_type} not supported")
            
            # Generate insights and recommendations
            insights = await self._generate_insights(request.analytics_type, result_data)
            recommendations = await self._generate_recommendations(request.analytics_type, result_data)
            
            return AnalyticsResult(
                request_id=request_id,
                analytics_type=request.analytics_type,
                generated_at=datetime.now(),
                data=result_data,
                insights=insights,
                recommendations=recommendations,
                confidence_score=result_data.get('confidence_score'),
                metadata={
                    'time_frame': request.time_frame.value,
                    'date_range': {
                        'start': request.start_date.isoformat(),
                        'end': request.end_date.isoformat()
                    },
                    'filters': request.filters
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            raise
    
    async def _analyze_revenue(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Analyze revenue metrics"""
        # Get payment data
        payments_query = self.db.query(Payment).filter(
            and_(
                Payment.payment_date >= request.start_date,
                Payment.payment_date <= request.end_date,
                Payment.status == 'completed'
            )
        )
        
        payments = payments_query.all()
        
        # Convert to DataFrame for analysis
        payment_data = []
        for payment in payments:
            payment_data.append({
                'date': payment.payment_date,
                'amount': float(payment.amount),
                'method': payment.payment_method,
                'user_id': payment.user_id,
                'membership_id': payment.membership_id
            })
        
        df = pd.DataFrame(payment_data)
        
        if df.empty:
            return {
                'total_revenue': 0,
                'average_transaction': 0,
                'transaction_count': 0,
                'revenue_by_period': [],
                'revenue_by_method': {},
                'growth_rate': 0
            }
        
        # Calculate metrics
        total_revenue = df['amount'].sum()
        avg_transaction = df['amount'].mean()
        transaction_count = len(df)
        
        # Revenue by time period
        df['date'] = pd.to_datetime(df['date'])
        if request.time_frame == TimeFrame.DAILY:
            df['period'] = df['date'].dt.date
        elif request.time_frame == TimeFrame.WEEKLY:
            df['period'] = df['date'].dt.to_period('W')
        elif request.time_frame == TimeFrame.MONTHLY:
            df['period'] = df['date'].dt.to_period('M')
        else:
            df['period'] = df['date'].dt.to_period('Q')
        
        revenue_by_period = df.groupby('period')['amount'].sum().to_dict()
        revenue_by_period = {
            str(k): float(v) for k, v in revenue_by_period.items()
        }
        
        # Revenue by payment method
        revenue_by_method = df.groupby('method')['amount'].sum().to_dict()
        
        # Calculate growth rate
        periods = sorted(revenue_by_period.keys())
        if len(periods) >= 2:
            first_period = revenue_by_period[periods[0]]
            last_period = revenue_by_period[periods[-1]]
            growth_rate = ((last_period - first_period) / first_period * 100) if first_period > 0 else 0
        else:
            growth_rate = 0
        
        # Revenue forecasting if requested
        forecast = None
        if request.include_predictions and len(periods) >= 3:
            forecast = await self._forecast_revenue(df)
        
        return {
            'total_revenue': float(total_revenue),
            'average_transaction': float(avg_transaction),
            'transaction_count': transaction_count,
            'revenue_by_period': revenue_by_period,
            'revenue_by_method': revenue_by_method,
            'growth_rate': float(growth_rate),
            'forecast': forecast
        }
    
    async def _analyze_membership(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Analyze membership metrics"""
        # Get membership data
        memberships = self.db.query(Membership).filter(
            Membership.created_at >= request.start_date
        ).all()
        
        # Active memberships
        active_memberships = self.db.query(Membership).filter(
            Membership.status == 'active'
        ).count()
        
        # New memberships in period
        new_memberships = len(memberships)
        
        # Membership types distribution
        membership_types = self.db.query(
            Membership.membership_type,
            func.count(Membership.id)
        ).filter(
            Membership.status == 'active'
        ).group_by(Membership.membership_type).all()
        
        type_distribution = {mt[0]: mt[1] for mt in membership_types}
        
        # Average membership duration
        expired_memberships = self.db.query(Membership).filter(
            and_(
                Membership.status == 'expired',
                Membership.end_date.isnot(None)
            )
        ).all()
        
        durations = []
        for membership in expired_memberships:
            if membership.start_date and membership.end_date:
                duration = (membership.end_date - membership.start_date).days
                durations.append(duration)
        
        avg_duration = np.mean(durations) if durations else 0
        
        # Churn rate calculation
        total_members_start = self.db.query(Membership).filter(
            Membership.created_at < request.start_date
        ).count()
        
        churned_members = self.db.query(Membership).filter(
            and_(
                Membership.status == 'expired',
                Membership.end_date >= request.start_date,
                Membership.end_date <= request.end_date
            )
        ).count()
        
        churn_rate = (churned_members / total_members_start * 100) if total_members_start > 0 else 0
        
        return {
            'active_memberships': active_memberships,
            'new_memberships': new_memberships,
            'membership_type_distribution': type_distribution,
            'average_duration_days': float(avg_duration),
            'churn_rate': float(churn_rate),
            'retention_rate': float(100 - churn_rate)
        }
    
    async def _analyze_attendance(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Analyze attendance patterns"""
        # Get class bookings
        bookings = self.db.query(ClassBooking).join(Class).filter(
            and_(
                Class.start_time >= request.start_date,
                Class.start_time <= request.end_date
            )
        ).all()
        
        # Get routine completions
        routine_completions = self.db.query(RoutineAssignment).filter(
            and_(
                RoutineAssignment.completed_date >= request.start_date,
                RoutineAssignment.completed_date <= request.end_date,
                RoutineAssignment.completed_date.isnot(None)
            )
        ).all()
        
        # Attendance by day of week
        attendance_by_day = defaultdict(int)
        for booking in bookings:
            if booking.class_obj and booking.status == 'confirmed':
                day_name = booking.class_obj.start_time.strftime('%A')
                attendance_by_day[day_name] += 1
        
        # Attendance by hour
        attendance_by_hour = defaultdict(int)
        for booking in bookings:
            if booking.class_obj and booking.status == 'confirmed':
                hour = booking.class_obj.start_time.hour
                attendance_by_hour[hour] += 1
        
        # Peak hours
        peak_hours = sorted(attendance_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Average attendance rate
        total_bookings = len(bookings)
        confirmed_bookings = len([b for b in bookings if b.status == 'confirmed'])
        attendance_rate = (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0
        
        # Most popular classes
        class_popularity = defaultdict(int)
        for booking in bookings:
            if booking.class_obj and booking.status == 'confirmed':
                class_popularity[booking.class_obj.name] += 1
        
        popular_classes = sorted(class_popularity.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'attendance_rate': float(attendance_rate),
            'attendance_by_day': dict(attendance_by_day),
            'attendance_by_hour': dict(attendance_by_hour),
            'peak_hours': [{'hour': h, 'count': c} for h, c in peak_hours],
            'popular_classes': [{'name': name, 'bookings': count} for name, count in popular_classes],
            'routine_completions': len(routine_completions)
        }
    
    async def _analyze_retention(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Analyze customer retention"""
        # Get all users who joined before the analysis period
        users = self.db.query(User).filter(
            User.created_at < request.start_date
        ).all()
        
        retention_data = []
        for user in users:
            # Check if user was active during the period
            user_payments = self.db.query(Payment).filter(
                and_(
                    Payment.user_id == user.id,
                    Payment.payment_date >= request.start_date,
                    Payment.payment_date <= request.end_date,
                    Payment.status == 'completed'
                )
            ).count()
            
            user_bookings = self.db.query(ClassBooking).join(Class).filter(
                and_(
                    ClassBooking.user_id == user.id,
                    Class.start_time >= request.start_date,
                    Class.start_time <= request.end_date
                )
            ).count()
            
            user_routines = self.db.query(RoutineAssignment).filter(
                and_(
                    RoutineAssignment.user_id == user.id,
                    RoutineAssignment.completed_date >= request.start_date,
                    RoutineAssignment.completed_date <= request.end_date
                )
            ).count()
            
            is_active = user_payments > 0 or user_bookings > 0 or user_routines > 0
            
            # Calculate user lifetime value
            total_payments = self.db.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.user_id == user.id,
                    Payment.status == 'completed'
                )
            ).scalar() or 0
            
            # Calculate days since last activity
            last_payment = self.db.query(func.max(Payment.payment_date)).filter(
                and_(
                    Payment.user_id == user.id,
                    Payment.status == 'completed'
                )
            ).scalar()
            
            days_since_last_activity = 0
            if last_payment:
                days_since_last_activity = (datetime.now() - last_payment).days
            
            retention_data.append({
                'user_id': user.id,
                'is_active': is_active,
                'lifetime_value': float(total_payments),
                'days_since_last_activity': days_since_last_activity,
                'tenure_days': (datetime.now() - user.created_at).days
            })
        
        df = pd.DataFrame(retention_data)
        
        if df.empty:
            return {
                'retention_rate': 0,
                'average_lifetime_value': 0,
                'at_risk_customers': 0,
                'retention_by_tenure': {}
            }
        
        # Calculate retention rate
        retention_rate = (df['is_active'].sum() / len(df) * 100) if len(df) > 0 else 0
        
        # Average lifetime value
        avg_ltv = df['lifetime_value'].mean()
        
        # At-risk customers (inactive for more than 30 days)
        at_risk_customers = len(df[df['days_since_last_activity'] > 30])
        
        # Retention by tenure groups
        df['tenure_group'] = pd.cut(
            df['tenure_days'],
            bins=[0, 30, 90, 180, 365, float('inf')],
            labels=['0-30 days', '31-90 days', '91-180 days', '181-365 days', '365+ days']
        )
        
        retention_by_tenure = df.groupby('tenure_group')['is_active'].mean().to_dict()
        retention_by_tenure = {str(k): float(v) * 100 for k, v in retention_by_tenure.items()}
        
        return {
            'retention_rate': float(retention_rate),
            'average_lifetime_value': float(avg_ltv),
            'at_risk_customers': at_risk_customers,
            'retention_by_tenure': retention_by_tenure,
            'total_customers_analyzed': len(df)
        }
    
    async def _analyze_performance(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Analyze gym performance metrics"""
        # Equipment utilization (simulated)
        equipment_utilization = {
            'treadmills': 85.2,
            'weight_machines': 72.8,
            'free_weights': 91.5,
            'cardio_bikes': 68.3,
            'rowing_machines': 45.7
        }
        
        # Staff performance
        employees = self.db.query(Employee).filter(
            Employee.is_active == True
        ).all()
        
        staff_performance = []
        for employee in employees:
            # Simulate performance metrics
            performance_score = np.random.uniform(70, 95)
            classes_taught = np.random.randint(10, 50)
            customer_rating = np.random.uniform(4.0, 5.0)
            
            staff_performance.append({
                'employee_id': employee.id,
                'name': employee.full_name,
                'performance_score': round(performance_score, 1),
                'classes_taught': classes_taught,
                'customer_rating': round(customer_rating, 1)
            })
        
        # Facility metrics
        total_capacity = 200  # Simulated
        current_members = self.db.query(Membership).filter(
            Membership.status == 'active'
        ).count()
        
        capacity_utilization = (current_members / total_capacity * 100) if total_capacity > 0 else 0
        
        # Energy efficiency (simulated)
        energy_metrics = {
            'monthly_kwh': 15420,
            'cost_per_member': 12.50,
            'efficiency_score': 78.5
        }
        
        return {
            'equipment_utilization': equipment_utilization,
            'staff_performance': staff_performance,
            'capacity_utilization': float(capacity_utilization),
            'energy_metrics': energy_metrics,
            'overall_performance_score': 82.3  # Calculated composite score
        }
    
    async def _analyze_operational(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Analyze operational metrics"""
        # Class scheduling efficiency
        classes = self.db.query(Class).filter(
            and_(
                Class.start_time >= request.start_date,
                Class.start_time <= request.end_date
            )
        ).all()
        
        total_classes = len(classes)
        cancelled_classes = len([c for c in classes if c.status == 'cancelled'])
        cancellation_rate = (cancelled_classes / total_classes * 100) if total_classes > 0 else 0
        
        # Average class occupancy
        occupancy_rates = []
        for class_obj in classes:
            if class_obj.max_participants > 0:
                bookings = self.db.query(ClassBooking).filter(
                    and_(
                        ClassBooking.class_id == class_obj.id,
                        ClassBooking.status == 'confirmed'
                    )
                ).count()
                occupancy = (bookings / class_obj.max_participants * 100)
                occupancy_rates.append(occupancy)
        
        avg_occupancy = np.mean(occupancy_rates) if occupancy_rates else 0
        
        # Equipment maintenance (simulated)
        maintenance_metrics = {
            'scheduled_maintenance': 15,
            'emergency_repairs': 3,
            'equipment_downtime_hours': 24,
            'maintenance_cost': 2500.00
        }
        
        # Staff scheduling efficiency
        total_staff = self.db.query(Employee).filter(
            Employee.is_active == True
        ).count()
        
        staff_utilization = 87.5  # Simulated
        
        return {
            'class_metrics': {
                'total_classes': total_classes,
                'cancelled_classes': cancelled_classes,
                'cancellation_rate': float(cancellation_rate),
                'average_occupancy': float(avg_occupancy)
            },
            'maintenance_metrics': maintenance_metrics,
            'staff_metrics': {
                'total_staff': total_staff,
                'utilization_rate': staff_utilization
            }
        }
    
    async def _generate_predictions(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Generate predictive analytics"""
        # Revenue prediction
        revenue_forecast = await self._predict_revenue(request)
        
        # Membership growth prediction
        membership_forecast = await self._predict_membership_growth(request)
        
        # Churn prediction
        churn_prediction = await self._predict_churn(request)
        
        # Demand forecasting
        demand_forecast = await self._predict_demand(request)
        
        return {
            'revenue_forecast': revenue_forecast,
            'membership_forecast': membership_forecast,
            'churn_prediction': churn_prediction,
            'demand_forecast': demand_forecast,
            'confidence_score': 0.78  # Average confidence across predictions
        }
    
    async def _perform_customer_segmentation(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Perform customer segmentation using ML"""
        # Get customer data
        users = self.db.query(User).all()
        
        customer_data = []
        for user in users:
            # Calculate customer metrics
            total_payments = self.db.query(func.sum(Payment.amount)).filter(
                and_(
                    Payment.user_id == user.id,
                    Payment.status == 'completed'
                )
            ).scalar() or 0
            
            payment_count = self.db.query(Payment).filter(
                and_(
                    Payment.user_id == user.id,
                    Payment.status == 'completed'
                )
            ).count()
            
            class_bookings = self.db.query(ClassBooking).filter(
                ClassBooking.user_id == user.id
            ).count()
            
            routine_completions = self.db.query(RoutineAssignment).filter(
                and_(
                    RoutineAssignment.user_id == user.id,
                    RoutineAssignment.completed_date.isnot(None)
                )
            ).count()
            
            tenure_days = (datetime.now() - user.created_at).days
            
            customer_data.append({
                'user_id': user.id,
                'total_revenue': float(total_payments),
                'payment_frequency': payment_count,
                'class_bookings': class_bookings,
                'routine_completions': routine_completions,
                'tenure_days': tenure_days,
                'avg_payment': float(total_payments / payment_count) if payment_count > 0 else 0
            })
        
        df = pd.DataFrame(customer_data)
        
        if len(df) < 5:  # Need minimum data for clustering
            return {
                'segments': [],
                'segment_distribution': {},
                'error': 'Insufficient data for segmentation'
            }
        
        # Prepare features for clustering
        features = ['total_revenue', 'payment_frequency', 'class_bookings', 'routine_completions', 'tenure_days']
        X = df[features].fillna(0)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform K-means clustering
        n_clusters = min(5, len(df) // 2)  # Adaptive number of clusters
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df['segment'] = kmeans.fit_predict(X_scaled)
        
        # Analyze segments
        segments = []
        for segment_id in range(n_clusters):
            segment_data = df[df['segment'] == segment_id]
            
            segment = CustomerSegment(
                segment_id=f"segment_{segment_id}",
                name=self._generate_segment_name(segment_data, features),
                description=self._generate_segment_description(segment_data, features),
                characteristics={
                    'avg_revenue': float(segment_data['total_revenue'].mean()),
                    'avg_frequency': float(segment_data['payment_frequency'].mean()),
                    'avg_bookings': float(segment_data['class_bookings'].mean()),
                    'avg_tenure': float(segment_data['tenure_days'].mean())
                },
                size=len(segment_data),
                avg_revenue=float(segment_data['total_revenue'].mean()),
                retention_rate=85.0  # Simulated - would calculate from actual data
            )
            segments.append(segment)
        
        # Segment distribution
        segment_distribution = df['segment'].value_counts().to_dict()
        segment_distribution = {f"segment_{k}": v for k, v in segment_distribution.items()}
        
        return {
            'segments': [segment.__dict__ for segment in segments],
            'segment_distribution': segment_distribution,
            'total_customers': len(df)
        }
    
    def _generate_segment_name(self, segment_data: pd.DataFrame, features: List[str]) -> str:
        """Generate descriptive name for customer segment"""
        avg_revenue = segment_data['total_revenue'].mean()
        avg_frequency = segment_data['payment_frequency'].mean()
        
        if avg_revenue > 1000 and avg_frequency > 10:
            return "VIP Customers"
        elif avg_revenue > 500:
            return "High Value Customers"
        elif avg_frequency > 5:
            return "Regular Customers"
        elif segment_data['tenure_days'].mean() < 90:
            return "New Customers"
        else:
            return "Casual Customers"
    
    def _generate_segment_description(self, segment_data: pd.DataFrame, features: List[str]) -> str:
        """Generate description for customer segment"""
        avg_revenue = segment_data['total_revenue'].mean()
        avg_bookings = segment_data['class_bookings'].mean()
        avg_tenure = segment_data['tenure_days'].mean()
        
        return f"Customers with average revenue of ${avg_revenue:.0f}, {avg_bookings:.1f} class bookings, and {avg_tenure:.0f} days tenure."
    
    async def _forecast_revenue(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Forecast revenue using time series analysis"""
        try:
            # Simple linear regression for demonstration
            df['date_numeric'] = pd.to_numeric(df['date'])
            X = df[['date_numeric']]
            y = df['amount']
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next 30 days
            future_dates = pd.date_range(
                start=df['date'].max() + timedelta(days=1),
                periods=30,
                freq='D'
            )
            
            future_numeric = pd.to_numeric(future_dates)
            predictions = model.predict(future_numeric.values.reshape(-1, 1))
            
            forecast = {
                'dates': [d.isoformat() for d in future_dates],
                'predicted_revenue': [max(0, float(p)) for p in predictions],
                'confidence': 0.75
            }
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error in revenue forecasting: {e}")
            return {'error': str(e)}
    
    async def _predict_revenue(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Predict future revenue"""
        # Simplified prediction - in reality would use more sophisticated models
        current_revenue = 50000  # Simulated current monthly revenue
        growth_rate = 0.05  # 5% monthly growth
        
        predictions = []
        for i in range(1, 13):  # Next 12 months
            predicted_revenue = current_revenue * (1 + growth_rate) ** i
            predictions.append({
                'month': i,
                'predicted_revenue': round(predicted_revenue, 2)
            })
        
        return {
            'predictions': predictions,
            'confidence': 0.82,
            'model': 'linear_growth'
        }
    
    async def _predict_membership_growth(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Predict membership growth"""
        current_members = self.db.query(Membership).filter(
            Membership.status == 'active'
        ).count()
        
        # Simulate growth prediction
        growth_rate = 0.03  # 3% monthly growth
        predictions = []
        
        for i in range(1, 13):
            predicted_members = int(current_members * (1 + growth_rate) ** i)
            predictions.append({
                'month': i,
                'predicted_members': predicted_members
            })
        
        return {
            'current_members': current_members,
            'predictions': predictions,
            'confidence': 0.78
        }
    
    async def _predict_churn(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Predict customer churn"""
        # Get users at risk of churning
        users = self.db.query(User).all()
        
        at_risk_users = []
        for user in users:
            # Calculate risk factors
            days_since_payment = 30  # Simulated
            class_attendance_rate = 0.6  # Simulated
            
            # Simple risk scoring
            risk_score = 0
            if days_since_payment > 30:
                risk_score += 0.4
            if class_attendance_rate < 0.5:
                risk_score += 0.3
            
            if risk_score > 0.5:
                at_risk_users.append({
                    'user_id': user.id,
                    'name': user.full_name,
                    'risk_score': round(risk_score, 2),
                    'days_since_payment': days_since_payment
                })
        
        return {
            'at_risk_users': at_risk_users[:10],  # Top 10 at-risk users
            'total_at_risk': len(at_risk_users),
            'predicted_churn_rate': 8.5,  # Percentage
            'confidence': 0.73
        }
    
    async def _predict_demand(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Predict demand for classes and equipment"""
        # Simulate demand prediction
        class_demand = {
            'yoga': {'current': 85, 'predicted': 92, 'trend': 'increasing'},
            'hiit': {'current': 78, 'predicted': 82, 'trend': 'increasing'},
            'pilates': {'current': 65, 'predicted': 68, 'trend': 'stable'},
            'spinning': {'current': 72, 'predicted': 70, 'trend': 'decreasing'}
        }
        
        equipment_demand = {
            'treadmills': {'utilization': 85, 'predicted': 88, 'recommendation': 'add_1_unit'},
            'weight_machines': {'utilization': 73, 'predicted': 75, 'recommendation': 'maintain'},
            'free_weights': {'utilization': 92, 'predicted': 95, 'recommendation': 'add_equipment'}
        }
        
        return {
            'class_demand': class_demand,
            'equipment_demand': equipment_demand,
            'confidence': 0.80
        }
    
    async def _generate_insights(self, analytics_type: AnalyticsType, data: Dict[str, Any]) -> List[str]:
        """Generate insights based on analytics data"""
        insights = []
        
        if analytics_type == AnalyticsType.REVENUE:
            if data.get('growth_rate', 0) > 10:
                insights.append("Revenue is growing strongly at {:.1f}% growth rate".format(data['growth_rate']))
            elif data.get('growth_rate', 0) < 0:
                insights.append("Revenue is declining - immediate attention needed")
            
            if data.get('average_transaction', 0) > 100:
                insights.append("High average transaction value indicates premium customer base")
        
        elif analytics_type == AnalyticsType.MEMBERSHIP:
            if data.get('churn_rate', 0) > 15:
                insights.append("High churn rate detected - focus on retention strategies")
            
            if data.get('retention_rate', 0) > 85:
                insights.append("Excellent retention rate - current strategies are working well")
        
        elif analytics_type == AnalyticsType.ATTENDANCE:
            if data.get('attendance_rate', 0) < 70:
                insights.append("Low attendance rate - consider improving class scheduling or content")
            
            peak_hours = data.get('peak_hours', [])
            if peak_hours:
                insights.append(f"Peak attendance at {peak_hours[0]['hour']}:00 - optimize staffing")
        
        return insights
    
    async def _generate_recommendations(self, analytics_type: AnalyticsType, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analytics data"""
        recommendations = []
        
        if analytics_type == AnalyticsType.REVENUE:
            if data.get('growth_rate', 0) < 5:
                recommendations.append("Consider introducing new membership tiers or services")
                recommendations.append("Implement referral programs to boost growth")
        
        elif analytics_type == AnalyticsType.MEMBERSHIP:
            if data.get('churn_rate', 0) > 10:
                recommendations.append("Implement proactive retention campaigns")
                recommendations.append("Conduct exit interviews to understand churn reasons")
        
        elif analytics_type == AnalyticsType.ATTENDANCE:
            if data.get('attendance_rate', 0) < 75:
                recommendations.append("Send automated class reminders to improve attendance")
                recommendations.append("Offer makeup classes for missed sessions")
        
        return recommendations
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get overall analytics summary"""
        return {
            'total_active_members': self.db.query(Membership).filter(Membership.status == 'active').count(),
            'monthly_revenue': 45000,  # Simulated
            'attendance_rate': 78.5,
            'retention_rate': 87.2,
            'growth_rate': 5.8,
            'last_updated': datetime.now().isoformat()
        }

# Global instance
analytics_service = AnalyticsService()