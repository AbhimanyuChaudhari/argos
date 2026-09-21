"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getContracts } from "@/lib/api";

function fDate(s: string | null | undefined) {
    if (!s) return "—";
    return new Date(s).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function fAmount(n: number | null | undefined) {
    if (n == null) return "—";
    if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
    if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
}

function amountColor(n: number | null | undefined) {
    if (!n) return "#4a6080";
    if (n >= 1e9) return "#f43f5e";
    if (n >= 1e8) return "#f59e0b";
    if (n >= 1e6) return "#10b981";
    return "#e8eef5";
}

export default function ContractsPage() {
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);

    const { data, isLoading, error } = useQuery({
        queryKey: ["contracts", page],
        queryFn: () => getContracts({ page, page_size: 25 }),
    });

    const filtered = data?.items.filter((c) =>
        search
            ? c.recipient_name?.toLowerCase().includes(search.toLowerCase()) ||
            c.agency_name?.toLowerCase().includes(search.toLowerCase()) ||
            c.ticker?.toLowerCase().includes(search.toLowerCase())
            : true
    );

    // Stats
    const totalValue = data?.items.reduce((sum, c) => sum + (c.total_amount ?? 0), 0);

    return (
        <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "#080d14" }}>

            {/* ── Header ── */}
            <div style={{ padding: "14px 20px", borderBottom: "1px solid #1a2840", background: "#080d14", flexShrink: 0 }}>
                <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 14 }}>
                    <div>
                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.12em", marginBottom: 4 }}>
                            GOVERNMENT · USASPENDING.GOV
                        </div>
                        <h1 style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 18, fontWeight: 700, color: "#e8eef5", margin: 0, letterSpacing: "0.05em" }}>
                            FEDERAL CONTRACTS
                        </h1>
                    </div>
                    <div style={{ display: "flex", gap: 24 }}>
                        {data && (
                            <>
                                <div style={{ textAlign: "right" }}>
                                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 20, fontWeight: 700, color: "#f59e0b" }}>
                                        {data.total.toLocaleString()}
                                    </div>
                                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.1em" }}>CONTRACTS</div>
                                </div>
                                {totalValue != null && (
                                    <div style={{ textAlign: "right" }}>
                                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 20, fontWeight: 700, color: "#f43f5e" }}>
                                            {fAmount(totalValue)}
                                        </div>
                                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.1em" }}>PAGE VALUE</div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>

                {/* Search */}
                <input
                    className="ag-input"
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search recipient, agency or ticker..."
                    style={{ maxWidth: 360 }}
                />
            </div>

            {/* ── Table ── */}
            <div style={{ flex: 1, overflowY: "auto" }}>
                <table className="ag-table" style={{ width: "100%" }}>
                    <thead style={{ position: "sticky", top: 0, zIndex: 10 }}>
                        <tr>
                            <th>RECIPIENT</th>
                            <th>AGENCY</th>
                            <th className="r">AMOUNT</th>
                            <th style={{ width: 100 }}>TYPE</th>
                            <th style={{ width: 100 }}>START</th>
                            <th style={{ width: 100 }}>END</th>
                            <th style={{ width: 60 }}>LINK</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading && (
                            [...Array(15)].map((_, i) => (
                                <tr key={i} style={{ borderBottom: "1px solid #0d1520" }}>
                                    {[180, 160, 80, 80, 80, 80, 40].map((w, j) => (
                                        <td key={j} style={{ padding: "8px 14px" }}>
                                            <span className="ag-skeleton" style={{ width: w * 0.7, height: 10 }} />
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                        {error && (
                            <tr>
                                <td colSpan={7} style={{ padding: "40px 14px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#f43f5e" }}>
                                    BACKEND UNAVAILABLE — IS THE API RUNNING ON PORT 8001?
                                </td>
                            </tr>
                        )}
                        {filtered?.map((c) => (
                            <tr
                                key={c.id}
                                style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                                onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                            >
                                <td style={{ padding: "7px 14px" }}>
                                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#e8eef5", fontWeight: 600 }}>
                                        {c.recipient_name}
                                    </div>
                                    {c.ticker && (
                                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, color: "#3b82f6", marginTop: 2 }}>
                                            {c.ticker}
                                        </div>
                                    )}
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                        {c.agency_name}
                                    </div>
                                    {c.sub_agency_name && c.sub_agency_name !== c.agency_name && (
                                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", marginTop: 2 }}>
                                            {c.sub_agency_name}
                                        </div>
                                    )}
                                </td>
                                <td style={{ padding: "7px 14px", textAlign: "right" }}>
                                    <span style={{
                                        fontFamily: "JetBrains Mono, monospace", fontSize: 12, fontWeight: 700,
                                        color: amountColor(c.total_amount),
                                    }}>
                                        {fAmount(c.total_amount)}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{
                                        fontFamily: "JetBrains Mono, monospace", fontSize: 9,
                                        background: "#111c2a", color: "#4a6080",
                                        border: "1px solid #1a2840", padding: "2px 6px", borderRadius: 2,
                                    }}>
                                        {c.award_type}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                        {fDate(c.start_date)}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                        {fDate(c.end_date)}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    {c.url && (
                                        <button
                                            onClick={() => window.open(c.url!, "_blank")}
                                            style={{
                                                fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700,
                                                color: "#2a3d55", background: "none", border: "none", cursor: "pointer",
                                                letterSpacing: "0.06em", transition: "color 0.15s",
                                            }}
                                            onMouseEnter={(e) => (e.currentTarget.style.color = "#3b82f6")}
                                            onMouseLeave={(e) => (e.currentTarget.style.color = "#2a3d55")}
                                        >
                                            VIEW →
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                        {filtered?.length === 0 && !isLoading && (
                            <tr>
                                <td colSpan={7} style={{ padding: "40px 14px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#2a3d55" }}>
                                    NO CONTRACTS FOUND
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* ── Pagination ── */}
            {data && (
                <div style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "8px 20px", borderTop: "1px solid #1a2840", background: "#080d14", flexShrink: 0,
                }}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#2a3d55" }}>
                        PAGE {data.page} · SHOWING {filtered?.length ?? 0} OF {data.total.toLocaleString()} CONTRACTS
                    </span>
                    <div style={{ display: "flex", gap: 6 }}>
                        <button
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1}
                            style={{
                                fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.08em",
                                padding: "5px 14px", borderRadius: 2, cursor: page === 1 ? "not-allowed" : "pointer",
                                background: "transparent", color: page === 1 ? "#1a2840" : "#4a6080",
                                border: `1px solid ${page === 1 ? "#111c2a" : "#1a2840"}`,
                            }}
                        >
                            ← PREV
                        </button>
                        <button
                            onClick={() => setPage((p) => p + 1)}
                            disabled={!data.has_more}
                            style={{
                                fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.08em",
                                padding: "5px 14px", borderRadius: 2, cursor: !data.has_more ? "not-allowed" : "pointer",
                                background: data.has_more ? "rgba(37,99,235,0.08)" : "transparent",
                                color: data.has_more ? "#3b82f6" : "#1a2840",
                                border: `1px solid ${data.has_more ? "rgba(37,99,235,0.3)" : "#111c2a"}`,
                            }}
                        >
                            NEXT →
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}