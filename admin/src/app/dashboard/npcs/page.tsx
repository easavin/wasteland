"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Npc {
  player_id: string;
  telegram_id: number;
  first_name: string;
  settlement_name: string;
  display_name: string;
  world_id: string;
  zone: number;
  population: number;
  food: number;
  scrap: number;
  gold: number;
  game_id: string;
}

interface World {
  id: string;
  name: string;
}

export default function NpcsPage() {
  const [npcs, setNpcs] = useState<Npc[]>([]);
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({
    displayName: "",
    settlementName: "",
    worldId: "",
    zone: 1,
    population: 50,
    food: 100,
    scrap: 80,
    gold: 50,
  });

  async function loadNpcs() {
    const res = await fetch("/api/npcs");
    const data = await res.json();
    if (res.ok) setNpcs(data.npcs || []);
  }

  async function loadWorlds() {
    const res = await fetch("/api/worlds");
    const data = await res.json();
    if (res.ok) setWorlds(data.worlds || []);
  }

  useEffect(() => {
    Promise.all([loadNpcs(), loadWorlds()]).finally(() => setLoading(false));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.displayName || !form.settlementName || !form.worldId) return;
    const res = await fetch("/api/npcs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    if (res.ok) {
      setCreateOpen(false);
      setForm({ displayName: "", settlementName: "", worldId: "", zone: 1, population: 50, food: 100, scrap: 80, gold: 50 });
      loadNpcs();
    } else {
      const err = await res.json();
      alert(err.error || "Failed to create NPC");
    }
  }

  async function handleDelete(playerId: string, name: string) {
    if (!confirm(`Delete NPC "${name}"? This cannot be undone.`)) return;
    const res = await fetch(`/api/npcs/${playerId}`, { method: "DELETE" });
    if (res.ok) loadNpcs();
    else alert("Failed to delete");
  }

  if (loading) {
    return (
      <div className="text-neutral-500">Loading NPCs…</div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">NPCs</h1>
        <button
          onClick={() => setCreateOpen(true)}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
        >
          + Create NPC
        </button>
      </div>

      <p className="text-neutral-500 text-sm mb-6">
        NPCs populate the wasteland. Players can see them in /market, trade with them, and do mini quests. They cannot receive whispers, challenges, or guild invites.
      </p>

      {createOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-lg font-bold text-white mb-4">Create NPC</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Display name</label>
                <input
                  value={form.displayName}
                  onChange={(e) => setForm({ ...form, displayName: e.target.value })}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  placeholder="e.g. Old Trader"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Settlement name</label>
                <input
                  value={form.settlementName}
                  onChange={(e) => setForm({ ...form, settlementName: e.target.value })}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  placeholder="e.g. Scrap Haven"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">World</label>
                <select
                  value={form.worldId}
                  onChange={(e) => setForm({ ...form, worldId: e.target.value })}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  required
                >
                  <option value="">Select world</option>
                  {worlds.map((w) => (
                    <option key={w.id} value={w.id}>{w.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Zone</label>
                  <input
                    type="number"
                    min={1}
                    value={form.zone}
                    onChange={(e) => setForm({ ...form, zone: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Gold</label>
                  <input
                    type="number"
                    min={0}
                    value={form.gold}
                    onChange={(e) => setForm({ ...form, gold: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Population</label>
                  <input
                    type="number"
                    min={1}
                    value={form.population}
                    onChange={(e) => setForm({ ...form, population: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Food</label>
                  <input
                    type="number"
                    min={0}
                    value={form.food}
                    onChange={(e) => setForm({ ...form, food: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-neutral-400 mb-1">Scrap</label>
                  <input
                    type="number"
                    min={0}
                    value={form.scrap}
                    onChange={(e) => setForm({ ...form, scrap: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium"
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800">
              <th className="text-left px-4 py-3 text-neutral-500 font-medium">Name</th>
              <th className="text-left px-4 py-3 text-neutral-500 font-medium">Settlement</th>
              <th className="text-left px-4 py-3 text-neutral-500 font-medium">Zone</th>
              <th className="text-left px-4 py-3 text-neutral-500 font-medium">Resources</th>
              <th className="text-left px-4 py-3 text-neutral-500 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {npcs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-neutral-600">
                  No NPCs yet. Create one to populate the wasteland.
                </td>
              </tr>
            ) : (
              npcs.map((npc) => (
                <tr key={npc.player_id} className="border-b border-neutral-800/50 hover:bg-neutral-800/30">
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/npcs/${npc.player_id}`}
                      className="text-amber-400 hover:text-amber-300 font-medium"
                    >
                      {npc.display_name || npc.first_name || "?"}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-neutral-400">{npc.settlement_name}</td>
                  <td className="px-4 py-3 text-neutral-400">{npc.zone}</td>
                  <td className="px-4 py-3 text-neutral-400">
                    pop:{npc.population} food:{npc.food} scrap:{npc.scrap} gold:{npc.gold}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/dashboard/npcs/${npc.player_id}`}
                      className="text-amber-400 hover:text-amber-300 text-xs mr-3"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(npc.player_id, npc.display_name || npc.first_name)}
                      className="text-red-400 hover:text-red-300 text-xs"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
