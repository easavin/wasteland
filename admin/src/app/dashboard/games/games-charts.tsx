"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface GamesChartsProps {
  actions: { action: string; count: number }[];
}

export function GamesCharts({ actions }: GamesChartsProps) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
      <h3 className="text-sm font-medium text-neutral-400 mb-4">
        Most Popular Actions
      </h3>
      {actions.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-neutral-600">
          No action data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={actions} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#333" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: "#999", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="action"
              tick={{ fill: "#999", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={120}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1a1a1a",
                border: "1px solid #333",
                borderRadius: "8px",
                color: "#fff",
              }}
            />
            <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
