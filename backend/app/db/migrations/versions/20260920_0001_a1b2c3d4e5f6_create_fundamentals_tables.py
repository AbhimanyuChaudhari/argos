"""create fundamentals tables

Revision ID: a1b2c3d4e5f6
Revises: 0e6dc52d15fc
Create Date: 2026-09-20 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '0e6dc52d15fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ------------------------------------------------------------------
    # fundamentals_facts
    # Raw XBRL values — one row per concept per period per ticker
    # Audit trail — never deleted, only upserted
    # ------------------------------------------------------------------
    op.create_table(
        'fundamentals_facts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('cik', sa.String(length=20), nullable=False),
        sa.Column('concept', sa.String(length=200), nullable=False,
                  comment='XBRL concept name e.g. us-gaap/Revenues'),
        sa.Column('label', sa.String(length=200), nullable=True,
                  comment='Human readable label from XBRL taxonomy'),
        sa.Column('value', sa.Numeric(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True,
                  comment='USD, shares, pure'),
        sa.Column('period_start', sa.Date(), nullable=True,
                  comment='Start of period — null for instant facts'),
        sa.Column('period_end', sa.Date(), nullable=False,
                  comment='End of period or instant date'),
        sa.Column('period_type', sa.String(length=10), nullable=True,
                  comment='annual or quarterly'),
        sa.Column('form', sa.String(length=20), nullable=True,
                  comment='10-K or 10-Q'),
        sa.Column('filed_at', sa.Date(), nullable=True),
        sa.Column('parsed_by', sa.String(length=20), nullable=True,
                  comment='xbrl or llm — tracks which parser extracted this'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Raw XBRL facts from SEC EDGAR — audit trail'
    )
    op.create_index('ix_fundamentals_facts_id', 'fundamentals_facts', ['id'], unique=False)
    op.create_index('ix_fundamentals_facts_ticker', 'fundamentals_facts', ['ticker'], unique=False)
    op.create_index('ix_fundamentals_facts_cik', 'fundamentals_facts', ['cik'], unique=False)
    op.create_index('ix_fundamentals_facts_concept', 'fundamentals_facts', ['concept'], unique=False)
    op.create_index('ix_fundamentals_facts_period_end', 'fundamentals_facts', ['period_end'], unique=False)
    op.create_index('ix_fundamentals_facts_period_type', 'fundamentals_facts', ['period_type'], unique=False)
    op.create_index('ix_fundamentals_facts_form', 'fundamentals_facts', ['form'], unique=False)
    op.create_index('ix_fundamentals_facts_parsed_by', 'fundamentals_facts', ['parsed_by'], unique=False)
    op.create_index(
        'uq_fundamentals_facts_ticker_concept_period',
        'fundamentals_facts',
        ['ticker', 'concept', 'period_end', 'period_type'],
        unique=True
    )

    # ------------------------------------------------------------------
    # fundamentals_summary
    # Pre-aggregated clean data — one row per ticker per period
    # Powers the API fast — no joins needed
    # ------------------------------------------------------------------
    op.create_table(
        'fundamentals_summary',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('cik', sa.String(length=20), nullable=True),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('period_type', sa.String(length=10), nullable=True,
                  comment='annual or quarterly'),
        sa.Column('form', sa.String(length=20), nullable=True),
        sa.Column('filed_at', sa.Date(), nullable=True),
        # Income statement
        sa.Column('revenue', sa.Numeric(), nullable=True),
        sa.Column('gross_profit', sa.Numeric(), nullable=True),
        sa.Column('gross_margin', sa.Numeric(), nullable=True,
                  comment='gross_profit / revenue'),
        sa.Column('operating_income', sa.Numeric(), nullable=True),
        sa.Column('operating_margin', sa.Numeric(), nullable=True,
                  comment='operating_income / revenue'),
        sa.Column('net_income', sa.Numeric(), nullable=True),
        sa.Column('net_margin', sa.Numeric(), nullable=True,
                  comment='net_income / revenue'),
        sa.Column('ebitda', sa.Numeric(), nullable=True,
                  comment='operating_income + depreciation'),
        sa.Column('ebitda_margin', sa.Numeric(), nullable=True,
                  comment='ebitda / revenue'),
        sa.Column('eps_basic', sa.Numeric(), nullable=True),
        sa.Column('eps_diluted', sa.Numeric(), nullable=True),
        sa.Column('shares_outstanding', sa.Numeric(), nullable=True),
        # Balance sheet
        sa.Column('total_assets', sa.Numeric(), nullable=True),
        sa.Column('total_liabilities', sa.Numeric(), nullable=True),
        sa.Column('total_equity', sa.Numeric(), nullable=True),
        sa.Column('cash', sa.Numeric(), nullable=True),
        sa.Column('total_debt', sa.Numeric(), nullable=True),
        sa.Column('net_debt', sa.Numeric(), nullable=True,
                  comment='total_debt - cash'),
        # Cash flow
        sa.Column('operating_cash_flow', sa.Numeric(), nullable=True),
        sa.Column('capex', sa.Numeric(), nullable=True),
        sa.Column('free_cash_flow', sa.Numeric(), nullable=True,
                  comment='operating_cash_flow - capex'),
        sa.Column('depreciation', sa.Numeric(), nullable=True),
        # Derived ratios
        sa.Column('debt_to_equity', sa.Numeric(), nullable=True),
        sa.Column('current_ratio', sa.Numeric(), nullable=True),
        sa.Column('roe', sa.Numeric(), nullable=True,
                  comment='net_income / total_equity'),
        sa.Column('roic', sa.Numeric(), nullable=True,
                  comment='operating_income / (total_assets - total_liabilities)'),
        # Meta
        sa.Column('parsed_by', sa.String(length=20), nullable=True,
                  comment='xbrl, llm, or hybrid'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Pre-aggregated fundamentals — one row per ticker per period'
    )
    op.create_index('ix_fundamentals_summary_id', 'fundamentals_summary', ['id'], unique=False)
    op.create_index('ix_fundamentals_summary_ticker', 'fundamentals_summary', ['ticker'], unique=False)
    op.create_index('ix_fundamentals_summary_cik', 'fundamentals_summary', ['cik'], unique=False)
    op.create_index('ix_fundamentals_summary_period_end', 'fundamentals_summary', ['period_end'], unique=False)
    op.create_index('ix_fundamentals_summary_period_type', 'fundamentals_summary', ['period_type'], unique=False)
    op.create_index('ix_fundamentals_summary_form', 'fundamentals_summary', ['form'], unique=False)
    op.create_index('ix_fundamentals_summary_filed_at', 'fundamentals_summary', ['filed_at'], unique=False)
    op.create_index(
        'uq_fundamentals_summary_ticker_period',
        'fundamentals_summary',
        ['ticker', 'period_end', 'period_type'],
        unique=True
    )

    # ------------------------------------------------------------------
    # fundamentals_errors
    # Dead letter queue — failed tickers logged here for manual review
    # ------------------------------------------------------------------
    op.create_table(
        'fundamentals_errors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=True),
        sa.Column('cik', sa.String(length=20), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False,
                  comment='fetch, parse, normalize, write'),
        sa.Column('error_type', sa.String(length=100), nullable=True,
                  comment='Exception class name'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True,
                  comment='Partial data at time of failure for debugging'),
        sa.Column('resolved', sa.Boolean(), nullable=False,
                  server_default=sa.text('false'),
                  comment='True once manually resolved or retried successfully'),
        sa.Column('retry_count', sa.Integer(), nullable=False,
                  server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Dead letter queue for failed fundamentals pipeline runs'
    )
    op.create_index('ix_fundamentals_errors_id', 'fundamentals_errors', ['id'], unique=False)
    op.create_index('ix_fundamentals_errors_ticker', 'fundamentals_errors', ['ticker'], unique=False)
    op.create_index('ix_fundamentals_errors_stage', 'fundamentals_errors', ['stage'], unique=False)
    op.create_index('ix_fundamentals_errors_resolved', 'fundamentals_errors', ['resolved'], unique=False)
    op.create_index('ix_fundamentals_errors_created_at', 'fundamentals_errors', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_fundamentals_errors_created_at', table_name='fundamentals_errors')
    op.drop_index('ix_fundamentals_errors_resolved', table_name='fundamentals_errors')
    op.drop_index('ix_fundamentals_errors_stage', table_name='fundamentals_errors')
    op.drop_index('ix_fundamentals_errors_ticker', table_name='fundamentals_errors')
    op.drop_index('ix_fundamentals_errors_id', table_name='fundamentals_errors')
    op.drop_table('fundamentals_errors')

    op.drop_index('uq_fundamentals_summary_ticker_period', table_name='fundamentals_summary')
    op.drop_index('ix_fundamentals_summary_filed_at', table_name='fundamentals_summary')
    op.drop_index('ix_fundamentals_summary_form', table_name='fundamentals_summary')
    op.drop_index('ix_fundamentals_summary_period_type', table_name='fundamentals_summary')
    op.drop_index('ix_fundamentals_summary_period_end', table_name='fundamentals_summary')
    op.drop_index('ix_fundamentals_summary_cik', table_name='fundamentals_summary')
    op.drop_index('ix_fundamentals_summary_ticker', table_name='fundamentals_summary')
    op.drop_index('ix_fundamentals_summary_id', table_name='fundamentals_summary')
    op.drop_table('fundamentals_summary')

    op.drop_index('uq_fundamentals_facts_ticker_concept_period', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_parsed_by', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_form', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_period_type', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_period_end', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_concept', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_cik', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_ticker', table_name='fundamentals_facts')
    op.drop_index('ix_fundamentals_facts_id', table_name='fundamentals_facts')
    op.drop_table('fundamentals_facts')