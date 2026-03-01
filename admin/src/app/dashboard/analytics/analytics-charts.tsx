"use client";

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
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

const tooltipStyle = {
  backgroundColor: "#1a1a1a",
  border: "1px solid #333",
  borderRadius: "8px",
  color: "#fff",
};

interface AnalyticsChartsProps {
  languages: { language: string; count: number }[];
  turnsDistribution: { bucket: string; count: number }[];
  skillPopularity: { skill: string; ranks: number }[];
  goldEconomy: { day: string; earned: number; spent: number }[];
}

export function AnalyticsCharts({
  languages,
  turnsDistribution,
  skillPopularity,
  goldEconomy,
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
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Turns Distribution */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Game Length Distribution (weeks)
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
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Skill Popularity */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Most Popular Skills (total ranks invested)
        </h3>
        {skillPopularity.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No skills data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={skillPopularity} layout="vertical">
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
                dataKey="skill"
                tick={{ fill: "#999", fontSize: 10 }}
                tickLine={false}
                axisLine={false}
                width={140}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="ranks" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Gold Economy */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Gold Economy (30 days)
        </h3>
        {goldEconomy.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No gold data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={goldEconomy}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="day"
                tick={{ fill: "#999", fontSize: 11 }}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: "#999", fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ color: "#999" }} />
              <Line
                type="monotone"
                dataKey="earned"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="Gold Earned"
              />
              <Line
                type="monotone"
                dataKey="spent"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                name="Gold Spent"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
