"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getBills } from "@/lib/api";

const CHAMBERS = ["house", "senate"];
const POLICY_AREAS = [
    "economics", "finance", "trade", "energy", "healthcare",
    "technology", "defense", "environment", "infrastructure",
    "agriculture", "housing", "labor", "immigration", "foreign_policy",
];

const STATUS_STYLE: Record<string, { bg: string; color: string; border: string }> = {
    introduced: { bg: "rgba(59,130,246,0.08)", color: "#3b82f6", border: "rgba(59,130,246,0.25)" },
    referred: { bg: "rgba(99,102,241,0.08)", color: "#818cf8", border: "rgba(99,102,241,0.25)" },
    in_committee: { bg: "rgba(245,158,11,0.08)", color: "#f59e0b", border: "rgba(245,158,11,0.25)" },
    passed_committee: { bg: "rgba(245,158,11,0.12)", color: "#d97706", border: "rgba(245,158,11,0.3)" },
    passed_house: { bg: "rgba(16,185,129,0.08)", color: "#10b981", border: "rgba(16,185,129,0.25)" },
    passed_senate: { bg: "rgba(16,185,129,0.12)", color: "#059669", border: "rgba(16,185,129,0.3)" },
    signed: { bg: "rgba(16,185,129,0.15)", color: "#34d399", border: "rgba(16,185,129,0.4)" },
    failed: { bg: "rgba(244,63,94,0.08)", color: "#f43f5e", border: "rgba(244,63,94,0.25)" },
};

const CHAMBER_STYLE: Record<string, { color: string }> = {
    house: { color: "#3b82f6" },
    senate: { color: "#a855f7" },
};

