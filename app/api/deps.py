from app.services.answer_service import AnswerService
from app.services.admin_service import AdminService
from app.services.browse_service import BrowseService
from app.services.chat_service import ChatService
from app.services.comment_service import CommentService
from app.services.feedback_service import FeedbackService
from app.services.favorite_service import FavoriteService
from app.services.media_service import MediaService
from app.services.meta_service import MetaService
from app.services.question_service import QuestionService
from app.services.recommendation_service import RecommendationService
from app.services.search_service import SearchService
from app.services.user_center_service import UserCenterService


def get_question_service() -> QuestionService:
    return QuestionService()


def get_admin_service() -> AdminService:
    return AdminService()


def get_answer_service() -> AnswerService:
    return AnswerService()


def get_comment_service() -> CommentService:
    return CommentService()


def get_chat_service() -> ChatService:
    return ChatService()


def get_meta_service() -> MetaService:
    return MetaService()


def get_browse_service() -> BrowseService:
    return BrowseService()


def get_favorite_service() -> FavoriteService:
    return FavoriteService()


def get_media_service() -> MediaService:
    return MediaService()


def get_feedback_service() -> FeedbackService:
    return FeedbackService()


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


def get_search_service() -> SearchService:
    return SearchService()


def get_user_center_service() -> UserCenterService:
    return UserCenterService()
