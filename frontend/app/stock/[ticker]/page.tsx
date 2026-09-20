"use client";

import { useParams } from "next/navigation";
import { useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
    getSnapshot,
    getBars,
    getFilings,
    getBills,
    getContracts,
    getFundamentalsSummary,
    getIncomeStatement,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowUpRight, ArrowDownRight, TrendingUp } from "lucide-react";
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from "lightweight-charts";

// ─── Formatters ───────────────────────────────────────────────
function fmtPrice(n: number | null | undefined) {
    if (n == null) return "—";
    return `$${n.toFixed(2)}`;
}
function fmtB(n: number | null | undefined) {
    if (n == null) return "—";
    if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
    if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
    return `$${n.toLocaleString()}`;
}
function fmtPct(n: number | null | undefined) {
    if (n == null) return "—";
    return `${(n * 100).toFixed(1)}%`;
}
function fmtDate(s: string) {
    return new Date(s).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}
function fmtVol(n: number | null | undefined) {
    if (n == null) return "—";
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
    return n.toString();
}

// ─── Stat card ────────────────────────────────────────────────
function Stat({ label, value, green }: { label: string; value: string; green?: boolean }) {
    return (
        <div className="space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
            <p className={`text-sm font-mono font-bold ${green ? "text-emerald-400" : ""}`}>{value}</p>
        </div>
    );
}

// ─── Price chart ──────────────────────────────────────────────
function PriceChart({ ticker }: { ticker: string }) {
    const chartRef = useRef<HTMLDivElement>(null);
    const { data: bars } = useQuery({
        queryKey: ["bars", ticker],
        queryFn: () => getBars({ ticker, timeframe: "1Day", limit: 365 }),
        enabled: !!ticker,
    });

    useEffect(() => {
        if (!chartRef.current || !bars || bars.length === 0) return;
        const chart = createChart(chartRef.current, {
            layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: "#94a3b8" },
            grid: { vertLines: { color: "#1e293b" }, horzLines: { color: "#1e293b" } },
            crosshair: { vertLine: { color: "#475569" }, horzLine: { color: "#475569" } },
            rightPriceScale: { borderColor: "#1e293b" },
            timeScale: { borderColor: "#1e293b", timeVisible: true },
            width: chartRef.current.clientWidth,
            height: 320,
        });
        const candle = chart.addSeries(CandlestickSeries, {
            upColor: "#22c55e", downColor: "#ef4444",
            borderUpColor: "#22c55e", borderDownColor: "#ef4444",
            wickUpColor: "#22c55e", wickDownColor: "#ef4444",
        });
        const vol = chart.addSeries(HistogramSeries, { color: "#334155", priceFormat: { type: "volume" }, priceScaleId: "vol" });
        chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });
        candle.setData(bars.map(b => ({ time: b.timestamp.split("T")[0], open: b.open, high: b.high, low: b.low, close: b.close })));
        vol.setData(bars.map(b => ({ time: b.timestamp.split("T")[0], value: b.volume, color: b.close >= b.open ? "#16a34a40" : "#dc262640" })));
        chart.timeScale().fitContent();
        const onResize = () => { if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth }); };
        window.addEventListener("resize", onResize);
        return () => { window.removeEventListener("resize", onResize); chart.remove(); };
    }, [bars]);

    if (!bars || bars.length === 0) {
        return (
            <div className="w-full h-[320px] flex items-center justify-center text-muted-foreground text-sm">
                Chart data unavailable — upgrade to Polygon Starter for historical bars
            </div>
        );
    }
    return <div ref={chartRef} className="w-full h-[320px]" />;
}

