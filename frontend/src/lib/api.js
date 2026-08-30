import axios from "axios";

export const apiBase = `${process.env.REACT_APP_BACKEND_URL}/api`;

const client = axios.create({ baseURL: apiBase });

client.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

client.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401 && !window.location.pathname.includes("/login")) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(e);
  }
);

export function formatApiError(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((x) => (x && typeof x.msg === "string" ? x.msg : JSON.stringify(x))).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

export const fmtMoney = (n, cur = "PKR") =>
  `${cur} ${Number(n || 0).toLocaleString("en-PK", { maximumFractionDigits: 0 })}`;

export const api = {
  login: (body) => client.post("/auth/login", body),
  register: (body) => client.post("/auth/register", body),
  me: () => client.get("/auth/me"),

  getRestaurant: () => client.get("/restaurant"),
  updateRestaurant: (body) => client.put("/restaurant", body),
  getAISettings: () => client.get("/restaurant/ai-settings"),
  updateAISettings: (body) => client.put("/restaurant/ai-settings", body),

  getMenu: () => client.get("/menu"),
  createCategory: (body) => client.post("/menu/categories", body),
  deleteCategory: (id) => client.delete(`/menu/categories/${id}`),
  createItem: (body) => client.post("/menu/items", body),
  updateItem: (id, body) => client.put(`/menu/items/${id}`, body),
  deleteItem: (id) => client.delete(`/menu/items/${id}`),

  getOrders: (status) => client.get("/orders", { params: status ? { status } : {} }),
  getOrder: (id) => client.get(`/orders/${id}`),
  updateOrderStatus: (id, status) => client.patch(`/orders/${id}/status`, { status }),

  getCustomers: () => client.get("/customers"),
  getCustomer: (id) => client.get(`/customers/${id}`),

  getAnalytics: () => client.get("/analytics/summary"),

  getWhatsApp: () => client.get("/whatsapp/config"),
  setProvider: (provider) => client.post("/whatsapp/provider", { provider }),
  setEvolution: (body) => client.put("/whatsapp/evolution", body),
  setMeta: (body) => client.put("/whatsapp/meta", body),
  waConnect: () => client.post("/whatsapp/connect"),
  waDisconnect: () => client.post("/whatsapp/disconnect"),
  waStatus: () => client.get("/whatsapp/status"),

  getConversations: () => client.get("/conversations"),
  getMessages: (id) => client.get(`/conversations/${id}/messages`),
  setHandoff: (id, ai_active) => client.post(`/conversations/${id}/handoff`, { ai_active }),
  humanReply: (id, text) => client.post(`/conversations/${id}/reply`, { text }),

  simSend: (body) => client.post("/simulator/message", body),
  simMessages: (phone) => client.get("/simulator/messages", { params: { phone } }),
};

export default client;
