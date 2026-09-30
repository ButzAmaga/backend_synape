"""
Purpose: Data access layer for category entities in SQLite.
Flow:
      1. Query category by ID.
Inputs: AsyncSession database handle.
Outputs: CategoryModel entity or None.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import CategoryModel


class CategoryRepository:
    """
    Purpose: Encapsulates database operations for categories.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: str) -> Optional[CategoryModel]:
        """
        Purpose: Fetches category record by unique ID.
        Flow:
              1. Execute SELECT query on categories table matching category_id.
        Inputs: category_id (str).
        Outputs: CategoryModel instance or None.
        """
        result = await self.db.execute(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )
        return result.scalar_one_or_none()