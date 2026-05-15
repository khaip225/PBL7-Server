"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Checkpoint, TrainingJob } from "@/lib/types";
import { Download, CheckCircle, Trash2 } from "lucide-react";

export default function ModelsPage() {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [filterJob, setFilterJob] = useState<string>("");

  useEffect(() => {
    fetchCheckpoints();
    api.jobs.list({ limit: "50" }).then(res => setJobs(res.items)).catch(() => {});
  }, [filterJob]);

  async function fetchCheckpoints() {
    const params: Record<string, string> = { limit: "50" };
    if (filterJob) params.job_id = filterJob;
    try {
      const res = await api.models.list(params);
      setCheckpoints(res.items);
    } catch {}
  }

  async function handleActivate(id: string) {
    await api.models.activate(id);
    fetchCheckpoints();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this checkpoint?")) return;
    await api.models.delete(id);
    fetchCheckpoints();
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Models & Checkpoints</h2>
        <select
          value={filterJob}
          onChange={(e) => setFilterJob(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
        >
          <option value="">All jobs</option>
          {jobs.map((j) => (
            <option key={j.id} value={j.id}>{j.name}</option>
          ))}
        </select>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-left text-gray-400">
              <th className="p-4">Round</th>
              <th className="p-4">File</th>
              <th className="p-4">Size</th>
              <th className="p-4">SHA256</th>
              <th className="p-4">Status</th>
              <th className="p-4">Created</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {checkpoints.map((cp) => (
              <tr key={cp.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="p-4 font-medium">Round {cp.round_number}</td>
                <td className="p-4 text-gray-400 font-mono text-xs">{cp.file_path}</td>
                <td className="p-4 text-gray-400 text-xs">
                  {cp.file_size_bytes ? `${(cp.file_size_bytes / 1e6).toFixed(1)} MB` : "-"}
                </td>
                <td className="p-4 text-gray-500 font-mono text-xs">
                  {cp.sha256_hash ? cp.sha256_hash.slice(0, 16) + "..." : "-"}
                </td>
                <td className="p-4">
                  <div className="flex gap-1.5">
                    {cp.is_best && <span className="px-2 py-0.5 rounded text-xs bg-yellow-900/30 text-yellow-400">Best</span>}
                    {cp.is_active && <span className="px-2 py-0.5 rounded text-xs bg-green-900/30 text-green-400">Active</span>}
                  </div>
                </td>
                <td className="p-4 text-gray-500 text-xs">{new Date(cp.created_at).toLocaleString()}</td>
                <td className="p-4">
                  <div className="flex gap-2">
                    <a
                      href={api.models.downloadUrl(cp.id)}
                      className="p-1.5 rounded bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700"
                      title="Download"
                    >
                      <Download size={14} />
                    </a>
                    {!cp.is_active && (
                      <button onClick={() => handleActivate(cp.id)} className="p-1.5 rounded bg-gray-800 text-gray-400 hover:text-green-400" title="Activate">
                        <CheckCircle size={14} />
                      </button>
                    )}
                    <button onClick={() => handleDelete(cp.id)} className="p-1.5 rounded bg-gray-800 text-gray-400 hover:text-red-400" title="Delete">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {checkpoints.length === 0 && (
              <tr><td colSpan={7} className="p-8 text-center text-gray-500">No checkpoints yet. Run a training job!</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
