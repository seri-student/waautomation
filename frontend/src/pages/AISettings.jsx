import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Save, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";

const MODELS = [
  { id: "gemini-3-flash-preview", label: "Gemini 3 Flash (fast, recommended)" },
  { id: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
  { id: "gemini-3.1-pro-preview", label: "Gemini 3.1 Pro (most capable)" },
];

export default function AISettings() {
  const { data, isLoading } = useQuery({ queryKey: ["ai-settings"], queryFn: async () => (await api.getAISettings()).data });
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { if (data) setForm(data); }, [data]);
  if (isLoading || !form) return <p className="text-muted-foreground">Loading…</p>;

  const save = async () => {
    setSaving(true);
    try {
      await api.updateAISettings({
        provider: form.provider, model: form.model, personality: form.personality,
        language_behavior: form.language_behavior, upsell_enabled: form.upsell_enabled,
        max_upsell_attempts: Number(form.max_upsell_attempts), human_handoff_enabled: form.human_handoff_enabled,
      });
      toast.success("AI settings saved");
    } catch {
      toast.error("Could not save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl font-extrabold flex items-center gap-2"><Sparkles className="w-6 h-6 text-primary" /> AI Settings</h1>
          <p className="text-muted-foreground mt-1">Tune how your assistant talks and sells.</p>
        </div>
        <Button data-testid="save-ai-btn" onClick={save} disabled={saving} className="rounded-full gap-2">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save
        </Button>
      </div>

      <Card className="rounded-2xl border-border shadow-sm p-6 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <Label>AI Provider</Label>
            <Select value={form.provider} onValueChange={(v) => setForm({ ...form, provider: v })}>
              <SelectTrigger data-testid="ai-provider" className="mt-1.5"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="gemini">Gemini (active)</SelectItem>
                <SelectItem value="ollama" disabled>Ollama — local (coming soon)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Model</Label>
            <Select value={form.model} onValueChange={(v) => setForm({ ...form, model: v })}>
              <SelectTrigger data-testid="ai-model" className="mt-1.5"><SelectValue /></SelectTrigger>
              <SelectContent>
                {MODELS.map((m) => <SelectItem key={m.id} value={m.id}>{m.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <Label>Personality</Label>
          <Input data-testid="ai-personality" value={form.personality || ""} onChange={(e) => setForm({ ...form, personality: e.target.value })} className="mt-1.5" />
        </div>
        <div>
          <Label>Language Behavior</Label>
          <Textarea data-testid="ai-language" value={form.language_behavior || ""} onChange={(e) => setForm({ ...form, language_behavior: e.target.value })} className="mt-1.5" rows={2} />
        </div>
      </Card>

      <Card className="rounded-2xl border-border shadow-sm p-6 space-y-5">
        <h2 className="font-display text-lg font-bold">Selling & Handoff</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-sm">Upselling</p>
            <p className="text-xs text-muted-foreground">Suggest one relevant add-on per order.</p>
          </div>
          <Switch data-testid="ai-upsell" checked={form.upsell_enabled} onCheckedChange={(v) => setForm({ ...form, upsell_enabled: v })} />
        </div>
        <div>
          <Label>Max Upsell Attempts</Label>
          <Input data-testid="ai-max-upsell" type="number" min={0} max={3} value={form.max_upsell_attempts} onChange={(e) => setForm({ ...form, max_upsell_attempts: e.target.value })} className="mt-1.5 w-32" />
        </div>
        <div className="flex items-center justify-between border-t border-border pt-4">
          <div>
            <p className="font-medium text-sm">Human Handoff</p>
            <p className="text-xs text-muted-foreground">Allow the AI to transfer chats to staff.</p>
          </div>
          <Switch data-testid="ai-handoff" checked={form.human_handoff_enabled} onCheckedChange={(v) => setForm({ ...form, human_handoff_enabled: v })} />
        </div>
      </Card>
    </div>
  );
}
