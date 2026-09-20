"use client";

import { useParams } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSnapshot, getBars, getFilings, getBills, getContracts } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowUpRight, ArrowDownRight, TrendingUp, Volume2, Activity } from "lucide-react";
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from "lightweight-charts";

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
    return (
        <div className="space-y-1">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">{label}</p>
            <p className="text-sm font-mono font-bold">{value}</p>
            {sub && <p className="text-xs text-muted-foreground font-mono">{sub}</p>}
        </div>
    );
}

function formatPrice(n: number | null | undefined) {
    if (n == null) return "—";
    return `$${n.toFixed(2)}`;
}

function formatVolume(n: number | null | undefined) {
    if (n == null) return "—";
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
    return n.toString();
}

function formatDate(s: string) {
    return new Date(s).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

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
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: "#94a3b8",
            },
            grid: {
                vertLines: { color: "#1e293b" },
                horzLines: { color: "#1e293b" },
            },
            crosshair: {
                vertLine: { color: "#475569" },
                horzLine: { color: "#475569" },
            },
            rightPriceScale: { borderColor: "#1e293b" },
            timeScale: { borderColor: "#1e293b", timeVisible: true },
            width: chartRef.current.clientWidth,
            height: 340,
        });

        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#22c55e",
            downColor: "#ef4444",
            borderUpColor: "#22c55e",
            borderDownColor: "#ef4444",
            wickUpColor: "#22c55e",
            wickDownColor: "#ef4444",
        });

        const volumeSeries = chart.addSeries(HistogramSeries, {
            color: "#334155",
            priceFormat: { type: "volume" },
            priceScaleId: "volume",
        });

        chart.priceScale("volume").applyOptions({
            scaleMargins: { top: 0.85, bottom: 0 },
        });

        const candleData = bars.map((b) => ({
            time: b.timestamp.split("T")[0],
            open: b.open,
            high: b.high,
            low: b.low,
            close: b.close,
        }));

        const volumeData = bars.map((b) => ({
            time: b.timestamp.split("T")[0],
            value: b.volume,
            color: b.close >= b.open ? "#16a34a40" : "#dc262640",
        }));

        candleSeries.setData(candleData);
        volumeSeries.setData(volumeData);
        chart.timeScale().fitContent();

        const handleResize = () => {
            if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth });
        };
        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, [bars]);

    return (
        <div ref={chartRef} className="w-full h-[340px]" />
    );
}

