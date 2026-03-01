import { db } from "@/lib/db";
import { players, gameStates, turnHistory, payments, analyticsEvents } from "@/lib/schema";
import { sql, eq, gte, count, sum } from "drizzle-orm";
import { OverviewCharts } from "./overview-charts";

export const dynamic = "force-dynamic";

async function getStats() {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

  const [[totalPlayers], [activeGames], [dauToday], [revenue30d]] =
    await Promise.all([
      db.select({ value: count() }).from(players),
      db
        .select({ value: count() })
        .from(gameStates)
        .where(eq(gameStates.status, "active")),
      db
        .select({ value: count() })
        .from(analyticsEvents)
        .where(
          sql`${analyticsEvents.createdAt} >= ${today} AND ${analyticsEvents.eventType} = 'game_start'`
        ),
      db
        .select({ value: sum(payments.amount) })
        .from(payments)
        .where(
          sql`${payments.status} = 'completed' AND ${payments.createdAt} >= ${thirtyDaysAgo}`
        ),
    ]);

  return {
    totalPlayers: totalPlayers.value,
    activeGames: activeGames.value,
    dauToday: dauToday.value,
    revenue30d: Number(revenue30d.value || 0),
  };
}

async function getDauChart() {
  const thirtyDaysAgo = new Date(
    Date.now() - 30 * 24 * 60 * 60 * 1000
  );

  const rows = await db.execute(sql`
    SELECT
      DATE(created_at) as day,
      COUNT(DISTINCT player_id) as dau
    FROM analytics_events
    WHERE created_at >= ${thirtyDaysAgo}
      AND event_type IN ('game_start', 'turn_played')
    GROUP BY DATE(created_at)
    ORDER BY day
  `);

  return rows.rows.map((r: any) => ({
    day: new Date(r.day).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    dau: Number(r.dau),
  }));
}

async function getTurnsPerDayChart() {
  const thirtyDaysAgo = new Date(
    Date.now() - 30 * 24 * 60 * 60 * 1000
  );

  const rows = await db.execute(sql`
    SELECT
      DATE(created_at) as day,
      COUNT(*) as turns
    FROM turn_history
    WHERE created_at >= ${thirtyDaysAgo}
    GROUP BY DATE(created_at)
    ORDER BY day
  `);

  return rows.rows.map((r: any) => ({
    day: new Date(r.day).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    turns: Number(r.turns),
  }));
}

async function getOutcomes() {
  const rows = await db.execute(sql`
    SELECT status, COUNT(*) as count
    FROM game_states
    WHERE status != 'active'
    GROUP BY status
  `);

  return rows.rows.map((r: any) => ({
    name: r.status.charAt(0).toUpperCase() + r.status.slice(1),
    value: Number(r.count),
  }));
}

async function getTopPlayers() {
  const rows = await db.execute(sql`
    SELECT
      g.settlement_name,
      g.player_class,
      g.level,
      g.zone,
      g.turn_number,
      g.population,
      g.gold,
      p.username,
      p.first_name
    FROM game_states g
    JOIN players p ON p.id = g.player_id
    WHERE g.status = 'active'
    ORDER BY g.level DESC, g.xp DESC
    LIMIT 5
  `);

  return rows.rows as any[];
}

export default async function DashboardOverview() {
  const [stats, dauData, turnsData, outcomes, topPlayers] = await Promise.all([
    getStats(),
    getDauChart(),
    getTurnsPerDayChart(),
    getOutcomes(),
    getTopPlayers(),
  ]);

  const cards = [
    {
      label: "Total Players",
      value: stats.totalPlayers.toLocaleString(),
      icon: "\u{1F465}",
    },
    {
      label: "Active Games",
      value: stats.activeGames.toLocaleString(),
      icon: "\u{1F3AE}",
    },
    {
      label: "DAU (Today)",
      value: stats.dauToday.toLocaleString(),
      icon: "\u{1F4C5}",
    },
    {
      label: "Revenue (30d)",
      value: `$${stats.revenue30d.toFixed(2)}`,
      icon: "\u{1F4B0}",
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Overview</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map((card) => (
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
      <OverviewCharts
        dauData={dauData}
        turnsData={turnsData}
        outcomes={outcomes}
      />

      {/* Top Players Leaderboard */}
      {topPlayers.length > 0 && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden mt-6">
          <div className="px-5 py-4 border-b border-neutral-800">
            <h2 className="text-sm font-medium text-neutral-400">
              Top Active Players (by level)
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                    #
                  </th>
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
                    Zone
                  </th>
                  <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                    Week
                  </th>
                </tr>
              </thead>
              <tbody>
                {topPlayers.map((p: any, i: number) => {
                  const classEmoji: Record<string, string> = {
                    scavenger: "\u{1F50D}",
                    warden: "\u{1F6E1}",
                    trader: "\u{1F4B0}",
                    diplomat: "\u{1F54A}",
                    medic: "\u{1F48A}",
                  };
                  return (
                    <tr
                      key={i}
                      className="border-b border-neutral-800/50 hover:bg-neutral-800/30"
                    >
                      <td className="px-4 py-3 text-neutral-500 font-mono">
                        {i + 1}
                      </td>
                      <td className="px-4 py-3 text-white">
                        {p.username || p.first_name || "Anonymous"}
                      </td>
                      <td className="px-4 py-3 text-amber-400 font-medium">
                        {p.settlement_name}
                      </td>
                      <td className="px-4 py-3 text-neutral-400">
                        {classEmoji[p.player_class] || ""} {p.player_class}
                      </td>
                      <td className="px-4 py-3 text-white font-bold">
                        {p.level}
                      </td>
                      <td className="px-4 py-3 text-neutral-400">{p.zone}</td>
                      <td className="px-4 py-3 text-neutral-400">
                        {p.turn_number}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
