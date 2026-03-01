"use client";

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const CLASS_COLORS = ["#f59e0b", "#6366f1", "#22c55e", "#ec4899", "#06b6d4"];
const LEVEL_COLOR = "#8b5cf6";

interface GamesChartsProps {
  actions: { action: string; count: number }[];
  classDistribution: { name: string; value: number }[];
  levelDistribution: { bucket: string; count: number }[];
}

export function GamesCharts({
  actions,
  classDistribution,
  levelDistribution,
}: GamesChartsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Class Distribution Pie */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Class Distribution (active games)
        </h3>
        {classDistribution.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No active games
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={classDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={3}
                dataKey="value"
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
              >
                {classDistribution.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={CLASS_COLORS[index % CLASS_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #333",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Legend wrapperStyle={{ color: "#999" }} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Level Distribution Bar */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Level Distribution (active games)
        </h3>
        {levelDistribution.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No active games
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={levelDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="bucket"
                tick={{ fill: "#999", fontSize: 12 }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#999", fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #333",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Bar dataKey="count" fill={LEVEL_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Action Distribution Bar */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 lg:col-span-2">
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
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#333"
                horizontal={false}
              />
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
    </div>
  );
}
