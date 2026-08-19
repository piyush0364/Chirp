import os
import sys

# Add the apps/api directory to the path so we can import chirp_api
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import bcrypt

from chirp_api.db import SessionLocal
from chirp_api.db.models import User


def migrate_passwords():
    """Wrap all non-bcrypt password hashes with bcrypt."""
    with SessionLocal() as session:
        users = session.query(User).all()
        migrated_count = 0

        for user in users:
            if not (user.password_hash.startswith("$2a$") or user.password_hash.startswith("$2b$")):
                hashed = bcrypt.hashpw(user.password_hash.encode("utf-8"), bcrypt.gensalt())
                new_hash = hashed.decode("utf-8")
                user.password_hash = new_hash
                migrated_count += 1

        session.commit()
        print(f"Successfully migrated {migrated_count} legacy password hashes.")

if __name__ == "__main__":
    migrate_passwords()
