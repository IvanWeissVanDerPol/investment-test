"use client"

import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { PriceCard } from '@/components/trading/price-card'
import { SignalIndicator } from '@/components/trading/signal-indicator'
import { PriceChart } from '@/components/charts/price-chart'
import { PerformanceChart } from '@/components/charts/performance-chart'
import { DataTable } from '@/components/tables/data-table'
import { MotionDiv, StaggerContainer, AnimatedCounter } from '@/components/animations/motion-components'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useNotification } from '@/components/ui/notification'
import { useMarketWebSocket } from '@/hooks/use-websocket'
import { TrendingUp, TrendingDown, DollarSign, Activity, Users, Target } from 'lucide-react'

// Sample data for demonstration
const samplePriceData = Array.from({ length: 100 }, (_, i) => ({
  timestamp: new Date(Date.now() - (100 - i) * 24 * 60 * 60 * 1000).toISOString(),
  open: 100 + Math.random() * 20,
  high: 105 + Math.random() * 25,
  low: 95 + Math.random() * 15,
  close: 100 + Math.random() * 20,
  volume: Math.floor(Math.random() * 1000000),
  sma20: 100 + Math.random() * 15,
  sma50: 100 + Math.random() * 10,
}))

const sampleSignal = {
  symbol: 'AAPL',
  timestamp: new Date().toISOString(),
  signal: 'buy' as const,
  conf: 0.85,
  probUp: 0.73,
  expectedReturn: 0.05,
  risk: {
    kellyFrac: 0.15,
    targetVol: 0.20,
    maxDrawdown: 0.08,
  },
  sizing: {
    navFrac: 0.12,
    positionSize: 1000,
  },
  model: {
    ensemble: 'ML-Enhanced',
    version: 'v2.1.0',
  },
}

const performanceMetrics = [
  { metric: 'Returns', value: 85, benchmark: 60 },
  { metric: 'Volatility', value: 45, benchmark: 70 },
  { metric: 'Sharpe', value: 90, benchmark: 55 },
  { metric: 'Max DD', value: 30, benchmark: 40 },
  { metric: 'Win Rate', value: 75, benchmark: 50 },
]

const portfolioAllocation = [
  { asset: 'Equities', value: 150000, percentage: 60 },
  { asset: 'Bonds', value: 50000, percentage: 20 },
  { asset: 'Crypto', value: 25000, percentage: 10 },
  { asset: 'Commodities', value: 15000, percentage: 6 },
  { asset: 'Cash', value: 10000, percentage: 4 },
]

const tableData = [
  { symbol: 'AAPL', price: 185.23, change: 2.34, changePercent: 1.28, volume: '45.2M', signal: 'buy' },
  { symbol: 'GOOGL', price: 2842.19, change: -15.67, changePercent: -0.55, volume: '1.8M', signal: 'hold' },
  { symbol: 'MSFT', price: 378.91, change: 8.12, changePercent: 2.19, volume: '28.7M', signal: 'buy' },
  { symbol: 'TSLA', price: 248.56, change: -12.33, changePercent: -4.72, volume: '67.1M', signal: 'sell' },
  { symbol: 'NVDA', price: 498.34, change: 23.45, changePercent: 4.94, volume: '52.3M', signal: 'buy' },
]

