from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.task import Task
from models.user import User
from schemas.base import APIResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=APIResponse[dict])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return APIResponse(
        success=True,
        data={"id": task.id, "type": task.type, "status": task.status, "result": task.result},
    )
