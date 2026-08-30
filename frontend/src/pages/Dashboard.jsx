import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ShoppingBag, TrendingUp, Clock, CheckCircle2, Wallet, MessageCircle, ArrowUpRight,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge, ConnectionBadge } from "@/components/StatusBadge";
import { api, fmtMoney } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

function StatCard({ icon: Icon, label, value, accent, testId }) {
  return (
    <Card data-testid={testId} className="p-5 rounded-2xl border-border shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-300">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">{label}</p>
          <p className="font-display text-2xl md:text-3xl font-extrabold mt-2">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${accent}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </Card>
  );
}

export default function Dashboard() {
  const { restaurant } = useAuth();
  const cur = restaurant?.currency || "PKR";

  const { data: a } = useQuery({
    queryKey: ["analytics"],
    queryFn: async () => (await api.getAnalytics()).data,
    refetchInterval: 15000,
  });
  const { data: orders } = useQuery({
    queryKey: ["orders"],
    queryFn: async () => (await api.getOrders()).data,
    refetchInterval: 15000,
  });
  const { data: wa } = useQuery({
    queryKey: ["whatsapp-config"],
    queryFn: async () => (await api.getWhatsApp()).data,
  });

  const recent = (orders || []).slice(0, 6);
  const providerLabel = { simulator: "Simulator", evolution: "Evolution API", meta: "Meta Cloud API" }[wa?.provider] || "Simulator";

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Here's what's happening at {restaurant?.name} today.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard testId="stat-today-orders" icon={ShoppingBag} label="Today's Orders" value={a?.today_orders ?? "—"} accent="bg-primary/10 text-primary" />
        <StatCard testId="stat-today-sales" icon={TrendingUp} label="Today's Sales" value={fmtMoney(a?.today_sales, cur)} accent="bg-emerald-100 text-emerald-700" />
        <StatCard testId="stat-pending" icon={Clock} label="Pending Orders" value={a?.pending_orders ?? "—"} accent="bg-amber-100 text-amber-700" />
        <StatCard testId="stat-aov" icon={Wallet} label="Avg Order Value" value={fmtMoney(a?.average_order_value, cur)} accent="bg-sky-100 text-sky-700" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Orders */}
        <Card className="lg:col-span-2 rounded-2xl border-border shadow-sm">
          <div className="flex items-center justify-between p-5 border-b border-border">
            <h2 className="font-display text-lg font-bold">Recent Orders</h2>
            <Link to="/orders" data-testid="view-all-orders" className="text-sm font-semibold text-primary flex items-center gap-1 hover:gap-2 transition-all">
              View all <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-border">
            {recent.length === 0 && <p className="p-6 text-sm text-muted-foreground">No orders yet.</p>}
            {recent.map((o) => (
              <Link
                key={o.id}
                to={`/orders/${o.id}`}
                data-testid={`recent-order-${o.order_number}`}
                className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <div className="w-11 h-11 rounded-xl bg-secondary flex flex-col items-center justify-center flex-shrink-0">
                    <span className="text-[10px] text-muted-foreground -mb-0.5">#</span>
                    <span className="font-display font-bold text-sm">{o.order_number}</span>
                  </div>
                  <div className="min-w-0">
                    <p className="font-semibold text-sm truncate">{o.customer_name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {o.items.reduce((s, i) => s + i.qty, 0)} items · {o.order_type}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-display font-bold text-sm hidden sm:block">{fmtMoney(o.total, o.currency)}</span>
                  <StatusBadge status={o.status} />
                </div>
              </Link>
            ))}
          </div>
        </Card>

        {/* Right column */}
        <div className="space-y-6">
          <Card className="rounded-2xl border-border shadow-sm p-5">
            <div className="flex items-center gap-2 mb-4">
              <MessageCircle className="w-4 h-4 text-emerald-600" />
              <h2 className="font-display text-lg font-bold">WhatsApp</h2>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Status</span>
                <ConnectionBadge status={wa?.status} testId="dash-wa-status" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Active Provider</span>
                <span className="font-semibold">{providerLabel}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Number</span>
                <span className="font-semibold">{wa?.connected_number || "—"}</span>
              </div>
            </div>
            <Link to="/whatsapp" data-testid="dash-open-whatsapp" className="mt-4 block text-center text-sm font-semibold text-primary hover:underline">
              Manage connection & test →
            </Link>
          </Card>

          <Card className="rounded-2xl border-border shadow-sm p-5">
            <h2 className="font-display text-lg font-bold mb-4">Top Items</h2>
            <div className="space-y-3">
              {(a?.top_items || []).length === 0 && <p className="text-sm text-muted-foreground">No data yet.</p>}
              {(a?.top_items || []).map((it, i) => (
                <div key={it.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-5 h-5 rounded-md bg-secondary text-secondary-foreground text-xs font-bold flex items-center justify-center flex-shrink-0">{i + 1}</span>
                    <span className="truncate">{it.name}</span>
                  </div>
                  <span className="text-muted-foreground font-medium">{it.qty} sold</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
