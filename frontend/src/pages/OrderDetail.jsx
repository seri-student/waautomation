import React from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, MapPin, Phone, User, Clock, Bike, Store, Check } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { api, fmtMoney } from "@/lib/api";

const FLOW = ["New", "Confirmed", "Preparing", "Ready", "Out for Delivery", "Delivered"];

export default function OrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: o, isLoading } = useQuery({
    queryKey: ["order", id],
    queryFn: async () => (await api.getOrder(id)).data,
    refetchInterval: 10000,
  });

  const mut = useMutation({
    mutationFn: (status) => api.updateOrderStatus(id, status),
    onSuccess: (res) => {
      qc.setQueryData(["order", id], res.data);
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["analytics"] });
      toast.success(`Order marked ${res.data.status}`, { description: "Customer notified on WhatsApp." });
    },
    onError: () => toast.error("Could not update status"),
  });

  if (isLoading || !o) return <p className="text-muted-foreground">Loading order…</p>;

  const currentIdx = FLOW.indexOf(o.status);
  const nextStatus = currentIdx >= 0 && currentIdx < FLOW.length - 1 ? FLOW[currentIdx + 1] : null;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <button onClick={() => navigate(-1)} data-testid="back-btn" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h1 className="font-display text-3xl font-extrabold">Order #{o.order_number}</h1>
          <StatusBadge status={o.status} />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {nextStatus && (
            <Button data-testid="advance-status-btn" onClick={() => mut.mutate(nextStatus)} disabled={mut.isPending} className="rounded-full gap-2">
              <Check className="w-4 h-4" /> Mark {nextStatus}
            </Button>
          )}
          {o.status !== "Cancelled" && o.status !== "Delivered" && (
            <Button data-testid="cancel-order-btn" variant="outline" onClick={() => mut.mutate("Cancelled")} disabled={mut.isPending} className="rounded-full text-destructive border-destructive/30 hover:bg-destructive/5">
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Status stepper */}
      <Card className="rounded-2xl border-border shadow-sm p-5">
        <div className="flex items-center gap-2 overflow-x-auto thin-scroll pb-2">
          {FLOW.map((s, i) => {
            const done = currentIdx >= i && currentIdx >= 0;
            return (
              <React.Fragment key={s}>
                <button
                  data-testid={`set-status-${s.replace(/\s+/g, "-")}`}
                  onClick={() => mut.mutate(s)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                    done ? "bg-secondary text-secondary-foreground" : "bg-muted text-muted-foreground hover:bg-secondary/60"
                  }`}
                >
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center ${done ? "bg-secondary-foreground text-secondary" : "bg-border"}`}>
                    {done && <Check className="w-2.5 h-2.5" />}
                  </span>
                  {s}
                </button>
                {i < FLOW.length - 1 && <span className="text-border">—</span>}
              </React.Fragment>
            );
          })}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Items */}
        <Card className="lg:col-span-2 rounded-2xl border-border shadow-sm">
          <div className="p-5 border-b border-border">
            <h2 className="font-display text-lg font-bold">Items</h2>
          </div>
          <div className="divide-y divide-border">
            {o.items.map((it, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-secondary text-secondary-foreground font-bold text-sm flex items-center justify-center">{it.qty}x</span>
                  <span className="font-medium text-sm">{it.name}</span>
                </div>
                <span className="text-sm text-muted-foreground">{fmtMoney(it.line_total, o.currency)}</span>
              </div>
            ))}
          </div>
          <div className="p-5 border-t border-border space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Subtotal</span><span>{fmtMoney(o.subtotal, o.currency)}</span></div>
            {o.delivery_fee > 0 && <div className="flex justify-between"><span className="text-muted-foreground">Delivery Fee</span><span>{fmtMoney(o.delivery_fee, o.currency)}</span></div>}
            <div className="flex justify-between font-display text-lg font-extrabold pt-2 border-t border-border">
              <span>Total</span><span className="text-primary">{fmtMoney(o.total, o.currency)}</span>
            </div>
          </div>
        </Card>

        {/* Customer + meta */}
        <div className="space-y-6">
          <Card className="rounded-2xl border-border shadow-sm p-5 space-y-3">
            <h2 className="font-display text-lg font-bold">Customer</h2>
            <p className="flex items-center gap-2 text-sm"><User className="w-4 h-4 text-muted-foreground" /> {o.customer_name}</p>
            <p className="flex items-center gap-2 text-sm"><Phone className="w-4 h-4 text-muted-foreground" /> {o.customer_phone}</p>
            <p className="flex items-center gap-2 text-sm">
              {o.order_type === "delivery" ? <Bike className="w-4 h-4 text-muted-foreground" /> : <Store className="w-4 h-4 text-muted-foreground" />}
              <span className="capitalize">{o.order_type}</span>
            </p>
            {o.address && <p className="flex items-start gap-2 text-sm"><MapPin className="w-4 h-4 text-muted-foreground mt-0.5" /> {o.address}</p>}
            <p className="flex items-center gap-2 text-sm"><Clock className="w-4 h-4 text-muted-foreground" /> ETA {o.eta_min}–{o.eta_max} min</p>
            <Link to={`/customers/${o.customer_id}`} data-testid="view-customer-link" className="block text-sm font-semibold text-primary hover:underline pt-1">
              View customer profile →
            </Link>
          </Card>

          <Card className="rounded-2xl border-border shadow-sm p-5">
            <h2 className="font-display text-lg font-bold mb-3">Timeline</h2>
            <div className="space-y-3">
              {(o.status_history || []).map((h, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span className="w-2 h-2 rounded-full bg-primary" />
                  <span className="font-medium">{h.status}</span>
                  <span className="text-muted-foreground text-xs ml-auto">{new Date(h.at).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
