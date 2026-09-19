"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    FileText,
    ScrollText,
    Building2,
    BarChart3,
    Globe,
    Settings,
    Landmark,
    Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
    {
        name: "Dashboard",
        href: "/",
        icon: BarChart3,
    },
    {
        name: "Filings",
        href: "/government/filings",
        icon: FileText,
    },
    {
        name: "Bills",
        href: "/government/bills",
        icon: ScrollText,
    },
    {
        name: "Contracts",
        href: "/government/contracts",
        icon: Building2,
    },
    {
        name: "Lobbying",
        href: "/government/lobbying",
        icon: Landmark,
    },
    {
        name: "Global",
        href: "/global",
        icon: Globe,
    },
    {
        name: "Settings",
        href: "/settings",
        icon: Settings,
    },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="flex flex-col w-56 border-r border-border bg-card h-screen">
            {/* Logo */}
            <div className="flex items-center gap-2 px-4 py-4 border-b border-border">
                <Eye className="w-5 h-5 text-primary" />
                <span className="font-mono font-bold text-sm tracking-widest uppercase text-foreground">
                    Argos
                </span>
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