"""Add frequency and priority enum

Revision ID: f304c64db8e8
Revises: faf9233facf3
Create Date: 2024-03-19 12:34:56.789012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f304c64db8e8'
down_revision: Union[str, None] = 'faf9233facf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE taskfrequency AS ENUM ('daily', 'weekly', 'biweekly', 'monthly', 'custom')")
    op.execute("CREATE TYPE taskpriority AS ENUM ('high', 'medium', 'low')")
    
    # Convert existing data to lowercase and ensure valid values
    op.execute("""
        UPDATE care_plans 
        SET frequency = LOWER(frequency),
            priority = LOWER(priority)
        WHERE frequency IS NOT NULL 
           OR priority IS NOT NULL
    """)
    
    # Alter columns with USING clause
    op.execute('ALTER TABLE care_plans ALTER COLUMN frequency TYPE taskfrequency USING frequency::taskfrequency')
    op.execute('ALTER TABLE care_plans ALTER COLUMN priority TYPE taskpriority USING priority::taskpriority')
    
    # Convert timestamp columns to timezone-aware
    op.execute('ALTER TABLE care_plans ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE care_plans ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE care_plans ALTER COLUMN start_date TYPE TIMESTAMP WITH TIME ZONE USING start_date AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE care_plans ALTER COLUMN end_date TYPE TIMESTAMP WITH TIME ZONE USING end_date AT TIME ZONE \'UTC\'')


def downgrade() -> None:
    # Convert timestamp columns back to timezone-naive
    op.execute('ALTER TABLE care_plans ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE care_plans ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE care_plans ALTER COLUMN start_date TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE care_plans ALTER COLUMN end_date TYPE TIMESTAMP WITHOUT TIME ZONE')
    
    # Convert back to VARCHAR
    op.execute('ALTER TABLE care_plans ALTER COLUMN frequency TYPE VARCHAR USING frequency::VARCHAR')
    op.execute('ALTER TABLE care_plans ALTER COLUMN priority TYPE VARCHAR USING priority::VARCHAR')
    
    # Drop enum types
    op.execute('DROP TYPE taskfrequency')
    op.execute('DROP TYPE taskpriority')
