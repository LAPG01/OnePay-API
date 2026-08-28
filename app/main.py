import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.db import create_all_tables
from app.routers import auth, customers, plans  #, invoices,subscriptions, transactions

#Membership Management System.

app = FastAPI(lifespan=create_all_tables, title="OnePay API", description="Membership and Recurring Payments API", version="1.0.0")

# --- MIDDLEWARES ---

origins = [
    "http://localhost:3000",     
    "http://localhost:5173",      
    "http://127.0.0.1:3000",   
    # TODO: Add production domains
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         
    allow_credentials=True,      
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], 
    allow_headers=["Authorization", "Content-Type"], 
)

@app.middleware("http") 
async def log_request_headers(request: Request, call_next):
    print("--- Request Headers ---")
    for header, value in request.headers.items():
        print(f"{header}: {value}")
    print("-----------------------")

    response = await call_next(request) 
    return response

# --- ROUTERS ---

@app.get("/", tags=['home'])
async def root (): 
            return {"message": "Welcome to OnePay API. Visit /docs for API documentation."}
        
# --- RUTAS ---

app.include_router(customers.router)
app.include_router(auth.router)
app.include_router(plans.router)
#app.include_router(invoices.router)
#app.include_router(transactions.router)
#app.include_router(plans.router)
#app.include_router(subscriptions.router)
