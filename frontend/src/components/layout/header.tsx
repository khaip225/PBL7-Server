"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function Header() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    const interval = setInterval(() => {
      api.health().then(setHealth).catch(() => {});
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-gray-800 bg-gray-900/50 flex items-center justify-between px-6">
      <div className="flex items-center gap-4 text-sm">
        {health && (
          <>
            <span className="flex items-center gap-1.5 text-gray-400">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              System OK
            </span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-400">
              {health.active_ws_connections as number} WS
            </span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-400">
              {health.running_jobs as number} jobs running
            </span>
          </>
        )}
      </div>
      <span className="text-xs text-gray-500">UTC {new Date().toISOString().slice(0, 19).replace("T", " ")}</span>
    </header>
  );
}
