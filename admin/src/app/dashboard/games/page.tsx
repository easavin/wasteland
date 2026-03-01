import { db } from "@/lib/db";
import { sql } from "drizzle-orm";
import { GamesCharts } from "./games-charts";

export const dynamic = "force-dynamic";

async function getGameStats() {
  const [active, winRate, avgSurvival] = await Promise.all([
    db.execute(sql`
      SELECT COUNT(*) as count FROM game_states WHERE status = 'active'
    `),
    db.execute(sql`
      SELECT
        COUNT(CASE WHEN status = 'won' THEN 1 END)::float /
        NULLIF(COUNT(CASE WHEN status != 'active' THEN 1 END), 0) * 100 as win_rate
      FROM game_states
    `),
    db.execute(sql`
      SELECT AVG(turn_number)::numeric(10,1) as avg_turns
      FROM game_states
      WHERE status IN ('lost', 'abandoned')
    `),
  ]);

  return {
    activeGames: Number(active.rows[0]?.count || 0),
    winRate: Number(winRate.rows[0]?.win_rate || 0).toFixed(1),
    avgSurvival: Number(avgSurvival.rows[0]?.avg_turns || 0).toFixed(1),
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

async function getRecentGames() {
  const result = await db.execute(sql`
    SELECT
      g.id,
      g.status,
      g.turn_number,
      g.settlement_name,
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

export default async function GamesPage() {
  const [stats, actions, recentGames] = await Promise.all([
    getGameStats(),
    getActionDistribution(),
    getRecentGames(),
  ]);

  const statCards = [
    {
      label: "Active Games",
      value: stats.activeGames.toLocaleString(),
      icon: "\u{1F3AE}",
    },
    { label: "Win Rate", value: `${stats.winRate}%`, icon: "\u{1F3C6}" },
    {
      label: "Avg Survival (turns)",
      value: stats.avgSurvival,
      icon: "\u{1F480}",
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Games</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
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

      {/* Action Distribution Chart */}
      <GamesCharts actions={actions} />

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
                  Status
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Turns
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Pop
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
                    colSpan={7}
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
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          game.status === "active"
                            ? "bg-blue-900/40 text-blue-400"
                            : game.status === "won"
                              ? "bg-green-900/40 text-green-400"
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
                    <td className="px-4 py-3 text-neutral-400">
                      {game.population}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs font-mono">
                      F:{game.food} S:{game.scrap} M:{game.morale} D:
                      {game.defense}
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
