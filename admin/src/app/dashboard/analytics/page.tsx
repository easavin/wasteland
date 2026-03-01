import { db } from "@/lib/db";
import { sql } from "drizzle-orm";
import { AnalyticsCharts } from "./analytics-charts";

export const dynamic = "force-dynamic";

async function getRetention() {
  // Day 1 retention: players who played on day after registration
  const d1 = await db.execute(sql`
    SELECT
      COUNT(DISTINCT CASE
        WHEN EXISTS (
          SELECT 1 FROM analytics_events ae2
          WHERE ae2.player_id = p.id
            AND DATE(ae2.created_at) = DATE(p.created_at) + INTERVAL '1 day'
        ) THEN p.id
      END)::float /
      NULLIF(COUNT(DISTINCT p.id), 0) * 100 as retention_d1
    FROM players p
    WHERE p.created_at < NOW() - INTERVAL '1 day'
  `);

  // Day 7 retention
  const d7 = await db.execute(sql`
    SELECT
      COUNT(DISTINCT CASE
        WHEN EXISTS (
          SELECT 1 FROM analytics_events ae2
          WHERE ae2.player_id = p.id
            AND DATE(ae2.created_at) = DATE(p.created_at) + INTERVAL '7 days'
        ) THEN p.id
      END)::float /
      NULLIF(COUNT(DISTINCT p.id), 0) * 100 as retention_d7
    FROM players p
    WHERE p.created_at < NOW() - INTERVAL '7 days'
  `);

  return {
    d1: Number(d1.rows[0]?.retention_d1 || 0).toFixed(1),
    d7: Number(d7.rows[0]?.retention_d7 || 0).toFixed(1),
  };
}

async function getVoiceUsage() {
  const result = await db.execute(sql`
    SELECT
      COUNT(CASE WHEN voice_input = true THEN 1 END)::float /
      NULLIF(COUNT(*), 0) * 100 as voice_pct
    FROM turn_history
  `);

  return Number(result.rows[0]?.voice_pct || 0).toFixed(1);
}

async function getLanguageDistribution() {
  const result = await db.execute(sql`
    SELECT language, COUNT(*) as count
    FROM players
    GROUP BY language
    ORDER BY count DESC
    LIMIT 10
  `);

  return result.rows.map((r: any) => ({
    language: r.language.toUpperCase(),
    count: Number(r.count),
  }));
}

async function getAvgTurnsPerGame() {
  const result = await db.execute(sql`
    SELECT AVG(turn_number)::numeric(10,1) as avg_turns
    FROM game_states
    WHERE status != 'active'
  `);

  return Number(result.rows[0]?.avg_turns || 0).toFixed(1);
}

async function getTurnsDistribution() {
  const result = await db.execute(sql`
    SELECT
      CASE
        WHEN turn_number <= 5 THEN '1-5'
        WHEN turn_number <= 10 THEN '6-10'
        WHEN turn_number <= 20 THEN '11-20'
        WHEN turn_number <= 30 THEN '21-30'
        ELSE '31+'
      END as bucket,
      COUNT(*) as count
    FROM game_states
    WHERE status != 'active'
    GROUP BY bucket
    ORDER BY MIN(turn_number)
  `);

  return result.rows.map((r: any) => ({
    bucket: r.bucket,
    count: Number(r.count),
  }));
}

export default async function AnalyticsPage() {
  const [retention, voicePct, languages, avgTurns, turnsDistribution] =
    await Promise.all([
      getRetention(),
      getVoiceUsage(),
      getLanguageDistribution(),
      getAvgTurnsPerGame(),
      getTurnsDistribution(),
    ]);

  const statCards = [
    { label: "Day 1 Retention", value: `${retention.d1}%`, icon: "\u{1F504}" },
    { label: "Day 7 Retention", value: `${retention.d7}%`, icon: "\u{1F4C6}" },
    { label: "Voice Usage", value: `${voicePct}%`, icon: "\u{1F3A4}" },
    {
      label: "Avg Turns / Game",
      value: avgTurns,
      icon: "\u{1F3B2}",
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Analytics</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => (
          <div
            key={card.label}
            className="bg-neutral-900 border border-neutral-800 rounded-xl p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-neutral-500 text-sm">{card.label}</span>
              <span className="text-xl">{card.icon}</span>
            </div>
            <div className="text-2xl font-bold text-white">{card.value}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <AnalyticsCharts
        languages={languages}
        turnsDistribution={turnsDistribution}
      />
    </div>
  );
}
