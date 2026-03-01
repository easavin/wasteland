"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface NpcDetail {
  player_id: string;
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

export default function NpcDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [npc, setNpc] = useState<NpcDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<Partial<NpcDetail>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`/api/npcs`)
      .then((r) => r.json())
      .then((data) => {
        const found = (data.npcs || []).find((n: any) => n.player_id === id);
        if (found) {
          setNpc(found);
          setForm({
            display_name: found.display_name,
            settlement_name: found.settlement_name,
            zone: found.zone,
            population: found.population,
            food: found.food,
            scrap: found.scrap,
            gold: found.gold,
            first_name: found.first_name,
          });
        }
        setLoading(false);
      });
  }, [id]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch(`/api/npcs/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          displayName: form.display_name,
          settlementName: form.settlement_name,
          firstName: form.first_name,
          zone: form.zone,
          population: form.population,
          food: form.food,
          scrap: form.scrap,
          gold: form.gold,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setNpc((prev) => (prev ? { ...prev, ...data.npc } : null));
      } else {
        const err = await res.json();
        alert(err.error || "Failed to update");
      }
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="text-neutral-500">Loading…</div>;
  if (!npc) return <div className="text-neutral-500">NPC not found.</div>;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/npcs" className="text-neutral-500 hover:text-neutral-300">
          ← NPCs
        </Link>
        <span className="text-neutral-700">/</span>
        <h1 className="text-2xl font-bold text-white">{npc.display_name || npc.first_name}</h1>
      </div>

      <form onSubmit={handleSave} className="max-w-xl space-y-4">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-4">
          <h2 className="text-sm font-medium text-neutral-400">Edit NPC</h2>
          <div>
            <label className="block text-sm text-neutral-500 mb-1">Display name</label>
            <input
              value={form.display_name ?? ""}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-neutral-500 mb-1">Settlement name</label>
            <input
              value={form.settlement_name ?? ""}
              onChange={(e) => setForm({ ...form, settlement_name: e.target.value })}
              className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-neutral-500 mb-1">Zone</label>
              <input
                type="number"
                min={1}
                value={form.zone ?? 1}
                onChange={(e) => setForm({ ...form, zone: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-500 mb-1">Population</label>
              <input
                type="number"
                min={0}
                value={form.population ?? 0}
                onChange={(e) => setForm({ ...form, population: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
              />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-neutral-500 mb-1">Food</label>
              <input
                type="number"
                min={0}
                value={form.food ?? 0}
                onChange={(e) => setForm({ ...form, food: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-500 mb-1">Scrap</label>
              <input
                type="number"
                min={0}
                value={form.scrap ?? 0}
                onChange={(e) => setForm({ ...form, scrap: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-500 mb-1">Gold</label>
              <input
                type="number"
                min={0}
                value={form.gold ?? 0}
                onChange={(e) => setForm({ ...form, gold: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium"
          >
            {saving ? "Saving…" : "Save changes"}
          </button>
        </div>
      </form>

      <p className="mt-6 text-sm text-neutral-600">
        Quest management coming soon. NPCs appear in /market and can be discovered via /quest in-game.
      </p>
    </div>
  );
}
