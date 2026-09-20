"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
    FileText,
    ScrollText,
    Building2,
    BarChart3,
    Globe,
    Settings,
    Landmark,
    Eye,
    Search,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
    { name: "Dashboard", href: "/", icon: BarChart3 },
    { name: "Filings", href: "/government/filings", icon: FileText },
    { name: "Bills", href: "/government/bills", icon: ScrollText },
    { name: "Contracts", href: "/government/contracts", icon: Building2 },
    { name: "Lobbying", href: "/government/lobbying", icon: Landmark },
    { name: "Global", href: "/global", icon: Globe },
    { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const [ticker, setTicker] = useState("");

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        const t = ticker.trim().toUpperCase();
        if (t) {
            router.push(`/stock/${t}`);
            setTicker("");
        }
    };

    return (
        <div className="flex flex-col w-56 border-r border-border bg-card h-screen">
            {/* Logo */}
            <div className="flex items-center gap-2 px-4 py-4 border-b border-border">
                <Eye className="w-5 h-5 text-primary" />
                <span className="font-mono font-bold text-sm tracking-widest uppercase text-foreground">
                    Argos
                </span>
            </div>

            {/* Ticker search */}
            <div className="px-3 py-3 border-b border-border">
                <form onSubmit={handleSearch}>
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                        <input
                            type="text"
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            placeholder="Search ticker..."
                            maxLength={10}
                            className="w-full pl-8 pr-3 py-1.5 text-xs font-mono bg-muted border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-colors"
                        />
                    </div>
                </form>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-2 py-3 space-y-1">
                {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                                isActive
                                    ? "bg-primary/10 text-primary font-medium"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                            )}
                        >
                            <item.icon className="w-4 h-4 shrink-0" />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-border">
                <p className="text-xs text-muted-foreground font-mono">
                    v0.1.0 — local
                </p>
            </div>
        </div>
    );
}