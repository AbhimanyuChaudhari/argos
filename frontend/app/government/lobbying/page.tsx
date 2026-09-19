"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getLobbying } from "@/lib/api";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { ExternalLink, Search } from "lucide-react";

function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function formatAmount(amount: number) {
    if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
    if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
    return `$${amount.toLocaleString()}`;
}

export default function LobbyingPage() {
    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);

    const { data, isLoading, error } = useQuery({
        queryKey: ["lobbying", page],
        queryFn: () => getLobbying({ page, page_size: 20 }),
    });

    const filtered = data?.items.filter((l) =>
        search
            ? l.client_name?.toLowerCase().includes(search.toLowerCase()) ||
            l.lobbyist_firm?.toLowerCase().includes(search.toLowerCase()) ||
            l.ticker?.toLowerCase().includes(search.toLowerCase())
            : true
    );

    return (
        <div className="p-6 space-y-4">
            <div className="space-y-1">
                <h1 className="text-2xl font-bold tracking-tight">Lobbying Disclosures</h1>
                <p className="text-sm text-muted-foreground">
                    OpenSecrets — federal lobbying activity
                </p>
            </div>

            <div className="flex gap-3">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        placeholder="Search client, firm or ticker..."
                        className="pl-9"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
            </div>

            <div className="text-sm text-muted-foreground">
                {data ? `${data.total} disclosures` : "Loading..."}
            </div>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Client</TableHead>
                                <TableHead>Lobbyist Firm</TableHead>
                                <TableHead>Amount</TableHead>
                                <TableHead>Year</TableHead>
                                <TableHead>Quarter</TableHead>
                                <TableHead>Issues</TableHead>
                                <TableHead></TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading && (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                                        Loading disclosures...
                                    </TableCell>
                                </TableRow>
                            )}
                            {error && (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-destructive py-8">
                                        No data yet — add your OpenSecrets API key to ingestion/.env to enable lobbying data.
                                    </TableCell>
                                </TableRow>
                            )}
                            {filtered?.length === 0 && !isLoading && !error && (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                                        No lobbying data yet. Add OPENSECRETS_API_KEY to ingestion/.env and run the ingestion pipeline.
                                    </TableCell>
                                </TableRow>
                            )}
                            {filtered?.map((item) => (
                                <TableRow key={item.id} className="hover:bg-muted/50">
                                    <TableCell>
                                        <div>
                                            <p className="font-medium text-sm">{item.client_name}</p>
                                            {item.ticker && (
                                                <p className="text-xs text-muted-foreground font-mono">{item.ticker}</p>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-sm">{item.lobbyist_firm ?? "—"}</TableCell>
                                    <TableCell>
                                        <span className="font-mono font-bold text-sm text-emerald-400">
                                            {item.amount ? formatAmount(item.amount) : "—"}
                                        </span>
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground font-mono">
                                        {item.year ?? "—"}
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground font-mono">
                                        {item.quarter ? `Q${item.quarter}` : "—"}
                                    </TableCell>
                                    <TableCell className="max-w-xs">
                                        {item.issues && item.issues.length > 0 && (
                                            <div className="flex gap-1 flex-wrap">
                                                {item.issues.slice(0, 2).map((issue: string) => (
                                                    <span key={issue} className="text-xs bg-muted px-1.5 py-0.5 rounded border border-border">
                                                        {issue}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        {item.url && (
                                            <button
                                                onClick={() => window.open(item.url!, "_blank")}
                                                className="text-muted-foreground hover:text-primary transition-colors"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </button>
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
                    <span>Page {data.page} — showing {filtered?.length ?? 0} of {data.total}</span>
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