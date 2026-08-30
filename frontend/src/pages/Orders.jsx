import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { MapPin, Bike, Store } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/StatusBadge";
import { api, fmtMoney } from "@/lib/api";

const COLUMNS = ["New", "Confirmed", "Preparing", "Ready", "Out for Delivery", "Delivered"];

function OrderCard({ o }) {
  return (
    <Link
      to={`/orders/${o.id}`}
      data-testid={`order-card-${o.order_number}`}
      className="block bg-card border border-border rounded-xl p-4 shadow-sm hover:shadow-md hover:border-primary/30 transition-all duration-200"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-display font-bold text-sm">#{o.order_number}</span>
        <span className="text-xs text-muted-foreground flex items-center gap-1">
          {o.order_type === "delivery" ? <Bike className="w-3.5 h-3.5" /> : <Store className="w-3.5 h-3.5" />}
          {o.order_type}
        </span>
      </div>
      <p className="font-semibold text-sm">{o.customer_name}</p>
      <p className="text-xs text-muted-foreground mb-2">{o.customer_phone}</p>
      <div className="text-xs text-muted-foreground space-y-0.5 mb-3">
        {o.items.slice(0, 3).map((i, idx) => (
          <p key={idx} className="truncate">{i.qty}x {i.name}</p>
        ))}
        {o.items.length > 3 && <p>+{o.items.length - 3} more…</p>}
      </div>
      {o.address && (
        <p className="text-[11px] text-muted-foreground flex items-start gap-1 mb-2">
          <MapPin className="w-3 h-3 mt-0.5 flex-shrink-0" /> <span className="line-clamp-1">{o.address}</span>
        </p>
      )}
      <div className="flex items-center justify-between border-t border-border pt-2">
        <span className="font-display font-bold text-sm">{fmtMoney(o.total, o.currency)}</span>
        <StatusBadge status={o.status} />
      </div>
    </Link>
  );
}

export default function Orders() {
  const { data: orders, isLoading } = useQuery({
    queryKey: ["orders"],
    queryFn: async () => (await api.getOrders()).data,
    refetchInterval: 12000,
  });

  const grouped = COLUMNS.reduce((acc, c) => ({ ...acc, [c]: [] }), {});
  (orders || []).forEach((o) => {
    if (grouped[o.status]) grouped[o.status].push(o);
  });
  const cancelled = (orders || []).filter((o) => o.status === "Cancelled");

  return (
    <div className="max-w-full mx-auto space-y-6">
      <div>
        <h1 className="font-display text-3xl font-extrabold">Orders</h1>
        <p className="text-muted-foreground mt-1">Live order board — updates automatically as new orders arrive.</p>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading orders…</p>
      ) : (
        <div className="flex gap-4 overflow-x-auto thin-scroll pb-4">
          {COLUMNS.map((col) => (
            <div key={col} data-testid={`orders-col-${col.replace(/\s+/g, "-")}`} className="bg-muted/60 rounded-2xl p-3 flex flex-col gap-3 min-w-[290px] w-[290px] flex-shrink-0">
              <div className="flex items-center justify-between px-1">
                <StatusBadge status={col} />
                <span className="text-xs font-bold text-muted-foreground bg-card rounded-full px-2 py-0.5">
                  {grouped[col].length}
                </span>
              </div>
              <div className="flex flex-col gap-3">
                {grouped[col].length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-6">No orders</p>
                )}
                {grouped[col].map((o) => (
                  <OrderCard key={o.id} o={o} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {cancelled.length > 0 && (
        <div>
          <h2 className="font-display text-lg font-bold mb-3">Cancelled</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {cancelled.map((o) => (
              <OrderCard key={o.id} o={o} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
