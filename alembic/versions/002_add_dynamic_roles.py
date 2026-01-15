"""add dynamic roles

Revision ID: 002
Revises: 001_initial
Create Date: 2026-01-14 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Создаём таблицу project_roles
    op.create_table(
        'project_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('can_manage_roles', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('can_manage_tasks', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('can_manage_members', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('can_manage_settings', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('managed_by_role_ids', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Добавляем колонку role_id в project_members
    op.add_column('project_members', sa.Column('role_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_project_members_role_id',
        'project_members',
        'project_roles',
        ['role_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Удаляем foreign key и колонку role_id
    op.drop_constraint('fk_project_members_role_id', 'project_members', type_='foreignkey')
    op.drop_column('project_members', 'role_id')
    
    # Удаляем таблицу project_roles
    op.drop_table('project_roles')
