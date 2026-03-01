import { db } from "@/lib/db";
import { sql } from "drizzle-orm";
import { GamesCharts } from "./games-charts";

export const dynamic = "force-dynamic";

async function getGameStats() {
  const [active, avgSurvival, avgLevel, totalGold] = await Promise.all([
    db.execute(sql`
      SELECT COUNT(*) as count FROM game_states WHERE status = 'active'
    `),
    db.execute(sql`
      SELECT AVG(turn_number)::numeric(10,1) as avg_turns
      FROM game_states
      WHERE status IN ('lost', 'abandoned')
    `),
    db.execute(sql`
      SELECT AVG(level)::numeric(10,1) as avg_level
      FROM game_states
      WHERE status = 'active'
    `),
    db.execute(sql`
      SELECT SUM(gold) as total_gold
      FROM game_states
      WHERE status = 'active'
    `),
  ]);

  return {
    activeGames: Number(active.rows[0]?.count || 0),
    avgSurvival: Number(avgSurvival.rows[0]?.avg_turns || 0).toFixed(1),
    avgLevel: Number(avgLevel.rows[0]?.avg_level || 0).toFixed(1),
    totalGold: Number(totalGold.rows[0]?.total_gold || 0),
  };
}

async function getActionDistribution() {
  const result = await db.execute(sql`
    SELECT
      player_action,
      COUNT(*) as count
    FROM turn_history
    GROUP BY player_action
    ORDER BY count DESC
    LIMIT 10
  `);

  return result.rows.map((r: any) => ({
    action: r.player_action,
    count: Number(r.count),
  }));
}

async function getClassDistribution() {
  const result = await db.execute(sql`
    SELECT
      CASE WHEN player_class = '' THEN 'unknown' ELSE player_class END as class,
      COUNT(*) as count
    FROM game_states
    WHERE status = 'active'
    GROUP BY class
    ORDER BY count DESC
  `);

  const CLASS_LABELS: Record<string, string> = {
    scavenger: "🔍 Scavenger",
    warden: "🛡 Warden",
    trader: "💰 Trader",
    diplomat: "🕊 Diplomat",
    medic: "💊 Medic",
    unknown: "❓ Unknown",
  };

  return result.rows.map((r: any) => ({
    name: CLASS_LABELS[r.class] || r.class,
    value: Number(r.count),
  }));
}

async function getLevelDistribution() {
  const result = await db.execute(sql`
    SELECT
      CASE
        WHEN level <= 3 THEN '1-3'
        WHEN level <= 7 THEN '4-7'
        WHEN level <= 12 THEN '8-12'
        WHEN level <= 20 THEN '13-20'
        ELSE '21+'
      END as bucket,
      COUNT(*) as count
    FROM game_states
    WHERE status = 'active'
    GROUP BY bucket
    ORDER BY MIN(level)
  `);

  return result.rows.map((r: any) => ({
    bucket: r.bucket,
    count: Number(r.count),
  }));
}

async function getRecentGames() {
  const result = await db.execute(sql`
    SELECT
      g.id,
      g.status,
      g.turn_number,
      g.settlement_name,
      g.player_class,
      g.level,
      g.zone,
      g.gold,
      g.population,
      g.food,
      g.scrap,
      g.morale,
      g.defense,
      g.started_at,
      g.ended_at,
      p.username,
      p.first_name,
      p.telegram_id
    FROM game_states g
    JOIN players p ON p.id = g.player_id
    ORDER BY g.started_at DESC
    LIMIT 30
  `);

  return result.rows as any[];
}

const CLASS_EMOJI: Record<string, string> = {
  scavenger: "🔍",
  warden: "🛡",
  trader: "💰",
  diplomat: "🕊",
  medic: "💊",
};

export default async function GamesPage() {
  const [stats, actions, classDistro, levelDistro, recentGames] =
    await Promise.all([
      getGameStats(),
      getActionDistribution(),
      getClassDistribution(),
      getLevelDistribution(),
      getRecentGames(),
    ]);

  const statCards = [
    {
      label: "Active Games",
      value: stats.activeGames.toLocaleString(),
      icon: "\u{1F3AE}",
    },
    {
      label: "Avg Survival (weeks)",
      value: stats.avgSurvival,
      icon: "\u{1F480}",
    },
    {
      label: "Avg Level (active)",
      value: stats.avgLevel,
      icon: "\u{2B50}",
    },
    {
      label: "Total Gold (active)",
      value: stats.totalGold.toLocaleString(),
      icon: "\u{1F4B0}",
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Games</h1>

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
      <GamesCharts
        actions={actions}
        classDistribution={classDistro}
        levelDistribution={levelDistro}
      />

      {/* Recent Games Table */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden mt-6">
        <div className="px-5 py-4 border-b border-neutral-800">
          <h2 className="text-sm font-medium text-neutral-400">
            Recent Games
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Player
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Settlement
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Class
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Level
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Status
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Week
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Resources
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Started
                </th>
              </tr>
            </thead>
            <tbody>
              {recentGames.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-8 text-center text-neutral-600"
                  >
                    No games yet
                  </td>
                </tr>
              ) : (
                recentGames.map((game: any) => (
                  <tr
                    key={game.id}
                    className="border-b border-neutral-800/50 hover:bg-neutral-800/30"
                  >
                    <td className="px-4 py-3 text-white">
                      {game.username || game.first_name || game.telegram_id}
                    </td>
                    <td className="px-4 py-3 text-amber-400 font-medium">
                      {game.settlement_name}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {CLASS_EMOJI[game.player_class] || ""}{" "}
                      {game.player_class || "-"}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      L{game.level} Z{game.zone}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          game.status === "active"
                            ? "bg-blue-900/40 text-blue-400"
                            : game.status === "lost"
                              ? "bg-red-900/40 text-red-400"
                              : "bg-neutral-800 text-neutral-500"
                        }`}
                      >
                        {game.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {game.turn_number}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs font-mono">
                      👥{game.population} 🌾{game.food} 🔩{game.scrap} 💰
                      {game.gold} 😊{game.morale} 🛡{game.defense}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs">
                      {new Date(game.started_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
