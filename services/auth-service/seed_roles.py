from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Role

def seed_roles():
    session = SessionLocal()

    try:
        # Check if roles table is empty
        result = session.execute(select(Role)).first()

        if result:
            print("Roles already exist. Seeder skipped.")
            return

        # Insert default roles
        roles = [
            Role(name="SuperAdmin"),
            Role(name="AdminManager"),
            Role(name="AdminSupport"),
            Role(name="VendorAdmin"),
            Role(name="VendorDriver"),
            Role(name="VendorManager"),
            Role(name="VendorSupport"),
            Role(name="User"),
        ]

        session.add_all(roles)
        session.commit()
        print("Roles seeding completed.")

    except Exception as e:
        print("Error seeding roles:", e)
        session.rollback()

    finally:
        session.close()


if __name__ == "__main__":
    seed_roles()
