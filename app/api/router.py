from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.answers import router as answers_router
from app.api.routes.browse import router as browse_router
from app.api.routes.comments import router as comments_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.favorites import router as favorites_router
from app.api.routes.media import router as media_router
from app.api.routes.meta import router as meta_router
from app.api.routes.questions import router as questions_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.search import router as search_router
from app.api.routes.users import router as users_router


api_router = APIRouter(prefix="/api")
api_router.include_router(admin_router)
api_router.include_router(answers_router)
api_router.include_router(browse_router)
api_router.include_router(comments_router)
api_router.include_router(feedback_router)
api_router.include_router(favorites_router)
api_router.include_router(media_router)
api_router.include_router(meta_router)
api_router.include_router(questions_router)
api_router.include_router(recommendations_router)
api_router.include_router(search_router)
api_router.include_router(users_router)
