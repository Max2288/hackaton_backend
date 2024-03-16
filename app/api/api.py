from fastapi import APIRouter

from app.api import auth, user
from app.api.log_route import LogRoute

router = APIRouter(route_class=LogRoute)

router.include_router(user.router, prefix="/user", tags=["USER API"])
router.include_router(auth.router, prefix="/token", tags=["AUTH API"])
