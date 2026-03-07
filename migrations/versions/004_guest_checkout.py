"""Add guest checkout support - session_id and nullable user_id

Revision ID: 004
Revises: 003
Create Date: 2026-03-07 16:55:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add session_id to invoices and generated_images, make user_id nullable"""
    
    # Add session_id column to invoices
    op.add_column('invoices', 
        sa.Column('session_id', sa.String(255), nullable=True, index=True)
    )
    
    # Add session_id column to generated_images
    op.add_column('generated_images', 
        sa.Column('session_id', sa.String(255), nullable=True, index=True)
    )
    
    # Make user_id nullable in invoices (for guest checkout)
    op.alter_column('invoices', 'user_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )
    
    # Make user_id nullable in generated_images (for guest generations)
    op.alter_column('generated_images', 'user_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )
    
    # Create index for session_id lookups
    op.create_index('ix_invoices_session_id', 'invoices', ['session_id'])
    op.create_index('ix_generated_images_session_id', 'generated_images', ['session_id'])


def downgrade():
    """Revert changes"""
    
    # Remove indexes
    op.drop_index('ix_generated_images_session_id', table_name='generated_images')
    op.drop_index('ix_invoices_session_id', table_name='invoices')
    
    # Make user_id NOT NULL again (this will fail if there are NULL values)
    op.alter_column('generated_images', 'user_id',
        existing_type=postgresql.UUID(),
        nullable=False
    )
    
    op.alter_column('invoices', 'user_id',
        existing_type=postgresql.UUID(),
        nullable=False
    )
    
    # Remove session_id columns
    op.drop_column('generated_images', 'session_id')
    op.drop_column('invoices', 'session_id')
