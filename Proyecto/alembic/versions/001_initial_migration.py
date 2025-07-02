"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE user_role_enum AS ENUM ('usuario', 'operador', 'admin')")
    op.execute("CREATE TYPE user_affiliation_enum AS ENUM ('estudiante', 'docente', 'administrativo')")
    op.execute("CREATE TYPE bike_status_enum AS ENUM ('disponible', 'prestada', 'mantenimiento', 'retirada')")
    op.execute("CREATE TYPE loan_status_enum AS ENUM ('abierto', 'cerrado', 'tardio', 'perdido')")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cedula', sa.String(length=15), nullable=False),
        sa.Column('carnet', sa.String(length=20), nullable=False),
        sa.Column('full_name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('affiliation', postgresql.ENUM('estudiante', 'docente', 'administrativo', name='user_affiliation_enum'), nullable=True),
        sa.Column('role', postgresql.ENUM('usuario', 'operador', 'admin', name='user_role_enum'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cedula'),
        sa.UniqueConstraint('carnet')
    )
    
    # Create bicycles table
    op.create_table('bicycles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('serial_number', sa.String(length=40), nullable=False),
        sa.Column('bike_code', sa.String(length=10), nullable=False),
        sa.Column('status', postgresql.ENUM('disponible', 'prestada', 'mantenimiento', 'retirada', name='bike_status_enum'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bike_code'),
        sa.UniqueConstraint('serial_number')
    )
    
    # Create stations table
    op.create_table('stations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Create loans table
    op.create_table('loans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bike_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('station_out_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('time_out', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('station_in_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('time_in', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', postgresql.ENUM('abierto', 'cerrado', 'tardio', 'perdido', name='loan_status_enum'), nullable=True),
        sa.ForeignKeyConstraint(['bike_id'], ['bicycles.id'], ),
        sa.ForeignKeyConstraint(['station_in_id'], ['stations.id'], ),
        sa.ForeignKeyConstraint(['station_out_id'], ['stations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('loans')
    op.drop_table('stations')
    op.drop_table('bicycles')
    op.drop_table('users')
    op.execute("DROP TYPE loan_status_enum")
    op.execute("DROP TYPE bike_status_enum")
    op.execute("DROP TYPE user_affiliation_enum")
    op.execute("DROP TYPE user_role_enum") 