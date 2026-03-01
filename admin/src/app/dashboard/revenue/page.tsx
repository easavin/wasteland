import { db } from "@/lib/db";
import { sql } from "drizzle-orm";
import { RevenueCharts } from "./revenue-charts";

export const dynamic = "force-dynamic";

async function getTotalRevenue() {
  const result = await db.execute(sql`
    SELECT
      COALESCE(SUM(amount), 0) as total
    FROM payments
    WHERE status = 'completed'
  `);
  return Number(result.rows[0]?.total || 0);
}

async function getRevenueByDay() {
  const result = await db.execute(sql`
    SELECT
      DATE(completed_at) as day,
      SUM(amount)::numeric(12,2) as revenue
    FROM payments
    WHERE status = 'completed'
      AND completed_at >= NOW() - INTERVAL '30 days'
    GROUP BY DATE(completed_at)
    ORDER BY day
  `);

  return result.rows.map((r: any) => ({
    day: new Date(r.day).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    revenue: Number(r.revenue),
  }));
}

async function getPaymentMethodBreakdown() {
  const result = await db.execute(sql`
    SELECT
      payment_type,
      COUNT(*) as count,
      SUM(amount)::numeric(12,2) as total
    FROM payments
    WHERE status = 'completed'
    GROUP BY payment_type
  `);

  return result.rows.map((r: any) => ({
    type: r.payment_type,
    count: Number(r.count),
    total: Number(r.total),
  }));
}

async function getRecentTransactions() {
  const result = await db.execute(sql`
    SELECT
      pay.id,
      pay.payment_type,
      pay.status,
      pay.amount,
      pay.currency,
      pay.stars_amount,
      pay.created_at,
      pay.completed_at,
      p.username,
      p.first_name,
      p.telegram_id
    FROM payments pay
    JOIN players p ON p.id = pay.player_id
    ORDER BY pay.created_at DESC
    LIMIT 30
  `);

  return result.rows as any[];
}

export default async function RevenuePage() {
  const [totalRevenue, revenueByDay, methodBreakdown, recentTx] =
    await Promise.all([
      getTotalRevenue(),
      getRevenueByDay(),
      getPaymentMethodBreakdown(),
      getRecentTransactions(),
    ]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Revenue</h1>

      {/* Top cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <div className="text-neutral-500 text-sm mb-2">Total Revenue</div>
          <div className="text-2xl font-bold text-white">
            ${totalRevenue.toFixed(2)}
          </div>
        </div>
        {methodBreakdown.map((m) => (
          <div
            key={m.type}
            className="bg-neutral-900 border border-neutral-800 rounded-xl p-5"
          >
            <div className="text-neutral-500 text-sm mb-2 capitalize">
              {m.type} Revenue
            </div>
            <div className="text-2xl font-bold text-white">
              ${m.total.toFixed(2)}
            </div>
            <div className="text-neutral-600 text-xs mt-1">
              {m.count} transactions
            </div>
          </div>
        ))}
      </div>

      {/* Revenue Chart */}
      <RevenueCharts revenueByDay={revenueByDay} />

      {/* Recent Transactions */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden mt-6">
        <div className="px-5 py-4 border-b border-neutral-800">
          <h2 className="text-sm font-medium text-neutral-400">
            Recent Transactions
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
                  Type
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Status
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Amount
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Stars
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {recentTx.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-neutral-600"
                  >
                    No transactions yet
                  </td>
                </tr>
              ) : (
                recentTx.map((tx: any) => (
                  <tr
                    key={tx.id}
                    className="border-b border-neutral-800/50 hover:bg-neutral-800/30"
                  >
                    <td className="px-4 py-3 text-white">
                      {tx.username || tx.first_name || tx.telegram_id}
                    </td>
                    <td className="px-4 py-3 text-neutral-400 capitalize">
                      {tx.payment_type}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          tx.status === "completed"
                            ? "bg-green-900/40 text-green-400"
                            : tx.status === "pending"
                              ? "bg-yellow-900/40 text-yellow-400"
                              : tx.status === "failed"
                                ? "bg-red-900/40 text-red-400"
                                : "bg-neutral-800 text-neutral-500"
                        }`}
                      >
                        {tx.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white font-mono">
                      {tx.amount} {tx.currency}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {tx.stars_amount || "-"}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs">
                      {new Date(tx.created_at).toLocaleString()}
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
