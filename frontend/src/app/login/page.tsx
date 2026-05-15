"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { HeartPulse, LogIn, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Vui lòng nhập username và password");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await login(username, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Đăng nhập thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center relative overflow-hidden">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-950/20 via-transparent to-gray-950" />

      {/* Decorative lung shapes */}
      <div className="absolute inset-0 pointer-events-none select-none overflow-hidden">
        {/* Left lung */}
        <div className="absolute left-[10%] top-1/2 -translate-y-1/2 animate-lung-inhale">
          <div
            className="h-64 w-44 opacity-[0.08]"
            style={{
              background: "radial-gradient(ellipse at 40% 30%, #3b82f6 0%, transparent 70%)",
              borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
              transform: "rotate(-8deg)",
            }}
          />
        </div>
        {/* Left lung highlight */}
        <div className="absolute left-[12%] top-1/2 -translate-y-1/2 animate-lung-inhale">
          <div
            className="h-56 w-36 opacity-[0.06]"
            style={{
              background: "radial-gradient(ellipse at 50% 30%, #60a5fa 0%, transparent 70%)",
              borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
              transform: "rotate(-8deg)",
            }}
          />
        </div>

        {/* Right lung */}
        <div className="absolute right-[10%] top-1/2 -translate-y-1/2 animate-lung-inhale-right">
          <div
            className="h-64 w-44 opacity-[0.08]"
            style={{
              background: "radial-gradient(ellipse at 60% 30%, #06b6d4 0%, transparent 70%)",
              borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
              transform: "rotate(8deg)",
            }}
          />
        </div>
        {/* Right lung highlight */}
        <div className="absolute right-[12%] top-1/2 -translate-y-1/2 animate-lung-inhale-right">
          <div
            className="h-56 w-36 opacity-[0.06]"
            style={{
              background: "radial-gradient(ellipse at 50% 30%, #22d3ee 0%, transparent 70%)",
              borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
              transform: "rotate(8deg)",
            }}
          />
        </div>
      </div>

      {/* Login card */}
      <div className="animate-card-enter relative z-10 w-full max-w-md mx-4">
        <div className="bg-gray-900/80 backdrop-blur-xl border border-gray-800 rounded-2xl shadow-2xl shadow-blue-900/10 p-8">
          {/* Logo & branding */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-blue-600/10 border border-blue-600/20 mb-4">
              <HeartPulse className="h-8 w-8 text-blue-400" />
            </div>
            <h1 className="text-xl font-bold text-white">PBL7 FL Platform</h1>
            <p className="text-sm text-gray-400 mt-1">Pneumonia Diagnosis System</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
                autoComplete="username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              {submitting ? (
                <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <LogIn className="h-5 w-5" />
              )}
              {submitting ? "Đang đăng nhập..." : "Đăng nhập"}
            </button>
          </form>

          <p className="text-center text-xs text-gray-500 mt-6">
            PBL7 Federated Learning &bull; Pneumonia Detection
          </p>
        </div>
      </div>
    </div>
  );
}
