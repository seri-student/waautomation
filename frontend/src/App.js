import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { RealtimeProvider } from "@/context/RealtimeContext";
import DashboardLayout from "@/components/layout/DashboardLayout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Orders from "@/pages/Orders";
import OrderDetail from "@/pages/OrderDetail";
import Customers from "@/pages/Customers";
import CustomerDetail from "@/pages/CustomerDetail";
import Menu from "@/pages/Menu";
import WhatsAppPage from "@/pages/WhatsAppPage";
import Settings from "@/pages/Settings";
import AISettings from "@/pages/AISettings";

function FullLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <FullLoader />;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <RealtimeProvider>
      <DashboardLayout>{children}</DashboardLayout>
    </RealtimeProvider>
  );
}

function LoginRoute() {
  const { user, loading } = useAuth();
  if (loading) return <FullLoader />;
  if (user) return <Navigate to="/dashboard" replace />;
  return <Login />;
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
            <Route path="/orders" element={<Protected><Orders /></Protected>} />
            <Route path="/orders/:id" element={<Protected><OrderDetail /></Protected>} />
            <Route path="/customers" element={<Protected><Customers /></Protected>} />
            <Route path="/customers/:id" element={<Protected><CustomerDetail /></Protected>} />
            <Route path="/menu" element={<Protected><Menu /></Protected>} />
            <Route path="/whatsapp" element={<Protected><WhatsAppPage /></Protected>} />
            <Route path="/settings" element={<Protected><Settings /></Protected>} />
            <Route path="/ai-settings" element={<Protected><AISettings /></Protected>} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
          <Toaster position="bottom-right" richColors />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
