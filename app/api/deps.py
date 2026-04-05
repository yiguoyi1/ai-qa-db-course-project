from app.services.comment_service import CommentService
from app.services.answer_service import AnswerService
from app.services.browse_service import BrowseService
from app.services.feedback_service import FeedbackService
from app.services.favorite_service import FavoriteService
from app.services.meta_service import MetaService
from app.services.question_service import QuestionService
from app.services.recommendation_service import RecommendationService
from app.services.search_service import SearchService


def get_question_service() -> QuestionService:
    return QuestionService()


def get_answer_service() -> AnswerService:
    return AnswerService()


def get_comment_service() -> CommentService:
    return CommentService()


def get_meta_service() -> MetaService:
    return MetaService()


def get_browse_service() -> BrowseService:
    return BrowseService()


def get_favorite_service() -> FavoriteService:
    return FavoriteService()


def get_feedback_service() -> FeedbackService:
    return FeedbackService()


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


def get_search_service() -> SearchService:
    return SearchService()
