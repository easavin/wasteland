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

async function getSkillPopularity() {
  // Aggregate skills JSONB across active games
  const result = await db.execute(sql`
    SELECT key as skill, SUM(value::int) as total_ranks
    FROM game_states, jsonb_each_text(skills)
    WHERE status = 'active' AND skills != '{}'::jsonb
    GROUP BY key
    ORDER BY total_ranks DESC
    LIMIT 12
  `);

  const SKILL_LABELS: Record<string, string> = {
    iron_stomach: "Iron Stomach",
    field_medic: "Field Medic",
    inspiring_leader: "Inspiring Leader",
    scrap_mastery: "Scrap Mastery",
    haggler: "Haggler",
    black_market: "Black Market",
    salvage_expert: "Salvage Expert",
    thick_skin: "Thick Skin",
    fortification_expert: "Fortification Expert",
    patrol_routes: "Patrol Routes",
    raiders_instinct: "Raider's Instinct",
    caravan_network: "Caravan Network",
  };

  return result.rows.map((r: any) => ({
    skill: SKILL_LABELS[r.skill] || r.skill,
    ranks: Number(r.total_ranks),
  }));
}

async function getGoldEconomy() {
  // Daily gold earned and spent via turn history
  const result = await db.execute(sql`
    SELECT
      DATE(created_at) as day,
      SUM(CASE WHEN gold_delta > 0 THEN gold_delta ELSE 0 END) as earned,
      SUM(CASE WHEN gold_delta < 0 THEN ABS(gold_delta) ELSE 0 END) as spent
    FROM turn_history
    WHERE created_at >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(created_at)
    ORDER BY day
  `);

  return result.rows.map((r: any) => ({
    day: new Date(r.day).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    earned: Number(r.earned),
    spent: Number(r.spent),
  }));
}

export default async function AnalyticsPage() {
  const [
    retention,
    voicePct,
    languages,
    avgTurns,
    turnsDistribution,
    skillPopularity,
    goldEconomy,
  ] = await Promise.all([
    getRetention(),
    getVoiceUsage(),
    getLanguageDistribution(),
    getAvgTurnsPerGame(),
    getTurnsDistribution(),
    getSkillPopularity(),
    getGoldEconomy(),
  ]);

  const statCards = [
    { label: "Day 1 Retention", value: `${retention.d1}%`, icon: "\u{1F504}" },
    { label: "Day 7 Retention", value: `${retention.d7}%`, icon: "\u{1F4C6}" },
    { label: "Voice Usage", value: `${voicePct}%`, icon: "\u{1F3A4}" },
    {
      label: "Avg Weeks / Game",
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
        skillPopularity={skillPopularity}
        goldEconomy={goldEconomy}
      />
    </div>
  );
}
