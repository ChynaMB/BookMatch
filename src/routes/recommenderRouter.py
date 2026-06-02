from fastapi import APIRouter, UploadFile, File
from src.services.recommender import Recommender
router = APIRouter(prefix="/recommendations")

@router.post("/")
def upload_csv(file: UploadFile = File(...)):
    df = load_and_validate_csv(file)
    generate_matches(df)
    return {"message": "CSV processed successfully"}

@router.get("/")
def return_matches():
    return get_matches()