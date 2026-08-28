from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import Plan, PlanCreate, PlanPublic, PlanUpdate
from app.security import oauth2_scheme

# 🔒 Protegemos la ruta: Solo admins con JWT pueden gestionar planes
router = APIRouter(
    prefix="/plans",
    tags=["Plans"],
    dependencies=[Depends(oauth2_scheme)]
)

@router.post("/", response_model=PlanPublic, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan_in: PlanCreate,
    session: Annotated[Session, Depends(get_session)],
):

    existing_plan = session.exec(select(Plan).where(Plan.name == plan_in.name)).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A plan with this name already exists."
        )

    db_plan = Plan.model_validate(plan_in)
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)

    return db_plan


@router.get("/", response_model=list[PlanPublic])
def get_plans(
    session: Annotated[Session, Depends(get_session)],
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,
):
    statement = select(Plan).where(Plan.is_active == is_active).offset(skip).limit(limit)
    return session.exec(statement).all()

@router.get("/{plan_id}", response_model=PlanPublic)
def get_plan(
    plan_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    plan = session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Plan not found"
        )
    return plan

@router.patch("/{plan_id}", response_model=PlanPublic)
def update_plan(
    plan_id: int,
    plan_in: PlanUpdate,
    session: Annotated[Session, Depends(get_session)],
):
    plan = session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    if plan_in.name is not None and plan_in.name != plan.name:
        existing_plan = session.exec(select(Plan).where(Plan.name == plan_in.name)).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A plan with this name already exists."
            )

    update_data = plan_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    plan = session.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    plan.is_active = False
    session.add(plan)
    session.commit()
    
    