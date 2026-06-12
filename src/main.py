from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from src.services.recommender import Recommender
import uuid

app = FastAPI()

class MatchResponse(BaseModel):
    title: str
    authors: list[str]
    matchScore: float    

jobs = {} #Temporary in-memory store —> holds results while they're being processed

@app.post("/upload_csv")
async def upload_csv(file: UploadFile, background_tasks: BackgroundTasks):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")
    try:
        fileContent = await file.read()
        fileContent = fileContent.decode("utf-8")
        job_id = str(uuid.uuid4())  # generates a unique ID e.g. "a3f4c2d1-..."
        jobs[job_id] = {"status": "processing", "results": None}
        background_tasks.add_task(run_recommender, job_id, fileContent)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    return {"job_id": job_id, "status": "processing"}
    
def run_recommender(job_id: str, fileContent: str):
    try:
        recommender = Recommender(fileContent)
        matches = recommender.recommend()
        jobs[job_id] = {"status": "done", "results": matches}
    except Exception as e:
        jobs[job_id] = {"status": "failed", "error": str(e)}

@app.get("/results/{job_id}", response_model=list[MatchResponse])
async def get_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=202, detail="Still processing, try again soon")
    
    if job["status"] == "failed":
        raise HTTPException(status_code=500, detail=job["error"])
    
    return job["results"]