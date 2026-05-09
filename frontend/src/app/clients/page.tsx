"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Client } from "@/lib/types";
import { Wifi, WifiOff, Cpu, HardDrive } from "lucide-react";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClients();
    const interval = setInterval(fetchClients, 10000);
    return () => clearInterval(interval);
  }, []);

  async function fetchClients() {
    try {
      const res = await api.clients.list({ limit: "50" });
      setClients(res.items);
    } catch {}
    setLoading(false);
  }

  const statusIcon = (status: string) => {
    if (status === "online") return <Wifi size={14} className="text-green-400" />;
    if (status === "idle") return <Wifi size={14} className="text-yellow-400" />;
    return <WifiOff size={14} className="text-red-400" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Clients</h2>
        <span className="text-sm text-gray-400">
          {clients.filter(c => c.status === "online").length} / {clients.length} online
        </span>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-left text-gray-400">
              <th className="p-4">Status</th>
              <th className="p-4">Name</th>
              <th className="p-4">Host</th>
              <th className="p-4">Task</th>
              <th className="p-4">Hardware</th>
              <th className="p-4">Dataset</th>
              <th className="p-4">Latency</th>
              <th className="p-4">Last Heartbeat</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => (
              <tr key={client.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="p-4">
                  <span className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-xs ${
                    client.status === "online" ? "bg-green-900/30 text-green-400" :
                    client.status === "idle" ? "bg-yellow-900/30 text-yellow-400" :
                    "bg-red-900/30 text-red-400"
                  }`}>
                    {statusIcon(client.status)} {client.status}
                  </span>
                </td>
                <td className="p-4 font-medium">{client.client_name}</td>
                <td className="p-4 text-gray-400 font-mono text-xs">{client.client_host}</td>
                <td className="p-4">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    client.task_type === "audio" ? "bg-purple-900/30 text-purple-400" : "bg-blue-900/30 text-blue-400"
                  }`}>
                    {client.task_type}
                  </span>
                </td>
                <td className="p-4 text-gray-400 text-xs">
                  <div className="flex items-center gap-1"><Cpu size={12} /> {client.hardware_info?.gpu_name || "N/A"}</div>
                  <div className="flex items-center gap-1 mt-0.5"><HardDrive size={12} /> {client.hardware_info?.ram_total_gb || "?"} GB RAM</div>
                </td>
                <td className="p-4 text-gray-400 text-xs">
                  {client.dataset_info?.total_samples ?? "?"} samples
                </td>
                <td className="p-4 text-gray-400">{client.latency_ms?.toFixed(0)} ms</td>
                <td className="p-4 text-gray-500 text-xs">
                  {client.last_heartbeat ? new Date(client.last_heartbeat).toLocaleString() : "Never"}
                </td>
              </tr>
            ))}
            {clients.length === 0 && !loading && (
              <tr><td colSpan={8} className="p-8 text-center text-gray-500">No clients connected</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
