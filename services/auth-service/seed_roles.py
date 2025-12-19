from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Role

def seed_roles():
    session = SessionLocal()

    try:
        # Desired roles
        role_names = [
            "SuperAdmin",
            "AdminManager",
            "AdminSupport",
            "VendorAdmin",
            "VendorDriver",
            "VendorManager",
            "VendorSupport",
            "IndependentDriver",
            "User",
        ]

        # Fetch existing role names
        existing_roles = session.execute(
            select(Role.name)
        ).scalars().all()

        existing_roles = set(existing_roles)

        # Insert only missing roles
        new_roles = [
            Role(name=name)
            for name in role_names
            if name not in existing_roles
        ]

        if not new_roles:
            print("All roles already exist. Seeder skipped.")
            return

        session.add_all(new_roles)
        session.commit()

        print(f"Inserted roles: {[r.name for r in new_roles]}")

    except Exception as e:
        print("Error seeding roles:", e)
        session.rollback()

    finally:
        session.close()


if __name__ == "__main__":
    seed_roles()
