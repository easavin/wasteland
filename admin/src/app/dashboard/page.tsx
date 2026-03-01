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

export default async function DashboardOverview() {
  const [stats, dauData, turnsData, outcomes] = await Promise.all([
    getStats(),
    getDauChart(),
    getTurnsPerDayChart(),
    getOutcomes(),
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
    </div>
  );
}
