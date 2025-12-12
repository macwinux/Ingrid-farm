from app.database.db import Database

def get_db() -> Database:
    """Get the singleton database instance"""
    return Database.get_instance()

__all__ = ["Database", "get_db"]