"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TrainingJob, RoundMetrics } from "@/lib/types";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function MetricsPage() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<string>("");
  const [rounds, setRounds] = useState<RoundMetrics[]>([]);

  useEffect(() => {
    api.jobs.list({ limit: "50" }).then((res) => {
      setJobs(res.items);
      const running = res.items.find((j: TrainingJob) => j.status === "running" || j.status === "completed");
      if (running) setSelectedJob(running.id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedJob) return;
    api.metrics.convergence(selectedJob).then((data) => {
      setRounds(data.rounds || []);
    }).catch(() => {});
  }, [selectedJob]);

  const chartData = rounds.map((r) => ({
    round: r.round_number,
    loss: r.loss != null ? Number(r.loss.toFixed(4)) : null,
    accuracy: r.accuracy != null ? Number((r.accuracy * 100).toFixed(1)) : null,
    auroc: r.auroc_macro != null ? Number((r.auroc_macro * 100).toFixed(1)) : null,
    clients: r.num_clients,
  }));

  // Per-class AUROC for the latest round
  const latestRound = rounds.length > 0 ? rounds[rounds.length - 1] : null;
  const perClassAuroc = latestRound?.per_class_auroc
    ? Object.entries(latestRound.per_class_auroc).map(([cls, val]) => ({
        class: cls,
        auroc: Number((val * 100).toFixed(1)),
      }))
    : [];

  // Bar colors for per-class
  const classColors: Record<string, string> = {
    Crackle: "#06b6d4",
    Wheeze: "#eab308",
    Pneumonia: "#ef4444",
    COPD_Emphysema: "#f97316",
    Fibrosis: "#8b5cf6",
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Metrics & Analytics</h2>
        <select
          value={selectedJob}
          onChange={(e) => setSelectedJob(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
        >
          <option value="">Select job...</option>
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>{j.name} ({j.status})</option>
          ))}
        </select>
      </div>

      {selectedJob && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-xs text-gray-500">Total Rounds</p>
              <p className="text-2xl font-bold text-white">{rounds.length}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-xs text-gray-500">Best AUROC</p>
              <p className="text-2xl font-bold text-green-400">
                {rounds.length > 0
                  ? `${Math.max(...rounds.filter(r => r.auroc_macro != null).map(r => r.auroc_macro! * 100), 0).toFixed(1)}%`
                  : "-"}
              </p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-xs text-gray-500">Best Loss</p>
              <p className="text-2xl font-bold text-red-400">
                {rounds.length > 0
                  ? Math.min(...rounds.filter(r => r.loss != null).map(r => r.loss!)).toFixed(4)
                  : "-"}
              </p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-xs text-gray-500">Latest Accuracy</p>
              <p className="text-2xl font-bold text-blue-400">
                {latestRound?.accuracy != null
                  ? `${(latestRound.accuracy * 100).toFixed(1)}%`
                  : "-"}
              </p>
            </div>
          </div>

          {/* Charts: Loss + AUROC */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">Loss Curve</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="round" stroke="#6b7280" fontSize={12} />
                  <YAxis stroke="#6b7280" fontSize={12} />
                  <Tooltip
                    contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "8px", fontSize: "12px" }}
                  />
                  <Line type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} name="Loss" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">AUROC Curve (Macro)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="round" stroke="#6b7280" fontSize={12} />
                  <YAxis stroke="#6b7280" fontSize={12} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "8px", fontSize: "12px" }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="auroc" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} name="AUROC %" />
                  {chartData.some(d => d.accuracy != null) && (
                    <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} name="Accuracy %" strokeDasharray="5 5" />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Per-class AUROC bar */}
          {perClassAuroc.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">
                Per-Class AUROC (Round {latestRound?.round_number})
              </h3>
              <div className="space-y-3">
                {perClassAuroc.map(({ class: cls, auroc }) => (
                  <div key={cls}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-300">{cls}</span>
                      <span className="font-mono text-gray-400">{auroc}%</span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.max(0, auroc)}%`,
                          backgroundColor: classColors[cls] || "#6b7280",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Communication Stats Table */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-400 mb-4">Communication Stats</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400 border-b border-gray-800">
                    <th className="p-3">Round</th>
                    <th className="p-3">Clients</th>
                    <th className="p-3">Skipped</th>
                    <th className="p-3">Loss</th>
                    <th className="p-3">AUROC</th>
                    <th className="p-3">Accuracy</th>
                    <th className="p-3">Duration</th>
                    <th className="p-3">Aggregated At</th>
                  </tr>
                </thead>
                <tbody>
                  {rounds.map((r) => (
                    <tr key={r.id} className="border-b border-gray-800/50">
                      <td className="p-3 font-medium">Round {r.round_number}</td>
                      <td className="p-3">{r.num_clients}</td>
                      <td className="p-3 text-gray-500">{r.num_skipped}</td>
                      <td className="p-3 font-mono text-red-400">{r.loss?.toFixed(4) ?? "-"}</td>
                      <td className="p-3 font-mono text-green-400">
                        {r.auroc_macro != null ? `${(r.auroc_macro * 100).toFixed(1)}%` : "-"}
                      </td>
                      <td className="p-3 font-mono text-blue-400">
                        {r.accuracy != null ? `${(r.accuracy * 100).toFixed(1)}%` : "-"}
                      </td>
                      <td className="p-3 text-gray-500">{r.duration_seconds ? `${r.duration_seconds.toFixed(1)}s` : "-"}</td>
                      <td className="p-3 text-gray-500 text-xs">{new Date(r.aggregated_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!selectedJob && (
        <div className="text-center py-20 text-gray-500">Select a training job to view metrics</div>
      )}
    </div>
  );
}
