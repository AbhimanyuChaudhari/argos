"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getLobbying } from "@/lib/api";

function fDate(s: string | null | undefined) {
    if (!s) return "—";
    return new Date(s).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function fAmount(n: number | null | undefined) {
    if (n == null) return "—";
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
    if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
    return `$${n.toLocaleString()}`;
}

export default function LobbyingPage() {
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);

    const { data, isLoading, error } = useQuery({
        queryKey: ["lobbying", page],
        queryFn: () => getLobbying({ page, page_size: 25 }),
    });

    const filtered = data?.items.filter((l) =>
        search
            ? l.client_name?.toLowerCase().includes(search.toLowerCase()) ||
            l.lobbyist_firm?.toLowerCase().includes(search.toLowerCase()) ||
            l.ticker?.toLowerCase().includes(search.toLowerCase())
            : true
    );

    const isEmpty = !isLoading && (!filtered || filtered.length === 0);

    return (
        <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "#080d14" }}>

            {/* ── Header ── */}
            <div style={{ padding: "14px 20px", borderBottom: "1px solid #1a2840", background: "#080d14", flexShrink: 0 }}>
                <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 14 }}>
                    <div>
                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.12em", marginBottom: 4 }}>
                            GOVERNMENT · OPENSECRETS
                        </div>
                        <h1 style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 18, fontWeight: 700, color: "#e8eef5", margin: 0, letterSpacing: "0.05em" }}>
                            LOBBYING DISCLOSURES
                        </h1>
                    </div>
                    {data && data.total > 0 && (
                        <div style={{ textAlign: "right" }}>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 20, fontWeight: 700, color: "#a855f7" }}>
                                {data.total.toLocaleString()}
                            </div>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.1em" }}>DISCLOSURES</div>
                        </div>
                    )}
                </div>

                <input
                    className="ag-input"
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search client, firm or ticker..."
                    style={{ maxWidth: 360 }}
                />
            </div>

            {/* ── Table or empty state ── */}
            <div style={{ flex: 1, overflowY: "auto" }}>
                {isEmpty && !error ? (
                    /* ── Empty state ── */
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 20 }}>
                        <div style={{ textAlign: "center" }}>
                            {/* Lock icon */}
                            <div style={{ marginBottom: 16, opacity: 0.3 }}>
                                <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                                    <rect x="8" y="18" width="24" height="18" rx="2" stroke="#4a6080" strokeWidth="1.5" />
                                    <path d="M13 18V13a7 7 0 0114 0v5" stroke="#4a6080" strokeWidth="1.5" strokeLinecap="round" />
                                    <circle cx="20" cy="27" r="2" fill="#4a6080" />
                                    <line x1="20" y1="29" x2="20" y2="32" stroke="#4a6080" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                            </div>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 13, fontWeight: 700, color: "#4a6080", letterSpacing: "0.08em", marginBottom: 8 }}>
                                NO LOBBYING DATA
                            </div>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#2a3d55", marginBottom: 20, letterSpacing: "0.04em" }}>
                                OpenSecrets API key required to ingest disclosure data
                            </div>

                            {/* Steps */}
                            <div style={{ textAlign: "left", maxWidth: 420, background: "#0d1520", border: "1px solid #1a2840", borderRadius: 4, padding: "16px 20px" }}>
                                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.12em", marginBottom: 12 }}>
                                    SETUP INSTRUCTIONS
                                </div>
                                {[
                                    { step: "01", text: "Register at opensecrets.org/api/admin" },
                                    { step: "02", text: 'Add OPENSECRETS_API_KEY to ingestion/.env' },
                                    { step: "03", text: "Run: python run_all.py" },
                                    { step: "04", text: "Lobbying data will appear here" },
                                ].map((s) => (
                                    <div key={s.step} style={{ display: "flex", gap: 12, marginBottom: 10, alignItems: "flex-start" }}>
                                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#1a2840", fontWeight: 700, flexShrink: 0, marginTop: 1 }}>
                                            {s.step}
                                        </span>
                                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                            {s.text}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    <table className="ag-table" style={{ width: "100%" }}>
                        <thead style={{ position: "sticky", top: 0, zIndex: 10 }}>
                            <tr>
                                <th>CLIENT</th>
                                <th>LOBBYIST FIRM</th>
                                <th className="r">AMOUNT</th>
                                <th style={{ width: 60 }}>YEAR</th>
                                <th style={{ width: 60 }}>QTR</th>
                                <th>ISSUES</th>
                                <th style={{ width: 60 }}>LINK</th>
                            </tr>
                        </thead>
                        <tbody>
                            {isLoading && (
                                [...Array(15)].map((_, i) => (
                                    <tr key={i} style={{ borderBottom: "1px solid #0d1520" }}>
                                        {[180, 160, 80, 50, 50, 150, 40].map((w, j) => (
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
                            {filtered?.map((item) => (
                                <tr
                                    key={item.id}
                                    style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                                    onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                                >
                                    <td style={{ padding: "7px 14px" }}>
                                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#e8eef5", fontWeight: 600 }}>
                                            {item.client_name}
                                        </div>
                                        {item.ticker && (
                                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, color: "#3b82f6", marginTop: 2 }}>
                                                {item.ticker}
                                            </div>
                                        )}
                                    </td>
                                    <td style={{ padding: "7px 14px" }}>
                                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                            {item.lobbyist_firm ?? "—"}
                                        </span>
                                    </td>
                                    <td style={{ padding: "7px 14px", textAlign: "right" }}>
                                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12, fontWeight: 700, color: "#10b981" }}>
                                            {fAmount(item.amount)}
                                        </span>
                                    </td>
                                    <td style={{ padding: "7px 14px" }}>
                                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                            {item.year ?? "—"}
                                        </span>
                                    </td>
                                    <td style={{ padding: "7px 14px" }}>
                                        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                            {item.quarter ? `Q${item.quarter}` : "—"}
                                        </span>
                                    </td>
                                    <td style={{ padding: "7px 14px" }}>
                                        {item.issues && item.issues.length > 0 && (
                                            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                                                {item.issues.slice(0, 2).map((issue: string) => (
                                                    <span key={issue} style={{
                                                        fontFamily: "JetBrains Mono, monospace", fontSize: 9,
                                                        background: "#111c2a", color: "#4a6080",
                                                        border: "1px solid #1a2840", padding: "1px 5px", borderRadius: 2,
                                                    }}>
                                                        {issue}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </td>
                                    <td style={{ padding: "7px 14px" }}>
                                        {item.url && (
                                            <button
                                                onClick={() => window.open(item.url!, "_blank")}
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
                        </tbody>
                    </table>
                )}
            </div>

            {/* ── Pagination ── */}
            {data && data.total > 0 && (
                <div style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "8px 20px", borderTop: "1px solid #1a2840", background: "#080d14", flexShrink: 0,
                }}>
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#2a3d55" }}>
                        PAGE {data.page} · SHOWING {filtered?.length ?? 0} OF {data.total.toLocaleString()} DISCLOSURES
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