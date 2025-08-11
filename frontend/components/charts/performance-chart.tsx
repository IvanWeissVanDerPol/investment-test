"use client"

import React from 'react'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface PerformanceMetric {
  metric: string
  value: number
  benchmark: number
}

interface PortfolioAllocation {
  asset: string
  value: number
  percentage: number
}

interface PerformanceChartProps {
  metrics?: PerformanceMetric[]
  allocation?: PortfolioAllocation[]
  type?: 'radar' | 'pie'
  title?: string
  className?: string
}

const COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--success))',
  'hsl(var(--warning))',
  'hsl(var(--danger))',
  '#8b5cf6',
  '#ec4899',
  '#f59e0b',
  '#10b981',
]

export function PerformanceChart({
  metrics,
  allocation,
  type = 'radar',
  title,
  className,
}: PerformanceChartProps) {
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null

    return (
      <div className="rounded-lg border bg-card p-3 shadow-lg">
        <p className="text-sm font-medium mb-2">{payload[0].name || payload[0].dataKey}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex justify-between gap-4 text-sm">
            <span className="text-muted-foreground">{entry.dataKey}:</span>
            <span className="font-mono font-medium">
              {typeof entry.value === 'number' 
                ? entry.value.toFixed(2) 
                : entry.value}
            </span>
          </div>
        ))}
      </div>
    )
  }

  const renderChart = () => {
    if (type === 'radar' && metrics) {
      return (
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={metrics}>
            <PolarGrid 
              gridType="polygon" 
              className="stroke-border/50"
              radialLines={false}
            />
            <PolarAngleAxis 
              dataKey="metric" 
              className="text-xs"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <PolarRadiusAxis
              domain={[0, 100]}
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
              className="text-xs"
            />
            <Tooltip content={<CustomTooltip />} />
            <Radar
              name="Current"
              dataKey="value"
              stroke="hsl(var(--primary))"
              fill="hsl(var(--primary))"
              fillOpacity={0.3}
              strokeWidth={2}
            />
            <Radar
              name="Benchmark"
              dataKey="benchmark"
              stroke="hsl(var(--muted-foreground))"
              fill="hsl(var(--muted-foreground))"
              fillOpacity={0.1}
              strokeWidth={1}
              strokeDasharray="5 5"
            />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      )
    }

    if (type === 'pie' && allocation) {
      const RADIAN = Math.PI / 180
      const renderCustomizedLabel = ({
        cx,
        cy,
        midAngle,
        innerRadius,
        outerRadius,
        percentage,
      }: any) => {
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5
        const x = cx + radius * Math.cos(-midAngle * RADIAN)
        const y = cy + radius * Math.sin(-midAngle * RADIAN)

        if (percentage < 5) return null

        return (
          <text
            x={x}
            y={y}
            fill="white"
            textAnchor={x > cx ? 'start' : 'end'}
            dominantBaseline="central"
            className="text-xs font-medium"
          >
            {`${percentage.toFixed(1)}%`}
          </text>
        )
      }

      return (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={allocation}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={100}
              fill="#8884d8"
              dataKey="percentage"
              animationBegin={0}
              animationDuration={500}
            >
              {allocation.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[index % COLORS.length]}
                  className="hover:opacity-80 transition-opacity cursor-pointer"
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              verticalAlign="bottom" 
              height={36}
              formatter={(value, entry: any) => (
                <span className="text-sm">
                  {entry.payload.asset}: ${entry.payload.value.toLocaleString()}
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      )
    }

    return null
  }

  return (
    <Card className={cn('', className)}>
      {title && (
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
      )}
      <CardContent>
        {renderChart()}
      </CardContent>
    </Card>
  )
}