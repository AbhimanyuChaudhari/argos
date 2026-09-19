"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getBills } from "@/lib/api";
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

const POLICY_AREAS = [
    "economics", "finance", "trade", "energy", "healthcare",
    "technology", "defense", "environment", "infrastructure",
    "agriculture", "housing", "labor", "immigration",
    "foreign_policy", "other",
];

const CHAMBERS = ["house", "senate"];

function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function StatusBadge({ status }: { status: string }) {
    const colors: Record<string, string> = {
        introduced: "bg-blue-500/20 text-blue-400 border-blue-500/30",
        referred: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
        in_committee: "bg-amber-500/20 text-amber-400 border-amber-500/30",
        passed_committee: "bg-orange-500/20 text-orange-400 border-orange-500/30",
        passed_house: "bg-green-500/20 text-green-400 border-green-500/30",
        passed_senate: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
        signed: "bg-teal-500/20 text-teal-400 border-teal-500/30",
        failed: "bg-red-500/20 text-red-400 border-red-500/30",
    };
    const colorClass = colors[status] || "bg-muted text-muted-foreground";
    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${colorClass}`}>
            {status.replace(/_/g, " ")}
        </span>
    );
}

function PolicyBadge({ area }: { area: string }) {
    return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-muted text-muted-foreground border border-border">
            {area.replace(/_/g, " ")}
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
        queryFn: () =>
            getBills({
                chamber: chamber === "all" ? undefined : chamber,
                policy_area: policyArea === "all" ? undefined : policyArea,
                page,
                page_size: 20,
            }),
    });

    const filtered = data?.items.filter((b) =>
        search
            ? b.title?.toLowerCase().includes(search.toLowerCase()) ||
            b.bill_number?.toLowerCase().includes(search.toLowerCase())
            : true
    );

    return (
        <div className="p-6 space-y-4">
            <div className="space-y-1">
                <h1 className="text-2xl font-bold tracking-tight">Congressional Bills</h1>
                <p className="text-sm text-muted-foreground">
                    119th Congress — live legislative tracker
                </p>
            </div>

            <div className="flex gap-3 flex-wrap">
                <div className="relative flex-1 min-w-48">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        placeholder="Search bills..."
                        className="pl-9"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <Select
                    value={chamber}
                    onValueChange={(v: string | null) => {
                        if (!v) return;
                        setChamber(v);
                        setPage(1);
                    }}
                >
                    <SelectTrigger className="w-36">
                        <SelectValue placeholder="Chamber" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All chambers</SelectItem>
                        {CHAMBERS.map((c) => (
                            <SelectItem key={c} value={c}>
                                {c.charAt(0).toUpperCase() + c.slice(1)}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                <Select
                    value={policyArea}
                    onValueChange={(v: string | null) => {
                        if (!v) return;
                        setPolicyArea(v);
                        setPage(1);
                    }}
                >
                    <SelectTrigger className="w-44">
                        <SelectValue placeholder="Policy area" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All areas</SelectItem>
                        {POLICY_AREAS.map((a) => (
                            <SelectItem key={a} value={a}>
                                {a.replace(/_/g, " ")}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            <div className="text-sm text-muted-foreground">
                {data ? `${data.total} bills` : "Loading..."}
            </div>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Bill</TableHead>
                                <TableHead>Title</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Policy Area</TableHead>
                                <TableHead>Sponsor</TableHead>
                                <TableHead>Introduced</TableHead>
                                <TableHead></TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading && (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                                        Loading bills...
                                    </TableCell>
                                </TableRow>
                            )}
                            {error && (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-destructive py-8">
                                        Failed to load. Is the backend running on port 8001?
                                    </TableCell>
                                </TableRow>
                            )}
                            {filtered?.map((bill) => (
                                <TableRow key={bill.id} className="hover:bg-muted/50">
                                    <TableCell className="font-mono text-xs whitespace-nowrap">
                                        {bill.bill_number}
                                    </TableCell>
                                    <TableCell className="max-w-xs">
                                        <p className="text-sm line-clamp-2">{bill.title}</p>
                                    </TableCell>
                                    <TableCell>
                                        <StatusBadge status={bill.status} />
                                    </TableCell>
                                    <TableCell>
                                        <PolicyBadge area={bill.policy_area} />
                                    </TableCell>
                                    <TableCell>
                                        <div>
                                            <p className="text-sm">{bill.sponsor_name ?? "—"}</p>
                                            {bill.sponsor_party && (
                                                <p className="text-xs text-muted-foreground">
                                                    {bill.sponsor_party} · {bill.sponsor_state}
                                                </p>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground font-mono whitespace-nowrap">
                                        {formatDate(bill.introduced_at)}
                                    </TableCell>
                                    <TableCell>
                                        {bill.url && (
                                            <a
                                                href={bill.url}
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