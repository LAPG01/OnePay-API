import os
import sys

# Le decimos a Python que la raíz del proyecto también existe
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session

from app.db import engine
from app.models import User
from app.security import get_password_hash


def create_first_admin():
    with Session(engine) as session:
        admin = User(
            email="leo@onepay.com",
            hashed_password=get_password_hash("admin123"), 
            is_superuser=True
        )
        session.add(admin)
        session.commit()
        print("✅ ¡Súper-Administrador creado con éxito!")

if __name__ == "__main__":
    create_first_admin()