import React, { createContext, useContext, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiBase } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const RealtimeCtx = createContext(null);

function playChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [880, 1174];
    notes.forEach((f, i) => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = f;
      o.connect(g);
      g.connect(ctx.destination);
      const t0 = ctx.currentTime + i * 0.14;
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(0.25, t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.25);
      o.start(t0);
      o.stop(t0 + 0.28);
    });
  } catch {
    /* audio not available */
  }
}

export function RealtimeProvider({ children }) {
  const { user } = useAuth();
  const qc = useQueryClient();
  const listenersRef = useRef(new Set());

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!user || !token) return;
    const es = new EventSource(`${apiBase}/stream?token=${token}`);

    es.onmessage = (ev) => {
      let payload;
      try {
        payload = JSON.parse(ev.data);
      } catch {
        return;
      }
      const { type, data } = payload;
      if (type === "new_order") {
        qc.invalidateQueries({ queryKey: ["orders"] });
        qc.invalidateQueries({ queryKey: ["analytics"] });
        playChime();
        const o = data.order;
        toast.success(`New order #${o.order_number}`, {
          description: `${o.customer_name} • ${o.currency} ${Number(o.total).toLocaleString("en-PK")}`,
        });
      } else if (type === "order_update") {
        qc.invalidateQueries({ queryKey: ["orders"] });
        qc.invalidateQueries({ queryKey: ["analytics"] });
      } else if (type === "message" || type === "handoff" || type === "handoff_pending") {
        qc.invalidateQueries({ queryKey: ["conversations"] });
      }
      listenersRef.current.forEach((fn) => fn(payload));
    };

    es.onerror = () => {
      /* browser auto-reconnects */
    };

    return () => es.close();
  }, [user, qc]);

  const subscribe = (fn) => {
    listenersRef.current.add(fn);
    return () => listenersRef.current.delete(fn);
  };

  return <RealtimeCtx.Provider value={{ subscribe }}>{children}</RealtimeCtx.Provider>;
}

export const useRealtime = () => useContext(RealtimeCtx);
