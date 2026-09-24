from fastapi import APIRouter
from pydantic import BaseModel
import subprocess
import os

router = APIRouter(prefix="/migration", tags=["migration"])

class MigrationResponse(BaseModel):
    status: str
    output: str

@router.get("/run-production-seed", response_model=MigrationResponse)
async def run_production_seed():
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'migrate_production.py')
        result = subprocess.run(["python", script_path], capture_output=True, text=True)
        return {"status": "success" if result.returncode == 0 else "error", "output": result.stdout + result.stderr}
    except Exception as e:
        return {"status": "error", "output": str(e)}
