"use client"

import React from 'react'
import { cn } from '@/lib/utils'
import { ArrowUpRight, ArrowDownRight, Minus, AlertCircle, Zap } from 'lucide-react'
import { TradingSignal } from '@/types/market'

interface SignalIndicatorProps {
  signal: TradingSignal
  showDetails?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function SignalIndicator({
  signal,
  showDetails = true,
  size = 'md',
  className,
}: SignalIndicatorProps) {
  const direction = signal.probUp > 0.6 ? 'buy' : signal.probUp < 0.4 ? 'sell' : 'hold'
  
  const sizeClasses = {
    sm: 'p-2',
    md: 'p-3',
    lg: 'p-4',
  }
  
  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  }
  
  const getSignalColor = (confidence: number) => {
    if (confidence >= 0.8) return 'from-success to-emerald-600'
    if (confidence >= 0.6) return 'from-blue-500 to-indigo-600'
    if (confidence >= 0.4) return 'from-warning to-orange-600'
    return 'from-muted to-muted-foreground'
  }
  
  const getDirectionIcon = () => {
    switch (direction) {
      case 'buy':
        return <ArrowUpRight className={cn(iconSizes[size], 'text-success')} />
      case 'sell':
        return <ArrowDownRight className={cn(iconSizes[size], 'text-danger')} />
      default:
        return <Minus className={cn(iconSizes[size], 'text-warning')} />
    }
  }
  
  const confidenceLevel = Math.round(signal.conf * 100)
  const expectedReturnPercent = (signal.expectedReturn * 100).toFixed(2)
  
  return (
    <div
      className={cn(
        'relative rounded-lg border bg-card overflow-hidden transition-all duration-300 hover:shadow-md',
        sizeClasses[size],
        className
      )}
    >
      {/* Confidence gradient background */}
      <div
        className={cn(
          'absolute inset-0 bg-gradient-to-r opacity-5',
          getSignalColor(signal.conf)
        )}
      />
      
      <div className="relative">
        {/* Signal header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {getDirectionIcon()}
            <span
              className={cn(
                'font-semibold uppercase tracking-wide',
                direction === 'buy' && 'text-success',
                direction === 'sell' && 'text-danger',
                direction === 'hold' && 'text-warning',
                size === 'sm' && 'text-xs',
                size === 'md' && 'text-sm',
                size === 'lg' && 'text-base'
              )}
            >
              {direction}
            </span>
          </div>
          
          {/* Confidence badge */}
          <div className="flex items-center gap-1">
            <Zap
              className={cn(
                'text-primary',
                size === 'sm' && 'h-3 w-3',
                size === 'md' && 'h-4 w-4',
                size === 'lg' && 'h-5 w-5'
              )}
            />
            <span
              className={cn(
                'font-mono font-medium',
                confidenceLevel >= 80 && 'text-success',
                confidenceLevel >= 60 && confidenceLevel < 80 && 'text-primary',
                confidenceLevel < 60 && 'text-warning',
                size === 'sm' && 'text-xs',
                size === 'md' && 'text-sm',
                size === 'lg' && 'text-base'
              )}
            >
              {confidenceLevel}%
            </span>
          </div>
        </div>
        
        {showDetails && (
          <>
            {/* Probability bar */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Probability</span>
                <span>{Math.round(signal.probUp * 100)}%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full transition-all duration-500 rounded-full',
                    direction === 'buy' && 'bg-gradient-to-r from-success/50 to-success',
                    direction === 'sell' && 'bg-gradient-to-r from-danger/50 to-danger',
                    direction === 'hold' && 'bg-gradient-to-r from-warning/50 to-warning'
                  )}
                  style={{ width: `${signal.probUp * 100}%` }}
                />
              </div>
            </div>
            
            {/* Signal metrics */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="space-y-1">
                <div className="text-muted-foreground">Expected Return</div>
                <div
                  className={cn(
                    'font-mono font-medium',
                    parseFloat(expectedReturnPercent) > 0 ? 'text-success' : 'text-danger'
                  )}
                >
                  {parseFloat(expectedReturnPercent) > 0 ? '+' : ''}{expectedReturnPercent}%
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-muted-foreground">Risk Score</div>
                <div className="font-mono font-medium">
                  {(signal.risk.kellyFrac * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-muted-foreground">Target Vol</div>
                <div className="font-mono font-medium">
                  {(signal.risk.targetVol * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="text-muted-foreground">Position Size</div>
                <div className="font-mono font-medium">
                  {(signal.sizing.navFrac * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            
            {/* Model info */}
            <div className="mt-3 pt-3 border-t border-border/50">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1 text-muted-foreground">
                  <AlertCircle className="h-3 w-3" />
                  <span>{signal.model.ensemble}</span>
                </div>
                <div className="text-muted-foreground">
                  {signal.model.version}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}