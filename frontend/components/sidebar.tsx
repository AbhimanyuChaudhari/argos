"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";

const GOV_LINKS = [
    { label: "Filings", href: "/government/filings" },
    { label: "Bills", href: "/government/bills" },
    { label: "Contracts", href: "/government/contracts" },
    { label: "Lobbying", href: "/government/lobbying" },
];

const QUICK = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"];

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const [ticker, setTicker] = useState("");
    const [govOpen, setGovOpen] = useState(true);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const t = ticker.trim().toUpperCase();
        if (t) { router.push(`/stock/${t}`); setTicker(""); }
    };

    const isActive = (href: string) => pathname === href;
    const isGovActive = pathname.startsWith("/government");

    return (
        <aside
            style={{ background: "#080d14", borderRight: "1px solid #1a2840" }}
            className="w-48 flex flex-col h-screen shrink-0"
        >
            {/* Logo */}
            <div style={{ borderBottom: "1px solid #1a2840", padding: "14px 16px" }}>
                <div className="flex items-center gap-2.5">
                    {/* Argos eye icon — custom SVG */}
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <circle cx="10" cy="10" r="9" stroke="#2563eb" strokeWidth="1.5" strokeOpacity="0.6" />
                        <circle cx="10" cy="10" r="5" stroke="#3b82f6" strokeWidth="1" />
                        <circle cx="10" cy="10" r="2" fill="#2563eb" />
                        <circle cx="10" cy="10" r="1" fill="#93c5fd" />
                    </svg>
                    <div>
                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "12px", fontWeight: 700, letterSpacing: "0.15em", color: "#e8eef5" }}>
                            ARGOS
                        </div>
                        <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "#2a3d55", letterSpacing: "0.1em" }}>
                            TERMINAL
                        </div>
                    </div>
                </div>
            </div>

            {/* Ticker search */}
            <div style={{ padding: "10px 10px", borderBottom: "1px solid #1a2840" }}>
                <form onSubmit={handleSearch}>
                    <input
                        type="text"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        placeholder="Symbol lookup..."
                        maxLength={10}
                        className="ag-input"
                        style={{ fontSize: "10px", padding: "5px 8px" }}
                    />
                </form>
                <div className="flex flex-wrap gap-1.5 mt-2">
                    {QUICK.map((t) => (
                        <button
                            key={t}
                            onClick={() => router.push(`/stock/${t}`)}
                            style={{
                                fontFamily: "JetBrains Mono, monospace",
                                fontSize: "9px",
                                color: "#2a3d55",
                                background: "none",
                                border: "none",
                                cursor: "pointer",
                                padding: 0,
                                transition: "color 0.15s",
                            }}
                            onMouseEnter={(e) => (e.currentTarget.style.color = "#3b82f6")}
                            onMouseLeave={(e) => (e.currentTarget.style.color = "#2a3d55")}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {/* Nav */}
            <nav style={{ flex: 1, padding: "8px 0", overflowY: "auto" }}>

                {/* Dashboard */}
                <Link
                    href="/"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        padding: "7px 16px",
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "10px",
                        fontWeight: 600,
                        letterSpacing: "0.08em",
                        textDecoration: "none",
                        color: isActive("/") ? "#3b82f6" : "#2a3d55",
                        background: isActive("/") ? "rgba(37,99,235,0.08)" : "transparent",
                        borderLeft: isActive("/") ? "2px solid #2563eb" : "2px solid transparent",
                        transition: "all 0.15s",
                    }}
                >
                    DASHBOARD
                </Link>

                {/* Government group */}
                <div>
                    <button
                        onClick={() => setGovOpen(!govOpen)}
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            width: "100%",
                            padding: "7px 16px",
                            fontFamily: "JetBrains Mono, monospace",
                            fontSize: "10px",
                            fontWeight: 600,
                            letterSpacing: "0.08em",
                            color: isGovActive ? "#3b82f6" : "#2a3d55",
                            background: "none",
                            border: "none",
                            borderLeft: isGovActive ? "2px solid #2563eb" : "2px solid transparent",
                            cursor: "pointer",
                            transition: "all 0.15s",
                        }}
                    >
                        <span>GOVERNMENT</span>
                        <span style={{ fontSize: "8px", opacity: 0.5 }}>{govOpen ? "▲" : "▼"}</span>
                    </button>
                    {govOpen && (
                        <div style={{ borderLeft: "1px solid #1a2840", marginLeft: "22px" }}>
                            {GOV_LINKS.map((item) => (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    style={{
                                        display: "block",
                                        padding: "5px 12px",
                                        fontFamily: "JetBrains Mono, monospace",
                                        fontSize: "9px",
                                        letterSpacing: "0.06em",
                                        textDecoration: "none",
                                        color: isActive(item.href) ? "#3b82f6" : "#2a3d55",
                                        background: isActive(item.href) ? "rgba(37,99,235,0.06)" : "transparent",
                                        transition: "all 0.15s",
                                    }}
                                    onMouseEnter={(e) => { if (!isActive(item.href)) e.currentTarget.style.color = "#8aa4c0"; }}
                                    onMouseLeave={(e) => { if (!isActive(item.href)) e.currentTarget.style.color = "#2a3d55"; }}
                                >
                                    {item.label.toUpperCase()}
                                </Link>
                            ))}
                        </div>
                    )}
                </div>

                {/* Global */}
                <Link
                    href="/global"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        padding: "7px 16px",
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "10px",
                        fontWeight: 600,
                        letterSpacing: "0.08em",
                        textDecoration: "none",
                        color: isActive("/global") ? "#3b82f6" : "#2a3d55",
                        background: isActive("/global") ? "rgba(37,99,235,0.08)" : "transparent",
                        borderLeft: isActive("/global") ? "2px solid #2563eb" : "2px solid transparent",
                        transition: "all 0.15s",
                    }}
                >
                    GLOBAL
                </Link>

                {/* Settings */}
                <Link
                    href="/settings"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        padding: "7px 16px",
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "10px",
                        fontWeight: 600,
                        letterSpacing: "0.08em",
                        textDecoration: "none",
                        color: isActive("/settings") ? "#3b82f6" : "#2a3d55",
                        background: isActive("/settings") ? "rgba(37,99,235,0.08)" : "transparent",
                        borderLeft: isActive("/settings") ? "2px solid #2563eb" : "2px solid transparent",
                        transition: "all 0.15s",
                    }}
                >
                    SETTINGS
                </Link>
            </nav>

            {/* Footer */}
            <div style={{ borderTop: "1px solid #1a2840", padding: "8px 16px" }}>
                <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "8px", color: "#2a3d55", letterSpacing: "0.1em" }}>
                    v0.1.0 · LOCAL
                </div>
            </div>
        </aside>
    );
}