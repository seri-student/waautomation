import React, { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [restaurant, setRestaurant] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      const { data } = await api.me();
      setUser(data.user);
      setRestaurant(data.restaurant);
    } catch {
      setUser(null);
      setRestaurant(null);
    }
  };

  useEffect(() => {
    const t = localStorage.getItem("token");
    if (!t) {
      setLoading(false);
      return;
    }
    refresh().finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.login({ email, password });
    localStorage.setItem("token", data.access_token);
    await refresh();
    return data;
  };

  const register = async (body) => {
    const { data } = await api.register(body);
    localStorage.setItem("token", data.access_token);
    await refresh();
    return data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    setRestaurant(null);
    window.location.href = "/login";
  };

  return (
    <AuthCtx.Provider value={{ user, restaurant, loading, login, register, logout, refresh, setRestaurant }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
