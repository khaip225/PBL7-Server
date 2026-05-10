"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import type { UserResponse } from "./types";

interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  login: async () => {},
  logout: () => {},
});

const COOKIE_NAME = "pbl7_auth";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name: string, value: string, days: number = 1) {
  const expires = new Date(Date.now() + days * 86400000).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function deleteCookie(name: string) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Check existing token on mount
  useEffect(() => {
    const savedToken = getCookie(COOKIE_NAME);
    if (savedToken) {
      setToken(savedToken);
      // Validate token by fetching /me
      fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/me`, {
        headers: { Authorization: `Bearer ${savedToken}` },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Invalid token");
          return res.json();
        })
        .then((userData: UserResponse) => {
          setUser(userData);
        })
        .catch(() => {
          deleteCookie(COOKIE_NAME);
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(detail || "Login failed");
    }
    const data = await res.json();
    setCookie(COOKIE_NAME, data.access_token);
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    deleteCookie(COOKIE_NAME);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
