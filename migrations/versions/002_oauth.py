"""add oauth fields to user

Revision ID: 002_oauth
Revises: 001_initial
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_oauth'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Hacer password_hash nullable (para usuarios OAuth)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=True)
    
    # Agregar nuevos campos
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('oauth_provider', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(255), nullable=True))
    
    # Crear índice para búsquedas de OAuth
    op.create_index('ix_users_oauth_provider_id', 'users', ['oauth_provider', 'oauth_id'])


def downgrade() -> None:
    # Remover índice
    op.drop_index('ix_users_oauth_provider_id', table_name='users')
    
    # Remover columnas
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'full_name')
    
    # Revertir password_hash a NOT NULL
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=False)