export default function StockPage() {
    const params = useParams();
    const ticker = (params.ticker as string).toUpperCase();

    const { data: snapshot, isLoading } = useQuery({
        queryKey: ["snapshot", ticker],
        queryFn: () => getSnapshot({ ticker }),
        refetchInterval: 30000,
    });

    const { data: filings } = useQuery({
        queryKey: ["filings", ticker],
        queryFn: () => getFilings({ ticker, page_size: 10 }),
    });

    const { data: bills } = useQuery({
        queryKey: ["bills-ticker", ticker],
        queryFn: () => getBills({ page_size: 10 }),
    });

    const { data: contracts } = useQuery({
        queryKey: ["contracts", ticker],
        queryFn: () => getContracts({ ticker, page_size: 10 }),
    });

    const isUp = (snapshot?.change ?? 0) >= 0;

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold font-mono tracking-tight">{ticker}</h1>
                    <p className="text-sm text-muted-foreground mt-1">Real-time quote · Alpaca Markets</p>
                </div>
                {snapshot && (
                    <div className="text-right">
                        <p className="text-3xl font-mono font-bold">{formatPrice(snapshot.price)}</p>
                        <div className={`flex items-center justify-end gap-1 mt-1 ${isUp ? "text-green-400" : "text-red-400"}`}>
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
                <Card>
                    <CardContent className="p-4">
                        <div className="grid grid-cols-4 gap-6 md:grid-cols-8">
                            <StatCard label="Open" value={formatPrice(snapshot.open)} />
                            <StatCard label="High" value={formatPrice(snapshot.high)} />
                            <StatCard label="Low" value={formatPrice(snapshot.low)} />
                            <StatCard label="Prev Close" value={formatPrice(snapshot.prev_close)} />
                            <StatCard label="Volume" value={formatVolume(snapshot.volume)} />
                            <StatCard label="VWAP" value={formatPrice(snapshot.vwap)} />
                            <StatCard label="Bid" value={formatPrice(snapshot.bid)} />
                            <StatCard label="Ask" value={formatPrice(snapshot.ask)} />
                        </div>
                    </CardContent>
                </Card>
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
            <Tabs defaultValue="filings">
                <TabsList>
                    <TabsTrigger value="filings">
                        SEC Filings {filings?.total ? `(${filings.total})` : ""}
                    </TabsTrigger>
                    <TabsTrigger value="contracts">
                        Contracts {contracts?.total ? `(${contracts.total})` : ""}
                    </TabsTrigger>
                    <TabsTrigger value="bills">
                        Bills
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="filings" className="mt-4">
                    <Card>
                        <CardContent className="p-0">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left p-3 text-muted-foreground font-medium">Type</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Filed</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Period</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Link</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filings?.items.map((f) => (
                                        <tr key={f.id} className="border-b border-border hover:bg-muted/50">
                                            <td className="p-3">
                                                <span className="font-mono text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded">
                                                    {f.filing_type}
                                                </span>
                                            </td>
                                            <td className="p-3 font-mono text-muted-foreground">{formatDate(f.filed_at)}</td>
                                            <td className="p-3 font-mono text-muted-foreground">
                                                {f.period_of_report ? formatDate(f.period_of_report) : "—"}
                                            </td>
                                            <td className="p-3">
                                                {f.url && (
                                                    <button
                                                        onClick={() => window.open(f.url!, "_blank")}
                                                        className="text-primary hover:underline text-xs"
                                                    >
                                                        View →
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                    {!filings?.items.length && (
                                        <tr>
                                            <td colSpan={4} className="p-6 text-center text-muted-foreground">
                                                No filings found for {ticker}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="contracts" className="mt-4">
                    <Card>
                        <CardContent className="p-0">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left p-3 text-muted-foreground font-medium">Agency</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Amount</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Type</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {contracts?.items.map((c) => (
                                        <tr key={c.id} className="border-b border-border hover:bg-muted/50">
                                            <td className="p-3">{c.agency_name}</td>
                                            <td className="p-3 font-mono text-emerald-400 font-bold">
                                                ${(c.total_amount / 1_000_000).toFixed(1)}M
                                            </td>
                                            <td className="p-3 font-mono text-xs">{c.award_type}</td>
                                            <td className="p-3 font-mono text-muted-foreground">
                                                {c.start_date ? formatDate(c.start_date) : "—"}
                                            </td>
                                        </tr>
                                    ))}
                                    {!contracts?.items.length && (
                                        <tr>
                                            <td colSpan={4} className="p-6 text-center text-muted-foreground">
                                                No contracts found for {ticker}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="bills" className="mt-4">
                    <Card>
                        <CardContent className="p-0">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left p-3 text-muted-foreground font-medium">Bill</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Title</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Status</th>
                                        <th className="text-left p-3 text-muted-foreground font-medium">Introduced</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {bills?.items.map((b) => (
                                        <tr key={b.id} className="border-b border-border hover:bg-muted/50">
                                            <td className="p-3 font-mono text-xs">{b.bill_number}</td>
                                            <td className="p-3 max-w-xs">
                                                <p className="line-clamp-2">{b.title}</p>
                                            </td>
                                            <td className="p-3">
                                                <span className="font-mono text-xs bg-muted px-2 py-0.5 rounded border border-border">
                                                    {b.status}
                                                </span>
                                            </td>
                                            <td className="p-3 font-mono text-muted-foreground">
                                                {formatDate(b.introduced_at)}
                                            </td>
                                        </tr>
                                    ))}
                                    {!bills?.items.length && (
                                        <tr>
                                            <td colSpan={4} className="p-6 text-center text-muted-foreground">
                                                No bills found
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}