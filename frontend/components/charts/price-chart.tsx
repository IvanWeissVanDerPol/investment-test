"use client"

import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
  Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn, formatCurrency, formatDate } from '@/lib/utils'
import { Maximize2, TrendingUp, TrendingDown, Activity } from 'lucide-react'

interface PriceDataPoint {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  sma20?: number
  sma50?: number
  ema12?: number
  ema26?: number
}

interface PriceChartProps {
  data: PriceDataPoint[]
  symbol: string
  interval?: '1m' | '5m' | '15m' | '30m' | '1h' | '1d'
  height?: number
  showVolume?: boolean
  showIndicators?: boolean
  className?: string
}

const timeRanges = [
  { label: '1D', value: 1 },
  { label: '1W', value: 7 },
  { label: '1M', value: 30 },
  { label: '3M', value: 90 },
  { label: '1Y', value: 365 },
  { label: 'ALL', value: -1 },
]

const chartTypes = ['line', 'area', 'candle'] as const
type ChartType = typeof chartTypes[number]

export function PriceChart({
  data,
  symbol,
  interval = '1d',
  height = 400,
  showVolume = true,
  showIndicators = true,
  className,
}: PriceChartProps) {
  const [chartType, setChartType] = useState<ChartType>('area')
  const [selectedRange, setSelectedRange] = useState(30)
  const [displayData, setDisplayData] = useState(data)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    if (selectedRange === -1) {
      setDisplayData(data)
    } else {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - selectedRange)
      setDisplayData(
        data.filter(d => new Date(d.timestamp) >= cutoffDate)
      )
    }
  }, [data, selectedRange])

  const latestPrice = displayData[displayData.length - 1]?.close || 0
  const firstPrice = displayData[0]?.close || latestPrice
  const priceChange = latestPrice - firstPrice
  const priceChangePercent = (priceChange / firstPrice) * 100
  const isPositive = priceChange >= 0

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null

    const data = payload[0].payload
    return (
      <div className="rounded-lg border bg-card p-3 shadow-lg">
        <p className="text-xs text-muted-foreground mb-1">
          {formatDate(label, 'short')}
        </p>
        <div className="space-y-1">
          <div className="flex justify-between gap-4 text-sm">
            <span className="text-muted-foreground">Close:</span>
            <span className="font-mono font-medium">{formatCurrency(data.close)}</span>
          </div>
          {chartType === 'candle' && (
            <>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Open:</span>
                <span className="font-mono">{formatCurrency(data.open)}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">High:</span>
                <span className="font-mono">{formatCurrency(data.high)}</span>
              </div>
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">Low:</span>
                <span className="font-mono">{formatCurrency(data.low)}</span>
              </div>
            </>
          )}
          {showVolume && (
            <div className="flex justify-between gap-4 text-sm">
              <span className="text-muted-foreground">Volume:</span>
              <span className="font-mono">{data.volume.toLocaleString()}</span>
            </div>
          )}
          {showIndicators && data.sma20 && (
            <div className="flex justify-between gap-4 text-sm">
              <span className="text-muted-foreground">SMA20:</span>
              <span className="font-mono">{formatCurrency(data.sma20)}</span>
            </div>
          )}
          {showIndicators && data.sma50 && (
            <div className="flex justify-between gap-4 text-sm">
              <span className="text-muted-foreground">SMA50:</span>
              <span className="font-mono">{formatCurrency(data.sma50)}</span>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderChart = () => {
    const chartHeight = showVolume ? height * 0.7 : height
    const volumeHeight = height * 0.25

    switch (chartType) {
      case 'line':
        return (
          <>
            <ResponsiveContainer width="100%" height={chartHeight}>
              <LineChart data={displayData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => formatDate(value, 'short')}
                  className="text-xs"
                />
                <YAxis
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(value) => formatCurrency(value, 'USD', true)}
                  className="text-xs"
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke={isPositive ? 'hsl(var(--success))' : 'hsl(var(--danger))'}
                  strokeWidth={2}
                  dot={false}
                  animationDuration={500}
                />
                {showIndicators && (
                  <>
                    <Line
                      type="monotone"
                      dataKey="sma20"
                      stroke="hsl(var(--primary))"
                      strokeWidth={1}
                      dot={false}
                      strokeDasharray="5 5"
                    />
                    <Line
                      type="monotone"
                      dataKey="sma50"
                      stroke="hsl(var(--warning))"
                      strokeWidth={1}
                      dot={false}
                      strokeDasharray="5 5"
                    />
                  </>
                )}
                <Brush
                  dataKey="timestamp"
                  height={30}
                  stroke="hsl(var(--primary))"
                  tickFormatter={(value) => formatDate(value, 'short')}
                />
              </LineChart>
            </ResponsiveContainer>
            {showVolume && (
              <ResponsiveContainer width="100%" height={volumeHeight}>
                <BarChart data={displayData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => formatDate(value, 'short')}
                    className="text-xs"
                  />
                  <YAxis
                    tickFormatter={(value) => (value / 1000000).toFixed(0) + 'M'}
                    className="text-xs"
                  />
                  <Bar
                    dataKey="volume"
                    fill="hsl(var(--muted-foreground))"
                    opacity={0.3}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </>
        )

      case 'area':
        return (
          <>
            <ResponsiveContainer width="100%" height={chartHeight}>
              <AreaChart data={displayData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorPositive" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--success))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--success))" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorNegative" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--danger))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--danger))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => formatDate(value, 'short')}
                  className="text-xs"
                />
                <YAxis
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(value) => formatCurrency(value, 'USD', true)}
                  className="text-xs"
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke={isPositive ? 'hsl(var(--success))' : 'hsl(var(--danger))'}
                  strokeWidth={2}
                  fill={isPositive ? 'url(#colorPositive)' : 'url(#colorNegative)'}
                  animationDuration={500}
                />
                {showIndicators && (
                  <>
                    <Line
                      type="monotone"
                      dataKey="sma20"
                      stroke="hsl(var(--primary))"
                      strokeWidth={1}
                      dot={false}
                      strokeDasharray="5 5"
                    />
                    <Line
                      type="monotone"
                      dataKey="sma50"
                      stroke="hsl(var(--warning))"
                      strokeWidth={1}
                      dot={false}
                      strokeDasharray="5 5"
                    />
                  </>
                )}
                <Brush
                  dataKey="timestamp"
                  height={30}
                  stroke="hsl(var(--primary))"
                  tickFormatter={(value) => formatDate(value, 'short')}
                />
              </AreaChart>
            </ResponsiveContainer>
            {showVolume && (
              <ResponsiveContainer width="100%" height={volumeHeight}>
                <BarChart data={displayData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => formatDate(value, 'short')}
                    className="text-xs"
                  />
                  <YAxis
                    tickFormatter={(value) => (value / 1000000).toFixed(0) + 'M'}
                    className="text-xs"
                  />
                  <Bar
                    dataKey="volume"
                    fill="hsl(var(--muted-foreground))"
                    opacity={0.3}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </>
        )

      default:
        return null
    }
  }

  return (
    <Card className={cn('relative', isFullscreen && 'fixed inset-4 z-50', className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <CardTitle className="text-xl font-bold">{symbol}</CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-mono font-bold">
                {formatCurrency(latestPrice)}
              </span>
              <div
                className={cn(
                  'flex items-center gap-1 px-2 py-1 rounded text-sm font-medium',
                  isPositive
                    ? 'bg-success/10 text-success'
                    : 'bg-danger/10 text-danger'
                )}
              >
                {isPositive ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )}
                <span>{formatCurrency(Math.abs(priceChange))}</span>
                <span>({priceChangePercent.toFixed(2)}%)</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Time range selector */}
            <div className="flex items-center rounded-lg border border-border p-1">
              {timeRanges.map((range) => (
                <Button
                  key={range.label}
                  variant={selectedRange === range.value ? 'default' : 'ghost'}
                  size="xs"
                  onClick={() => setSelectedRange(range.value)}
                  className="px-3"
                >
                  {range.label}
                </Button>
              ))}
            </div>

            {/* Chart type selector */}
            <div className="flex items-center rounded-lg border border-border p-1">
              {chartTypes.map((type) => (
                <Button
                  key={type}
                  variant={chartType === type ? 'default' : 'ghost'}
                  size="xs"
                  onClick={() => setChartType(type)}
                  className="px-3 capitalize"
                >
                  {type}
                </Button>
              ))}
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {renderChart()}
      </CardContent>
    </Card>
  )
}