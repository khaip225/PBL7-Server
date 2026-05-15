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
    loss: r.loss?.toFixed(4),
    accuracy: r.accuracy ? (r.accuracy * 100).toFixed(1) : null,
    clients: r.num_clients,
  }));

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
                  <Line type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">Accuracy Curve</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="round" stroke="#6b7280" fontSize={12} />
                  <YAxis stroke="#6b7280" fontSize={12} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: "8px", fontSize: "12px" }}
                  />
                  <Line type="monotone" dataKey="accuracy" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-400 mb-4">Communication Stats</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-800">
                  <th className="p-3">Round</th>
                  <th className="p-3">Clients</th>
                  <th className="p-3">Skipped</th>
                  <th className="p-3">Loss</th>
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
                    <td className="p-3 font-mono text-green-400">{r.accuracy ? `${(r.accuracy * 100).toFixed(1)}%` : "-"}</td>
                    <td className="p-3 text-gray-500">{r.duration_seconds ? `${r.duration_seconds.toFixed(1)}s` : "-"}</td>
                    <td className="p-3 text-gray-500 text-xs">{new Date(r.aggregated_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!selectedJob && (
        <div className="text-center py-20 text-gray-500">Select a training job to view metrics</div>
      )}
    </div>
  );
}