// ─── Fundamentals tab ─────────────────────────────────────────
function FundamentalsTab({ ticker }: { ticker: string }) {
    const { data: summary } = useQuery({
        queryKey: ["fundamentals-summary", ticker],
        queryFn: () => getFundamentalsSummary(ticker),
    });
    const { data: history } = useQuery({
        queryKey: ["income-statement", ticker],
        queryFn: () => getIncomeStatement({ ticker, period_type: "annual", limit: 5 }),
    });

    if (!summary) return <div className="p-6 text-muted-foreground text-sm">Loading fundamentals...</div>;

    return (
        <div className="space-y-4 p-1">
            {/* Key metrics grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Card><CardContent className="p-4 space-y-3">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Revenue</p>
                    <p className="text-lg font-mono font-bold">{fmtB(summary.revenue)}</p>
                    <p className="text-xs text-muted-foreground">{summary.period_type} · {fmtDate(summary.period_end)}</p>
                </CardContent></Card>
                <Card><CardContent className="p-4 space-y-3">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Net Income</p>
                    <p className="text-lg font-mono font-bold text-emerald-400">{fmtB(summary.net_income)}</p>
                    <p className="text-xs text-muted-foreground">Margin: {fmtPct(summary.net_margin)}</p>
                </CardContent></Card>
                <Card><CardContent className="p-4 space-y-3">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Free Cash Flow</p>
                    <p className="text-lg font-mono font-bold text-emerald-400">{fmtB(summary.free_cash_flow)}</p>
                    <p className="text-xs text-muted-foreground">OCF: {fmtB(summary.operating_cash_flow)}</p>
                </CardContent></Card>
                <Card><CardContent className="p-4 space-y-3">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">EPS Diluted</p>
                    <p className="text-lg font-mono font-bold">{fmtPrice(summary.eps_diluted)}</p>
                    <p className="text-xs text-muted-foreground">Basic: {fmtPrice(summary.eps_basic)}</p>
                </CardContent></Card>
            </div>

            {/* Margins + ratios */}
            <Card><CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3">Margins & Ratios</p>
                <div className="grid grid-cols-4 md:grid-cols-8 gap-4">
                    <Stat label="Gross Margin" value={fmtPct(summary.gross_margin)} />
                    <Stat label="Op Margin" value={fmtPct(summary.operating_margin)} />
                    <Stat label="Net Margin" value={fmtPct(summary.net_margin)} />
                    <Stat label="EBITDA Margin" value={fmtPct(summary.ebitda_margin)} />
                    <Stat label="ROE" value={fmtPct(summary.roe)} green />
                    <Stat label="ROIC" value={fmtPct(summary.roic)} green />
                    <Stat label="Debt/Equity" value={summary.debt_to_equity?.toFixed(2) ?? "—"} />
                    <Stat label="Current Ratio" value={summary.current_ratio?.toFixed(2) ?? "—"} />
                </div>
            </CardContent></Card>

            {/* Balance sheet */}
            <Card><CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3">Balance Sheet</p>
                <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
                    <Stat label="Total Assets" value={fmtB(summary.total_assets)} />
                    <Stat label="Total Liabilities" value={fmtB(summary.total_liabilities)} />
                    <Stat label="Total Equity" value={fmtB(summary.total_equity)} />
                    <Stat label="Cash" value={fmtB(summary.cash)} green />
                    <Stat label="Total Debt" value={fmtB(summary.total_debt)} />
                    <Stat label="Net Debt" value={fmtB(summary.net_debt)} />
                </div>
            </CardContent></Card>

            {/* Annual income statement history */}
            {history && history.length > 0 && (
                <Card><CardContent className="p-0">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border">
                                <th className="text-left p-3 text-muted-foreground font-medium">Period</th>
                                <th className="text-right p-3 text-muted-foreground font-medium">Revenue</th>
                                <th className="text-right p-3 text-muted-foreground font-medium">Gross Profit</th>
                                <th className="text-right p-3 text-muted-foreground font-medium">Net Income</th>
                                <th className="text-right p-3 text-muted-foreground font-medium">FCF</th>
                                <th className="text-right p-3 text-muted-foreground font-medium">EPS</th>
                                <th className="text-right p-3 text-muted-foreground font-medium">Net Margin</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map((row) => (
                                <tr key={row.period_end} className="border-b border-border hover:bg-muted/50">
                                    <td className="p-3 font-mono text-xs text-muted-foreground">{fmtDate(row.period_end)}</td>
                                    <td className="p-3 font-mono text-right">{fmtB(row.revenue)}</td>
                                    <td className="p-3 font-mono text-right">{fmtB(row.gross_profit)}</td>
                                    <td className="p-3 font-mono text-right text-emerald-400">{fmtB(row.net_income)}</td>
                                    <td className="p-3 font-mono text-right text-emerald-400">{fmtB(row.free_cash_flow)}</td>
                                    <td className="p-3 font-mono text-right">{fmtPrice(row.eps_diluted)}</td>
                                    <td className="p-3 font-mono text-right">{fmtPct(row.net_margin)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent></Card>
            )}
        </div>
    );
}

// ─── Main page ────────────────────────────────────────────────
export default function StockPage() {
    const params = useParams();
    const ticker = (params.ticker as string).toUpperCase();

    const { data: snapshot } = useQuery({
        queryKey: ["snapshot", ticker],
        queryFn: () => getSnapshot({ ticker }),
        refetchInterval: 30000,
    });
    const { data: filings } = useQuery({
        queryKey: ["filings", ticker],
        queryFn: () => getFilings({ ticker, page_size: 10 }),
    });
    const { data: contracts } = useQuery({
        queryKey: ["contracts", ticker],
        queryFn: () => getContracts({ ticker, page_size: 10 }),
    });
    const { data: bills } = useQuery({
        queryKey: ["bills"],
        queryFn: () => getBills({ page_size: 10 }),
    });

    const isUp = (snapshot?.change ?? 0) >= 0;

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold font-mono tracking-tight">{ticker}</h1>
                    <p className="text-sm text-muted-foreground mt-1">Real-time · Alpaca Markets</p>
                </div>
                {snapshot && (
                    <div className="text-right">
                        <p className="text-3xl font-mono font-bold">{fmtPrice(snapshot.price)}</p>
                        <div className={`flex items-center justify-end gap-1 mt-1 ${isUp ? "text-emerald-400" : "text-red-400"}`}>
                            {isUp ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                            <span className="font-mono text-sm">
                                {isUp ? "+" : ""}{snapshot.change?.toFixed(2)} ({isUp ? "+" : ""}{snapshot.change_pct?.toFixed(2)}%)
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* Stats row */}
            {snapshot && (
                <Card><CardContent className="p-4">
                    <div className="grid grid-cols-4 gap-6 md:grid-cols-8">
                        <Stat label="Open" value={fmtPrice(snapshot.open)} />
                        <Stat label="High" value={fmtPrice(snapshot.high)} />
                        <Stat label="Low" value={fmtPrice(snapshot.low)} />
                        <Stat label="Prev Close" value={fmtPrice(snapshot.prev_close)} />
                        <Stat label="Volume" value={fmtVol(snapshot.volume)} />
                        <Stat label="VWAP" value={fmtPrice(snapshot.vwap)} />
                        <Stat label="Bid" value={fmtPrice(snapshot.bid)} />
                        <Stat label="Ask" value={fmtPrice(snapshot.ask)} />
                    </div>
                </CardContent></Card>
            )}

            {/* Chart */}
            <Card>
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono text-muted-foreground flex items-center gap-2">
                        <TrendingUp className="w-4 h-4" /> 1Y Price Chart
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-2">
                    <PriceChart ticker={ticker} />
                </CardContent>
            </Card>

            {/* Tabs */}
            <Tabs defaultValue="fundamentals">
                <TabsList>
                    <TabsTrigger value="fundamentals">Fundamentals</TabsTrigger>
                    <TabsTrigger value="filings">Filings {filings?.total ? `(${filings.total})` : ""}</TabsTrigger>
                    <TabsTrigger value="contracts">Contracts {contracts?.total ? `(${contracts.total})` : ""}</TabsTrigger>
                    <TabsTrigger value="bills">Bills</TabsTrigger>
                </TabsList>

                <TabsContent value="fundamentals" className="mt-4">
                    <FundamentalsTab ticker={ticker} />
                </TabsContent>

                <TabsContent value="filings" className="mt-4">
                    <Card><CardContent className="p-0">
                        <table className="w-full text-sm">
                            <thead><tr className="border-b border-border">
                                <th className="text-left p-3 text-muted-foreground font-medium">Type</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Filed</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Period</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Link</th>
                            </tr></thead>
                            <tbody>
                                {filings?.items.map((f) => (
                                    <tr key={f.id} className="border-b border-border hover:bg-muted/50">
                                        <td className="p-3">
                                            <span className="font-mono text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded">{f.filing_type}</span>
                                        </td>
                                        <td className="p-3 font-mono text-muted-foreground">{fmtDate(f.filed_at)}</td>
                                        <td className="p-3 font-mono text-muted-foreground">{f.period_of_report ? fmtDate(f.period_of_report) : "—"}</td>
                                        <td className="p-3">
                                            {f.url && <button onClick={() => window.open(f.url!, "_blank")} className="text-primary hover:underline text-xs">View →</button>}
                                        </td>
                                    </tr>
                                ))}
                                {!filings?.items.length && (
                                    <tr><td colSpan={4} className="p-6 text-center text-muted-foreground">No filings found for {ticker}</td></tr>
                                )}
                            </tbody>
                        </table>
                    </CardContent></Card>
                </TabsContent>

                <TabsContent value="contracts" className="mt-4">
                    <Card><CardContent className="p-0">
                        <table className="w-full text-sm">
                            <thead><tr className="border-b border-border">
                                <th className="text-left p-3 text-muted-foreground font-medium">Agency</th>
                                <th className="text-right p-3 text-muted-foreground font-medium">Amount</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Type</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Date</th>
                            </tr></thead>
                            <tbody>
                                {contracts?.items.map((c) => (
                                    <tr key={c.id} className="border-b border-border hover:bg-muted/50">
                                        <td className="p-3">{c.agency_name}</td>
                                        <td className="p-3 font-mono text-right text-emerald-400 font-bold">{fmtB(c.total_amount)}</td>
                                        <td className="p-3 font-mono text-xs">{c.award_type}</td>
                                        <td className="p-3 font-mono text-muted-foreground">{c.start_date ? fmtDate(c.start_date) : "—"}</td>
                                    </tr>
                                ))}
                                {!contracts?.items.length && (
                                    <tr><td colSpan={4} className="p-6 text-center text-muted-foreground">No contracts found for {ticker}</td></tr>
                                )}
                            </tbody>
                        </table>
                    </CardContent></Card>
                </TabsContent>

                <TabsContent value="bills" className="mt-4">
                    <Card><CardContent className="p-0">
                        <table className="w-full text-sm">
                            <thead><tr className="border-b border-border">
                                <th className="text-left p-3 text-muted-foreground font-medium">Bill</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Title</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Status</th>
                                <th className="text-left p-3 text-muted-foreground font-medium">Introduced</th>
                            </tr></thead>
                            <tbody>
                                {bills?.items.map((b) => (
                                    <tr key={b.id} className="border-b border-border hover:bg-muted/50">
                                        <td className="p-3 font-mono text-xs">{b.bill_number}</td>
                                        <td className="p-3 max-w-xs"><p className="line-clamp-2">{b.title}</p></td>
                                        <td className="p-3"><span className="font-mono text-xs bg-muted px-2 py-0.5 rounded border border-border">{b.status}</span></td>
                                        <td className="p-3 font-mono text-muted-foreground">{fmtDate(b.introduced_at)}</td>
                                    </tr>
                                ))}
                                {!bills?.items.length && (
                                    <tr><td colSpan={4} className="p-6 text-center text-muted-foreground">No bills found</td></tr>
                                )}
                            </tbody>
                        </table>
                    </CardContent></Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}