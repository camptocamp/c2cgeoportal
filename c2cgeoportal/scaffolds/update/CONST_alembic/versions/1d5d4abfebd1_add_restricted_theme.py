"""Add restricted theme

Revision ID: 1d5d4abfebd1
Revises: 54645a535ad6
Create Date: 2014-11-25 16:51:51.567026

"""

# revision identifiers, used by Alembic.
revision = '1d5d4abfebd1'
down_revision = '54645a535ad6'

from alembic import op, context
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, Boolean


def upgrade():
    schema = context.get_context().config.get_main_option('schema')

    engine = op.get_bind().engine
    if op.get_context().dialect.has_table(
        engine, 'restricted_role_theme', schema=schema
    ):  # pragma: nocover
        return

    op.add_column('theme', Column(
        'public', Boolean, server_default='t', nullable=False
    ), schema=schema)
    op.create_table(
        'restricted_role_theme',
        Column(
            'role_id', Integer, ForeignKey(schema + '.role.id'), primary_key=True
        ),
        Column(
            'theme_id', Integer, ForeignKey(schema + '.theme.id'), primary_key=True
        ),
        schema=schema
    )


def downgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.drop_table('restricted_role_theme', schema=schema)
    op.drop_column('theme', 'public', schema=schema)
