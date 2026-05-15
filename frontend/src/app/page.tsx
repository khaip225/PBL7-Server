"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/use-websocket";
import type { OverviewMetrics, WSMessage } from "@/lib/types";
import { Activity, Users, Play, Zap, Trophy, Radio } from "lucide-react";

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewMetrics | null>(null);
  const [liveEvents, setLiveEvents] = useState<WSMessage[]>([]);
  const { messages } = useWebSocket();

  useEffect(() => {
    api.metrics.overview().then(setOverview).catch(console.error);
    const interval = setInterval(() => {
      api.metrics.overview().then(setOverview).catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    setLiveEvents(messages.slice(-20).reverse());
  }, [messages]);

  const stats = [
    { label: "Online Clients", value: overview?.online_clients ?? "-", icon: Users, color: "text-green-400", bg: "bg-green-900/20" },
    { label: "Active Jobs", value: overview?.active_jobs ?? "-", icon: Play, color: "text-blue-400", bg: "bg-blue-900/20" },
    { label: "Completed Jobs", value: overview?.completed_jobs ?? "-", icon: Trophy, color: "text-yellow-400", bg: "bg-yellow-900/20" },
    { label: "Best Accuracy", value: overview?.best_accuracy ? `${(overview.best_accuracy * 100).toFixed(1)}%` : "-", icon: Zap, color: "text-purple-400", bg: "bg-purple-900/20" },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className={`${stat.bg} border border-gray-800 rounded-xl p-5`}>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">{stat.label}</span>
              <stat.icon size={20} className={stat.color} />
            </div>
            <p className="text-2xl font-bold mt-2">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
            <Radio size={16} className="text-green-400 animate-pulse" /> Live Events
          </h3>
          <div className="h-80 overflow-y-auto space-y-1.5 text-sm">
            {liveEvents.length === 0 && <p className="text-gray-600 p-4 text-center">Waiting for events...</p>}
            {liveEvents.map((ev, i) => (
              <div key={i} className="flex items-start gap-2 p-2 rounded bg-gray-800/50 hover:bg-gray-800">
                <span className="text-gray-500 text-xs font-mono shrink-0">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                  ev.type.includes("error") ? "bg-red-900/30 text-red-400" :
                  ev.type.includes("completed") ? "bg-green-900/30 text-green-400" :
                  "bg-gray-700 text-gray-300"
                }`}>{ev.type}</span>
                <span className="text-gray-500 text-xs truncate">{JSON.stringify(ev.payload).slice(0, 100)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
            <Activity size={16} /> System Status
          </h3>
          <div className="space-y-4">
            {[
              ["Total Clients", overview?.total_clients ?? "-"],
              ["Online Clients", overview?.online_clients ?? "-", "text-green-400"],
              ["Active Jobs Running", overview?.active_jobs ?? "-", "text-blue-400"],
              ["Total Checkpoints", overview?.total_checkpoints ?? "-"],
              ["Best Global Accuracy", overview?.best_accuracy ? `${(overview.best_accuracy * 100).toFixed(2)}%` : "N/A", "text-purple-400 font-bold"],
            ].map(([label, value, extraClass]) => (
              <div key={label as string} className="flex justify-between items-center p-3 rounded-lg bg-gray-800/30">
                <span className="text-gray-400 text-sm">{label as string}</span>
                <span className={`text-sm ${extraClass || ""}`}>{value as string}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
