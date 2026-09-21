"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getFilings } from "@/lib/api";

const FILING_TYPES = ["10-K", "10-Q", "8-K", "8-K/A", "S-1", "4", "DEF 14A", "SC 13G", "SC 13D"];

const TYPE_STYLE: Record<string, { bg: string; color: string; border: string }> = {
    "10-K": { bg: "rgba(59,130,246,0.08)", color: "#3b82f6", border: "rgba(59,130,246,0.25)" },
    "10-Q": { bg: "rgba(99,102,241,0.08)", color: "#818cf8", border: "rgba(99,102,241,0.25)" },
    "8-K": { bg: "rgba(245,158,11,0.08)", color: "#f59e0b", border: "rgba(245,158,11,0.25)" },
    "8-K/A": { bg: "rgba(245,158,11,0.06)", color: "#d97706", border: "rgba(245,158,11,0.2)" },
    "S-1": { bg: "rgba(16,185,129,0.08)", color: "#10b981", border: "rgba(16,185,129,0.25)" },
    "4": { bg: "rgba(168,85,247,0.08)", color: "#a855f7", border: "rgba(168,85,247,0.25)" },
    "DEF 14A": { bg: "rgba(236,72,153,0.08)", color: "#ec4899", border: "rgba(236,72,153,0.25)" },
};

function fDate(s: string | null | undefined) {
    if (!s) return "—";
    return new Date(s).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function FilingBadge({ type }: { type: string }) {
    const s = TYPE_STYLE[type] ?? { bg: "rgba(74,96,128,0.1)", color: "#4a6080", border: "rgba(74,96,128,0.2)" };
    return (
        <span style={{
            display: "inline-flex", alignItems: "center",
            padding: "2px 7px", borderRadius: 2,
            fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
            background: s.bg, color: s.color, border: `1px solid ${s.border}`,
        }}>
            {type}
        </span>
    );
}

export default function FilingsPage() {
    const [search, setSearch] = useState("");
    const [filingType, setFilingType] = useState("all");
    const [page, setPage] = useState(1);

    const { data, isLoading, error } = useQuery({
        queryKey: ["filings", filingType, page],
        queryFn: () => getFilings({
            filing_type: filingType === "all" ? undefined : filingType,
            page, page_size: 25,
        }),
    });

    const filtered = data?.items.filter((f) =>
        search
            ? f.company_name?.toLowerCase().includes(search.toLowerCase()) ||
            f.ticker?.toLowerCase().includes(search.toLowerCase())
            : true
    );

    return (
        <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "#080d14" }}>

            {/* ── Header ── */}
            <div style={{ padding: "14px 20px", borderBottom: "1px solid #1a2840", background: "#080d14", flexShrink: 0 }}>
                <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
                    <div>
                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.12em", marginBottom: 4 }}>
                            GOVERNMENT · EDGAR
                        </div>
                        <h1 style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 18, fontWeight: 700, color: "#e8eef5", margin: 0, letterSpacing: "0.05em" }}>
                            SEC FILINGS
                        </h1>
                    </div>
                    {data && (
                        <div style={{ textAlign: "right" }}>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 20, fontWeight: 700, color: "#3b82f6" }}>
                                {data.total.toLocaleString()}
                            </div>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.1em" }}>TOTAL FILINGS</div>
                        </div>
                    )}
                </div>

                {/* Controls */}
                <div style={{ display: "flex", gap: 10, marginTop: 14, alignItems: "center" }}>
                    {/* Search */}
                    <div style={{ position: "relative", flex: 1, maxWidth: 320 }}>
                        <input
                            className="ag-input"
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Search company or ticker..."
                            style={{ paddingLeft: 10 }}
                        />
                    </div>

                    {/* Type filter */}
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        <button
                            onClick={() => { setFilingType("all"); setPage(1); }}
                            style={{
                                fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
                                padding: "4px 10px", borderRadius: 2, cursor: "pointer", transition: "all 0.15s",
                                background: filingType === "all" ? "rgba(37,99,235,0.15)" : "rgba(37,99,235,0.04)",
                                color: filingType === "all" ? "#3b82f6" : "#2a3d55",
                                border: filingType === "all" ? "1px solid rgba(37,99,235,0.4)" : "1px solid #1a2840",
                            }}
                        >
                            ALL
                        </button>
                        {FILING_TYPES.map((t) => (
                            <button
                                key={t}
                                onClick={() => { setFilingType(t); setPage(1); }}
                                style={{
                                    fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
                                    padding: "4px 10px", borderRadius: 2, cursor: "pointer", transition: "all 0.15s",
                                    background: filingType === t ? (TYPE_STYLE[t]?.bg ?? "rgba(37,99,235,0.1)") : "rgba(37,99,235,0.02)",
                                    color: filingType === t ? (TYPE_STYLE[t]?.color ?? "#3b82f6") : "#2a3d55",
                                    border: filingType === t ? `1px solid ${TYPE_STYLE[t]?.border ?? "rgba(37,99,235,0.3)"}` : "1px solid #1a2840",
                                }}
                            >
                                {t}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Table ── */}
            <div style={{ flex: 1, overflowY: "auto" }}>
                <table className="ag-table" style={{ width: "100%" }}>
                    <thead style={{ position: "sticky", top: 0, zIndex: 10 }}>
                        <tr>
                            <th style={{ width: 80 }}>TYPE</th>
                            <th>COMPANY</th>
                            <th>TICKER</th>
                            <th>FILED</th>
                            <th>PERIOD</th>
                            <th>ITEMS</th>
                            <th style={{ width: 60 }}>LINK</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading && (
                            [...Array(15)].map((_, i) => (
                                <tr key={i} style={{ borderBottom: "1px solid #0d1520" }}>
                                    {[80, 200, 60, 100, 100, 120, 50].map((w, j) => (
                                        <td key={j} style={{ padding: "8px 14px" }}>
                                            <span className="ag-skeleton" style={{ width: w * 0.6, height: 10 }} />
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
                        {filtered?.map((f) => (
                            <tr
                                key={f.id}
                                style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s", cursor: "default" }}
                                onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                            >
                                <td style={{ padding: "7px 14px" }}>
                                    <FilingBadge type={f.filing_type} />
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#e8eef5" }}>
                                        {f.company_name?.split("(")[0].trim() ?? "—"}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    {f.ticker && (
                                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, fontWeight: 700, color: "#3b82f6" }}>
                                            {f.ticker}
                                        </span>
                                    )}
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                        {fDate(f.filed_at)}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                        {f.period_of_report ? fDate(f.period_of_report) : "—"}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    {f.items && f.items.length > 0 && (
                                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                                            {f.items.slice(0, 3).map((item) => (
                                                <span key={item} style={{
                                                    fontFamily: "JetBrains Mono, monospace", fontSize: 9,
                                                    background: "#111c2a", color: "#4a6080",
                                                    border: "1px solid #1a2840", padding: "1px 5px", borderRadius: 2,
                                                }}>
                                                    {item}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    {f.url && (
                                        <button
                                            onClick={() => window.open(f.url!, "_blank")}
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
                                    NO FILINGS FOUND
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
                        PAGE {data.page} · SHOWING {filtered?.length ?? 0} OF {data.total.toLocaleString()} FILINGS
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
                                transition: "all 0.15s",
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
                                transition: "all 0.15s",
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