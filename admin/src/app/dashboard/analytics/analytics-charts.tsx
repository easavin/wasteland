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

const LANG_COLORS = [
  "#f59e0b",
  "#6366f1",
  "#22c55e",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#14b8a6",
  "#f97316",
  "#64748b",
];

interface AnalyticsChartsProps {
  languages: { language: string; count: number }[];
  turnsDistribution: { bucket: string; count: number }[];
}

export function AnalyticsCharts({
  languages,
  turnsDistribution,
}: AnalyticsChartsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Language Distribution */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Language Distribution
        </h3>
        {languages.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={languages}
                cx="50%"
                cy="50%"
                outerRadius={100}
                paddingAngle={2}
                dataKey="count"
                nameKey="language"
                label={({ language, percent }) =>
                  `${language} ${(percent * 100).toFixed(0)}%`
                }
              >
                {languages.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={LANG_COLORS[index % LANG_COLORS.length]}
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
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Turns Distribution */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Game Length Distribution (turns)
        </h3>
        {turnsDistribution.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={turnsDistribution}>
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
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
