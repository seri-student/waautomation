"use strict";
const express = require("express");
const path = require("path");
const fs = require("fs");
const axios = require("axios");
const qrcode = require("qrcode");
const pino = require("pino");
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  Browsers,
  fetchLatestBaileysVersion,
} = require("@whiskeysockets/baileys");

const PORT = process.env.PORT || 3001;
const SECRET = process.env.WHATSAPP_GATEWAY_SECRET || "";
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8001";
const SESSIONS_DIR = path.join(__dirname, "sessions");
fs.mkdirSync(SESSIONS_DIR, { recursive: true });

const logger = pino({ level: "silent" });
const app = express();
app.use(express.json({ limit: "2mb" }));

// shared-secret guard
app.use((req, res, next) => {
  if (req.path === "/health") return next();
  if (SECRET && req.headers["x-gateway-secret"] !== SECRET) {
    return res.status(401).json({ error: "unauthorized" });
  }
  next();
});

// restaurantId -> { sock, status, qr, number, starting }
const sessions = new Map();

function sessionDir(rid) {
  return path.join(SESSIONS_DIR, rid.replace(/[^a-zA-Z0-9_-]/g, "_"));
}

function phoneFromJid(jid) {
  return (jid || "").split("@")[0].split(":")[0];
}

async function forwardIncoming(rid, msg) {
  try {
    await axios.post(
      `${BACKEND_URL}/api/webhooks/whatsapp/baileys/${rid}`,
      msg,
      { headers: { "x-gateway-secret": SECRET }, timeout: 15000 }
    );
  } catch (e) {
    logger.error(`forward failed: ${e.message}`);
  }
}

async function startSession(rid) {
  let s = sessions.get(rid);
  if (s && (s.status === "connected" || s.starting)) return s;

  s = s || {};
  s.starting = true;
  s.status = s.status || "connecting";
  sessions.set(rid, s);

  const { state, saveCreds } = await useMultiFileAuthState(sessionDir(rid));
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
    browser: Browsers.ubuntu("Chrome"),
    markOnlineOnConnect: false,
    syncFullHistory: false,
  });
  s.sock = sock;

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (u) => {
    const { connection, lastDisconnect, qr } = u;
    if (qr) {
      s.qr = await qrcode.toDataURL(qr);
      s.status = "connecting";
    }
    if (connection === "open") {
      s.status = "connected";
      s.qr = null;
      s.number = phoneFromJid(sock.user && sock.user.id);
      s.starting = false;
      logger.info(`[${rid}] connected as ${s.number}`);
    }
    if (connection === "close") {
      s.starting = false;
      const code = lastDisconnect && lastDisconnect.error && lastDisconnect.error.output
        ? lastDisconnect.error.output.statusCode
        : undefined;
      if (code === DisconnectReason.loggedOut) {
        s.status = "disconnected";
        s.qr = null;
        s.number = null;
        try { fs.rmSync(sessionDir(rid), { recursive: true, force: true }); } catch (_) {}
      } else {
        // transient — reconnect
        s.status = "connecting";
        setTimeout(() => startSession(rid).catch(() => {}), 2500);
      }
    }
  });

  sock.ev.on("messages.upsert", async (ev) => {
    if (ev.type !== "notify") return;
    for (const m of ev.messages) {
      if (!m.message || m.key.fromMe) continue;
      const jid = m.key.remoteJid || "";
      if (jid.endsWith("@g.us") || jid === "status@broadcast") continue;
      const text =
        m.message.conversation ||
        (m.message.extendedTextMessage && m.message.extendedTextMessage.text) ||
        (m.message.imageMessage && m.message.imageMessage.caption) ||
        (m.message.buttonsResponseMessage && m.message.buttonsResponseMessage.selectedDisplayText) ||
        "";
      if (!text.trim()) continue;
      await forwardIncoming(rid, {
        phone: phoneFromJid(jid),
        text: text.trim(),
        messageId: m.key.id,
        pushName: m.pushName || null,
        timestamp: new Date().toISOString(),
      });
    }
  });

  return s;
}

// ---- Routes ----
app.get("/health", (_req, res) => res.json({ ok: true }));

app.post("/instance/:rid/connect", async (req, res) => {
  const rid = req.params.rid;
  try {
    const s = await startSession(rid);
    // wait briefly for a QR (or an already-open session) to appear
    for (let i = 0; i < 20 && !s.qr && s.status !== "connected"; i++) {
      await new Promise((r) => setTimeout(r, 400));
    }
    res.json({ status: s.status, qr: s.qr || null, number: s.number || null });
  } catch (e) {
    logger.error(e.message);
    res.status(500).json({ status: "error", detail: e.message });
  }
});

app.get("/instance/:rid/status", (req, res) => {
  const s = sessions.get(req.params.rid);
  if (!s) return res.json({ status: "disconnected", qr: null, number: null });
  res.json({ status: s.status, qr: s.qr || null, number: s.number || null });
});

app.post("/instance/:rid/send", async (req, res) => {
  const s = sessions.get(req.params.rid);
  if (!s || !s.sock || s.status !== "connected") {
    return res.status(409).json({ error: "not_connected" });
  }
  try {
    const to = String(req.body.to || "");
    const jid = to.includes("@") ? to : `${to}@s.whatsapp.net`;
    await s.sock.sendMessage(jid, { text: String(req.body.text || "") });
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post("/instance/:rid/logout", async (req, res) => {
  const rid = req.params.rid;
  const s = sessions.get(rid);
  try {
    if (s && s.sock) { try { await s.sock.logout(); } catch (_) {} }
  } finally {
    try { fs.rmSync(sessionDir(rid), { recursive: true, force: true }); } catch (_) {}
    sessions.delete(rid);
  }
  res.json({ status: "disconnected" });
});

// Resume any previously-authenticated sessions after a restart
function resumeSaved() {
  let dirs = [];
  try { dirs = fs.readdirSync(SESSIONS_DIR); } catch (_) { return; }
  for (const d of dirs) {
    const creds = path.join(SESSIONS_DIR, d, "creds.json");
    if (fs.existsSync(creds)) {
      logger.info(`resuming session ${d}`);
      startSession(d).catch(() => {});
    }
  }
}

app.listen(PORT, () => {
  console.log(`WhatsApp (Baileys) gateway listening on ${PORT}`);
  resumeSaved();
});
