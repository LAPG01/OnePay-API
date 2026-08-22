from datetime import datetime, timezone
from enum import Enum

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


# 1. ENUMS (International Standards)
class BillingInterval(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class DocumentTypeEnum(str, Enum):
    PASSPORT = "passport"           
    NATIONAL_ID = "national_id"     
    TAX_ID = "tax_id"

class CurrencyEnum(str, Enum):
    USD = "usd"
    EUR = "eur"
    VES = "ves"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"       
    OPEN = "open"         
    PAID = "paid"         
    VOID = "void"         

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"

class SubscriptionStatus(str, Enum):
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"

class PaymentProviderEnum(str, Enum):
    STRIPE = "stripe"
    BINANCE_PAY = "binance_pay"
    PAYPAL = "paypal"
    MANUAL = "manual"
    MERCADO_PAGO = "mercado_pago"
    ZINLI = "zinli"               

# 2. BASE MODELS AND TABLES

# --- Plans (Products) ---
class PlanBase(SQLModel):
    name: str 
    price: int 
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD) 
    interval: BillingInterval = Field(default=BillingInterval.MONTH)
    interval_count: int = Field(default=1) 
    description: str | None = None
    is_active: bool = Field(default=True)

class Plan(PlanBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subscriptions: list["Subscription"] = Relationship(back_populates="plan")


# --- Customers ---
class CustomerBase(SQLModel):
    name: str = Field(default="Nombre")
    description: str | None = Field(default=None)
    email: EmailStr = Field(unique=True, index=True)  
    phone: str | None = Field(default=None, max_length=20)
    
    document_type: DocumentTypeEnum = Field(default=DocumentTypeEnum.NATIONAL_ID)
    document_number: str = Field(index=True, max_length=50)
    country: str = Field(default="US", max_length=2) 
    is_active: bool = Field(default=True)

    @field_validator("document_number")
    @classmethod
    def clean_document_number(cls, v: str) -> str:
        return v.replace(".", "").replace(" ", "").replace("-", "")

class CustomerCreate(CustomerBase):
    password: str 

class CustomerPublic(CustomerBase):
    id: int

class CustomerUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    email: EmailStr | None = None
    phone: str | None = None 
    document_type: DocumentTypeEnum | None = None
    document_number: str | None = None
    country: str | None = None

class Customer(CustomerBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    is_admin: bool = Field(default=False)
    deleted_at: datetime | None = Field(default=None) 

    subscriptions: list["Subscription"] = Relationship(back_populates="customer")
    invoices: list["Invoice"] = Relationship(back_populates="customer")


# --- Subscriptions (Billing Engine) ---
class Subscription(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="plan.id", ondelete="RESTRICT")
    customer_id: int = Field(foreign_key="customer.id", ondelete="RESTRICT")
    
    quantity: int = Field(default=1)
    status: SubscriptionStatus = Field(default=SubscriptionStatus.INCOMPLETE)
    
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_period_end: datetime | None = Field(default=None) 
    cancel_at_period_end: bool = Field(default=False)
    canceled_at: datetime | None = Field(default=None)
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = Field(default=None) 

    customer: Customer = Relationship(back_populates="subscriptions")
    plan: Plan = Relationship(back_populates="subscriptions")
    invoices: list["Invoice"] = Relationship(back_populates="subscription")

    __table_args__ = (UniqueConstraint("customer_id", "plan_id"),)

class SubscriptionCreate(SQLModel):
    customer_id: int
    plan_id: int
    quantity: int = 1
    status: SubscriptionStatus = SubscriptionStatus.INCOMPLETE


# --- Invoices ---
class Invoice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    
    customer_id: int = Field(foreign_key="customer.id", ondelete="RESTRICT")
    subscription_id: int | None = Field(default=None, foreign_key="subscription.id", ondelete="RESTRICT")
    
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD)
    amount_due: int       
    amount_paid: int = Field(default=0)     
    amount_remaining: int 
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: datetime | None = Field(default=None) 

    customer: Customer = Relationship(back_populates="invoices")
    subscription: Subscription | None = Relationship(back_populates="invoices") 
    transactions: list["Transaction"] = Relationship(back_populates="invoice")


# --- Transactions (Processed Payments) ---
class TransactionBase(SQLModel):
    amount: int
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD)
    description: str | None = None   
    
    provider: PaymentProviderEnum = Field(default=PaymentProviderEnum.STRIPE)
    provider_transaction_id: str | None = Field(default=None, index=True)
    payment_method: str | None = Field(default=None)

class TransactionCreate(TransactionBase):
    invoice_id: int 

class Transaction(TransactionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id", ondelete="RESTRICT")
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    invoice: Invoice = Relationship(back_populates="transactions")
    
# --- Users (Administrators) ---
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)