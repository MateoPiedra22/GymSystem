from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import numpy as np
from ..models.user import User
from ..models.exercise import Exercise, ExerciseCategory, MuscleGroup, DifficultyLevel
from ..models.routine import RoutineType, RoutineTemplate, Routine
from ..core.database import get_db
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User fitness profile for AI recommendations"""
    fitness_level: str  # beginner, intermediate, advanced
    goals: List[str]  # weight_loss, muscle_gain, strength, endurance
    available_time: int  # minutes per session
    frequency: int  # sessions per week
    preferred_muscle_groups: List[str]
    equipment_access: List[str]
    limitations: List[str]  # injuries, restrictions
    experience_level: int  # 1-10 scale

@dataclass
class ExerciseRecommendation:
    """Exercise recommendation with reasoning"""
    exercise_id: int
    exercise_name: str
    sets: int
    reps: str  # Can be range like "8-12" or specific number
    rest_time: int  # seconds
    weight_percentage: Optional[float]  # % of 1RM if applicable
    reasoning: str
    priority_score: float

class RoutineAIService:
    """AI-powered routine generation and optimization service"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.exercise_vectors = None
        self.exercises_data = []
        self._initialize_ai_models()
    
    def _initialize_ai_models(self):
        """Initialize AI models with exercise data"""
        try:
            db = next(get_db())
            exercises = db.query(Exercise).filter(Exercise.is_active == True).all()
            
            # Prepare exercise data for vectorization
            self.exercises_data = []
            exercise_texts = []
            
            for exercise in exercises:
                exercise_info = {
                    'id': exercise.id,
                    'name': exercise.name,
                    'category': exercise.category.value,
                    'muscle_groups': [mg.value for mg in exercise.primary_muscles],
                    'secondary_muscles': [mg.value for mg in exercise.secondary_muscles],
                    'difficulty': exercise.difficulty_level.value,
                    'equipment': exercise.equipment_needed or [],
                    'description': exercise.description or ""
                }
                
                # Create text representation for vectorization
                text = f"{exercise.name} {exercise.category.value} {' '.join([mg.value for mg in exercise.primary_muscles])} {exercise.difficulty_level.value} {exercise.description or ''}"
                
                self.exercises_data.append(exercise_info)
                exercise_texts.append(text)
            
            # Create exercise vectors
            if exercise_texts:
                self.exercise_vectors = self.vectorizer.fit_transform(exercise_texts)
                logger.info(f"AI models initialized with {len(exercises)} exercises")
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
    
    async def generate_personalized_routine(
        self,
        user: User,
        user_profile: UserProfile,
        routine_type: RoutineType,
        duration_weeks: int = 4
    ) -> Dict[str, Any]:
        """Generate a personalized routine using AI"""
        try:
            # Analyze user profile and goals
            goal_analysis = self._analyze_user_goals(user_profile)
            
            # Select appropriate exercises
            recommended_exercises = self._recommend_exercises(
                user_profile, routine_type, goal_analysis
            )
            
            # Structure the routine
            routine_structure = self._structure_routine(
                recommended_exercises, user_profile, routine_type
            )
            
            # Generate progression plan
            progression_plan = self._generate_progression_plan(
                routine_structure, duration_weeks, user_profile
            )
            
            return {
                "success": True,
                "routine_structure": routine_structure,
                "progression_plan": progression_plan,
                "estimated_duration": self._estimate_session_duration(routine_structure),
                "difficulty_score": self._calculate_difficulty_score(routine_structure),
                "goal_alignment": goal_analysis,
                "recommendations": self._generate_routine_recommendations(user_profile, routine_structure)
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized routine: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_user_goals(self, profile: UserProfile) -> Dict[str, Any]:
        """Analyze user goals and provide insights"""
        goal_weights = {
            "weight_loss": 0.0,
            "muscle_gain": 0.0,
            "strength": 0.0,
            "endurance": 0.0,
            "flexibility": 0.0
        }
        
        # Assign weights based on goals
        for goal in profile.goals:
            if goal in goal_weights:
                goal_weights[goal] = 1.0
        
        # Normalize weights
        total_weight = sum(goal_weights.values())
        if total_weight > 0:
            goal_weights = {k: v/total_weight for k, v in goal_weights.items()}
        
        return {
            "primary_goals": profile.goals,
            "goal_weights": goal_weights,
            "focus_areas": self._determine_focus_areas(goal_weights),
            "training_style": self._determine_training_style(profile)
        }
    
    def _recommend_exercises(
        self,
        profile: UserProfile,
        routine_type: RoutineType,
        goal_analysis: Dict[str, Any]
    ) -> List[ExerciseRecommendation]:
        """Recommend exercises based on user profile and goals"""
        recommendations = []
        
        # Filter exercises based on profile
        suitable_exercises = self._filter_exercises_by_profile(profile)
        
        # Score exercises based on goals and profile
        scored_exercises = []
        for exercise in suitable_exercises:
            score = self._score_exercise_for_user(exercise, profile, goal_analysis)
            if score > 0.3:  # Minimum threshold
                scored_exercises.append((exercise, score))
        
        # Sort by score and select top exercises
        scored_exercises.sort(key=lambda x: x[1], reverse=True)
        
        # Generate recommendations with sets/reps
        for exercise, score in scored_exercises[:20]:  # Limit to top 20
            recommendation = self._create_exercise_recommendation(
                exercise, profile, goal_analysis, score
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _filter_exercises_by_profile(self, profile: UserProfile) -> List[Dict[str, Any]]:
        """Filter exercises based on user profile constraints"""
        suitable_exercises = []
        
        for exercise in self.exercises_data:
            # Check difficulty level
            if not self._is_suitable_difficulty(exercise['difficulty'], profile.fitness_level):
                continue
            
            # Check equipment availability
            if exercise['equipment'] and not self._has_required_equipment(
                exercise['equipment'], profile.equipment_access
            ):
                continue
            
            # Check limitations/restrictions
            if self._conflicts_with_limitations(exercise, profile.limitations):
                continue
            
            suitable_exercises.append(exercise)
        
        return suitable_exercises
    
    def _score_exercise_for_user(
        self,
        exercise: Dict[str, Any],
        profile: UserProfile,
        goal_analysis: Dict[str, Any]
    ) -> float:
        """Score an exercise for a specific user"""
        score = 0.0
        
        # Goal alignment score
        goal_score = self._calculate_goal_alignment_score(exercise, goal_analysis)
        score += goal_score * 0.4
        
        # Muscle group preference score
        muscle_score = self._calculate_muscle_preference_score(exercise, profile)
        score += muscle_score * 0.3
        
        # Difficulty appropriateness score
        difficulty_score = self._calculate_difficulty_appropriateness(exercise, profile)
        score += difficulty_score * 0.2
        
        # Exercise variety score (to avoid repetition)
        variety_score = self._calculate_variety_score(exercise)
        score += variety_score * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _structure_routine(
        self,
        recommendations: List[ExerciseRecommendation],
        profile: UserProfile,
        routine_type: RoutineType
    ) -> Dict[str, Any]:
        """Structure exercises into a coherent routine"""
        # Group exercises by muscle groups and categories
        exercise_groups = self._group_exercises(recommendations)
        
        # Create workout sessions based on frequency
        sessions = self._create_workout_sessions(
            exercise_groups, profile.frequency, profile.available_time
        )
        
        # Add warm-up and cool-down
        for session in sessions:
            session['warm_up'] = self._generate_warmup(session['exercises'])
            session['cool_down'] = self._generate_cooldown(session['exercises'])
        
        return {
            "sessions": sessions,
            "frequency_per_week": profile.frequency,
            "estimated_duration_per_session": profile.available_time,
            "routine_type": routine_type.value,
            "total_exercises": len(recommendations)
        }
    
    def _generate_progression_plan(
        self,
        routine_structure: Dict[str, Any],
        duration_weeks: int,
        profile: UserProfile
    ) -> Dict[str, Any]:
        """Generate a progression plan for the routine"""
        progression_phases = []
        
        # Phase 1: Adaptation (Weeks 1-2)
        phase1 = {
            "phase": 1,
            "weeks": [1, 2],
            "focus": "Adaptation and Form",
            "intensity": "60-70%",
            "volume_modifier": 0.8,
            "notes": "Focus on proper form and technique"
        }
        progression_phases.append(phase1)
        
        # Phase 2: Development (Weeks 3-4)
        if duration_weeks >= 4:
            phase2 = {
                "phase": 2,
                "weeks": [3, 4],
                "focus": "Strength and Volume Development",
                "intensity": "70-80%",
                "volume_modifier": 1.0,
                "notes": "Increase intensity and volume"
            }
            progression_phases.append(phase2)
        
        # Additional phases for longer programs
        if duration_weeks > 4:
            remaining_weeks = duration_weeks - 4
            for i in range(0, remaining_weeks, 2):
                phase_num = len(progression_phases) + 1
                start_week = 5 + i
                end_week = min(start_week + 1, duration_weeks)
                
                phase = {
                    "phase": phase_num,
                    "weeks": list(range(start_week, end_week + 1)),
                    "focus": "Progressive Overload",
                    "intensity": "75-85%",
                    "volume_modifier": 1.1 + (i * 0.05),
                    "notes": "Continue progressive overload"
                }
                progression_phases.append(phase)
        
        return {
            "total_duration_weeks": duration_weeks,
            "phases": progression_phases,
            "progression_strategy": self._determine_progression_strategy(profile),
            "deload_weeks": self._calculate_deload_weeks(duration_weeks)
        }
    
    def _generate_routine_recommendations(
        self,
        profile: UserProfile,
        routine_structure: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized recommendations for the routine"""
        recommendations = []
        
        # Nutrition recommendations
        if "weight_loss" in profile.goals:
            recommendations.append("Maintain a caloric deficit of 300-500 calories for optimal fat loss")
        elif "muscle_gain" in profile.goals:
            recommendations.append("Consume 1.6-2.2g protein per kg body weight for muscle growth")
        
        # Recovery recommendations
        if profile.frequency >= 5:
            recommendations.append("Ensure adequate sleep (7-9 hours) for recovery with high training frequency")
        
        # Progression recommendations
        if profile.fitness_level == "beginner":
            recommendations.append("Focus on form over weight - increase load by 2.5-5% when you can complete all sets with perfect form")
        
        # Time-specific recommendations
        if profile.available_time < 45:
            recommendations.append("Consider supersets or circuits to maximize efficiency in shorter sessions")
        
        return recommendations
    
    async def optimize_existing_routine(
        self,
        routine_id: int,
        user_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize an existing routine based on user feedback and progress"""
        try:
            db = next(get_db())
            routine = db.query(Routine).filter(Routine.id == routine_id).first()
            
            if not routine:
                return {"success": False, "error": "Routine not found"}
            
            # Analyze feedback
            feedback_analysis = self._analyze_user_feedback(user_feedback)
            
            # Generate optimization suggestions
            optimizations = self._generate_optimizations(routine, feedback_analysis)
            
            return {
                "success": True,
                "current_routine": routine.name,
                "feedback_analysis": feedback_analysis,
                "optimizations": optimizations,
                "estimated_improvement": self._estimate_improvement_potential(optimizations)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing routine: {e}")
            return {"success": False, "error": str(e)"}
    
    def _analyze_user_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user feedback to identify optimization opportunities"""
        analysis = {
            "satisfaction_score": feedback.get("satisfaction", 5),
            "difficulty_rating": feedback.get("difficulty", 5),
            "time_rating": feedback.get("time_appropriateness", 5),
            "enjoyment_score": feedback.get("enjoyment", 5),
            "progress_satisfaction": feedback.get("progress", 5),
            "areas_for_improvement": []
        }
        
        # Identify areas for improvement
        if analysis["satisfaction_score"] < 4:
            analysis["areas_for_improvement"].append("overall_satisfaction")
        if analysis["difficulty_rating"] < 3:
            analysis["areas_for_improvement"].append("too_easy")
        elif analysis["difficulty_rating"] > 7:
            analysis["areas_for_improvement"].append("too_difficult")
        if analysis["time_rating"] < 4:
            analysis["areas_for_improvement"].append("time_management")
        if analysis["enjoyment_score"] < 4:
            analysis["areas_for_improvement"].append("exercise_variety")
        
        return analysis
    
    # Helper methods
    def _is_suitable_difficulty(self, exercise_difficulty: str, user_level: str) -> bool:
        """Check if exercise difficulty matches user level"""
        difficulty_map = {
            "beginner": ["beginner", "intermediate"],
            "intermediate": ["beginner", "intermediate", "advanced"],
            "advanced": ["intermediate", "advanced"]
        }
        return exercise_difficulty in difficulty_map.get(user_level, [])
    
    def _has_required_equipment(self, required: List[str], available: List[str]) -> bool:
        """Check if user has required equipment"""
        return all(eq in available for eq in required)
    
    def _conflicts_with_limitations(self, exercise: Dict[str, Any], limitations: List[str]) -> bool:
        """Check if exercise conflicts with user limitations"""
        # Simple conflict detection - can be expanded
        exercise_name = exercise['name'].lower()
        for limitation in limitations:
            if limitation.lower() in exercise_name:
                return True
        return False
    
    def _estimate_session_duration(self, routine_structure: Dict[str, Any]) -> int:
        """Estimate session duration in minutes"""
        total_time = 0
        for session in routine_structure['sessions']:
            session_time = 10  # Warm-up
            for exercise in session['exercises']:
                # Estimate time per exercise (sets * (work + rest))
                sets = exercise.sets
                rest_time = exercise.rest_time / 60  # Convert to minutes
                work_time = 1.5  # Assume 1.5 minutes per set
                session_time += sets * (work_time + rest_time)
            session_time += 10  # Cool-down
            total_time = max(total_time, session_time)
        
        return int(total_time)
    
    def _calculate_difficulty_score(self, routine_structure: Dict[str, Any]) -> float:
        """Calculate overall difficulty score (1-10)"""
        total_score = 0
        total_exercises = 0
        
        difficulty_values = {
            "beginner": 3,
            "intermediate": 6,
            "advanced": 9
        }
        
        for session in routine_structure['sessions']:
            for exercise in session['exercises']:
                # Get exercise difficulty from exercises_data
                exercise_data = next(
                    (e for e in self.exercises_data if e['id'] == exercise.exercise_id),
                    None
                )
                if exercise_data:
                    total_score += difficulty_values.get(exercise_data['difficulty'], 5)
                    total_exercises += 1
        
        return total_score / total_exercises if total_exercises > 0 else 5.0

# Global instance
routine_ai_service = RoutineAIService()