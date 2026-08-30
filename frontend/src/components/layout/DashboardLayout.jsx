import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard, ShoppingBag, Users, UtensilsCrossed, MessageCircle,
  Settings as SettingsIcon, Sparkles, LogOut, Menu as MenuIcon, Pizza,
} from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { ConnectionBadge } from "@/components/StatusBadge";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, testId: "nav-dashboard" },
  { to: "/orders", label: "Orders", icon: ShoppingBag, testId: "nav-orders" },
  { to: "/customers", label: "Customers", icon: Users, testId: "nav-customers" },
  { to: "/menu", label: "Menu", icon: UtensilsCrossed, testId: "nav-menu" },
  { to: "/whatsapp", label: "WhatsApp", icon: MessageCircle, testId: "nav-whatsapp" },
  { to: "/settings", label: "Restaurant Settings", icon: SettingsIcon, testId: "nav-settings" },
  { to: "/ai-settings", label: "AI Settings", icon: Sparkles, testId: "nav-ai-settings" },
];

function SidebarContent({ onNav }) {
  const { restaurant } = useAuth();
  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center shadow-sm">
            <Pizza className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="font-display font-bold text-[15px] leading-tight truncate">{restaurant?.name || "Restaurant"}</p>
            <p className="text-xs text-muted-foreground">AI Ordering</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto thin-scroll">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            data-testid={n.testId}
            onClick={onNav}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors duration-200 ${
                isActive ? "bg-secondary text-secondary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`
            }
          >
            <n.icon className="w-[18px] h-[18px]" />
            {n.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export default function DashboardLayout({ children }) {
  const { logout, user } = useAuth();
  const [open, setOpen] = useState(false);
  const location = useLocation();

  const { data: wa } = useQuery({
    queryKey: ["whatsapp-config"],
    queryFn: async () => (await api.getWhatsApp()).data,
    refetchInterval: 20000,
  });

  const providerLabel = { simulator: "Simulator", evolution: "Evolution API", meta: "Meta Cloud API" }[wa?.provider] || "Simulator";

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <aside className="w-64 bg-card border-r border-border flex-shrink-0 hidden md:flex flex-col z-20">
        <SidebarContent />
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-card/80 backdrop-blur border-b border-border flex items-center justify-between px-4 md:px-8 flex-shrink-0 z-10">
          <div className="flex items-center gap-3">
            <div className="md:hidden">
              <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" data-testid="mobile-menu-btn">
                    <MenuIcon className="w-5 h-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="p-0 w-64">
                  <SidebarContent onNav={() => setOpen(false)} />
                </SheetContent>
              </Sheet>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Provider:</span>
              <span data-testid="active-provider" className="font-semibold text-secondary-foreground">{providerLabel}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ConnectionBadge status={wa?.status} testId="topbar-wa-status" />
            <div className="hidden sm:block text-right leading-tight">
              <p className="text-sm font-semibold">{user?.name}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <Button variant="outline" size="sm" onClick={logout} data-testid="logout-btn" className="rounded-full gap-2">
              <LogOut className="w-4 h-4" /> <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </header>

        <main key={location.pathname} className="flex-1 overflow-y-auto thin-scroll p-4 md:p-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
          {children}
        </main>
      </div>
    </div>
  );
}
