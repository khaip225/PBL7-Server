"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TrainingJob } from "@/lib/types";
import { Play, Square, Plus, RefreshCw } from "lucide-react";

export default function JobsPage() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  async function fetchJobs() {
    try {
      const res = await api.jobs.list({ limit: "50" });
      setJobs(res.items);
    } catch {}
  }

  async function handleStart(jobId: string) {
    try {
      await api.jobs.start(jobId);
      fetchJobs();
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function handleStop(jobId: string) {
    try {
      await api.jobs.stop(jobId);
      fetchJobs();
    } catch (e: any) {
      alert(e.message);
    }
  }

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      draft: "bg-gray-700 text-gray-300",
      pending: "bg-yellow-900/30 text-yellow-400 border border-yellow-600/30",
      running: "bg-green-900/30 text-green-400 border border-green-600/30 animate-pulse",
      completed: "bg-blue-900/30 text-blue-400",
      stopped: "bg-orange-900/30 text-orange-400",
      failed: "bg-red-900/30 text-red-400",
    };
    return `px-2 py-0.5 rounded text-xs ${colors[status] || colors.draft}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Training Jobs</h2>
        <div className="flex gap-2">
          <button onClick={fetchJobs} className="p-2 rounded-lg border border-gray-700 text-gray-400 hover:text-white"><RefreshCw size={16} /></button>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
            <Plus size={16} /> New Job
          </button>
        </div>
      </div>

      {showCreate && <CreateJobForm onDone={() => { setShowCreate(false); fetchJobs(); }} onCancel={() => setShowCreate(false)} />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {jobs.map((job) => (
          <div key={job.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex justify-between items-start mb-3">
              <div>
                <h3 className="font-semibold">{job.name}</h3>
                <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs ${
                  job.task_type === "audio" ? "bg-purple-900/30 text-purple-400" : "bg-blue-900/30 text-blue-400"
                }`}>{job.task_type}</span>
              </div>
              <span className={statusBadge(job.status)}>{job.status}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-4">
              <div>Strategy: <span className="text-gray-300">{job.strategy}</span></div>
              <div>Rounds: <span className="text-gray-300">{job.current_round}/{job.num_rounds}</span></div>
              <div>Min Clients: <span className="text-gray-300">{job.min_clients}</span></div>
              <div>Min Samples: <span className="text-gray-300">{job.min_samples}</span></div>
              {job.pid && <div>PID: <span className="text-gray-300 font-mono">{job.pid}</span></div>}
              {job.started_at && <div>Started: <span className="text-gray-300">{new Date(job.started_at).toLocaleString()}</span></div>}
            </div>

            <div className="flex gap-2">
              {job.status === "draft" && (
                <button onClick={() => handleStart(job.id)} className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded text-xs hover:bg-green-700">
                  <Play size={14} /> Start
                </button>
              )}
              {job.status === "running" && (
                <button onClick={() => handleStop(job.id)} className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded text-xs hover:bg-red-700">
                  <Square size={14} /> Stop
                </button>
              )}
              {job.status === "completed" && (
                <span className="text-xs text-gray-500">Completed {job.completed_at ? new Date(job.completed_at).toLocaleString() : ""}</span>
              )}
              {job.status === "failed" && (
                <span className="text-xs text-red-400">Failed - check logs</span>
              )}
            </div>
          </div>
        ))}
        {jobs.length === 0 && <p className="text-gray-500 col-span-2 text-center py-12">No training jobs yet. Create one!</p>}
      </div>
    </div>
  );
}

function CreateJobForm({ onDone, onCancel }: { onDone: () => void; onCancel: () => void }) {
  const [name, setName] = useState("");
  const [taskType, setTaskType] = useState<"audio" | "image">("image");
  const [numRounds, setNumRounds] = useState(10);
  const [minClients, setMinClients] = useState(2);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.jobs.create({
        name,
        task_type: taskType,
        strategy: "fedavg",
        num_rounds: numRounds,
        min_clients: minClients,
        min_samples: 300,
        model_config: { lr: 1e-4, batch_size: 16, local_epochs: 2, mu: 0.001 },
      });
      onDone();
    } catch (e: any) {
      alert("Error: " + e.message);
    }
    setLoading(false);
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
        <h3 className="text-lg font-bold mb-4">Create Training Job</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Job Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Task Type</label>
            <select value={taskType} onChange={(e) => setTaskType(e.target.value as any)} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
              <option value="image">Image (X-ray)</option>
              <option value="audio">Audio (Lung Sound)</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Rounds</label>
              <input type="number" value={numRounds} onChange={(e) => setNumRounds(Number(e.target.value))} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" min={1} />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Min Clients</label>
              <input type="number" value={minClients} onChange={(e) => setMinClients(Number(e.target.value))} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" min={1} />
            </div>
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button type="button" onClick={onCancel} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
            <button type="submit" disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
              {loading ? "Creating..." : "Create Job"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
