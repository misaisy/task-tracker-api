"""switch_to_uuid

Revision ID: b8733071e145
Revises: 86b236863f45
Create Date: 2026-06-21 21:49:34.547543

"""
from collections.abc import Sequence

from alembic import op

revision: str = 'b8733071e145'
down_revision: str | Sequence[str] | None = '86b236863f45'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint('comments_task_id_fkey', 'comments', type_='foreignkey')
    op.drop_constraint('comments_author_id_fkey', 'comments', type_='foreignkey')
    op.drop_constraint('task_history_task_id_fkey', 'task_history', type_='foreignkey')
    op.drop_constraint('tasks_owner_id_fkey', 'tasks', type_='foreignkey')
    op.drop_constraint('tasks_assignee_id_fkey', 'tasks', type_='foreignkey')

    for table in ('users', 'tasks', 'comments', 'task_history'):
        op.execute(f'ALTER TABLE {table} ALTER COLUMN id DROP IDENTITY IF EXISTS')
        op.execute(f'ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT')

    for table in ('users', 'tasks', 'comments', 'task_history'):
        op.execute(f'ALTER TABLE {table} ALTER COLUMN id TYPE UUID USING gen_random_uuid()')

    for col in ('owner_id', 'assignee_id'):
        op.execute(f'ALTER TABLE tasks ALTER COLUMN {col} TYPE UUID USING NULL')
    for col in ('task_id', 'author_id'):
        op.execute(f'ALTER TABLE comments ALTER COLUMN {col} TYPE UUID USING NULL')
    op.execute('ALTER TABLE task_history ALTER COLUMN task_id TYPE UUID USING NULL')

    op.create_foreign_key('tasks_owner_id_fkey', 'tasks', 'users', ['owner_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('tasks_assignee_id_fkey', 'tasks', 'users', ['assignee_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('comments_task_id_fkey', 'comments', 'tasks', ['task_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('comments_author_id_fkey', 'comments', 'users', ['author_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('task_history_task_id_fkey', 'task_history', 'tasks', ['task_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    pass
