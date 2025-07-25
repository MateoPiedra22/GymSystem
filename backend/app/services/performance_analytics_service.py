from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
import pandas as pd
from dataclasses import dataclass
import logging
from ..models.user import User
from ..models.routine import Routine, RoutineAssignment, RoutineExercise
from ..models.exercise import Exercise
from ..models.membership import Membership
from ..core.database import get_db
import json
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(Enum):
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    FLEXIBILITY = "flexibility"
    BODY_COMPOSITION = "body_composition"
    CARDIOVASCULAR = "cardiovascular"
    CONSISTENCY = "consistency"

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_type: MetricType
    value: float
    unit: str
    date: datetime
    exercise_id: Optional[int] = None
    notes: Optional[str] = None

@dataclass
class ProgressTrend:
    """Progress trend analysis"""
    metric_type: MetricType
    trend_direction: str  # "improving", "declining", "stable"
    trend_strength: float  # 0-1 scale
    rate_of_change: float
    confidence_score: float
    prediction_next_month: Optional[float] = None

@dataclass
class PerformanceInsight:
    """AI-generated performance insight"""
    insight_type: str
    title: str
    description: str
    recommendation: str
    priority: str  # "high", "medium", "low"
    confidence: float
    supporting_data: Dict[str, Any]

class PerformanceAnalyticsService:
    """Advanced performance analytics and insights service"""
    
    def __init__(self):
        self.db = next(get_db())
    
    async def generate_comprehensive_report(
        self,
        user_id: int,
        period_days: int = 90
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report for user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Collect all performance data
            performance_data = await self._collect_performance_data(user_id, start_date, end_date)
            
            # Analyze trends
            trends = await self._analyze_performance_trends(performance_data)
            
            # Generate insights
            insights = await self._generate_performance_insights(user, performance_data, trends)
            
            # Calculate scores
            scores = await self._calculate_performance_scores(performance_data, trends)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(user, insights, trends)
            
            # Create visualizations data
            visualizations = await self._prepare_visualization_data(performance_data, trends)
            
            return {
                "success": True,
                "user_id": user_id,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days
                },
                "performance_scores": scores,
                "trends": [trend.__dict__ for trend in trends],
                "insights": [insight.__dict__ for insight in insights],
                "recommendations": recommendations,
                "visualizations": visualizations,
                "summary": await self._generate_summary(scores, trends, insights)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"success": False, "error": str(e)}
    
    async def _collect_performance_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[PerformanceMetric]]:
        """Collect all performance data for the specified period"""
        data = {
            "strength": [],
            "endurance": [],
            "consistency": [],
            "body_composition": [],
            "cardiovascular": []
        }
        
        # Get routine assignments and completions
        assignments = self.db.query(RoutineAssignment).filter(
            and_(
                RoutineAssignment.user_id == user_id,
                RoutineAssignment.assigned_date >= start_date,
                RoutineAssignment.assigned_date <= end_date
            )
        ).all()
        
        # Analyze workout consistency
        consistency_metrics = self._analyze_workout_consistency(assignments, start_date, end_date)
        data["consistency"].extend(consistency_metrics)
        
        # Analyze strength progression
        strength_metrics = await self._analyze_strength_progression(user_id, start_date, end_date)
        data["strength"].extend(strength_metrics)
        
        # Analyze endurance improvements
        endurance_metrics = await self._analyze_endurance_progression(user_id, start_date, end_date)
        data["endurance"].extend(endurance_metrics)
        
        # Get body composition data (if available)
        body_comp_metrics = await self._get_body_composition_data(user_id, start_date, end_date)
        data["body_composition"].extend(body_comp_metrics)
        
        # Analyze cardiovascular improvements
        cardio_metrics = await self._analyze_cardiovascular_data(user_id, start_date, end_date)
        data["cardiovascular"].extend(cardio_metrics)
        
        return data
    
    def _analyze_workout_consistency(
        self,
        assignments: List[RoutineAssignment],
        start_date: datetime,
        end_date: datetime
    ) -> List[PerformanceMetric]:
        """Analyze workout consistency patterns"""
        metrics = []
        
        # Calculate weekly consistency
        total_days = (end_date - start_date).days
        weeks = total_days // 7
        
        if weeks > 0:
            completed_workouts = len([a for a in assignments if a.completed_date])
            total_assigned = len(assignments)
            
            # Completion rate
            completion_rate = (completed_workouts / total_assigned * 100) if total_assigned > 0 else 0
            
            metrics.append(PerformanceMetric(
                metric_type=MetricType.CONSISTENCY,
                value=completion_rate,
                unit="percentage",
                date=end_date,
                notes="Workout completion rate"
            ))
            
            # Weekly frequency
            weekly_frequency = completed_workouts / weeks
            metrics.append(PerformanceMetric(
                metric_type=MetricType.CONSISTENCY,
                value=weekly_frequency,
                unit="workouts_per_week",
                date=end_date,
                notes="Average weekly workout frequency"
            ))
        
        return metrics
    
    async def _analyze_strength_progression(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[PerformanceMetric]:
        """Analyze strength progression across exercises"""
        metrics = []
        
        # Get strength-based exercises
        strength_exercises = self.db.query(Exercise).filter(
            Exercise.category.in_(['strength', 'powerlifting', 'bodybuilding'])
        ).all()
        
        for exercise in strength_exercises:
            # Get user's performance data for this exercise
            # This would typically come from workout logs
            # For now, we'll simulate some progression data
            
            # Calculate 1RM progression (simulated)
            initial_1rm = 100  # This would come from actual data
            current_1rm = initial_1rm * 1.15  # 15% improvement simulation
            
            metrics.append(PerformanceMetric(
                metric_type=MetricType.STRENGTH,
                value=current_1rm,
                unit="kg",
                date=end_date,
                exercise_id=exercise.id,
                notes=f"Estimated 1RM for {exercise.name}"
            ))
        
        return metrics
    
    async def _analyze_endurance_progression(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[PerformanceMetric]:
        """Analyze endurance improvements"""
        metrics = []
        
        # Get endurance-based exercises
        endurance_exercises = self.db.query(Exercise).filter(
            Exercise.category.in_(['cardio', 'endurance'])
        ).all()
        
        for exercise in endurance_exercises:
            # Simulate endurance progression
            if 'running' in exercise.name.lower():
                # Running pace improvement
                metrics.append(PerformanceMetric(
                    metric_type=MetricType.ENDURANCE,
                    value=5.2,  # minutes per km
                    unit="min_per_km",
                    date=end_date,
                    exercise_id=exercise.id,
                    notes=f"Average pace for {exercise.name}"
                ))
            elif 'cycling' in exercise.name.lower():
                # Cycling power output
                metrics.append(PerformanceMetric(
                    metric_type=MetricType.ENDURANCE,
                    value=250,  # watts
                    unit="watts",
                    date=end_date,
                    exercise_id=exercise.id,
                    notes=f"Average power output for {exercise.name}"
                ))
        
        return metrics
    
    async def _get_body_composition_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[PerformanceMetric]:
        """Get body composition data"""
        metrics = []
        
        # This would typically come from body composition measurements
        # For now, we'll simulate some data
        
        metrics.extend([
            PerformanceMetric(
                metric_type=MetricType.BODY_COMPOSITION,
                value=75.5,
                unit="kg",
                date=end_date,
                notes="Body weight"
            ),
            PerformanceMetric(
                metric_type=MetricType.BODY_COMPOSITION,
                value=15.2,
                unit="percentage",
                date=end_date,
                notes="Body fat percentage"
            ),
            PerformanceMetric(
                metric_type=MetricType.BODY_COMPOSITION,
                value=63.8,
                unit="kg",
                date=end_date,
                notes="Lean body mass"
            )
        ])
        
        return metrics
    
    async def _analyze_cardiovascular_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[PerformanceMetric]:
        """Analyze cardiovascular improvements"""
        metrics = []
        
        # Simulate cardiovascular metrics
        metrics.extend([
            PerformanceMetric(
                metric_type=MetricType.CARDIOVASCULAR,
                value=65,
                unit="bpm",
                date=end_date,
                notes="Resting heart rate"
            ),
            PerformanceMetric(
                metric_type=MetricType.CARDIOVASCULAR,
                value=185,
                unit="bpm",
                date=end_date,
                notes="Maximum heart rate"
            ),
            PerformanceMetric(
                metric_type=MetricType.CARDIOVASCULAR,
                value=45,
                unit="ml_kg_min",
                date=end_date,
                notes="Estimated VO2 max"
            )
        ])
        
        return metrics
    
    async def _analyze_performance_trends(
        self,
        performance_data: Dict[str, List[PerformanceMetric]]
    ) -> List[ProgressTrend]:
        """Analyze trends in performance data"""
        trends = []
        
        for metric_type, metrics in performance_data.items():
            if len(metrics) >= 2:
                # Calculate trend for this metric type
                values = [m.value for m in metrics]
                dates = [m.date for m in metrics]
                
                # Simple linear trend analysis
                if len(values) > 1:
                    # Calculate rate of change
                    rate_of_change = (values[-1] - values[0]) / len(values)
                    
                    # Determine trend direction
                    if rate_of_change > 0.05:
                        direction = "improving"
                        strength = min(abs(rate_of_change) / 10, 1.0)
                    elif rate_of_change < -0.05:
                        direction = "declining"
                        strength = min(abs(rate_of_change) / 10, 1.0)
                    else:
                        direction = "stable"
                        strength = 0.1
                    
                    # Calculate confidence based on data points
                    confidence = min(len(values) / 10, 1.0)
                    
                    # Predict next month value
                    prediction = values[-1] + (rate_of_change * 4)  # 4 weeks
                    
                    trends.append(ProgressTrend(
                        metric_type=MetricType(metric_type),
                        trend_direction=direction,
                        trend_strength=strength,
                        rate_of_change=rate_of_change,
                        confidence_score=confidence,
                        prediction_next_month=prediction
                    ))
        
        return trends
    
    async def _generate_performance_insights(
        self,
        user: User,
        performance_data: Dict[str, List[PerformanceMetric]],
        trends: List[ProgressTrend]
    ) -> List[PerformanceInsight]:
        """Generate AI-powered performance insights"""
        insights = []
        
        # Analyze consistency
        consistency_metrics = performance_data.get("consistency", [])
        if consistency_metrics:
            completion_rate = next(
                (m.value for m in consistency_metrics if "completion" in m.notes.lower()),
                0
            )
            
            if completion_rate < 70:
                insights.append(PerformanceInsight(
                    insight_type="consistency",
                    title="Low Workout Consistency",
                    description=f"Your workout completion rate is {completion_rate:.1f}%, which is below the recommended 80%.",
                    recommendation="Try scheduling workouts at consistent times and setting realistic goals.",
                    priority="high",
                    confidence=0.9,
                    supporting_data={"completion_rate": completion_rate}
                ))
            elif completion_rate > 90:
                insights.append(PerformanceInsight(
                    insight_type="consistency",
                    title="Excellent Consistency",
                    description=f"Outstanding workout completion rate of {completion_rate:.1f}%!",
                    recommendation="Consider gradually increasing workout intensity or adding new challenges.",
                    priority="medium",
                    confidence=0.95,
                    supporting_data={"completion_rate": completion_rate}
                ))
        
        # Analyze strength trends
        strength_trend = next(
            (t for t in trends if t.metric_type == MetricType.STRENGTH),
            None
        )
        
        if strength_trend:
            if strength_trend.trend_direction == "improving" and strength_trend.trend_strength > 0.5:
                insights.append(PerformanceInsight(
                    insight_type="strength",
                    title="Strong Strength Gains",
                    description="Your strength is improving consistently across multiple exercises.",
                    recommendation="Continue current training approach and consider progressive overload.",
                    priority="medium",
                    confidence=strength_trend.confidence_score,
                    supporting_data={"trend_strength": strength_trend.trend_strength}
                ))
            elif strength_trend.trend_direction == "declining":
                insights.append(PerformanceInsight(
                    insight_type="strength",
                    title="Strength Plateau or Decline",
                    description="Your strength gains have plateaued or are declining.",
                    recommendation="Consider deload week, form check, or program variation.",
                    priority="high",
                    confidence=strength_trend.confidence_score,
                    supporting_data={"trend_direction": strength_trend.trend_direction}
                ))
        
        # Analyze body composition
        body_comp_metrics = performance_data.get("body_composition", [])
        if body_comp_metrics:
            weight_metric = next(
                (m for m in body_comp_metrics if "weight" in m.notes.lower()),
                None
            )
            bf_metric = next(
                (m for m in body_comp_metrics if "fat" in m.notes.lower()),
                None
            )
            
            if weight_metric and bf_metric:
                if bf_metric.value < 15 and weight_metric.value > 70:
                    insights.append(PerformanceInsight(
                        insight_type="body_composition",
                        title="Excellent Body Composition",
                        description="You have achieved a healthy body fat percentage with good muscle mass.",
                        recommendation="Focus on maintaining current composition while continuing strength training.",
                        priority="low",
                        confidence=0.8,
                        supporting_data={
                            "body_fat": bf_metric.value,
                            "weight": weight_metric.value
                        }
                    ))
        
        return insights
    
    async def _calculate_performance_scores(
        self,
        performance_data: Dict[str, List[PerformanceMetric]],
        trends: List[ProgressTrend]
    ) -> Dict[str, float]:
        """Calculate overall performance scores"""
        scores = {
            "overall": 0.0,
            "strength": 0.0,
            "endurance": 0.0,
            "consistency": 0.0,
            "progress": 0.0
        }
        
        # Calculate consistency score
        consistency_metrics = performance_data.get("consistency", [])
        if consistency_metrics:
            completion_rate = next(
                (m.value for m in consistency_metrics if "completion" in m.notes.lower()),
                0
            )
            scores["consistency"] = min(completion_rate / 100 * 10, 10.0)
        
        # Calculate strength score based on trends
        strength_trend = next(
            (t for t in trends if t.metric_type == MetricType.STRENGTH),
            None
        )
        if strength_trend:
            if strength_trend.trend_direction == "improving":
                scores["strength"] = 7.0 + (strength_trend.trend_strength * 3)
            elif strength_trend.trend_direction == "stable":
                scores["strength"] = 6.0
            else:
                scores["strength"] = 4.0 - (strength_trend.trend_strength * 2)
        
        # Calculate endurance score
        endurance_trend = next(
            (t for t in trends if t.metric_type == MetricType.ENDURANCE),
            None
        )
        if endurance_trend:
            if endurance_trend.trend_direction == "improving":
                scores["endurance"] = 7.0 + (endurance_trend.trend_strength * 3)
            elif endurance_trend.trend_direction == "stable":
                scores["endurance"] = 6.0
            else:
                scores["endurance"] = 4.0 - (endurance_trend.trend_strength * 2)
        
        # Calculate progress score (average of improving trends)
        improving_trends = [t for t in trends if t.trend_direction == "improving"]
        if improving_trends:
            avg_improvement = sum(t.trend_strength for t in improving_trends) / len(improving_trends)
            scores["progress"] = 5.0 + (avg_improvement * 5)
        else:
            scores["progress"] = 5.0
        
        # Calculate overall score
        component_scores = [scores["strength"], scores["endurance"], scores["consistency"], scores["progress"]]
        valid_scores = [s for s in component_scores if s > 0]
        if valid_scores:
            scores["overall"] = sum(valid_scores) / len(valid_scores)
        
        # Ensure all scores are between 0 and 10
        for key in scores:
            scores[key] = max(0.0, min(10.0, scores[key]))
        
        return scores
    
    async def _generate_recommendations(
        self,
        user: User,
        insights: List[PerformanceInsight],
        trends: List[ProgressTrend]
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # High priority insights first
        high_priority_insights = [i for i in insights if i.priority == "high"]
        for insight in high_priority_insights:
            recommendations.append({
                "type": "immediate_action",
                "title": insight.title,
                "description": insight.recommendation,
                "priority": "high",
                "category": insight.insight_type
            })
        
        # General recommendations based on trends
        declining_trends = [t for t in trends if t.trend_direction == "declining"]
        if declining_trends:
            recommendations.append({
                "type": "program_adjustment",
                "title": "Address Declining Performance",
                "description": "Consider taking a deload week or adjusting your training program.",
                "priority": "medium",
                "category": "general"
            })
        
        stable_trends = [t for t in trends if t.trend_direction == "stable"]
        if len(stable_trends) > 2:
            recommendations.append({
                "type": "progression",
                "title": "Break Through Plateaus",
                "description": "Try new exercises, increase intensity, or change training variables.",
                "priority": "medium",
                "category": "progression"
            })
        
        return recommendations
    
    async def _prepare_visualization_data(
        self,
        performance_data: Dict[str, List[PerformanceMetric]],
        trends: List[ProgressTrend]
    ) -> Dict[str, Any]:
        """Prepare data for frontend visualizations"""
        visualizations = {
            "performance_over_time": {},
            "trend_summary": {},
            "metric_distribution": {},
            "progress_radar": {}
        }
        
        # Performance over time data
        for metric_type, metrics in performance_data.items():
            if metrics:
                visualizations["performance_over_time"][metric_type] = [
                    {
                        "date": m.date.isoformat(),
                        "value": m.value,
                        "unit": m.unit
                    }
                    for m in sorted(metrics, key=lambda x: x.date)
                ]
        
        # Trend summary
        visualizations["trend_summary"] = {
            trend.metric_type.value: {
                "direction": trend.trend_direction,
                "strength": trend.trend_strength,
                "confidence": trend.confidence_score
            }
            for trend in trends
        }
        
        return visualizations
    
    async def _generate_summary(
        self,
        scores: Dict[str, float],
        trends: List[ProgressTrend],
        insights: List[PerformanceInsight]
    ) -> Dict[str, Any]:
        """Generate performance summary"""
        improving_count = len([t for t in trends if t.trend_direction == "improving"])
        declining_count = len([t for t in trends if t.trend_direction == "declining"])
        stable_count = len([t for t in trends if t.trend_direction == "stable"])
        
        high_priority_issues = len([i for i in insights if i.priority == "high"])
        
        overall_status = "excellent" if scores["overall"] >= 8 else \
                        "good" if scores["overall"] >= 6 else \
                        "needs_improvement" if scores["overall"] >= 4 else "poor"
        
        return {
            "overall_score": scores["overall"],
            "overall_status": overall_status,
            "trends_summary": {
                "improving": improving_count,
                "declining": declining_count,
                "stable": stable_count
            },
            "priority_issues": high_priority_issues,
            "key_strengths": self._identify_key_strengths(scores, trends),
            "areas_for_improvement": self._identify_improvement_areas(insights, trends)
        }
    
    def _identify_key_strengths(self, scores: Dict[str, float], trends: List[ProgressTrend]) -> List[str]:
        """Identify user's key strengths"""
        strengths = []
        
        if scores["consistency"] >= 8:
            strengths.append("Excellent workout consistency")
        
        if scores["strength"] >= 7:
            strengths.append("Strong strength progression")
        
        if scores["endurance"] >= 7:
            strengths.append("Good endurance development")
        
        improving_trends = [t for t in trends if t.trend_direction == "improving" and t.trend_strength > 0.6]
        if len(improving_trends) >= 2:
            strengths.append("Multiple areas showing improvement")
        
        return strengths
    
    def _identify_improvement_areas(self, insights: List[PerformanceInsight], trends: List[ProgressTrend]) -> List[str]:
        """Identify areas needing improvement"""
        areas = []
        
        high_priority_insights = [i for i in insights if i.priority == "high"]
        for insight in high_priority_insights:
            areas.append(insight.insight_type.replace("_", " ").title())
        
        declining_trends = [t for t in trends if t.trend_direction == "declining"]
        for trend in declining_trends:
            areas.append(f"{trend.metric_type.value.replace('_', ' ').title()} performance")
        
        return list(set(areas))  # Remove duplicates

# Global instance
performance_analytics_service = PerformanceAnalyticsService()