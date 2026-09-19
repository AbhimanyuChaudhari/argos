"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getFilings } from "@/lib/api";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { ExternalLink, Search } from "lucide-react";

const FILING_TYPES = ["10-K", "10-Q", "8-K", "8-K/A", "S-1", "4", "DEF 14A"];

function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function FilingTypeBadge({ type }: { type: string }) {
    const colors: Record<string, string> = {
        "10-K": "bg-blue-500/20 text-blue-400 border-blue-500/30",
        "10-Q": "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
        "8-K": "bg-amber-500/20 text-amber-400 border-amber-500/30",
        "8-K/A": "bg-orange-500/20 text-orange-400 border-orange-500/30",
        "S-1": "bg-green-500/20 text-green-400 border-green-500/30",
        "4": "bg-purple-500/20 text-purple-400 border-purple-500/30",
    };
    const colorClass = colors[type] || "bg-muted text-muted-foreground";
    return (
        <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${colorClass}`}
        >
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
        queryFn: () =>
            getFilings({
                filing_type: filingType === "all" ? undefined : filingType,
                page,
                page_size: 20,
            }),
    });

    const filtered = data?.items.filter((f) =>
        search
            ? f.company_name?.toLowerCase().includes(search.toLowerCase()) ||
            f.ticker?.toLowerCase().includes(search.toLowerCase())
            : true
    );

    return (
        <div className="p-6 space-y-4">
            <div className="space-y-1">
                <h1 className="text-2xl font-bold tracking-tight">SEC Filings</h1>
                <p className="text-sm text-muted-foreground">
                    EDGAR filings for all US public companies
                </p>
            </div>

            <div className="flex gap-3">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        placeholder="Search company or ticker..."
                        className="pl-9"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <Select
                    value={filingType}
                    onValueChange={(v: string | null) => {
                        if (!v) return;
                        setFilingType(v);
                        setPage(1);
                    }}
                >
                    <SelectTrigger className="w-40">
                        <SelectValue placeholder="Filing type" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All types</SelectItem>
                        {FILING_TYPES.map((t) => (
                            <SelectItem key={t} value={t}>
                                {t}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <div className="text-sm text-muted-foreground">
                {data ? `${data.total} filings` : "Loading..."}
            </div>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Company</TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead>Filed</TableHead>
                                <TableHead>Period</TableHead>
                                <TableHead>Items</TableHead>
                                <TableHead></TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading && (
                                <TableRow>
                                    <TableCell
                                        colSpan={6}
                                        className="text-center text-muted-foreground py-8"
                                    >
                                        Loading filings...
                                    </TableCell>
                                </TableRow>
                            )}
                            {error && (
                                <TableRow>
                                    <TableCell
                                        colSpan={6}
                                        className="text-center text-destructive py-8"
                                    >
                                        Failed to load. Is the backend running on port 8001?
                                    </TableCell>
                                </TableRow>
                            )}
                            {filtered?.map((filing) => (
                                <TableRow key={filing.id} className="hover:bg-muted/50">
                                    <TableCell>
                                        <div>
                                            <p className="font-medium text-sm">
                                                {filing.company_name?.split("(")[0].trim() ?? "Unknown"}
                                            </p>
                                            {filing.ticker && (
                                                <p className="text-xs text-muted-foreground font-mono">
                                                    {filing.ticker}
                                                </p>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <FilingTypeBadge type={filing.filing_type} />
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground font-mono">
                                        {formatDate(filing.filed_at)}
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground font-mono">
                                        {filing.period_of_report
                                            ? formatDate(filing.period_of_report)
                                            : "—"}
                                    </TableCell>
                                    <TableCell>
                                        {filing.items && filing.items.length > 0 && (
                                            <div className="flex gap-1 flex-wrap">
                                                {filing.items.slice(0, 3).map((item) => (
                                                    <span
                                                        key={item}
                                                        className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded"
                                                    >
                                                        {item}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        {filing.url && (
                                            <a
                                                href={filing.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-muted-foreground hover:text-primary transition-colors"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        )}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {data && (
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>
                        Page {data.page} — showing {filtered?.length ?? 0} of {data.total}
                    </span>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 rounded border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => setPage((p) => p + 1)}
                            disabled={!data.has_more}
                            className="px-3 py-1 rounded border border-border hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}