from fastapi import APIRouter

from app.api.v1 import chat, notifications, todos, cron, problems, user


router = APIRouter()
router.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
router.include_router(
    notifications.router,
    prefix="/v1/notifications",
    tags=["notifications"],
)
router.include_router(todos.router, prefix="/v1/todos", tags=["todos"])
router.include_router(cron.router, prefix="/v1/cron", tags=["cron"])
router.include_router(problems.router, prefix="/v1/problems", tags=["problems"])
router.include_router(user.router, prefix="/v1/user", tags=["user"])