const tableColumns = [
  { key: 'symbol', header: 'Symbol', accessor: (row: any) => row.symbol, sortable: true },
  { 
    key: 'price', 
    header: 'Price', 
    accessor: (row: any) => row.price, 
    sortable: true,
    render: (value: number) => `$${value.toFixed(2)}`
  },
  { 
    key: 'change', 
    header: 'Change', 
    accessor: (row: any) => row.change, 
    sortable: true,
    render: (value: number, row: any) => (
      <div className={`flex items-center gap-1 ${value >= 0 ? 'text-success' : 'text-danger'}`}>
        {value >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
        ${Math.abs(value).toFixed(2)} ({value >= 0 ? '+' : ''}{row.changePercent.toFixed(2)}%)
      </div>
    )
  },
  { key: 'volume', header: 'Volume', accessor: (row: any) => row.volume },
  { 
    key: 'signal', 
    header: 'Signal', 
    accessor: (row: any) => row.signal,
    render: (value: string) => (
      <span className={`px-2 py-1 rounded text-xs font-medium ${
        value === 'buy' ? 'bg-success/10 text-success' :
        value === 'sell' ? 'bg-danger/10 text-danger' :
        'bg-warning/10 text-warning'
      }`}>
        {value.toUpperCase()}
      </span>
    )
  },
]

export default function Dashboard() {
  const { addNotification } = useNotification()
  const { marketData, isConnected } = useMarketWebSocket(['AAPL', 'GOOGL', 'MSFT'])

  const handleTestNotification = () => {
    addNotification({
      type: 'success',
      title: 'Test Notification',
      message: 'This is a sample notification with smooth animations!',
    })
  }

  return (
    <DashboardLayout>
      <StaggerContainer className="space-y-6">
        {/* Header */}
        <MotionDiv variant="fadeInUp" delay={0.1}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold gradient-text">Dashboard</h1>
              <p className="text-muted-foreground mt-1">
                Welcome back! Here's your portfolio overview.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${
                isConnected ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
              }`}>
                <Activity className="h-4 w-4" />
                {isConnected ? 'Connected' : 'Disconnected'}
              </div>
              <Button onClick={handleTestNotification}>
                Test Notification
              </Button>
            </div>
          </div>
        </MotionDiv>

        {/* Stats Cards */}
        <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MotionDiv variant="fadeInUp">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Value</p>
                  <p className="text-2xl font-bold">
                    $<AnimatedCounter value={250000} />
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-primary" />
              </div>
            </Card>
          </MotionDiv>
          
          <MotionDiv variant="fadeInUp" delay={0.1}>
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Today's P&L</p>
                  <p className="text-2xl font-bold text-success">
                    +$<AnimatedCounter value={1250} />
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-success" />
              </div>
            </Card>
          </MotionDiv>
          
          <MotionDiv variant="fadeInUp" delay={0.2}>
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Active Positions</p>
                  <p className="text-2xl font-bold">
                    <AnimatedCounter value={12} />
                  </p>
                </div>
                <Target className="h-8 w-8 text-warning" />
              </div>
            </Card>
          </MotionDiv>
          
          <MotionDiv variant="fadeInUp" delay={0.3}>
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Win Rate</p>
                  <p className="text-2xl font-bold">
                    <AnimatedCounter value={73} />%
                  </p>
                </div>
                <Users className="h-8 w-8 text-blue-500" />
              </div>
            </Card>
          </MotionDiv>
        </StaggerContainer>

        {/* Price Cards */}
        <MotionDiv variant="fadeInUp" delay={0.4}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <PriceCard
              symbol="AAPL"
              name="Apple Inc."
              price={185.23}
              previousClose={182.89}
              volume={45234567}
              high={186.45}
              low={182.10}
              animate={true}
            />
            <PriceCard
              symbol="GOOGL"
              name="Alphabet Inc."
              price={2842.19}
              previousClose={2857.86}
              volume={1823456}
              high={2865.30}
              low={2835.22}
              animate={true}
            />
            <PriceCard
              symbol="MSFT"
              name="Microsoft Corp."
              price={378.91}
              previousClose={370.79}
              volume={28734567}
              high={380.15}
              low={375.33}
              animate={true}
            />
          </div>
        </MotionDiv>

        {/* Signal Indicator */}
        <MotionDiv variant="fadeInUp" delay={0.5}>
          <SignalIndicator signal={sampleSignal} />
        </MotionDiv>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MotionDiv variant="fadeInLeft" delay={0.6}>
            <PriceChart
              data={samplePriceData}
              symbol="AAPL"
              height={400}
              showVolume={true}
              showIndicators={true}
            />
          </MotionDiv>
          
          <div className="space-y-6">
            <MotionDiv variant="fadeInRight" delay={0.7}>
              <PerformanceChart
                metrics={performanceMetrics}
                type="radar"
                title="Performance Metrics"
              />
            </MotionDiv>
            
            <MotionDiv variant="fadeInRight" delay={0.8}>
              <PerformanceChart
                allocation={portfolioAllocation}
                type="pie"
                title="Portfolio Allocation"
              />
            </MotionDiv>
          </div>
        </div>

        {/* Data Table */}
        <MotionDiv variant="fadeInUp" delay={0.9}>
          <DataTable
            data={tableData}
            columns={tableColumns}
            searchable={true}
            filterable={true}
            exportable={true}
            virtualScroll={false}
          />
        </MotionDiv>
      </StaggerContainer>
    </DashboardLayout>
  )
}