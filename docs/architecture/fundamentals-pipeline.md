# Fundamentals Pipeline - Architecture

**Status:** In Development  
**Last Updated:** September 2026  
**Author:** Argos Engineering

---

## Overview

The fundamentals pipeline ingests, parses, normalizes, and serves financial statement data for all US public companies. Data is sourced directly from SEC EDGAR at zero cost using the XBRL API. A hybrid parsing approach (rule-based + LLM fallback) ensures high accuracy across all companies.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────┐
│                   SCHEDULER (daily)                  │
│         Prefect / APScheduler flow                   │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│              CHANGE DETECTOR                         │
│  GET /submissions/{CIK}.json                         │
│  Compare latest 10-K/10-Q filed_at vs our DB        │
│  Only proceed if new filing found                    │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│              XBRL FETCHER                            │
│  GET /api/xbrl/companyfacts/{CIK}.json              │
│  Raw JSON → store in S3 as backup                   │
│  Rate limit: 10 req/sec, retry with backoff         │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│           TRADITIONAL PARSER (Layer 1)               │
│  Maps 50 standard XBRL concepts → clean fields      │
│  Handles ~90% of companies                          │
│  Outputs structured dict or None per concept        │
└──────────────────┬──────────────────────────────────┘
                   ↓
         ┌─────────┴──────────┐
         ↓                    ↓
   concepts found        concepts missing
   (~90% of cases)       (~10% of cases)
         │                    ↓
         │       ┌────────────────────────┐
         │       │   LLM FALLBACK         │
         │       │   (Layer 2)            │
         │       │   Send only missing    │
         │       │   section to Claude    │
         │       │   Cache result in DB   │
         │       │   Never call twice for │
         │       │   same filing          │
         │       └────────────┬───────────┘
         │                    │
         └──────────┬─────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│              NORMALIZER                              │
│  Separate annual vs quarterly periods               │
│  Calculate derived metrics:                         │
│    EBITDA = operating_income + D&A                  │
│    FCF = OCF - capex                                │
│    Gross margin = gross_profit / revenue            │
│    ROIC, ROE, debt/equity ratios                   │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│              DB WRITER                               │
│  Upsert into fundamentals_facts                     │
│  Upsert into fundamentals_summary (pre-aggregated)  │
│  Update company.last_fundamentals_at                │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│              BACKEND API                             │
│  /fundamentals/{ticker}/income-statement            │
│  /fundamentals/{ticker}/balance-sheet               │
│  /fundamentals/{ticker}/cash-flow                   │
│  /fundamentals/{ticker}/metrics                     │
│  /fundamentals/{ticker}/dcf                         │
└─────────────────────────────────────────────────────┘
```

---

## Data Source

**SEC EDGAR XBRL API** - free, no API key required.

| Endpoint | Purpose |
|----------|---------|
| `https://data.sec.gov/submissions/CIK{cik}.json` | Latest filing dates for change detection |
| `https://data.sec.gov/api/xbrl/companyfacts/{CIK}.json` | All financial facts for a company |

---

## Parsing Strategy

### Layer 1 — Traditional Parser (rule-based)
Maps standard XBRL concepts to clean field names. Covers ~90% of companies.

**Income Statement concepts:**
| Clean Field | XBRL Concepts (in priority order) |
|------------|-----------------------------------|
| `revenue` | `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet` |
| `gross_profit` | `GrossProfit` |
| `operating_income` | `OperatingIncomeLoss` |
| `net_income` | `NetIncomeLoss` |
| `eps_basic` | `EarningsPerShareBasic` |
| `eps_diluted` | `EarningsPerShareDiluted` |
| `shares_outstanding` | `CommonStockSharesOutstanding` |

**Balance Sheet concepts:**
| Clean Field | XBRL Concepts |
|------------|---------------|
| `total_assets` | `Assets` |
| `total_liabilities` | `Liabilities` |
| `total_equity` | `StockholdersEquity` |
| `cash` | `CashAndCashEquivalentsAtCarryingValue` |
| `total_debt` | `LongTermDebt`, `DebtCurrent` |

**Cash Flow concepts:**
| Clean Field | XBRL Concepts |
|------------|---------------|
| `operating_cash_flow` | `NetCashProvidedByUsedInOperatingActivities` |
| `capex` | `PaymentsToAcquirePropertyPlantAndEquipment` |
| `depreciation` | `DepreciationDepletionAndAmortization` |

### Layer 2 — LLM Fallback (Claude)
- Only triggered when Layer 1 finds missing concepts
- Sends only the raw XBRL section for the missing concept
- Result cached in DB with `parsed_by = 'llm'`
- Never called twice for the same filing
- Estimated cost: ~$0.06 per company (10% of filings × ~$0.60 per full parse)

---

## Derived Metrics (Normalizer)

Calculated from parsed values - never stored as raw XBRL:

```
EBITDA         = operating_income + depreciation
FCF            = operating_cash_flow - capex
gross_margin   = gross_profit / revenue
operating_margin = operating_income / revenue
net_margin     = net_income / revenue
ebitda_margin  = ebitda / revenue
net_debt       = total_debt - cash
debt_to_equity = total_debt / total_equity
ROE            = net_income / total_equity
ROIC           = operating_income / (total_assets - total_liabilities)
```

---

## Database Schema

### `fundamentals_facts`
Raw facts — one row per concept per period. Audit trail.

