"use client";

import { useParams } from "next/navigation";
import { useRef, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
    getSnapshot, getBars, getFilings, getBills, getContracts,
    getFundamentalsSummary, getIncomeStatement, getBalanceSheet, getCashFlow,
} from "@/lib/api";
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from "lightweight-charts";

// ── Formatters ────────────────────────────────────────────────
const fP = (n?: number | null) => n == null ? "—" : `$${n.toFixed(2)}`;
const fB = (n?: number | null, d = 1) => {
    if (n == null) return "—";
    const a = Math.abs(n), s = n < 0 ? "-" : "";
    if (a >= 1e12) return `${s}$${(a / 1e12).toFixed(d)}T`;
    if (a >= 1e9) return `${s}$${(a / 1e9).toFixed(d)}B`;
    if (a >= 1e6) return `${s}$${(a / 1e6).toFixed(0)}M`;
    return `${s}$${a.toLocaleString()}`;
};
const fPct = (n?: number | null) => n == null ? "—" : `${(n * 100).toFixed(1)}%`;
const fDate = (s?: string | null) => {
    if (!s) return "—";
    return new Date(s).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
};
const fDateShort = (s?: string | null) => {
    if (!s) return "—";
    return new Date(s).toLocaleDateString("en-US", { month: "short", year: "2-digit" });
};
const fVol = (n?: number | null) => {
    if (n == null) return "—";
    if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
    if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
    if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`;
    return n.toString();
};
const yoy = (curr?: number | null, prev?: number | null) => {
    if (!curr || !prev || prev === 0) return null;
    return (curr - prev) / Math.abs(prev);
};

// ── Skeleton ─────────────────────────────────────────────────
function Sk({ w = 60, h = 10 }: { w?: number; h?: number }) {
    return <span className="ag-skeleton" style={{ width: w, height: h, display: "inline-block" }} />;
}

// ── YoY badge ────────────────────────────────────────────────
function YoY({ pct }: { pct: number | null }) {
    if (pct == null) return <span style={{ color: "#2a3d55", fontFamily: "JetBrains Mono, monospace", fontSize: 9 }}>—</span>;
    const up = pct >= 0;
    return (
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: up ? "#10b981" : "#f43f5e" }}>
            {up ? "▲" : "▼"} {Math.abs(pct * 100).toFixed(1)}%
        </span>
    );
}

// ── Stat cell ────────────────────────────────────────────────
function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
    return (
        <div style={{ padding: "8px 16px", borderRight: "1px solid #1a2840" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 600, letterSpacing: "0.1em", color: "#2a3d55", textTransform: "uppercase", marginBottom: 4 }}>
                {label}
            </div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12, fontWeight: 700, color: color ?? "#e8eef5", fontVariantNumeric: "tabular-nums" }}>
                {value}
            </div>
        </div>
    );
}

// ── Price chart ──────────────────────────────────────────────
function PriceChart({ ticker }: { ticker: string }) {
    const ref = useRef<HTMLDivElement>(null);
    const { data: bars, isLoading } = useQuery({
        queryKey: ["bars", ticker],
        queryFn: () => getBars({ ticker, timeframe: "1Day", limit: 365 }),
    });

    useEffect(() => {
        if (!ref.current || !bars || bars.length === 0) return;
        const chart = createChart(ref.current, {
            layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: "#2a3d55" },
            grid: { vertLines: { color: "#0d1520" }, horzLines: { color: "#0d1520" } },
            crosshair: { vertLine: { color: "#1a2840" }, horzLine: { color: "#1a2840" } },
            rightPriceScale: { borderColor: "#1a2840", textColor: "#4a6080" },
            timeScale: { borderColor: "#1a2840", timeVisible: true },
            width: ref.current.clientWidth,
            height: 260,
        });
        const candle = chart.addSeries(CandlestickSeries, {
            upColor: "#10b981", downColor: "#f43f5e",
            borderUpColor: "#10b981", borderDownColor: "#f43f5e",
            wickUpColor: "#059669", wickDownColor: "#be123c",
        });
        const vol = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, priceScaleId: "vol" });
        chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.88, bottom: 0 } });
        candle.setData(bars.map(b => ({ time: b.timestamp.split("T")[0] as any, open: b.open, high: b.high, low: b.low, close: b.close })));
        vol.setData(bars.map(b => ({ time: b.timestamp.split("T")[0] as any, value: b.volume, color: b.close >= b.open ? "#10b98120" : "#f43f5e20" })));
        chart.timeScale().fitContent();
        const onResize = () => { if (ref.current) chart.applyOptions({ width: ref.current.clientWidth }); };
        window.addEventListener("resize", onResize);
        return () => { window.removeEventListener("resize", onResize); chart.remove(); };
    }, [bars]);

    if (isLoading) return <div style={{ height: 260, display: "flex", alignItems: "center", justifyContent: "center" }}><Sk w={400} h={200} /></div>;

    if (!bars || bars.length === 0) {
        return (
            <div style={{ height: 260, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#2a3d55" }}>CHART UNAVAILABLE</div>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#1a2840" }}>Upgrade to Polygon Starter ($29/mo) for historical bars</div>
            </div>
        );
    }
    return <div ref={ref} style={{ width: "100%" }} />;
}

// ── Fundamentals panel ───────────────────────────────────────
function FundamentalsPanel({ ticker }: { ticker: string }) {
    const [view, setView] = useState<"annual" | "quarterly">("annual");

    const { data: summary, isLoading: ls } = useQuery({
        queryKey: ["fundamentals-summary", ticker],
        queryFn: () => getFundamentalsSummary(ticker),
    });
    const { data: income, isLoading: li } = useQuery({
        queryKey: ["income", ticker, view],
        queryFn: () => getIncomeStatement({ ticker, period_type: view, limit: 8 }),
    });
    const { data: balance } = useQuery({
        queryKey: ["balance", ticker, view],
        queryFn: () => getBalanceSheet({ ticker, period_type: view, limit: 8 }),
    });
    const { data: cashflow } = useQuery({
        queryKey: ["cashflow", ticker, view],
        queryFn: () => getCashFlow({ ticker, period_type: view, limit: 8 }),
    });

    if (ls) return (
        <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 8 }}>
            {[...Array(4)].map((_, i) => <Sk key={i} w={600} h={12} />)}
        </div>
    );

    if (!summary) return (
        <div style={{ padding: 40, textAlign: "center" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#2a3d55", marginBottom: 8 }}>
                NO FUNDAMENTAL DATA FOR {ticker}
            </div>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#1a2840" }}>
                Run: python run_fundamentals.py --ticker {ticker} --force
            </div>
        </div>
    );

    return (
        <div>
            {/* Key metrics */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", borderBottom: "1px solid #1a2840" }}>
                <Stat label="Revenue" value={fB(summary.revenue)} />
                <Stat label={`Net Income · ${fPct(summary.net_margin)}`} value={fB(summary.net_income)} color={summary.net_income && summary.net_income > 0 ? "#10b981" : "#f43f5e"} />
                <Stat label={`Free Cash Flow · OCF ${fB(summary.operating_cash_flow)}`} value={fB(summary.free_cash_flow)} color="#10b981" />
                <Stat label="EPS Diluted" value={fP(summary.eps_diluted)} />
            </div>

            {/* Margins row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 1fr)", borderBottom: "1px solid #1a2840", background: "#080d14" }}>
                <Stat label="Gross Margin" value={fPct(summary.gross_margin)} />
                <Stat label="Op Margin" value={fPct(summary.operating_margin)} />
                <Stat label="Net Margin" value={fPct(summary.net_margin)} />
                <Stat label="EBITDA Margin" value={fPct(summary.ebitda_margin)} />
                <Stat label="ROE" value={fPct(summary.roe)} color="#10b981" />
                <Stat label="ROIC" value={fPct(summary.roic)} color="#10b981" />
                <Stat label="Debt/Equity" value={summary.debt_to_equity?.toFixed(2) ?? "—"} />
                <Stat label="Current Ratio" value={summary.current_ratio?.toFixed(2) ?? "—"} />
            </div>

            {/* Balance sheet row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", borderBottom: "1px solid #1a2840" }}>
                <Stat label="Total Assets" value={fB(summary.total_assets)} />
                <Stat label="Total Liabilities" value={fB(summary.total_liabilities)} />
                <Stat label="Equity" value={fB(summary.total_equity)} />
                <Stat label="Cash" value={fB(summary.cash)} color="#10b981" />
                <Stat label="Total Debt" value={fB(summary.total_debt)} />
                <Stat label="Net Debt" value={fB(summary.net_debt)} color={summary.net_debt && summary.net_debt < 0 ? "#10b981" : "#e8eef5"} />
            </div>

            {/* View toggle */}
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 16px", borderBottom: "1px solid #1a2840", background: "#080d14" }}>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.1em" }}>VIEW</span>
                {(["annual", "quarterly"] as const).map((v) => (
                    <button
                        key={v}
                        onClick={() => setView(v)}
                        style={{
                            fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.08em",
                            padding: "3px 12px", borderRadius: 2, cursor: "pointer", transition: "all 0.15s",
                            background: view === v ? "rgba(37,99,235,0.12)" : "transparent",
                            color: view === v ? "#3b82f6" : "#2a3d55",
                            border: view === v ? "1px solid rgba(37,99,235,0.35)" : "1px solid #1a2840",
                        }}
                    >
                        {v.toUpperCase()}
                    </button>
                ))}
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#1a2840", marginLeft: 8 }}>
                    PARSED BY {summary.parsed_by?.toUpperCase() ?? "—"} · {fDate(summary.period_end)}
                </span>
            </div>

            {/* Income statement */}
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 600, letterSpacing: "0.12em", color: "#2a3d55", padding: "6px 16px", background: "#080d14", borderBottom: "1px solid #1a2840", display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 2, height: 10, background: "#3b82f6", borderRadius: 1, display: "inline-block" }} />
                INCOME STATEMENT
            </div>
            <table className="ag-table">
                <thead>
                    <tr>
                        <th>PERIOD</th>
                        <th className="r">REVENUE</th>
                        <th className="r">YOY</th>
                        <th className="r">GROSS PROFIT</th>
                        <th className="r">OP INCOME</th>
                        <th className="r">NET INCOME</th>
                        <th className="r">YOY</th>
                        <th className="r">FCF</th>
                        <th className="r">EPS</th>
                        <th className="r">NET MARGIN</th>
                    </tr>
                </thead>
                <tbody>
                    {li ? [...Array(5)].map((_, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid #0d1520" }}>
                            {[...Array(10)].map((_, j) => <td key={j} style={{ padding: "7px 14px" }}><Sk w={50} /></td>)}
                        </tr>
                    )) : income?.map((row, idx) => {
                        const prev = income[idx + 1];
                        return (
                            <tr key={row.period_end} style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                                onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                            >
                                <td className="dim" style={{ padding: "7px 14px" }}>{fDateShort(row.period_end)}</td>
                                <td className="r" style={{ padding: "7px 14px" }}>{fB(row.revenue)}</td>
                                <td className="r" style={{ padding: "7px 14px" }}><YoY pct={yoy(row.revenue, prev?.revenue)} /></td>
                                <td className="r" style={{ padding: "7px 14px" }}>{fB(row.gross_profit)}</td>
                                <td className="r" style={{ padding: "7px 14px" }}>{fB(row.operating_income)}</td>
                                <td className="r" style={{ padding: "7px 14px", color: row.net_income && row.net_income > 0 ? "#10b981" : "#f43f5e", fontWeight: 700 }}>{fB(row.net_income)}</td>
                                <td className="r" style={{ padding: "7px 14px" }}><YoY pct={yoy(row.net_income, prev?.net_income)} /></td>
                                <td className="r" style={{ padding: "7px 14px", color: "#10b981" }}>{fB(row.free_cash_flow)}</td>
                                <td className="r" style={{ padding: "7px 14px" }}>{fP(row.eps_diluted)}</td>
                                <td className="r" style={{ padding: "7px 14px" }}>{fPct(row.net_margin)}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>

            {/* Cash flow */}
            {cashflow && cashflow.length > 0 && (
                <>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 600, letterSpacing: "0.12em", color: "#2a3d55", padding: "6px 16px", background: "#080d14", borderTop: "1px solid #1a2840", borderBottom: "1px solid #1a2840", display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ width: 2, height: 10, background: "#10b981", borderRadius: 1, display: "inline-block" }} />
                        CASH FLOW
                    </div>
                    <table className="ag-table">
                        <thead>
                            <tr>
                                <th>PERIOD</th>
                                <th className="r">OPERATING CF</th>
                                <th className="r">CAPEX</th>
                                <th className="r">FREE CF</th>
                                <th className="r">D&A</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cashflow.map((row) => (
                                <tr key={row.period_end} style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                                    onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                                >
                                    <td className="dim" style={{ padding: "7px 14px" }}>{fDateShort(row.period_end)}</td>
                                    <td className="r" style={{ padding: "7px 14px", color: "#10b981" }}>{fB(row.operating_cash_flow)}</td>
                                    <td className="r" style={{ padding: "7px 14px", color: "#f43f5e" }}>{fB(row.capex)}</td>
                                    <td className="r" style={{ padding: "7px 14px", color: "#10b981", fontWeight: 700 }}>{fB(row.free_cash_flow)}</td>
                                    <td className="r" style={{ padding: "7px 14px" }}>{fB(row.depreciation)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}
        </div>
    );
}

// ── Filings panel ────────────────────────────────────────────
function FilingsPanel({ ticker }: { ticker: string }) {
    const { data } = useQuery({ queryKey: ["filings", ticker], queryFn: () => getFilings({ ticker, page_size: 15 }) });
    const TYPE_COLOR: Record<string, string> = {
        "10-K": "#3b82f6", "10-Q": "#818cf8", "8-K": "#f59e0b", "4": "#a855f7", "S-1": "#10b981",
    };
    return (
        <table className="ag-table">
            <thead><tr>
                <th style={{ width: 80 }}>TYPE</th>
                <th>COMPANY</th>
                <th>FILED</th>
                <th>PERIOD</th>
                <th>LINK</th>
            </tr></thead>
            <tbody>
                {data?.items.map((f) => (
                    <tr key={f.id} style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                        <td style={{ padding: "7px 14px" }}>
                            <span style={{
                                fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700,
                                color: TYPE_COLOR[f.filing_type] ?? "#4a6080",
                                background: `${TYPE_COLOR[f.filing_type] ?? "#4a6080"}15`,
                                border: `1px solid ${TYPE_COLOR[f.filing_type] ?? "#4a6080"}30`,
                                padding: "2px 6px", borderRadius: 2,
                            }}>{f.filing_type}</span>
                        </td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#e8eef5" }}>
                            {f.company_name?.split("(")[0].trim() ?? "—"}
                        </td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>{fDate(f.filed_at)}</td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>{f.period_of_report ? fDate(f.period_of_report) : "—"}</td>
                        <td style={{ padding: "7px 14px" }}>
                            {f.url && (
                                <button onClick={() => window.open(f.url!, "_blank")}
                                    style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, color: "#2a3d55", background: "none", border: "none", cursor: "pointer", transition: "color 0.15s" }}
                                    onMouseEnter={(e) => (e.currentTarget.style.color = "#3b82f6")}
                                    onMouseLeave={(e) => (e.currentTarget.style.color = "#2a3d55")}
                                >VIEW →</button>
                            )}
                        </td>
                    </tr>
                ))}
                {!data?.items.length && (
                    <tr><td colSpan={5} style={{ padding: "30px 14px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#2a3d55" }}>
                        NO FILINGS FOUND FOR {ticker}
                    </td></tr>
                )}
            </tbody>
        </table>
    );
}

// ── Contracts panel ──────────────────────────────────────────
function ContractsPanel({ ticker }: { ticker: string }) {
    const { data } = useQuery({ queryKey: ["contracts", ticker], queryFn: () => getContracts({ ticker, page_size: 15 }) });
    return (
        <table className="ag-table">
            <thead><tr>
                <th>AGENCY</th>
                <th className="r">AMOUNT</th>
                <th>TYPE</th>
                <th>START</th>
                <th>END</th>
            </tr></thead>
            <tbody>
                {data?.items.map((c) => (
                    <tr key={c.id} style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#4a6080" }}>{c.agency_name}</td>
                        <td className="r" style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 12, fontWeight: 700, color: "#10b981" }}>{fB(c.total_amount)}</td>
                        <td style={{ padding: "7px 14px" }}>
                            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, background: "#111c2a", color: "#4a6080", border: "1px solid #1a2840", padding: "2px 6px", borderRadius: 2 }}>{c.award_type}</span>
                        </td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>{fDate(c.start_date)}</td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>{fDate(c.end_date)}</td>
                    </tr>
                ))}
                {!data?.items.length && (
                    <tr><td colSpan={5} style={{ padding: "30px 14px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#2a3d55" }}>
                        NO CONTRACTS FOUND FOR {ticker}
                    </td></tr>
                )}
            </tbody>
        </table>
    );
}

// ── Bills panel ──────────────────────────────────────────────
function BillsPanel() {
    const { data } = useQuery({ queryKey: ["bills-stock"], queryFn: () => getBills({ page_size: 15 }) });
    return (
        <table className="ag-table">
            <thead><tr>
                <th style={{ width: 90 }}>BILL</th>
                <th>TITLE</th>
                <th style={{ width: 140 }}>STATUS</th>
                <th style={{ width: 80 }}>CHAMBER</th>
                <th style={{ width: 100 }}>INTRODUCED</th>
            </tr></thead>
            <tbody>
                {data?.items.map((b) => (
                    <tr key={b.id} style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 10, fontWeight: 700, color: "#3b82f6" }}>{b.bill_number}</td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#e8eef5", maxWidth: 360 }}>
                            <div style={{ overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{b.title}</div>
                        </td>
                        <td style={{ padding: "7px 14px" }}>
                            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, background: "#111c2a", color: "#4a6080", border: "1px solid #1a2840", padding: "2px 6px", borderRadius: 2 }}>
                                {b.status.replace(/_/g, " ").toUpperCase()}
                            </span>
                        </td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, color: b.chamber === "senate" ? "#a855f7" : "#3b82f6" }}>
                            {b.chamber.toUpperCase()}
                        </td>
                        <td style={{ padding: "7px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>{fDate(b.introduced_at)}</td>
                    </tr>
                ))}
                {!data?.items.length && (
                    <tr><td colSpan={5} style={{ padding: "30px 14px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#2a3d55" }}>NO BILLS FOUND</td></tr>
                )}
            </tbody>
        </table>
    );
}

// ── Main page ────────────────────────────────────────────────
export default function StockPage() {
    const params = useParams();
    const ticker = (params.ticker as string).toUpperCase();
    const [tab, setTab] = useState("fundamentals");

    const { data: snap, isLoading: ls } = useQuery({
        queryKey: ["snapshot", ticker],
        queryFn: () => getSnapshot({ ticker }),
        refetchInterval: 30000,
    });
    const { data: filings } = useQuery({ queryKey: ["filings-count", ticker], queryFn: () => getFilings({ ticker, page_size: 1 }) });
    const { data: contracts } = useQuery({ queryKey: ["contracts-count", ticker], queryFn: () => getContracts({ ticker, page_size: 1 }) });

    const isUp = (snap?.change ?? 0) >= 0;

    const tabs = [
        { key: "fundamentals", label: "FUNDAMENTALS" },
        { key: "filings", label: `FILINGS${filings?.total ? ` (${filings.total})` : ""}` },
        { key: "contracts", label: `CONTRACTS${contracts?.total ? ` (${contracts.total})` : ""}` },
        { key: "bills", label: "BILLS" },
    ];

    return (
        <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "#080d14" }}>

            {/* ── Top bar ── */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", height: 48, borderBottom: "1px solid #1a2840", background: "#080d14", flexShrink: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                    <div>
                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 16, fontWeight: 700, letterSpacing: "0.08em", color: "#e8eef5" }}>{ticker}</span>
                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", marginLeft: 8 }}>US EQUITY · ALPACA</span>
                    </div>
                    {ls ? <Sk w={120} h={20} /> : snap && (
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 20, fontWeight: 700, color: isUp ? "#10b981" : "#f43f5e", fontVariantNumeric: "tabular-nums" }}>
                                {fP(snap.price)}
                            </span>
                            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: isUp ? "#10b981" : "#f43f5e", fontVariantNumeric: "tabular-nums" }}>
                                {isUp ? "▲" : "▼"} {Math.abs(snap.change ?? 0).toFixed(2)} ({Math.abs(snap.change_pct ?? 0).toFixed(2)}%)
                            </span>
                        </div>
                    )}
                </div>
                <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55" }}>
                    {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })} ET · 30s REFRESH
                </span>
            </div>

            {/* ── Quote bar ── */}
            {snap && (
                <div style={{ display: "flex", borderBottom: "1px solid #1a2840", background: "#080d14", flexShrink: 0, overflowX: "auto" }}>
                    {[
                        { label: "OPEN", value: fP(snap.open) },
                        { label: "HIGH", value: fP(snap.high), color: "#10b981" },
                        { label: "LOW", value: fP(snap.low), color: "#f43f5e" },
                        { label: "PREV CLOSE", value: fP(snap.prev_close) },
                        { label: "VOLUME", value: fVol(snap.volume) },
                        { label: "VWAP", value: fP(snap.vwap) },
                        { label: "BID", value: fP(snap.bid) },
                        { label: "ASK", value: fP(snap.ask) },
                    ].map((s) => <Stat key={s.label} label={s.label} value={s.value} color={s.color} />)}
                </div>
            )}

            {/* ── Chart ── */}
            <div style={{ borderBottom: "1px solid #1a2840", flexShrink: 0 }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 600, letterSpacing: "0.12em", color: "#2a3d55", padding: "5px 16px", background: "#080d14", display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ width: 2, height: 10, background: "#2563eb", borderRadius: 1, display: "inline-block" }} />
                    1Y PRICE CHART · {ticker} · DAILY
                </div>
                <div style={{ padding: "0 12px 8px" }}>
                    <PriceChart ticker={ticker} />
                </div>
            </div>

            {/* ── Tabs ── */}
            <div className="ag-tabs" style={{ flexShrink: 0 }}>
                {tabs.map((t) => (
                    <button key={t.key} onClick={() => setTab(t.key)} className={`ag-tab${tab === t.key ? " active" : ""}`}>
                        {t.label}
                    </button>
                ))}
            </div>

            {/* ── Tab content ── */}
            <div style={{ flex: 1, overflowY: "auto" }}>
                {tab === "fundamentals" && <FundamentalsPanel ticker={ticker} />}
                {tab === "filings" && <FilingsPanel ticker={ticker} />}
                {tab === "contracts" && <ContractsPanel ticker={ticker} />}
                {tab === "bills" && <BillsPanel />}
            </div>
        </div>
    );
}