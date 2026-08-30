import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Save } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

function Field({ label, children }) {
  return (
    <div>
      <Label className="text-sm">{label}</Label>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

export default function Settings() {
  const { refresh } = useAuth();
  const { data, isLoading } = useQuery({ queryKey: ["restaurant"], queryFn: async () => (await api.getRestaurant()).data });
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { if (data) setForm(data); }, [data]);

  if (isLoading || !form) return <p className="text-muted-foreground">Loading…</p>;

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const setNum = (k) => (e) => setForm({ ...form, [k]: e.target.value === "" ? "" : Number(e.target.value) });

  const save = async () => {
    setSaving(true);
    try {
      await api.updateRestaurant({
        name: form.name, description: form.description, address: form.address, city: form.city,
        contact_number: form.contact_number, whatsapp_number: form.whatsapp_number,
        opening_hours: form.opening_hours, delivery_areas: form.delivery_areas,
        delivery_fee: Number(form.delivery_fee), min_order: Number(form.min_order),
        prep_time_min: Number(form.prep_time_min), prep_time_max: Number(form.prep_time_max),
        delivery_time_min: Number(form.delivery_time_min), delivery_time_max: Number(form.delivery_time_max),
        currency: form.currency, ai_greeting: form.ai_greeting,
      });
      toast.success("Settings saved");
      refresh();
    } catch {
      toast.error("Could not save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-extrabold">Restaurant Settings</h1>
          <p className="text-muted-foreground mt-1">Your profile, delivery rules and business info.</p>
        </div>
        <Button data-testid="save-settings-btn" onClick={save} disabled={saving} className="rounded-full gap-2">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save
        </Button>
      </div>

      <Card className="rounded-2xl border-border shadow-sm p-6 space-y-5">
        <h2 className="font-display text-lg font-bold">Profile</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Field label="Restaurant Name"><Input data-testid="set-name" value={form.name || ""} onChange={set("name")} /></Field>
          <Field label="Currency"><Input data-testid="set-currency" value={form.currency || ""} onChange={set("currency")} /></Field>
          <Field label="Contact Number"><Input data-testid="set-contact" value={form.contact_number || ""} onChange={set("contact_number")} /></Field>
          <Field label="WhatsApp Number"><Input data-testid="set-wa-number" value={form.whatsapp_number || ""} onChange={set("whatsapp_number")} /></Field>
          <Field label="City"><Input data-testid="set-city" value={form.city || ""} onChange={set("city")} /></Field>
          <Field label="Opening Hours"><Input data-testid="set-hours" value={form.opening_hours || ""} onChange={set("opening_hours")} /></Field>
        </div>
        <Field label="Address"><Input data-testid="set-address" value={form.address || ""} onChange={set("address")} /></Field>
        <Field label="Description"><Textarea data-testid="set-desc" value={form.description || ""} onChange={set("description")} rows={2} /></Field>
        <Field label="Delivery Areas"><Input data-testid="set-areas" value={form.delivery_areas || ""} onChange={set("delivery_areas")} /></Field>
      </Card>

      <Card className="rounded-2xl border-border shadow-sm p-6 space-y-5">
        <h2 className="font-display text-lg font-bold">Delivery & Timing</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
          <Field label="Delivery Fee (PKR)"><Input data-testid="set-delivery-fee" type="number" value={form.delivery_fee} onChange={setNum("delivery_fee")} /></Field>
          <Field label="Minimum Order (PKR)"><Input data-testid="set-min-order" type="number" value={form.min_order} onChange={setNum("min_order")} /></Field>
          <div />
          <Field label="Prep Time Min"><Input data-testid="set-prep-min" type="number" value={form.prep_time_min} onChange={setNum("prep_time_min")} /></Field>
          <Field label="Prep Time Max"><Input data-testid="set-prep-max" type="number" value={form.prep_time_max} onChange={setNum("prep_time_max")} /></Field>
          <div />
          <Field label="Delivery Time Min"><Input data-testid="set-del-min" type="number" value={form.delivery_time_min} onChange={setNum("delivery_time_min")} /></Field>
          <Field label="Delivery Time Max"><Input data-testid="set-del-max" type="number" value={form.delivery_time_max} onChange={setNum("delivery_time_max")} /></Field>
        </div>
      </Card>

      <Card className="rounded-2xl border-border shadow-sm p-6 space-y-5">
        <h2 className="font-display text-lg font-bold">AI Greeting</h2>
        <Field label="First message the assistant sends"><Textarea data-testid="set-greeting" value={form.ai_greeting || ""} onChange={set("ai_greeting")} rows={2} /></Field>
      </Card>
    </div>
  );
}
