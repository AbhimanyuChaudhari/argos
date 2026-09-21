"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getSnapshot } from "@/lib/api";

function fP(n: number | null | undefined) {
  if (n == null) return "—";
  return `$${n.toFixed(2)}`;
}

function WatchlistRow({ ticker }: { ticker: string }) {
  const router = useRouter();
  const { data, isLoading } = useQuery({
    queryKey: ["snapshot", ticker],
    queryFn: () => getSnapshot({ ticker }),
    refetchInterval: 30000,
  });
  const isUp = (data?.change_pct ?? 0) >= 0;

  return (
    <tr
      onClick={() => router.push(`/stock/${ticker}`)}
      style={{ borderBottom: "1px solid #0d1520", cursor: "pointer", transition: "background 0.1s" }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      <td style={{ padding: "6px 14px", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", fontWeight: 700, color: "#8aa4c0" }}>
        {ticker}
      </td>
      <td style={{ padding: "6px 14px", textAlign: "right", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", color: "#e8eef5" }}>
        {isLoading ? <span className="ag-skeleton" style={{ width: 52, height: 10 }} /> : fP(data?.price)}
      </td>
      <td style={{ padding: "6px 14px", textAlign: "right", fontFamily: "JetBrains Mono, monospace", fontSize: "11px", fontWeight: 700, color: isUp ? "#10b981" : "#f43f5e" }}>
        {isLoading ? <span className="ag-skeleton" style={{ width: 40, height: 10 }} /> : `${isUp ? "+" : ""}${(data?.change_pct ?? 0).toFixed(2)}%`}
      </td>
    </tr>
  );
}

const WATCHLIST = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "META", "AMZN", "JPM", "V"];

const GOV = [
  { tag: "EDGAR", label: "SEC Filings", href: "/government/filings", count: "500+", sub: "10-K · 10-Q · 8-K · DEF 14A", accent: "#3b82f6" },
  { tag: "GOVTRACK", label: "Congressional Bills", href: "/government/bills", count: "100+", sub: "119th Congress · Live tracking", accent: "#10b981" },
  { tag: "USASPENDING", label: "Federal Contracts", href: "/government/contracts", count: "100+", sub: "All agencies · All award types", accent: "#f59e0b" },
  { tag: "OPENSECRETS", label: "Lobbying", href: "/government/lobbying", count: "—", sub: "Pending API key", accent: "#2a3d55" },
];

const STATUS = [
  { label: "EDGAR XBRL Pipeline", ok: true },
  { label: "Alpaca Market Data", ok: true },
  { label: "PostgreSQL", ok: true },
  { label: "Redis", ok: true },
  { label: "OpenSecrets", ok: null },
  { label: "Polygon Bars", ok: null },
];

const ROADMAP = [
  "Macro Dashboard — FRED · ECB · RBI",
  "News Feed — NewsAPI · Benzinga",
  "Earnings Calendar — EPS beat/miss",
  "Two-stage DCF Engine",
  "Peer Comparison — Sector benchmarks",
  "Political Risk — GDELT tracker",
];

export default function HomePage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [time, setTime] = useState("");

  useEffect(() => {
    const tick = () => {
      setTime(new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const t = search.trim().toUpperCase();
    if (t) router.push(`/stock/${t}`);
  };

  const S = (style: React.CSSProperties) => style;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "#080d14" }}>

      {/* ── Top bar ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", height: 36, borderBottom: "1px solid #1a2840", background: "#080d14", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, fontWeight: 700, letterSpacing: "0.15em", color: "#e8eef5" }}>ARGOS</span>
          <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.08em" }}>FINANCIAL INTELLIGENCE TERMINAL</span>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#10b981", boxShadow: "0 0 6px rgba(16,185,129,0.8)", display: "inline-block" }} />
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#10b981", letterSpacing: "0.1em" }}>LIVE</span>
          </div>
        </div>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#2a3d55", letterSpacing: "0.08em" }}>{time} ET</span>
      </div>

      {/* ── Body ── */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

        {/* ── Watchlist column ── */}
        <div style={{ width: 220, borderRight: "1px solid #1a2840", display: "flex", flexDirection: "column", flexShrink: 0 }}>
          <div className="ag-panel-header">Watchlist</div>

          {/* Search */}
          <div style={{ padding: "8px 10px", borderBottom: "1px solid #1a2840" }}>
            <form onSubmit={handleSearch}>
              <input
                className="ag-input"
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value.toUpperCase())}
                placeholder="Lookup symbol..."
                maxLength={10}
                style={{ fontSize: 10, padding: "5px 8px" }}
              />
            </form>
          </div>

          {/* Table */}
          <div style={{ overflowY: "auto", flex: 1 }}>
            <table className="ag-table" style={{ width: "100%" }}>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th className="r">Last</th>
                  <th className="r">Chg%</th>
                </tr>
              </thead>
              <tbody>
                {WATCHLIST.map((t) => <WatchlistRow key={t} ticker={t} />)}
              </tbody>
            </table>
          </div>

          <div style={{ borderTop: "1px solid #1a2840", padding: "6px 14px" }}>
            <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 8, color: "#2a3d55", letterSpacing: "0.1em" }}>ALPACA · 30s</span>
          </div>
        </div>

        {/* ── Main ── */}
        <div style={{ flex: 1, overflowY: "auto" }}>

          {/* Search hero */}
          <div style={{ padding: "20px 24px", borderBottom: "1px solid #1a2840", background: "#080d14" }}>
            <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", letterSpacing: "0.12em", marginBottom: 10 }}>
              SECURITY LOOKUP
            </div>
            <form onSubmit={handleSearch} style={{ display: "flex", gap: 8, maxWidth: 440 }}>
              <input
                className="ag-input"
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value.toUpperCase())}
                placeholder="Enter ticker symbol (AAPL, MSFT, NVDA...)"
                maxLength={10}
                style={{ flex: 1, fontSize: 12 }}
              />
              <button className="ag-btn ag-btn-primary" type="submit">GO →</button>
            </form>
            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              {["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "AMZN", "META"].map((t) => (
                <button
                  key={t}
                  onClick={() => router.push(`/stock/${t}`)}
                  style={{
                    fontFamily: "JetBrains Mono, monospace", fontSize: 9, letterSpacing: "0.06em",
                    color: "#2a3d55", background: "rgba(37,99,235,0.04)", border: "1px solid #1a2840",
                    padding: "3px 8px", borderRadius: 2, cursor: "pointer", transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#3b82f6"; e.currentTarget.style.borderColor = "rgba(37,99,235,0.4)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#2a3d55"; e.currentTarget.style.borderColor = "#1a2840"; }}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Government modules */}
          <div style={{ borderBottom: "1px solid #1a2840" }}>
            <div className="ag-panel-header">Government Intelligence</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
              {GOV.map((m, i) => (
                <Link
                  key={m.label}
                  href={m.href}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "16px 20px",
                    textDecoration: "none",
                    borderRight: i % 2 === 0 ? "1px solid #1a2840" : "none",
                    borderBottom: i < 2 ? "1px solid #1a2840" : "none",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#0d1520")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                    <div style={{ width: 2, height: 32, background: m.accent, borderRadius: 1, flexShrink: 0, opacity: 0.8, marginTop: 2 }} />
                    <div>
                      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 8, fontWeight: 700, letterSpacing: "0.12em", color: m.accent, marginBottom: 4 }}>{m.tag}</div>
                      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, fontWeight: 700, color: "#e8eef5", marginBottom: 3 }}>{m.label}</div>
                      <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55" }}>{m.sub}</div>
                    </div>
                  </div>
                  <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 12 }}>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 24, fontWeight: 700, color: "#e8eef5", lineHeight: 1 }}>{m.count}</div>
                    <div style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 8, color: "#2a3d55", marginTop: 3, letterSpacing: "0.1em" }}>RECORDS</div>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Bottom: status + roadmap */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", borderBottom: "1px solid #1a2840" }}>

            {/* Status */}
            <div style={{ borderRight: "1px solid #1a2840" }}>
              <div className="ag-panel-header">System Status</div>
              {STATUS.map((s) => (
                <div key={s.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "9px 20px", borderBottom: "1px solid #0d1520" }}>
                  <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>{s.label}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span className={`ag-dot ${s.ok === true ? "ag-dot-up" : s.ok === false ? "ag-dot-down" : "ag-dot-warn"}`} />
                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, fontWeight: 700, letterSpacing: "0.08em", color: s.ok === true ? "#10b981" : s.ok === false ? "#f43f5e" : "#f59e0b" }}>
                      {s.ok === true ? "OK" : s.ok === false ? "ERROR" : "WARN"}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Roadmap */}
            <div>
              <div className="ag-panel-header">Roadmap</div>
              {ROADMAP.map((item, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "9px 20px", borderBottom: "1px solid #0d1520", opacity: 0.35 }}>
                  <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 9, color: "#2a3d55", width: 16, flexShrink: 0 }}>{String(i + 1).padStart(2, "0")}</span>
                  <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 10, color: "#4a6080" }}>{item}</span>
                </div>
              ))}
            </div>

          </div>
        </div>
      </div>

      {/* ── Bottom bar ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", height: 24, borderTop: "1px solid #1a2840", background: "#050a10", flexShrink: 0 }}>
        <div style={{ display: "flex", gap: 16 }}>
          {["POSTGRES", "REDIS", "ALPACA", "EDGAR"].map((s) => (
            <div key={s} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ width: 4, height: 4, borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
              <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 8, color: "#2a3d55", letterSpacing: "0.1em" }}>{s}</span>
            </div>
          ))}
        </div>
        <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 8, color: "#2a3d55", letterSpacing: "0.08em" }}>ARGOS v0.1.0 · LOCAL · NOT FOR DISTRIBUTION</span>
      </div>
    </div>
  );
}