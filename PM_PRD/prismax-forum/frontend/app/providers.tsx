"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { LoginModal } from "@/components/LoginModal";
import { Toast } from "@/components/Toast";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
  openLogin: () => void;
  /** Returns true if signed in; otherwise opens the login modal and returns false. */
  requireAuth: () => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const ToastContext = createContext<(msg: string) => void>(() => {});

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within Providers");
  return ctx;
}

export function useToast() {
  return useContext(ToastContext);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [loginOpen, setLoginOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refresh = useCallback(async () => {
    try {
      setUser(await api.me());
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2600);
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
    showToast("Signed out.");
  }, [showToast]);

  const openLogin = useCallback(() => setLoginOpen(true), []);

  const requireAuth = useCallback(() => {
    if (user) return true;
    setLoginOpen(true);
    return false;
  }, [user]);

  return (
    <AuthContext.Provider value={{ user, loading, refresh, logout, openLogin, requireAuth }}>
      <ToastContext.Provider value={showToast}>
        {children}
        {loginOpen && (
          <LoginModal
            onClose={() => setLoginOpen(false)}
            onSuccess={async () => {
              setLoginOpen(false);
              await refresh();
              showToast("Welcome to the monograph.");
            }}
          />
        )}
        {toast && <Toast message={toast} />}
      </ToastContext.Provider>
    </AuthContext.Provider>
  );
}
