"""update the appointment table

Revision ID: f704a106a904
Revises: 8b181a5d47f9
Create Date: 2024-03-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f704a106a904'
down_revision: Union[str, None] = '8b181a5d47f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create all enum types first
    provider_type = postgresql.ENUM('PRACTITIONER', 'PROFESSIONAL', name='providertype', create_type=True)
    appointment_type = postgresql.ENUM('REGULAR', 'MENTAL_HEALTH', 'CRISIS', 'ASSESSMENT', 'MEDICAL', 'SPECIALIST', name='appointmenttype', create_type=True)
    appointment_status = postgresql.ENUM('SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'RESCHEDULED', name='appointmentstatus', create_type=True)
    
    provider_type.create(op.get_bind())
    appointment_type.create(op.get_bind())
    appointment_status.create(op.get_bind())
    
    # Add the provider_type column as nullable first
    op.add_column('appointments', sa.Column('provider_type', sa.Enum('PRACTITIONER', 'PROFESSIONAL', name='providertype'), nullable=True))
    
    # Update existing records to have a default value
    op.execute("UPDATE appointments SET provider_type = 'PRACTITIONER' WHERE provider_type IS NULL")
    
    # Now make the column non-nullable
    op.alter_column('appointments', 'provider_type',
                    existing_type=sa.Enum('PRACTITIONER', 'PROFESSIONAL', name='providertype'),
                    nullable=False)
    
    # Add the provider_id column as nullable first
    op.add_column('appointments', sa.Column('provider_id', sa.Integer(), nullable=True))
    
    # Update existing records to have a default value (you may want to adjust this based on your data)
    op.execute("UPDATE appointments SET provider_id = 1 WHERE provider_id IS NULL")
    
    # Now make the column non-nullable
    op.alter_column('appointments', 'provider_id',
                    existing_type=sa.Integer(),
                    nullable=False)

    # Add other columns
    op.add_column('appointments', sa.Column('duration', sa.Integer(), nullable=False, server_default='30'))
    op.add_column('appointments', sa.Column('appointment_type', sa.Enum('REGULAR', 'MENTAL_HEALTH', 'CRISIS', 'ASSESSMENT', 'MEDICAL', 'SPECIALIST', name='appointmenttype'), nullable=False, server_default='REGULAR'))
    op.add_column('appointments', sa.Column('status', sa.Enum('SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'RESCHEDULED', name='appointmentstatus'), nullable=False, server_default='SCHEDULED'))
    op.add_column('appointments', sa.Column('notes', sa.String(), nullable=True))
    op.add_column('appointments', sa.Column('follow_up_required', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('appointments', sa.Column('follow_up_date', sa.DateTime(), nullable=True))
    op.add_column('appointments', sa.Column('session_summary', sa.String(), nullable=True))
    op.add_column('appointments', sa.Column('goals_discussed', sa.JSON(), nullable=True))
    op.add_column('appointments', sa.Column('homework_assigned', sa.JSON(), nullable=True))
    op.add_column('appointments', sa.Column('next_session_agenda', sa.String(), nullable=True))
    op.add_column('appointments', sa.Column('video_call_link', sa.String(), nullable=True))
    op.add_column('appointments', sa.Column('reminder_sent', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('appointments', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('appointments', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Drop the old column
    op.drop_column('appointments', 'doctor_name')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the old column
    op.add_column('appointments', sa.Column('doctor_name', sa.String(), nullable=True))
    
    # Drop the new columns
    op.drop_column('appointments', 'updated_at')
    op.drop_column('appointments', 'created_at')
    op.drop_column('appointments', 'reminder_sent')
    op.drop_column('appointments', 'video_call_link')
    op.drop_column('appointments', 'next_session_agenda')
    op.drop_column('appointments', 'homework_assigned')
    op.drop_column('appointments', 'goals_discussed')
    op.drop_column('appointments', 'session_summary')
    op.drop_column('appointments', 'follow_up_date')
    op.drop_column('appointments', 'follow_up_required')
    op.drop_column('appointments', 'notes')
    op.drop_column('appointments', 'status')
    op.drop_column('appointments', 'appointment_type')
    op.drop_column('appointments', 'duration')
    op.drop_column('appointments', 'provider_id')
    op.drop_column('appointments', 'provider_type')
    
    # Drop the enum types
    provider_type = postgresql.ENUM(name='providertype')
    appointment_type = postgresql.ENUM(name='appointmenttype')
    appointment_status = postgresql.ENUM(name='appointmentstatus')
    
    provider_type.drop(op.get_bind())
    appointment_type.drop(op.get_bind())
    appointment_status.drop(op.get_bind())
    # ### end Alembic commands ###
