import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { api, fmtMoney } from "@/lib/api";

export default function Customers() {
  const { data: customers, isLoading } = useQuery({
    queryKey: ["customers"],
    queryFn: async () => (await api.getCustomers()).data,
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="font-display text-3xl font-extrabold">Customers</h1>
        <p className="text-muted-foreground mt-1">Everyone who has ordered from your restaurant.</p>
      </div>

      <Card className="rounded-2xl border-border shadow-sm overflow-hidden">
        <div className="grid grid-cols-12 px-5 py-3 border-b border-border text-xs font-bold uppercase tracking-wider text-muted-foreground">
          <div className="col-span-5 sm:col-span-4">Customer</div>
          <div className="col-span-3 hidden sm:block">Phone</div>
          <div className="col-span-3 sm:col-span-2 text-center">Orders</div>
          <div className="col-span-4 sm:col-span-3 text-right">Total Spent</div>
        </div>
        {isLoading && <p className="p-6 text-sm text-muted-foreground">Loading…</p>}
        {!isLoading && (customers || []).length === 0 && (
          <div className="p-10 text-center text-muted-foreground">
            <Users className="w-8 h-8 mx-auto mb-3 opacity-40" />
            No customers yet.
          </div>
        )}
        <div className="divide-y divide-border">
          {(customers || []).map((c) => (
            <Link
              key={c.id}
              to={`/customers/${c.id}`}
              data-testid={`customer-row-${c.id}`}
              className="grid grid-cols-12 px-5 py-4 items-center hover:bg-muted/50 transition-colors"
            >
              <div className="col-span-5 sm:col-span-4 flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-full bg-secondary text-secondary-foreground font-bold text-sm flex items-center justify-center flex-shrink-0">
                  {(c.name || "?").charAt(0).toUpperCase()}
                </div>
                <span className="font-semibold text-sm truncate">{c.name || "Unknown"}</span>
              </div>
              <div className="col-span-3 hidden sm:block text-sm text-muted-foreground">{c.phone}</div>
              <div className="col-span-3 sm:col-span-2 text-center text-sm font-medium">{c.total_orders || 0}</div>
              <div className="col-span-4 sm:col-span-3 text-right font-display font-bold text-sm">{fmtMoney(c.total_spent)}</div>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}
