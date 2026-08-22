from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.db import SessionDep
from app.models import User
from app.security import create_access_token, verify_password

router = APIRouter(tags=["Authentication"])

@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    session: SessionDep
):

    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }