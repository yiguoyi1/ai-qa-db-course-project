from pydantic import BaseModel, Field

# 注册时的进件标准
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码至少6位")
    nickname: str | None = Field(None, description="社区昵称，可选")

# 登录时的进件标准
class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

# 给前端发“通行证”的标准
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str
