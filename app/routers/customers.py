from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, or_, select

from app.db import get_session
from app.models import Customer, CustomerCreate, CustomerPublic, CustomerUpdate
from app.security import get_password_hash, oauth2_scheme

router = APIRouter(
    prefix="/customers", 
    tags=["Customers"],
    dependencies=[Depends(oauth2_scheme)] 
)

@router.post("/", response_model=CustomerPublic, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    session: Annotated[Session, Depends(get_session)],
):
    
    statement = select(Customer).where(
        or_(
            Customer.email == customer_in.email,
            Customer.document_number == customer_in.document_number
        )
    )
    existing_customer = session.exec(statement).first()
    
    if existing_customer:
        if existing_customer.email == customer_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists."
            )
        if existing_customer.document_number == customer_in.document_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this document number already exists."
            )

    # Si todo está libre, procedemos a crearlo
    hashed_password = get_password_hash(customer_in.password)
    customer_data = customer_in.model_dump(exclude={"password"})
    db_customer = Customer(**customer_data, hashed_password=hashed_password)

    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)

    return db_customer


@router.get("/", response_model=list[CustomerPublic])
def get_customers(
    session: Annotated[Session, Depends(get_session)],
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,  
):
    statement = select(Customer).where(Customer.is_active == is_active).offset(skip).limit(limit)
    return session.exec(statement).all()


@router.get("/{customer_id}", response_model=CustomerPublic)
def get_customer(
    customer_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Customer not found"
        )
    return customer

@router.patch("/{customer_id}", response_model=CustomerPublic)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    session: Annotated[Session, Depends(get_session)],
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Customer not found"
        )
    
    conditions = []
    if customer_in.email:
        conditions.append(Customer.email == customer_in.email)
    if customer_in.document_number:
        conditions.append(Customer.document_number == customer_in.document_number)
        
    if conditions:
        statement = select(Customer).where(or_(*conditions), Customer.id != customer_id)
        existing_customer = session.exec(statement).first()
        
        if existing_customer:
            if existing_customer.email == customer_in.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The email is already in use by another customer."
                )
            if existing_customer.document_number == customer_in.document_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The document number is already in use by another customer."
                )

    customer_data = customer_in.model_dump(exclude_unset=True)
    for key, value in customer_data.items():
        setattr(customer, key, value)
    
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    return customer

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    session: Annotated[Session, Depends(get_session)],
):

    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Customer not found"
        )
        
    customer.is_active = False
    customer.deleted_at = datetime.now(timezone.utc)
    
    session.add(customer)
    session.commit()