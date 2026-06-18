from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from models import create_db_and_tables, engine, AIFeatureFlag, QualityEvaluation
from evaluator import evaluate_ai_response
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from models import create_db_and_tables, engine, AIFeatureFlag, QualityEvaluation

# Dependency to open a database session for our routes
def get_session():
    with Session(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up: Creating database tables if they don't exist...")
    create_db_and_tables()
    yield
    print("Shutting down...")

app = FastAPI(title="AI Feature Flag API", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "healthy", "postgres": "connected"}

# --- FLAG ENDPOINTS ---

@app.post("/flags/", response_model=AIFeatureFlag)
def create_flag(flag: AIFeatureFlag, session: Session = Depends(get_session)):
    """Create a new AI Feature Flag."""
    existing_flag = session.exec(select(AIFeatureFlag).where(AIFeatureFlag.name == flag.name)).first()
    if existing_flag:
        raise HTTPException(status_code=400, detail="Flag with this name already exists")
    
    session.add(flag)
    session.commit()
    session.refresh(flag)
    return flag

@app.get("/flags/", response_model=list[AIFeatureFlag])
def list_flags(session: Session = Depends(get_session)):
    """Get all AI Feature Flags."""
    flags = session.exec(select(AIFeatureFlag)).all()
    return flags

# --- EVALUATION ENDPOINTS ---

@app.get("/evaluations/", response_model=list[QualityEvaluation])
def list_evaluations(session: Session = Depends(get_session)):
    """Test endpoint to verify the QualityEvaluation table exists."""
    evals = session.exec(select(QualityEvaluation)).all()
    return evals

# --- BACKGROUND WORKER TASK ---

def background_evaluation_task(evaluation_id: int):
    """Runs in the background, grades the response, and triggers rollback if needed."""
    with Session(engine) as session:
        # 1. Fetch the pending evaluation
        evaluation = session.get(QualityEvaluation, evaluation_id)
        if not evaluation:
            return
        
        # 2. Run the LLM Judge
        result = evaluate_ai_response(evaluation.user_input, evaluation.ai_response)
        evaluation.quality_score = result["score"]
        evaluation.evaluator_reasoning = result["reasoning"]
        session.add(evaluation)
        session.commit()
        print(f"💾 Saved Evaluation {evaluation_id} with score {result['score']}")

        # 3. THE KILL SWITCH: Check if we need to auto-rollback
        if evaluation.variant_served == "experimental":
            flag = session.exec(select(AIFeatureFlag).where(AIFeatureFlag.name == evaluation.flag_name)).first()
            
            # Only check if the flag hasn't already been rolled back
            if flag and not flag.rollback_triggered:
                # Get the last 3 experimental evaluations to calculate a quick rolling average
                recent_evals = session.exec(
                    select(QualityEvaluation)
                    .where(QualityEvaluation.flag_name == flag.name)
                    .where(QualityEvaluation.variant_served == "experimental")
                    .where(QualityEvaluation.quality_score > 0) # Only count graded ones
                    .order_by(QualityEvaluation.id.desc())
                    .limit(3)
                ).all()
                
                # Wait until we have at least 2 grades before jumping to conclusions
                if len(recent_evals) >= 2:
                    avg_score = sum(e.quality_score for e in recent_evals) / len(recent_evals)
                    print(f"📊 Rolling Average Quality: {avg_score:.2f} / Threshold: {flag.minimum_quality_score}")
                    
                    if avg_score < flag.minimum_quality_score:
                        print(f"🚨 CRITICAL: Quality dropped below {flag.minimum_quality_score}!")
                        print(f"🚨 INITIATING AUTOMATIC ROLLBACK FOR '{flag.name}'...")
                        flag.rollout_percentage = 0
                        flag.rollback_triggered = True
                        session.add(flag)
                        session.commit()
                        print(f"🛑 Rollback complete. Flag '{flag.name}' locked at 0%.")
# --- INTERACTION LOGGING ENDPOINT ---

from pydantic import BaseModel

class InteractionLog(BaseModel):
    flag_name: str
    user_id: str
    variant_served: str
    user_input: str
    ai_response: str

@app.post("/log_interaction/")
def log_interaction(log: InteractionLog, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """SDK calls this after generating an AI response to trigger a quality check."""
    
    # 1. Save the initial interaction to the database with a score of 0.0
    new_eval = QualityEvaluation(
        flag_name=log.flag_name,
        user_id=log.user_id,
        variant_served=log.variant_served,
        user_input=log.user_input,
        ai_response=log.ai_response
    )
    session.add(new_eval)
    session.commit()
    session.refresh(new_eval)
    
    # 2. Trigger the background grading task
    background_tasks.add_task(background_evaluation_task, new_eval.id)
    
    return {"status": "Evaluation queued", "evaluation_id": new_eval.id}