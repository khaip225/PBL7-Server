"use client";

import { useEffect, useState } from "react";
import { Activity, LogOut, User } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Header() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const { user, logout } = useAuth();

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    const interval = setInterval(() => {
      api.health().then(setHealth).catch(() => {});
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-gray-800 bg-gray-900/50 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-3 text-sm">
        {health ? (
          <>
            <span className="flex items-center gap-1.5 text-green-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
              </span>
              System OK
            </span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-400 flex items-center gap-1">
              <Activity className="h-3 w-3" />
              WS: {String(health.active_ws_connections ?? 0)}
            </span>
            <span className="text-gray-400">Jobs: {String(health.running_jobs ?? 0)}</span>
          </>
        ) : (
          <span className="flex items-center gap-1.5 text-red-400">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            Offline
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-2 text-sm text-gray-300">
            <User className="h-4 w-4 text-blue-400" />
            <span className="font-medium">{user.display_name}</span>
          </div>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-red-400 transition-colors px-2 py-1 rounded hover:bg-gray-800"
        >
          <LogOut className="h-3.5 w-3.5" />
          Logout
        </button>
      </div>
    </header>
  );
}
