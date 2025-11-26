"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=False),
        sa.Column('last_name', sa.String(255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('users.telegram_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        # Настройки напоминаний
        sa.Column('reminders_enabled', sa.Boolean(), default=True),
        sa.Column('reminder_hour', sa.Integer(), default=9),
        sa.Column('reminder_minute', sa.Integer(), default=0),
        sa.Column('reminder_days_before', sa.Integer(), default=3),
    )
    
    # Project members table
    op.create_table(
        'project_members',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), default='member'),
        sa.Column('joined_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'user_id', name='unique_project_user'),
    )
    
    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('users.telegram_id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    
    # Task assignees table
    op.create_table(
        'task_assignees',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('task_id', 'user_id', name='unique_task_user'),
    )
    
    # Create indexes
    op.create_index('idx_users_telegram_id', 'users', ['telegram_id'])
    op.create_index('idx_projects_is_active', 'projects', ['is_active'])
    op.create_index('idx_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_deadline', 'tasks', ['deadline'])


def downgrade() -> None:
    op.drop_index('idx_tasks_deadline')
    op.drop_index('idx_tasks_status')
    op.drop_index('idx_tasks_project_id')
    op.drop_index('idx_projects_is_active')
    op.drop_index('idx_users_telegram_id')
    
    op.drop_table('task_assignees')
    op.drop_table('tasks')
    op.drop_table('project_members')
    op.drop_table('projects')
    op.drop_table('users')

