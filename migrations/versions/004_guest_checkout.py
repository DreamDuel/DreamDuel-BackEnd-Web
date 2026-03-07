"""Add guest checkout support - session_id and nullable user_id

Revision ID: 004_guest_checkout
Revises: 003_pay_per_image
Create Date: 2026-03-07 16:55:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_guest_checkout'
down_revision = '003_pay_per_image'
branch_labels = None
depends_on = None


def upgrade():
    """Add session_id to invoices and generated_images, make user_id nullable"""
    
    # Add session_id column to invoices (if not exists)
    with op.batch_alter_table('invoices') as batch_op:
        try:
            batch_op.add_column(sa.Column('session_id', sa.String(255), nullable=True))
        except Exception:
            pass  # Column already exists
    
    # Add session_id column to generated_images (if not exists)
    with op.batch_alter_table('generated_images') as batch_op:
        try:
            batch_op.add_column(sa.Column('session_id', sa.String(255), nullable=True))
        except Exception:
            pass  # Column already exists
    
    # Make user_id nullable in invoices (for guest checkout)
    with op.batch_alter_table('invoices') as batch_op:
        batch_op.alter_column('user_id',
            existing_type=postgresql.UUID(),
            nullable=True
        )
    
    # Make user_id nullable in generated_images (for guest generations)
    with op.batch_alter_table('generated_images') as batch_op:
        batch_op.alter_column('user_id',
            existing_type=postgresql.UUID(),
            nullable=True
        )
    
    # Create indexes for session_id lookups (if not exist)
    try:
        op.create_index('ix_invoices_session_id', 'invoices', ['session_id'])
    except Exception:
        pass  # Index already exists
    
    try:
        op.create_index('ix_generated_images_session_id', 'generated_images', ['session_id'])
    except Exception:
        pass  # Index already exists


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
