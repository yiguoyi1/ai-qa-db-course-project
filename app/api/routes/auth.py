from fastapi import APIRouter, Depends
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import AuthService

# 建立一个专属的路由器，前缀都带上 /api/auth
router = APIRouter(prefix="/api/auth", tags=["认证大门"])

# 依赖注入：告诉 FastAPI，每次有客人的时候，都叫一个“安全主管”过来
def get_auth_service():
    return AuthService()

@router.post("/register")
def register(payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)):
    # 直接把前台收到的表格（payload）交给安全主管去处理
    return auth_service.register(payload)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    # 登录成功后，返回那张印好的 JWT 房卡
    return auth_service.login(payload)