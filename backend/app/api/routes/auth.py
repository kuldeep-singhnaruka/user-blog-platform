"""Identity routes. JSON login is for the web client. The form token route is the OAuth2 password grant used by Swagger."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_tenant_blog
from app.models import Blog, User
from app.schemas import BlogOut, BlogUpdate, LoginIn, RegisterIn, TokenResponse, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService(db).login(payload)


@router.post("/token", response_model=TokenResponse)
def oauth_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    """OAuth2 resource-owner password grant. `username` is the account email.

    This is appropriate for this first-party app. A third-party client should use
    authorization-code + PKCE instead of collecting the user's password.
    """
    return AuthService(db).login(LoginIn(email=form.username, password=form.password))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/me/blog", response_model=BlogOut)
def my_blog(user: User = Depends(get_current_user), blog: Blog = Depends(get_tenant_blog), db: Session = Depends(get_db)) -> BlogOut:
    return AuthService(db).present_blog(blog)


@router.patch("/me/blog", response_model=BlogOut)
def update_blog(
    payload: BlogUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BlogOut:
    return AuthService(db).update_blog(user, payload)
