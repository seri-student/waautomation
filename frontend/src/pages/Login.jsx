import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Pizza, Loader2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("owner@pizzapalace.pk");
  const [password, setPassword] = useState("palace123");

  const [rName, setRName] = useState("");
  const [rRestaurant, setRRestaurant] = useState("");
  const [rEmail, setREmail] = useState("");
  const [rPassword, setRPassword] = useState("");

  const doLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const doRegister = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register({ name: rName, restaurant_name: rRestaurant, email: rEmail, password: rPassword });
      navigate("/dashboard");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left brand panel */}
      <div className="hidden lg:flex w-[45%] relative bg-[#1A1D1A] text-white flex-col justify-between p-12 overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=1000&q=80"
          alt="Signature burger and fries"
          className="absolute inset-0 w-full h-full object-cover opacity-40"
        />
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-primary flex items-center justify-center">
            <Pizza className="w-6 h-6" />
          </div>
          <span className="font-display font-bold text-xl">AI Restaurant Assistant</span>
        </div>
        <div className="relative z-10 max-w-md">
          <h1 className="font-display text-4xl xl:text-5xl font-extrabold leading-tight mb-4">
            Your 24/7 WhatsApp receptionist that takes orders.
          </h1>
          <p className="text-white/80 text-base leading-relaxed">
            Let AI greet customers in English, Urdu & Roman Urdu, build carts, and place orders — while you watch
            everything live from one dashboard.
          </p>
        </div>
        <div className="relative z-10 text-white/60 text-sm">Built for restaurants in Pakistan 🇵🇰</div>
      </div>

      {/* Right auth panel */}
      <div className="flex-1 flex items-center justify-center p-6 bg-background">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center">
              <Pizza className="w-5 h-5" />
            </div>
            <span className="font-display font-bold text-lg">AI Restaurant Assistant</span>
          </div>

          <h2 className="font-display text-2xl font-bold mb-1">Welcome back</h2>
          <p className="text-muted-foreground text-sm mb-6">Sign in to manage your restaurant.</p>

          <Tabs defaultValue="login">
            <TabsList className="grid grid-cols-2 mb-6 rounded-full">
              <TabsTrigger value="login" data-testid="tab-login" className="rounded-full">Sign In</TabsTrigger>
              <TabsTrigger value="register" data-testid="tab-register" className="rounded-full">Create Account</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={doLogin} className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" data-testid="login-email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1.5" required />
                </div>
                <div>
                  <Label htmlFor="password">Password</Label>
                  <Input id="password" data-testid="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1.5" required />
                </div>
                {error && <p data-testid="auth-error" className="text-sm text-destructive">{error}</p>}
                <Button type="submit" data-testid="login-submit" disabled={loading} className="w-full rounded-full h-11 gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Sign In <ArrowRight className="w-4 h-4" /></>}
                </Button>
              </form>
              <div className="mt-6 rounded-xl bg-secondary/60 border border-border p-4 text-sm">
                <p className="font-semibold mb-1">Demo account</p>
                <p className="text-muted-foreground">owner@pizzapalace.pk · palace123</p>
              </div>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={doRegister} className="space-y-4">
                <div>
                  <Label htmlFor="rName">Your Name</Label>
                  <Input id="rName" data-testid="reg-name" value={rName} onChange={(e) => setRName(e.target.value)} className="mt-1.5" required />
                </div>
                <div>
                  <Label htmlFor="rRestaurant">Restaurant Name</Label>
                  <Input id="rRestaurant" data-testid="reg-restaurant" value={rRestaurant} onChange={(e) => setRRestaurant(e.target.value)} className="mt-1.5" required />
                </div>
                <div>
                  <Label htmlFor="rEmail">Email</Label>
                  <Input id="rEmail" data-testid="reg-email" type="email" value={rEmail} onChange={(e) => setREmail(e.target.value)} className="mt-1.5" required />
                </div>
                <div>
                  <Label htmlFor="rPassword">Password</Label>
                  <Input id="rPassword" data-testid="reg-password" type="password" value={rPassword} onChange={(e) => setRPassword(e.target.value)} className="mt-1.5" required minLength={6} />
                </div>
                {error && <p data-testid="auth-error" className="text-sm text-destructive">{error}</p>}
                <Button type="submit" data-testid="register-submit" disabled={loading} className="w-full rounded-full h-11 gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Create Account <ArrowRight className="w-4 h-4" /></>}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
