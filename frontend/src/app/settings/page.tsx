"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Save, RotateCcw } from "lucide-react";

interface SettingItem {
  key: string;
  value: Record<string, unknown>;
  description: string | null;
  updated_at: string;
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingItem[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.settings.list().then(setSettings).catch(() => {});
  }, []);

  async function handleSave(key: string) {
    const value = editing[key];
    if (value === undefined) return;
    try {
      let parsed: unknown = value;
      try { parsed = JSON.parse(value); } catch { parsed = { v: value }; }
      await api.settings.update(key, { value: typeof parsed === "object" && parsed !== null ? parsed : { v: String(parsed) } });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      const updated = await api.settings.list();
      setSettings(updated);
    } catch {}
  }

  async function handleReset() {
    if (!confirm("Reset all settings to defaults?")) return;
    await fetch("http://localhost:8000/api/settings/reset", { method: "POST" });
    const updated = await api.settings.list();
    setSettings(updated);
  }

  function formatVal(v: unknown): string {
    if (typeof v === "object" && v !== null) return JSON.stringify(v, null, 0);
    return String(v);
  }

  const sections = [
    { title: "Flower Configuration", prefix: "flower." },
    { title: "Aggregation", prefix: "aggregation." },
    { title: "System", prefix: "system." },
    { title: "Other", prefix: "" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Settings</h2>
        <div className="flex gap-2">
          <button onClick={handleReset} className="flex items-center gap-2 px-4 py-2 border border-gray-700 text-gray-400 rounded-lg text-sm hover:text-white">
            <RotateCcw size={16} /> Reset Defaults
          </button>
          {saved && <span className="px-3 py-2 bg-green-900/30 text-green-400 rounded-lg text-sm">Saved!</span>}
        </div>
      </div>

      {sections.map((section) => {
        const filtered = settings.filter((s) =>
          section.prefix === "" ? !s.key.includes(".") || (!s.key.startsWith("flower.") && !s.key.startsWith("aggregation.") && !s.key.startsWith("system.")) :
          s.key.startsWith(section.prefix)
        );
        if (filtered.length === 0) return null;

        return (
          <div key={section.title} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <h3 className="p-4 border-b border-gray-800 text-sm font-semibold text-gray-400">{section.title}</h3>
            <div className="divide-y divide-gray-800">
              {filtered.map((s) => (
                <div key={s.key} className="flex items-center gap-4 p-4">
                  <div className="flex-1">
                    <label className="text-sm font-medium">{s.key}</label>
                    {s.description && <p className="text-xs text-gray-500 mt-0.5">{s.description}</p>}
                  </div>
                  <input
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm font-mono"
                    defaultValue={formatVal(s.value?.v ?? s.value)}
                    onChange={(e) => setEditing({ ...editing, [s.key]: e.target.value })}
                  />
                  <button
                    onClick={() => handleSave(s.key)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                  >
                    <Save size={12} /> Save
                  </button>
                  <span className="text-xs text-gray-600 w-32 text-right">
                    {new Date(s.updated_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
