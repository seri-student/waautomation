import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  QrCode, Loader2, RefreshCw, Power, Copy, Check, Bot, Headphones, Send, MessageSquare, Smartphone,
} from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import { ConnectionBadge } from "@/components/StatusBadge";
import Simulator from "@/components/Simulator";
import { api } from "@/lib/api";

const PROVIDERS = [
  { id: "simulator", title: "Built-in Simulator", desc: "Test the full ordering flow instantly — no credentials needed.", icon: Smartphone },
  { id: "evolution", title: "Evolution API", desc: "Self-hosted WhatsApp via QR code. Great for development/demo.", icon: QrCode },
  { id: "meta", title: "Meta Official API", desc: "Official WhatsApp Cloud API. Recommended for production.", icon: MessageSquare },
];

function CopyBtn({ text }) {
  const [done, setDone] = useState(false);
  return (
    <button
      data-testid="copy-webhook"
      onClick={() => { navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1500); }}
      className="text-muted-foreground hover:text-foreground"
    >
      {done ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
    </button>
  );
}

function EvolutionPanel({ wa, refetch }) {
  const [url, setUrl] = useState(wa.evolution?.evolution_api_url || "");
  const [key, setKey] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [qr, setQr] = useState(null);

  const saveCfg = async () => {
    await api.setEvolution({ evolution_api_url: url, ...(key ? { evolution_api_key: key } : {}) });
    toast.success("Evolution settings saved");
    refetch();
  };

  const connect = async () => {
    setConnecting(true);
    setQr(null);
    try {
      await api.setEvolution({ evolution_api_url: url, ...(key ? { evolution_api_key: key } : {}) });
      const { data } = await api.waConnect();
      setQr(data.qr_code || null);
      refetch();
      if (data.qr_code) toast.success("QR generated — scan it now");
      else toast.message(data.detail || "Connection requested");
    } catch {
      toast.error("Could not connect");
    } finally {
      setConnecting(false);
    }
  };

  const disconnect = async () => { await api.waDisconnect(); setQr(null); refetch(); toast.success("Disconnected"); };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <div>
          <Label>Evolution API URL</Label>
          <Input data-testid="evo-url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://your-evolution-host" className="mt-1.5" />
        </div>
        <div>
          <Label>API Key</Label>
          <Input data-testid="evo-key" type="password" value={key} onChange={(e) => setKey(e.target.value)} placeholder={wa.evolution?.evolution_api_key_masked || "••••"} className="mt-1.5" />
        </div>
        <div>
          <Label>Instance Name</Label>
          <Input value={wa.evolution?.evolution_instance_name || ""} readOnly className="mt-1.5 bg-muted" />
        </div>
        <div className="flex gap-2">
          <Button data-testid="evo-connect" onClick={connect} disabled={connecting} className="rounded-full gap-2">
            {connecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Connect / Reconnect
          </Button>
          <Button variant="outline" data-testid="evo-save" onClick={saveCfg} className="rounded-full">Save</Button>
          <Button variant="outline" data-testid="evo-disconnect" onClick={disconnect} className="rounded-full text-destructive border-destructive/30"><Power className="w-4 h-4" /></Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Webhook URL for Evolution:
          <span className="block mt-1 font-mono text-[11px] bg-muted rounded px-2 py-1 break-all">{wa.evolution_webhook_url}</span>
        </p>
      </div>

      <div className="flex flex-col items-center justify-center bg-muted/50 rounded-2xl p-6 border border-border">
        {qr ? (
          <>
            <img data-testid="evo-qr" src={qr.startsWith("data:") ? qr : `data:image/png;base64,${qr}`} alt="WhatsApp QR" className="w-52 h-52 rounded-lg bg-white p-2" />
            <p className="text-sm font-semibold mt-4 text-center">Scan this QR code with</p>
            <p className="text-sm text-muted-foreground text-center">WhatsApp → Linked Devices</p>
          </>
        ) : (
          <div className="text-center text-muted-foreground">
            <QrCode className="w-16 h-16 mx-auto mb-3 opacity-30" />
            <p className="text-sm max-w-[220px]">Add your Evolution URL & key, then click Connect to generate a QR code.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function MetaPanel({ wa, refetch }) {
  const [form, setForm] = useState({
    meta_phone_number_id: wa.meta?.meta_phone_number_id || "",
    meta_waba_id: wa.meta?.meta_waba_id || "",
    meta_access_token: "",
    meta_verify_token: wa.meta?.meta_verify_token || "",
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      const body = { ...form };
      if (!body.meta_access_token) delete body.meta_access_token;
      await api.setMeta(body);
      await api.waStatus();
      toast.success("Meta settings saved");
      refetch();
    } catch {
      toast.error("Could not save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <div>
          <Label>Phone Number ID</Label>
          <Input data-testid="meta-phone-id" value={form.meta_phone_number_id} onChange={(e) => setForm({ ...form, meta_phone_number_id: e.target.value })} className="mt-1.5" />
        </div>
        <div>
          <Label>WhatsApp Business Account (WABA) ID</Label>
          <Input data-testid="meta-waba-id" value={form.meta_waba_id} onChange={(e) => setForm({ ...form, meta_waba_id: e.target.value })} className="mt-1.5" />
        </div>
        <div>
          <Label>Access Token</Label>
          <Input data-testid="meta-token" type="password" value={form.meta_access_token} onChange={(e) => setForm({ ...form, meta_access_token: e.target.value })} placeholder={wa.meta?.meta_access_token_masked || "••••"} className="mt-1.5" />
        </div>
        <div>
          <Label>Verify Token</Label>
          <Input data-testid="meta-verify" value={form.meta_verify_token} onChange={(e) => setForm({ ...form, meta_verify_token: e.target.value })} className="mt-1.5" />
        </div>
        <Button data-testid="meta-save" onClick={save} disabled={saving} className="rounded-full gap-2">
          {saving && <Loader2 className="w-4 h-4 animate-spin" />} Save & Verify
        </Button>
      </div>
      <div className="space-y-4">
        <div className="bg-muted/50 rounded-2xl p-4 border border-border">
          <Label className="text-xs uppercase tracking-wider text-muted-foreground">Webhook URL</Label>
          <div className="flex items-center gap-2 mt-1.5">
            <code className="text-[11px] bg-card rounded px-2 py-1.5 break-all flex-1 border border-border">{wa.meta?.webhook_url}</code>
            <CopyBtn text={wa.meta?.webhook_url || ""} />
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            Configure this in Meta → WhatsApp → Configuration → Webhook, using your Verify Token above.
          </p>
        </div>
        <div className="bg-muted/50 rounded-2xl p-4 border border-border text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Credentials configured</span>
            <span className="font-semibold">{wa.meta?.configured ? "Yes" : "No"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function Conversations() {
  const qc = useQueryClient();
  const [selected, setSelected] = useState(null);
  const [reply, setReply] = useState("");

  const { data: convs } = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => (await api.getConversations()).data,
    refetchInterval: 8000,
  });
  const { data: detail } = useQuery({
    queryKey: ["conversation", selected],
    queryFn: async () => (await api.getMessages(selected)).data,
    enabled: !!selected,
    refetchInterval: 5000,
  });

  const handoff = useMutation({
    mutationFn: ({ id, active }) => api.setHandoff(id, active),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversations"] });
      qc.invalidateQueries({ queryKey: ["conversation", selected] });
    },
  });

  const sendReply = async () => {
    if (!reply.trim() || !selected) return;
    await api.humanReply(selected, reply.trim());
    setReply("");
    qc.invalidateQueries({ queryKey: ["conversation", selected] });
  };

  const conv = detail?.conversation;
  const aiActive = conv?.ai_active;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-[560px]">
      <Card className="rounded-2xl border-border shadow-sm overflow-hidden flex flex-col">
        <div className="p-4 border-b border-border font-display font-bold">Conversations</div>
        <div className="flex-1 overflow-y-auto thin-scroll divide-y divide-border">
          {(convs || []).length === 0 && <p className="p-4 text-sm text-muted-foreground">No conversations yet.</p>}
          {(convs || []).map((c) => (
            <button
              key={c.id}
              data-testid={`conv-${c.id}`}
              onClick={() => setSelected(c.id)}
              className={`w-full text-left p-3 hover:bg-muted/50 transition-colors ${selected === c.id ? "bg-secondary/40" : ""}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm truncate">{c.customer?.name || c.customer_phone}</span>
                {c.ai_active ? <Bot className="w-3.5 h-3.5 text-emerald-600" /> : <Headphones className="w-3.5 h-3.5 text-primary" />}
              </div>
              <p className="text-xs text-muted-foreground truncate mt-0.5">{c.last_message?.text || "…"}</p>
            </button>
          ))}
        </div>
      </Card>

      <Card className="md:col-span-2 rounded-2xl border-border shadow-sm overflow-hidden flex flex-col">
        {!selected ? (
          <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">Select a conversation</div>
        ) : (
          <>
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div>
                <p className="font-semibold text-sm">{conv?.customer_name || conv?.customer_phone}</p>
                <p className="text-xs text-muted-foreground">{aiActive ? "AI is handling this chat" : "Human takeover active"}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{aiActive ? "AI Active" : "Human Active"}</span>
                <Switch
                  data-testid="handoff-switch"
                  checked={!aiActive}
                  onCheckedChange={(v) => handoff.mutate({ id: selected, active: !v })}
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto thin-scroll wa-bg p-3 space-y-2">
              {(detail?.messages || []).map((m) => (
                <div key={m.id} className={`flex ${m.direction === "in" ? "justify-end" : "justify-start"}`}>
                  <div className={`px-3 py-2 rounded-2xl max-w-[80%] text-[13px] shadow-sm whitespace-pre-wrap ${m.direction === "in" ? "bg-[#DCF8C6] rounded-tr-sm" : m.sender === "system" ? "bg-[#FFF3CD] border border-amber-200 rounded-tl-sm" : m.sender === "human" ? "bg-primary/10 rounded-tl-sm" : "bg-white rounded-tl-sm"}`}>
                    {m.sender === "human" && <span className="block text-[10px] font-semibold text-primary mb-0.5">Staff</span>}
                    {m.text}
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t border-border flex items-center gap-2">
              <Input
                data-testid="human-reply-input"
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendReply()}
                placeholder={aiActive ? "Take over to reply manually…" : "Type a reply…"}
                disabled={aiActive}
                className="rounded-full"
              />
              <Button data-testid="human-reply-send" onClick={sendReply} disabled={aiActive || !reply.trim()} size="icon" className="rounded-full flex-shrink-0">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

export default function WhatsAppPage() {
  const qc = useQueryClient();
  const { data: wa, isLoading } = useQuery({
    queryKey: ["whatsapp-config"],
    queryFn: async () => (await api.getWhatsApp()).data,
  });
  const refetch = () => qc.invalidateQueries({ queryKey: ["whatsapp-config"] });

  const setProvider = useMutation({
    mutationFn: (p) => api.setProvider(p),
    onSuccess: () => { refetch(); toast.success("Provider updated"); },
  });

  if (isLoading || !wa) return <p className="text-muted-foreground">Loading…</p>;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-extrabold">WhatsApp</h1>
          <p className="text-muted-foreground mt-1">Connect a number, test the assistant, and manage live chats.</p>
        </div>
        <ConnectionBadge status={wa.status} testId="wa-page-status" />
      </div>

      <Tabs defaultValue="connection">
        <TabsList className="rounded-full">
          <TabsTrigger value="connection" data-testid="tab-connection" className="rounded-full">Connection</TabsTrigger>
          <TabsTrigger value="simulator" data-testid="tab-simulator" className="rounded-full">Test Simulator</TabsTrigger>
          <TabsTrigger value="conversations" data-testid="tab-conversations" className="rounded-full">Conversations</TabsTrigger>
        </TabsList>

        <TabsContent value="connection" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <RadioGroup value={wa.provider} onValueChange={(v) => setProvider.mutate(v)} className="contents">
              {PROVIDERS.map((p) => (
                <label
                  key={p.id}
                  htmlFor={`prov-${p.id}`}
                  data-testid={`provider-${p.id}`}
                  className={`cursor-pointer rounded-2xl border p-4 transition-all ${wa.provider === p.id ? "border-primary ring-2 ring-primary/20 bg-primary/5" : "border-border hover:border-primary/40"}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center"><p.icon className="w-5 h-5 text-secondary-foreground" /></div>
                    <RadioGroupItem value={p.id} id={`prov-${p.id}`} />
                  </div>
                  <p className="font-display font-bold mt-3">{p.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{p.desc}</p>
                </label>
              ))}
            </RadioGroup>
          </div>

          <Card className="rounded-2xl border-border shadow-sm p-6">
            {wa.provider === "simulator" && (
              <div className="text-center py-8">
                <Smartphone className="w-12 h-12 mx-auto mb-3 text-secondary-foreground" />
                <p className="font-display text-lg font-bold">Simulator is active & always connected</p>
                <p className="text-muted-foreground text-sm mt-1 max-w-md mx-auto">
                  Open the <span className="font-semibold">Test Simulator</span> tab to chat with your AI assistant exactly like a real customer would on WhatsApp.
                </p>
              </div>
            )}
            {wa.provider === "evolution" && <EvolutionPanel wa={wa} refetch={refetch} />}
            {wa.provider === "meta" && <MetaPanel wa={wa} refetch={refetch} />}
          </Card>

          {wa.provider === "evolution" && (
            <Card className="rounded-2xl border-border shadow-sm p-5">
              <h3 className="font-display font-bold mb-3">Connection Logs</h3>
              <div className="space-y-1 max-h-40 overflow-y-auto thin-scroll font-mono text-[11px] text-muted-foreground">
                {(wa.logs || []).length === 0 && <p>No logs yet.</p>}
                {(wa.logs || []).slice().reverse().map((l, i) => <p key={i}>{l}</p>)}
              </div>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="simulator" className="mt-6">
          <div className="max-w-md mx-auto">
            <Simulator />
          </div>
        </TabsContent>

        <TabsContent value="conversations" className="mt-6">
          <Conversations />
        </TabsContent>
      </Tabs>
    </div>
  );
}
