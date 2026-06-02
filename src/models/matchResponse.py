from pydantic import BaseModel

class MatchResponse(BaseModel):
    work_id: int
    score: float