function fDate(s: string | null | undefined) {
    if (!s) return "—";
    return new Date(s).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function StatusBadge({ status }: { status: string }) {
    const s = STATUS_STYLE[status] ?? { bg: "rgba(74,96,128,0.1)", color: "#4a6080", border: "rgba(74,96,128,0.2)" };
    return (
        <span style={{
            display: "inline-flex", alignItems: "center",
            padding: "2px 7px", borderRadius: 2,
            fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
            background: s.bg, color: s.color, border: `1px solid ${s.border}`,
            whiteSpace: "nowrap",
        }}>
            {status.replace(/_/g, " ").toUpperCase()}
        </span>
    );
}

export default function BillsPage() {
    const [search, setSearch] = useState("");
    const [chamber, setChamber] = useState("all");
    const [policyArea, setPolicyArea] = useState("all");
    const [page, setPage] = useState(1);

    const { data, isLoading, error } = useQuery({
        queryKey: ["bills", chamber, policyArea, page],
        queryFn: () => getBills({
            chamber: chamber === "all" ? undefined : chamber,
            policy_area: policyArea === "all" ? undefined : policyArea,
            page, page_size: 25,
        }),
    });

    const filtered = data?.items.filter((b) =>
        search
            ? b.title?.toLowerCase().includes(search.toLowerCase()) ||
            b.bill_number?.toLowerCase().includes(search.toLowerCase())
            : true
    );

    return (
        <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "#080d14" }}>

            {/* ── Header ── */}
            <div style={{ padding: "14px 20px", borderBottom: "1px solid #1a2840", background: "#080d14", flexShrink: 0 }}>
                <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 14 }}>
                    <div>
                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.12em", marginBottom: 4 }}>
                            GOVERNMENT · GOVTRACK · 119TH CONGRESS
                        </div>
                        <h1 style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 18, fontWeight: 700, color: "#e8eef5", margin: 0, letterSpacing: "0.05em" }}>
                            CONGRESSIONAL BILLS
                        </h1>
                    </div>
                    {data && (
                        <div style={{ textAlign: "right" }}>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 20, fontWeight: 700, color: "#10b981" }}>
                                {data.total.toLocaleString()}
                            </div>
                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.1em" }}>TOTAL BILLS</div>
                        </div>
                    )}
                </div>

                {/* Controls */}
                <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <input
                        className="ag-input"
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search bills..."
                        style={{ maxWidth: 260 }}
                    />

                    {/* Chamber filter */}
                    <div style={{ display: "flex", gap: 4 }}>
                        {["all", ...CHAMBERS].map((c) => (
                            <button
                                key={c}
                                onClick={() => { setChamber(c); setPage(1); }}
                                style={{
                                    fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
                                    padding: "4px 10px", borderRadius: 2, cursor: "pointer", transition: "all 0.15s",
                                    background: chamber === c ? "rgba(37,99,235,0.12)" : "rgba(37,99,235,0.02)",
                                    color: chamber === c ? "#3b82f6" : "#2a3d55",
                                    border: chamber === c ? "1px solid rgba(37,99,235,0.35)" : "1px solid #1a2840",
                                }}
                            >
                                {c.toUpperCase()}
                            </button>
                        ))}
                    </div>

                    {/* Policy area select */}
                    <select
                        value={policyArea}
                        onChange={(e) => { setPolicyArea(e.target.value); setPage(1); }}
                        style={{
                            fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
                            padding: "4px 10px", borderRadius: 2, cursor: "pointer",
                            background: "#080d14", color: policyArea === "all" ? "#2a3d55" : "#3b82f6",
                            border: "1px solid #1a2840", outline: "none",
                        }}
                    >
                        <option value="all">ALL POLICY AREAS</option>
                        {POLICY_AREAS.map((a) => (
                            <option key={a} value={a}>{a.replace(/_/g, " ").toUpperCase()}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* ── Table ── */}
            <div style={{ flex: 1, overflowY: "auto" }}>
                <table className="ag-table" style={{ width: "100%" }}>
                    <thead style={{ position: "sticky", top: 0, zIndex: 10 }}>
                        <tr>
                            <th style={{ width: 90 }}>BILL NO.</th>
                            <th>TITLE</th>
                            <th style={{ width: 140 }}>STATUS</th>
                            <th style={{ width: 80 }}>CHAMBER</th>
                            <th style={{ width: 120 }}>POLICY AREA</th>
                            <th style={{ width: 130 }}>SPONSOR</th>
                            <th style={{ width: 100 }}>INTRODUCED</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading && (
                            [...Array(15)].map((_, i) => (
                                <tr key={i} style={{ borderBottom: "1px solid #0d1520" }}>
                                    {[70, 300, 120, 70, 100, 110, 80].map((w, j) => (
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
                        {filtered?.map((b) => (
                            <tr
                                key={b.id}
                                style={{ borderBottom: "1px solid #0d1520", transition: "background 0.1s" }}
                                onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                            >
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, fontWeight: 700, color: "#3b82f6" }}>
                                        {b.bill_number}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px", maxWidth: 360 }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#e8eef5", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                                        {b.title}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <StatusBadge status={b.status} />
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{
                                        fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
                                        color: CHAMBER_STYLE[b.chamber]?.color ?? "#4a6080",
                                    }}>
                                        {b.chamber.toUpperCase()}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#4a6080" }}>
                                        {b.policy_area.replace(/_/g, " ")}
                                    </span>
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    {b.sponsor_name && (
                                        <div>
                                            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#e8eef5" }}>
                                                {b.sponsor_name.split(" ").slice(-1)[0]}
                                            </div>
                                            {b.sponsor_party && (
                                                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55" }}>
                                                    {b.sponsor_party} · {b.sponsor_state}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </td>
                                <td style={{ padding: "7px 14px" }}>
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>
                                        {fDate(b.introduced_at)}
                                    </span>
                                </td>
                            </tr>
                        ))}
                        {filtered?.length === 0 && !isLoading && (
                            <tr>
                                <td colSpan={7} style={{ padding: "40px 14px", textAlign: "center", fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#2a3d55" }}>
                                    NO BILLS FOUND
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
                        PAGE {data.page} · SHOWING {filtered?.length ?? 0} OF {data.total.toLocaleString()} BILLS
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