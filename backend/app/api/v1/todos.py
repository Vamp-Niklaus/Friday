from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import get_current_user
from app.database.repositories.task_repository import TaskRepository
from app.schemas.todos import TaskGroupResponse, TaskResponse, TaskUpdateRequest


router = APIRouter()


@router.get("/")
def todo_status() -> dict[str, str]:
    return {"status": "todo api ready"}


def group_tasks_by_todo_at(tasks: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = {}

    for task in tasks:
        grouped.setdefault(task["todo_at"], []).append(task)

    return {
        "groups": [
            {"date": todo_at, "tasks": grouped[todo_at]}
            for todo_at in sorted(grouped)
        ]
    }


@router.get("/open", response_model=TaskGroupResponse)
def list_open_todos(user_id: str = Depends(get_current_user)) -> dict:
    tasks = TaskRepository().list_by_status("open", user_id)
    return group_tasks_by_todo_at(tasks)


@router.get("/history", response_model=TaskGroupResponse)
def list_completed_todos(user_id: str = Depends(get_current_user)) -> dict:
    tasks = TaskRepository().list_by_status("completed", user_id)
    return group_tasks_by_todo_at(tasks)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, user_id: str = Depends(get_current_user)) -> dict:
    task = TaskRepository().get_by_id(task_id, user_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task_title(
    task_id: str, 
    payload: TaskUpdateRequest, 
    user_id: str = Depends(get_current_user)
) -> dict:
    title = payload.title.strip()

    if not title:
        raise HTTPException(status_code=400, detail="Task title cannot be empty.")

    task = TaskRepository().update_title(task_id, title, user_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: str, user_id: str = Depends(get_current_user)) -> dict:
    repository = TaskRepository()
    existing_task = repository.get_by_id(task_id, user_id)

    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if existing_task["status"] == "completed":
        return existing_task

    task = repository.mark_completed(task_id, user_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return task

@router.delete("/{task_id}")
def delete_task(task_id: str, user_id: str = Depends(get_current_user)) -> dict:
    repository = TaskRepository()
    success = repository.delete_task(task_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already deleted.")
    return {"status": "success"}