```sql
CREATE TABLE fundamentals_facts (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(20) NOT NULL,
    cik             VARCHAR(20) NOT NULL,
    concept         VARCHAR(200) NOT NULL,
    label           VARCHAR(200),
    value           NUMERIC NOT NULL,
    unit            VARCHAR(50),
    period_start    DATE,
    period_end      DATE NOT NULL,
    period_type     VARCHAR(10),   -- annual, quarterly
    form            VARCHAR(20),   -- 10-K, 10-Q
    filed_at        DATE,
    parsed_by       VARCHAR(20),   -- 'xbrl' or 'llm'
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, concept, period_end, period_type)
);
```

### `fundamentals_summary`
Pre-aggregated — one row per ticker per period. Powers the API fast.

```sql
CREATE TABLE fundamentals_summary (
    id                  SERIAL PRIMARY KEY,
    ticker              VARCHAR(20) NOT NULL,
    cik                 VARCHAR(20),
    period_end          DATE NOT NULL,
    period_type         VARCHAR(10),
    form                VARCHAR(20),
    filed_at            DATE,
    revenue             NUMERIC,
    gross_profit        NUMERIC,
    gross_margin        NUMERIC,
    operating_income    NUMERIC,
    operating_margin    NUMERIC,
    net_income          NUMERIC,
    net_margin          NUMERIC,
    ebitda              NUMERIC,
    ebitda_margin       NUMERIC,
    eps_basic           NUMERIC,
    eps_diluted         NUMERIC,
    shares_outstanding  NUMERIC,
    total_assets        NUMERIC,
    total_liabilities   NUMERIC,
    total_equity        NUMERIC,
    cash                NUMERIC,
    total_debt          NUMERIC,
    net_debt            NUMERIC,
    operating_cash_flow NUMERIC,
    capex               NUMERIC,
    free_cash_flow      NUMERIC,
    depreciation        NUMERIC,
    debt_to_equity      NUMERIC,
    roe                 NUMERIC,
    roic                NUMERIC,
    parsed_by           VARCHAR(20),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, period_end, period_type)
);
```

---

## Robustness Features

| Feature | Implementation |
|---------|---------------|
| Rate limiting | 10 req/sec max to EDGAR, token bucket |
| Retry logic | Exponential backoff, max 3 retries |
| S3 backup | Raw XBRL JSON stored before parsing |
| Idempotent writes | UPSERT on unique constraint |
| Change detection | Only fetch if new filing since last run |
| LLM caching | `parsed_by = 'llm'` flag, never re-call |
| Dead letter queue | Failed tickers logged to `fundamentals_errors` table |
| Audit trail | `fundamentals_facts` keeps raw values forever |

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /fundamentals/{ticker}/income-statement` | Revenue, margins, EPS - last 8 quarters + 5 years |
| `GET /fundamentals/{ticker}/balance-sheet` | Assets, liabilities, equity - last 8 quarters + 5 years |
| `GET /fundamentals/{ticker}/cash-flow` | OCF, capex, FCF - last 8 quarters + 5 years |
| `GET /fundamentals/{ticker}/metrics` | All derived ratios |
| `GET /fundamentals/{ticker}/dcf` | DCF intrinsic value calculation |

---

## DCF Model

Auto DCF using last 3 years of FCF from our DB:

```
1. Pull last 3 years FCF from fundamentals_summary
2. Calculate FCF growth rate (CAGR)
3. Project 5 years of FCF using growth rate
4. Calculate terminal value (Gordon Growth Model)
5. Discount all cash flows at WACC
6. WACC = cost of equity (CAPM) + cost of debt
7. Output: intrinsic value per share vs current price
8. Sensitivity table: ±2% on growth rate and WACC
```

---

## File Structure

```
backend/app/
├── models/fundamentals/
│   ├── facts.py
│   └── summary.py
├── schemas/fundamentals/
│   ├── facts.py
│   └── summary.py
├── services/fundamentals/
│   └── fundamentals_service.py
└── api/v1/routers/fundamentals/
    └── fundamentals.py

ingestion/app/
├── fetchers/fundamentals/
│   └── edgar_xbrl.py
├── parsers/fundamentals/
│   ├── xbrl_parser.py
│   └── llm_fallback.py
├── normalizers/fundamentals/
│   └── normalizer.py
└── db/
    └── fundamentals_writer.py
```

---

## Cost Analysis

| Item | Cost |
|------|------|
| EDGAR XBRL API | $0 — free forever |
| S3 storage (raw JSON) | ~$2/mo for 10K companies |
| LLM fallback (Claude) | ~$0.06/company one-time, ~$0.01/quarter update |
| Total ongoing (500 companies) | ~$5/mo |

---

## Build Order

- [ ] Step 1: DB migrations — create `fundamentals_facts` and `fundamentals_summary`
- [ ] Step 2: EDGAR XBRL fetcher — fetch + S3 backup
- [ ] Step 3: Traditional parser — 50 concept mappings
- [ ] Step 4: LLM fallback — Claude for missing concepts
- [ ] Step 5: Normalizer — derived metrics
- [ ] Step 6: DB writer — upsert both tables
- [ ] Step 7: Change detector — daily diff
- [ ] Step 8: Scheduler — Prefect flow
- [ ] Step 9: Backend API — 5 endpoints
- [ ] Step 10: DCF calculator