"""
Initialize database and create admin user
"""
import asyncio
from app.core.database import engine, Base, AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def init():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create admin user
    async with AsyncSessionLocal() as session:
        # Check if admin exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            admin = User(
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                name="Admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("Admin user created:")
            print("  Email: admin@example.com")
            print("  Password: admin123")
        else:
            print("Admin user already exists")

    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init())
