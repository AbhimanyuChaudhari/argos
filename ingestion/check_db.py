import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        "postgresql://argos:argos_password@localhost:5434/argos_db"
    )
    rows = await conn.fetch(
        """
        SELECT period_end, period_type, revenue, net_income,
               free_cash_flow, eps_diluted, roe
        FROM fundamentals_summary
        WHERE ticker = 'AAPL'
        ORDER BY period_end DESC
        LIMIT 5
        """
    )
    print(f"Found {len(rows)} rows for AAPL:")
    for r in rows:
        rev = f"${float(r['revenue'])/1e9:.1f}B" if r['revenue'] else "N/A"
        ni = f"${float(r['net_income'])/1e9:.1f}B" if r['net_income'] else "N/A"
        fcf = f"${float(r['free_cash_flow'])/1e9:.1f}B" if r['free_cash_flow'] else "N/A"
        eps = f"${float(r['eps_diluted']):.2f}" if r['eps_diluted'] else "N/A"
        roe = f"{float(r['roe'])*100:.1f}%" if r['roe'] else "N/A"
        print(f"  {r['period_end']} ({r['period_type']}): Rev={rev} NI={ni} FCF={fcf} EPS={eps} ROE={roe}")
    await conn.close()

asyncio.run(check())