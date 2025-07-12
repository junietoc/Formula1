"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2025-07-11

Esta migración inicial crea todas las tablas definidas actualmente en models.py. Usamos Base.metadata.create_all para generar el esquema completo en la base.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables using SQLAlchemy metadata."""
    # Importing here avoids Alembic loading models at import-time
    from models import Base  # pylint: disable=import-outside-toplevel

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop all tables in reverse order using SQLAlchemy metadata."""
    from models import Base  # pylint: disable=import-outside-toplevel

    bind = op.get_bind()
    # Drop all tables (this will cascade appropriately on supported DBs)
    Base.metadata.drop_all(bind=bind) 