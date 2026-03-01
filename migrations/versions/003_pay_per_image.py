"""Add pay-per-image model fields

Revision ID: 003_pay_per_image
Revises: 002_oauth
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_pay_per_image'
down_revision = '002_oauth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields to users table
    op.add_column('users', sa.Column('total_images_generated', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('paid_images_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Add new fields to invoices table
    op.add_column('invoices', sa.Column('paypal_order_id', sa.String(length=100), nullable=True))
    op.add_column('invoices', sa.Column('paypal_capture_id', sa.String(length=100), nullable=True))
    op.add_column('invoices', sa.Column('item_type', sa.String(length=50), nullable=False, server_default='image_generation'))
    op.add_column('invoices', sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'))
    
    # Create unique constraints for new PayPal IDs
    op.create_unique_constraint('uq_invoices_paypal_order_id', 'invoices', ['paypal_order_id'])
    op.create_unique_constraint('uq_invoices_paypal_capture_id', 'invoices', ['paypal_capture_id'])


def downgrade() -> None:
    # Drop unique constraints
    op.drop_constraint('uq_invoices_paypal_capture_id', 'invoices', type_='unique')
    op.drop_constraint('uq_invoices_paypal_order_id', 'invoices', type_='unique')
    
    # Drop new columns from invoices table
    op.drop_column('invoices', 'quantity')
    op.drop_column('invoices', 'item_type')
    op.drop_column('invoices', 'paypal_capture_id')
    op.drop_column('invoices', 'paypal_order_id')
    
    # Drop new columns from users table
    op.drop_column('users', 'paid_images_count')
    op.drop_column('users', 'total_images_generated')
