import React from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Phone, ShoppingBag, Wallet, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { api, fmtMoney } from "@/lib/api";

export default function CustomerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["customer", id],
    queryFn: async () => (await api.getCustomer(id)).data,
  });

  if (isLoading || !data) return <p className="text-muted-foreground">Loading customer…</p>;
  const { customer, orders, messages } = data;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <button onClick={() => navigate(-1)} data-testid="back-btn" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <div className="flex items-center gap-4">
        <div className="w-14 h-14 rounded-full bg-secondary text-secondary-foreground font-display font-bold text-xl flex items-center justify-center">
          {(customer.name || "?").charAt(0).toUpperCase()}
        </div>
        <div>
          <h1 className="font-display text-2xl font-extrabold">{customer.name || "Unknown"}</h1>
          <p className="text-muted-foreground text-sm flex items-center gap-1.5"><Phone className="w-3.5 h-3.5" /> {customer.phone}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="rounded-2xl border-border shadow-sm p-5">
          <ShoppingBag className="w-5 h-5 text-primary mb-2" />
          <p className="text-xs uppercase tracking-wider text-muted-foreground font-bold">Total Orders</p>
          <p className="font-display text-2xl font-extrabold mt-1">{customer.total_orders || 0}</p>
        </Card>
        <Card className="rounded-2xl border-border shadow-sm p-5">
          <Wallet className="w-5 h-5 text-emerald-600 mb-2" />
          <p className="text-xs uppercase tracking-wider text-muted-foreground font-bold">Total Spent</p>
          <p className="font-display text-2xl font-extrabold mt-1">{fmtMoney(customer.total_spent)}</p>
        </Card>
        <Card className="rounded-2xl border-border shadow-sm p-5">
          <Clock className="w-5 h-5 text-sky-600 mb-2" />
          <p className="text-xs uppercase tracking-wider text-muted-foreground font-bold">Last Order</p>
          <p className="font-display text-base font-bold mt-2">{customer.last_order_at ? new Date(customer.last_order_at).toLocaleDateString() : "—"}</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="rounded-2xl border-border shadow-sm">
          <div className="p-5 border-b border-border"><h2 className="font-display text-lg font-bold">Order History</h2></div>
          <div className="divide-y divide-border">
            {orders.length === 0 && <p className="p-5 text-sm text-muted-foreground">No orders.</p>}
            {orders.map((o) => (
              <Link key={o.id} to={`/orders/${o.id}`} data-testid={`cust-order-${o.order_number}`} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
                <div>
                  <p className="font-semibold text-sm">#{o.order_number}</p>
                  <p className="text-xs text-muted-foreground">{new Date(o.created_at).toLocaleDateString()} · {o.items.reduce((s, i) => s + i.qty, 0)} items</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-display font-bold text-sm">{fmtMoney(o.total, o.currency)}</span>
                  <StatusBadge status={o.status} />
                </div>
              </Link>
            ))}
          </div>
        </Card>

        <Card className="rounded-2xl border-border shadow-sm">
          <div className="p-5 border-b border-border"><h2 className="font-display text-lg font-bold">Recent Conversation</h2></div>
          <div className="p-4 space-y-2 max-h-[420px] overflow-y-auto thin-scroll">
            {messages.length === 0 && <p className="text-sm text-muted-foreground">No conversation yet.</p>}
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.direction === "in" ? "justify-start" : "justify-end"}`}>
                <div className={`px-3 py-2 rounded-2xl max-w-[85%] text-[13px] whitespace-pre-wrap ${m.direction === "in" ? "bg-muted text-foreground rounded-tl-sm" : "bg-secondary text-secondary-foreground rounded-tr-sm"}`}>
                  {m.text}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
