"use client";

import {
  LineChart,
  Line,
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

const PIE_COLORS = ["#22c55e", "#ef4444", "#f59e0b", "#6b7280"];

interface OverviewChartsProps {
  dauData: { day: string; dau: number }[];
  turnsData: { day: string; turns: number }[];
  outcomes: { name: string; value: number }[];
}

export function OverviewCharts({
  dauData,
  turnsData,
  outcomes,
}: OverviewChartsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* DAU Line Chart */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Daily Active Users (30 days)
        </h3>
        {dauData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={dauData}>
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
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #333",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Line
                type="monotone"
                dataKey="dau"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: "#f59e0b" }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Turns per Day Bar Chart */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Turns Per Day (30 days)
        </h3>
        {turnsData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={turnsData}>
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
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #333",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Bar dataKey="turns" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Game Outcomes Pie Chart */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 lg:col-span-2">
        <h3 className="text-sm font-medium text-neutral-400 mb-4">
          Game Outcomes
        </h3>
        {outcomes.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-neutral-600">
            No completed games yet
          </div>
        ) : (
          <div className="flex items-center justify-center">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={outcomes}
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
                  {outcomes.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={PIE_COLORS[index % PIE_COLORS.length]}
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
                <Legend
                  wrapperStyle={{ color: "#999" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
