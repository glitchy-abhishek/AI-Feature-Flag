from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Column, JSON
from datetime import datetime

class AIFeatureFlag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    is_active: bool = Field(default=True)

class QualityEvaluation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    flag_name: str = Field(index=True)
    user_id: str
    variant_served: str  # "baseline" or "experimental"
    
    # The actual text involved
    user_input: str
    ai_response: str
    
    # The grade (e.g., 1 to 5)
    quality_score: float = Field(default=0.0)
    evaluator_reasoning: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Rollout mechanics
    rollout_percentage: int = Field(default=0, ge=0, le=100)
    
    # Configurations stored as JSON
    baseline_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    experimental_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Quality & Rollback thresholds
    minimum_quality_score: float = Field(default=3.0)  # e.g., 1-5 LLM judge score
    rollback_triggered: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Database connection setup
from sqlmodel import create_engine
# Connect to the local PostgreSQL database we spun up with Docker
DATABASE_URL = "postgresql://admin:password@localhost:5432/aiflags"
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)