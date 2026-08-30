import React, { useEffect, useRef, useState } from "react";
import { Send, Phone, MoreVertical, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const DEFAULT_PHONE = "923001234567";
const DEFAULT_NAME = "Test Customer";

function Bubble({ m }) {
  const incoming = m.direction === "in";
  const isSystem = m.sender === "system";
  return (
    <div className={`flex ${incoming ? "justify-end" : "justify-start"}`}>
      <div
        className={`px-3 py-2 rounded-2xl max-w-[82%] text-[13px] leading-snug shadow-sm whitespace-pre-wrap ${
          incoming
            ? "bg-[#DCF8C6] text-gray-800 rounded-tr-sm"
            : isSystem
            ? "bg-[#FFF3CD] text-gray-800 rounded-tl-sm border border-amber-200"
            : "bg-white text-gray-800 rounded-tl-sm"
        }`}
      >
        {m.text}
        <div className="text-[10px] text-gray-400 mt-1 text-right">
          {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </div>
  );
}

export default function Simulator() {
  const [phone, setPhone] = useState(DEFAULT_PHONE);
  const [name] = useState(DEFAULT_NAME);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  const load = async (p) => {
    try {
      const { data } = await api.simMessages(p || phone);
      setMessages(data.messages || []);
    } catch {
      setMessages([]);
    }
  };

  useEffect(() => {
    load(phone);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  const send = async () => {
    const t = text.trim();
    if (!t || sending) return;
    setText("");
    setMessages((prev) => [
      ...prev,
      { id: `tmp-${Date.now()}`, direction: "in", sender: "customer", text: t, created_at: new Date().toISOString() },
    ]);
    setSending(true);
    try {
      const { data } = await api.simSend({ phone, name, text: t });
      setMessages(data.messages || []);
    } catch {
      /* keep optimistic */
    } finally {
      setSending(false);
    }
  };

  const reset = () => {
    const np = "9230" + Math.floor(10000000 + Math.random() * 89999999);
    setPhone(np);
    setMessages([]);
  };

  return (
    <div className="rounded-[2.2rem] border-[10px] border-gray-900 bg-[#EFEAE2] shadow-2xl overflow-hidden relative w-full max-w-[380px] h-[640px] flex flex-col mx-auto">
      {/* Header */}
      <div className="bg-[#075E54] text-white flex items-center gap-3 px-4 py-3 z-10">
        <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center font-semibold">
          {name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm leading-tight">{name}</p>
          <p className="text-[11px] text-emerald-100">{phone}</p>
        </div>
        <Phone className="w-4 h-4 opacity-80" />
        <button onClick={reset} title="New customer" data-testid="sim-reset" className="opacity-80 hover:opacity-100">
          <RotateCcw className="w-4 h-4" />
        </button>
        <MoreVertical className="w-4 h-4 opacity-80" />
      </div>

      {/* Chat */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto thin-scroll wa-bg p-3 space-y-2">
        {messages.length === 0 && (
          <div className="text-center text-xs text-gray-500 mt-10 px-6">
            Send a message as a customer to start chatting with the AI assistant. Try “menu dikhao”.
          </div>
        )}
        {messages.map((m) => (
          <Bubble key={m.id} m={m} />
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-400 typing-dot" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 rounded-full bg-gray-400 typing-dot" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 rounded-full bg-gray-400 typing-dot" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="bg-[#F0F0F0] p-2.5 flex items-center gap-2">
        <Input
          data-testid="sim-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Type a message"
          className="rounded-full bg-white border-none h-10 text-sm"
        />
        <Button
          data-testid="sim-send"
          onClick={send}
          disabled={sending || !text.trim()}
          size="icon"
          className="rounded-full bg-[#075E54] hover:bg-[#064c44] h-10 w-10 flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
