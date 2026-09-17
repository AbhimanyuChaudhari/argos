import json
import asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class DatabaseWriter:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def write_filings(self, records: list[dict]) -> dict:
        inserted = 0
        skipped = 0
        failed = 0

        for record in records:
            try:
                accession = record.get("accession_number")
                if accession:
                    existing = await self.session.execute(
                        text(
                            "SELECT id FROM government_filings "
                            "WHERE accession_number = :accession"
                        ),
                        {"accession": accession},
                    )
                    if existing.scalar_one_or_none():
                        skipped += 1
                        continue

                await self.session.execute(
                    text("""
                        INSERT INTO government_filings (
                            title, filing_type, source, status,
                            country, region, filed_at, url,
                            description, cik, accession_number,
                            company_name, ticker, period_of_report,
                            is_amendment, items, raw_data,
                            created_at, updated_at
                        ) VALUES (
                            :title, :filing_type, :source, :status,
                            :country, :region, :filed_at, :url,
                            :description, :cik, :accession_number,
                            :company_name, :ticker, :period_of_report,
                            :is_amendment,
                            CAST(:items AS jsonb),
                            CAST(:raw_data AS jsonb),
                            NOW(), NOW()
                        )
                    """),
                    {
                        "title": record.get("title", ""),
                        "filing_type": record.get("filing_type", ""),
                        "source": record.get("source", "sec_edgar"),
                        "status": record.get("status", "completed"),
                        "country": record.get("country", "US"),
                        "region": record.get("region", "AMER"),
                        "filed_at": record.get("filed_at"),
                        "url": record.get("url"),
                        "description": record.get("description"),
                        "cik": record.get("cik"),
                        "accession_number": record.get("accession_number"),
                        "company_name": record.get("company_name"),
                        "ticker": record.get("ticker"),
                        "period_of_report": record.get("period_of_report"),
                        "is_amendment": record.get("is_amendment", False),
                        "items": json.dumps(record.get("items")) if record.get("items") else "null",
                        "raw_data": json.dumps(record.get("raw_data")) if record.get("raw_data") else "{}",
                    },
                )
                inserted += 1

            except Exception as e:
                failed += 1
                await self.session.rollback()
                accession_num = record.get("accession_number")
                logger.error(
                    f"Failed to insert filing {accession_num}: {e}"
                )

        await self.session.commit()
        logger.info(
            f"Filings: inserted={inserted} "
            f"skipped={skipped} failed={failed}"
        )
        return {
            "inserted": inserted,
            "skipped": skipped,
            "failed": failed,
        }

    async def write_bills(self, records: list[dict]) -> dict:
        inserted = 0
        skipped = 0
        failed = 0

        for record in records:
            try:
                existing = await self.session.execute(
                    text(
                        "SELECT id FROM government_bills "
                        "WHERE bill_number = :bill_number "
                        "AND congress_number = :congress_number"
                    ),
                    {
                        "bill_number": record.get("bill_number"),
                        "congress_number": record.get("congress_number"),
                    },
                )
                if existing.scalar_one_or_none():
                    await self.session.execute(
                        text("""
                            UPDATE government_bills
                            SET status = :status,
                                last_action_at = :last_action_at,
                                cosponsors_count = :cosponsors_count,
                                actions = CAST(:actions AS jsonb),
                                updated_at = NOW()
                            WHERE bill_number = :bill_number
                            AND congress_number = :congress_number
                        """),
                        {
                            "status": record.get("status"),
                            "last_action_at": record.get("last_action_at"),
                            "cosponsors_count": record.get("cosponsors_count", 0),
                            "actions": json.dumps(record.get("actions")) if record.get("actions") else "null",
                            "bill_number": record.get("bill_number"),
                            "congress_number": record.get("congress_number"),
                        },
                    )
                    skipped += 1
                    continue

                await self.session.execute(
                    text("""
                        INSERT INTO government_bills (
                            bill_number, bill_type, congress_number,
                            title, short_title, summary, url,
                            status, chamber, policy_area,
                            country, region,
                            introduced_at, last_action_at,
                            sponsor_bioguide_id, sponsor_name,
                            sponsor_party, sponsor_state, sponsor_chamber,
                            cosponsors_count, actions, committees,
                            related_bills, subjects, raw_data,
                            created_at, updated_at
                        ) VALUES (
                            :bill_number, :bill_type, :congress_number,
                            :title, :short_title, :summary, :url,
                            :status, :chamber, :policy_area,
                            :country, :region,
                            :introduced_at, :last_action_at,
                            :sponsor_bioguide_id, :sponsor_name,
                            :sponsor_party, :sponsor_state, :sponsor_chamber,
                            :cosponsors_count,
                            CAST(:actions AS jsonb),
                            CAST(:committees AS jsonb),
                            CAST(:related_bills AS jsonb),
                            CAST(:subjects AS jsonb),
                            CAST(:raw_data AS jsonb),
                            NOW(), NOW()
                        )
                    """),
                    {
                        "bill_number": record.get("bill_number"),
                        "bill_type": record.get("bill_type"),
                        "congress_number": record.get("congress_number"),
                        "title": record.get("title"),
                        "short_title": record.get("short_title"),
                        "summary": record.get("summary"),
                        "url": record.get("url"),
                        "status": record.get("status"),
                        "chamber": record.get("chamber"),
                        "policy_area": record.get("policy_area", "other"),
                        "country": record.get("country", "US"),
                        "region": record.get("region", "AMER"),
                        "introduced_at": record.get("introduced_at"),
                        "last_action_at": record.get("last_action_at"),
                        "sponsor_bioguide_id": record.get("sponsor_bioguide_id"),
                        "sponsor_name": record.get("sponsor_name"),
                        "sponsor_party": record.get("sponsor_party"),
                        "sponsor_state": record.get("sponsor_state"),
                        "sponsor_chamber": record.get("sponsor_chamber"),
                        "cosponsors_count": record.get("cosponsors_count", 0),
                        "actions": json.dumps(record.get("actions")) if record.get("actions") else "null",
                        "committees": json.dumps(record.get("committees")) if record.get("committees") else "null",
                        "related_bills": json.dumps(record.get("related_bills")) if record.get("related_bills") else "null",
                        "subjects": json.dumps(record.get("subjects")) if record.get("subjects") else "null",
                        "raw_data": json.dumps(record.get("raw_data")) if record.get("raw_data") else "{}",
                    },
                )
                inserted += 1

            except Exception as e:
                failed += 1
                await self.session.rollback()
                logger.error(
                    f"Failed to insert bill {record.get('bill_number')}: {e}"
                )

        await self.session.commit()
        logger.info(
            f"Bills: inserted={inserted} "
            f"skipped={skipped} failed={failed}"
        )
        return {
            "inserted": inserted,
            "skipped": skipped,
            "failed": failed,
        }

    async def write_contracts(self, records: list[dict]) -> dict:
        inserted = 0
        skipped = 0
        failed = 0

        for record in records:
            try:
                existing = await self.session.execute(
                    text(
                        "SELECT id FROM government_contracts "
                        "WHERE award_id = :award_id"
                    ),
                    {"award_id": record.get("award_id")},
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                await self.session.execute(
                    text("""
                        INSERT INTO government_contracts (
                            award_id, award_type, description,
                            total_amount, base_amount, potential_amount,
                            start_date, end_date, signed_date,
                            agency_id, agency_name, sub_agency_name, agency_code,
                            recipient_id, recipient_name, recipient_uei,
                            parent_recipient_name, ticker,
                            recipient_country, recipient_state,
                            congressional_district, place_of_performance,
                            naics_code, naics_description,
                            psc_code, psc_description,
                            is_compete, number_of_offers,
                            country, region, url, raw_data,
                            created_at, updated_at
                        ) VALUES (
                            :award_id, :award_type, :description,
                            :total_amount, :base_amount, :potential_amount,
                            :start_date, :end_date, :signed_date,
                            :agency_id, :agency_name, :sub_agency_name, :agency_code,
                            :recipient_id, :recipient_name, :recipient_uei,
                            :parent_recipient_name, :ticker,
                            :recipient_country, :recipient_state,
                            :congressional_district, :place_of_performance,
                            :naics_code, :naics_description,
                            :psc_code, :psc_description,
                            :is_compete, :number_of_offers,
                            :country, :region, :url,
                            CAST(:raw_data AS jsonb),
                            NOW(), NOW()
                        )
                    """),
                    {
                        "award_id": record.get("award_id"),
                        "award_type": record.get("award_type"),
                        "description": record.get("description"),
                        "total_amount": record.get("total_amount", 0),
                        "base_amount": record.get("base_amount", 0),
                        "potential_amount": record.get("potential_amount"),
                        "start_date": record.get("start_date"),
                        "end_date": record.get("end_date"),
                        "signed_date": record.get("signed_date"),
                        "agency_id": record.get("agency_id"),
                        "agency_name": record.get("agency_name"),
                        "sub_agency_name": record.get("sub_agency_name"),
                        "agency_code": record.get("agency_code"),
                        "recipient_id": record.get("recipient_id"),
                        "recipient_name": record.get("recipient_name"),
                        "recipient_uei": record.get("recipient_uei"),
                        "parent_recipient_name": record.get("parent_recipient_name"),
                        "ticker": record.get("ticker"),
                        "recipient_country": record.get("recipient_country", "US"),
                        "recipient_state": record.get("recipient_state"),
                        "congressional_district": record.get("congressional_district"),
                        "place_of_performance": record.get("place_of_performance"),
                        "naics_code": record.get("naics_code"),
                        "naics_description": record.get("naics_description"),
                        "psc_code": record.get("psc_code"),
                        "psc_description": record.get("psc_description"),
                        "is_compete": record.get("is_compete", True),
                        "number_of_offers": record.get("number_of_offers"),
                        "country": record.get("country", "US"),
                        "region": record.get("region", "AMER"),
                        "url": record.get("url"),
                        "raw_data": json.dumps(record.get("raw_data")) if record.get("raw_data") else "{}",
                    },
                )
                inserted += 1

            except Exception as e:
                failed += 1
                await self.session.rollback()
                logger.error(
                    f"Failed to insert contract {record.get('award_id')}: {e}"
                )

        await self.session.commit()
        logger.info(
            f"Contracts: inserted={inserted} "
            f"skipped={skipped} failed={failed}"
        )
        return {
            "inserted": inserted,
            "skipped": skipped,
            "failed": failed,
        }

    async def write_lobbying(self, records: list[dict]) -> dict:
        inserted = 0
        skipped = 0
        failed = 0

        for record in records:
            try:
                existing = await self.session.execute(
                    text(
                        "SELECT id FROM government_lobbying "
                        "WHERE filing_id = :filing_id"
                    ),
                    {"filing_id": record.get("filing_id")},
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                await self.session.execute(
                    text("""
                        INSERT INTO government_lobbying (
                            filing_id, filing_type, filing_year,
                            filing_period, filed_at, amount,
                            client_id, client_name, client_industry,
                            ticker, registrant_id, registrant_name,
                            client_country, country, region,
                            lobbyists, issues,
                            has_former_government, yoy_change,
                            url, raw_data,
                            created_at, updated_at
                        ) VALUES (
                            :filing_id, :filing_type, :filing_year,
                            :filing_period, :filed_at, :amount,
                            :client_id, :client_name, :client_industry,
                            :ticker, :registrant_id, :registrant_name,
                            :client_country, :country, :region,
                            CAST(:lobbyists AS jsonb),
                            CAST(:issues AS jsonb),
                            :has_former_government, :yoy_change,
                            :url, CAST(:raw_data AS jsonb),
                            NOW(), NOW()
                        )
                    """),
                    {
                        "filing_id": record.get("filing_id"),
                        "filing_type": record.get("filing_type"),
                        "filing_year": record.get("filing_year"),
                        "filing_period": record.get("filing_period"),
                        "filed_at": record.get("filed_at"),
                        "amount": record.get("amount", 0),
                        "client_id": record.get("client_id"),
                        "client_name": record.get("client_name"),
                        "client_industry": record.get("client_industry"),
                        "ticker": record.get("ticker"),
                        "registrant_id": record.get("registrant_id"),
                        "registrant_name": record.get("registrant_name"),
                        "client_country": record.get("client_country", "US"),
                        "country": record.get("country", "US"),
                        "region": record.get("region", "AMER"),
                        "lobbyists": json.dumps(record.get("lobbyists")) if record.get("lobbyists") else "null",
                        "issues": json.dumps(record.get("issues")) if record.get("issues") else "null",
                        "has_former_government": record.get("has_former_government", False),
                        "yoy_change": record.get("yoy_change"),
                        "url": record.get("url"),
                        "raw_data": json.dumps(record.get("raw_data")) if record.get("raw_data") else "{}",
                    },
                )
                inserted += 1

            except Exception as e:
                failed += 1
                await self.session.rollback()
                logger.error(
                    f"Failed to insert lobbying {record.get('filing_id')}: {e}"
                )

        await self.session.commit()
        logger.info(
            f"Lobbying: inserted={inserted} "
            f"skipped={skipped} failed={failed}"
        )
        return {
            "inserted": inserted,
            "skipped": skipped,
            "failed": failed,
        }