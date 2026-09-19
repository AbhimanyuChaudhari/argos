import { BarChart3, FileText, ScrollText, Building2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

const stats = [
  {
    title: "SEC Filings",
    value: "500+",
    description: "10-K, 10-Q, 8-K and more",
    href: "/government/filings",
    icon: FileText,
    color: "text-blue-400",
  },
  {
    title: "Congressional Bills",
    value: "100+",
    description: "119th Congress live tracking",
    href: "/government/bills",
    icon: ScrollText,
    color: "text-green-400",
  },
  {
    title: "Federal Contracts",
    value: "100+",
    description: "USASpending.gov all agencies",
    href: "/government/contracts",
    icon: Building2,
    color: "text-amber-400",
  },
];

export default function HomePage() {
  return (
    <div className="p-6 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">
          Argos Terminal
        </h1>
        <p className="text-sm text-muted-foreground">
          Global financial intelligence. All markets. All at once.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <Link key={stat.title} href={stat.href}>
            <Card className="hover:border-primary/50 transition-colors cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className={"w-4 h-4 " + stat.color} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stat.description}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Government Intelligence</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              { label: "SEC Filings", href: "/government/filings", desc: "EDGAR filings for all public companies" },
              { label: "Congressional Bills", href: "/government/bills", desc: "Live legislative tracker" },
              { label: "Federal Contracts", href: "/government/contracts", desc: "USASpending.gov contract awards" },
              { label: "Lobbying", href: "/government/lobbying", desc: "OpenSecrets disclosure data" },
            ].map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="flex items-center justify-between p-2 rounded hover:bg-muted transition-colors group"
              >
                <div>
                  <p className="text-sm font-medium group-hover:text-primary transition-colors">
                    {item.label}
                  </p>
                  <p className="text-xs text-muted-foreground">{item.desc}</p>
                </div>
                <FileText className="w-4 h-4 text-muted-foreground" />
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Coming Soon</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              { label: "Market Data", desc: "Real-time prices via Alpaca" },
              { label: "Macro Dashboard", desc: "FRED, ECB, RBI indicators" },
              { label: "News Feed", desc: "NewsAPI + Benzinga" },
              { label: "Political Risk", desc: "GDELT global event tracker" },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center justify-between p-2 rounded opacity-50"
              >
                <div>
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="text-xs text-muted-foreground">{item.desc}</p>
                </div>
                <BarChart3 className="w-4 h-4 text-muted-foreground" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}