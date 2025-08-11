"use client"

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card } from '@/components/ui/card'
import { cn, formatCurrency, formatPercentage, getPriceChangeColor } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react'

interface PriceCardProps {
  symbol: string
  name?: string
  price: number
  previousClose: number
  volume?: number
  high?: number
  low?: number
  className?: string
  size?: 'sm' | 'md' | 'lg'
  animate?: boolean
}

export function PriceCard({
  symbol,
  name,
  price,
  previousClose,
  volume,
  high,
  low,
  className,
  size = 'md',
  animate = true,
}: PriceCardProps) {
  const [displayPrice, setDisplayPrice] = useState(price)
  const [isUpdating, setIsUpdating] = useState(false)
  
  const change = price - previousClose
  const changePercent = (change / previousClose) * 100
  const isPositive = change > 0
  const isNeutral = change === 0
  
  useEffect(() => {
    if (displayPrice !== price && animate) {
      setIsUpdating(true)
      const timer = setTimeout(() => {
        setDisplayPrice(price)
        setIsUpdating(false)
      }, 100)
      return () => clearTimeout(timer)
    } else {
      setDisplayPrice(price)
    }
  }, [price, displayPrice, animate])
  
  const sizeClasses = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  }
  
  const textSizes = {
    sm: {
      symbol: 'text-sm font-medium',
      name: 'text-xs',
      price: 'text-xl font-semibold',
      change: 'text-xs',
      meta: 'text-xs',
    },
    md: {
      symbol: 'text-base font-semibold',
      name: 'text-sm',
      price: 'text-2xl font-bold',
      change: 'text-sm',
      meta: 'text-sm',
    },
    lg: {
      symbol: 'text-lg font-bold',
      name: 'text-base',
      price: 'text-3xl font-bold',
      change: 'text-base',
      meta: 'text-base',
    },
  }
  
  const sizes = textSizes[size]
  
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={cn(
          'relative overflow-hidden transition-all duration-300',
          sizeClasses[size],
          isUpdating && 'ring-2 ring-primary/50',
          className
        )}
        hover
      >
        {/* Background gradient effect */}
        <motion.div
          className={cn(
            'absolute inset-0 opacity-5 transition-opacity duration-500',
            isPositive && 'bg-gradient-to-br from-success to-transparent opacity-10',
            !isPositive && !isNeutral && 'bg-gradient-to-br from-danger to-transparent opacity-10'
          )}
          animate={isUpdating ? { scale: [1, 1.02, 1] } : {}}
          transition={{ duration: 0.5 }}
        />
        
        <div className="relative">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className={cn('text-foreground', sizes.symbol)}>{symbol}</div>
            {name && (
              <div className={cn('text-muted-foreground mt-0.5', sizes.name)}>
                {name}
              </div>
            )}
          </div>
          
          <motion.div 
            className="flex items-center"
            animate={{ rotate: isPositive ? 45 : isNeutral ? 0 : -45 }}
            transition={{ duration: 0.3 }}
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={isPositive ? 'up' : isNeutral ? 'neutral' : 'down'}
                initial={{ scale: 0, rotate: 90 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0, rotate: -90 }}
                transition={{ duration: 0.2 }}
              >
                {isPositive ? (
                  <TrendingUp className="h-4 w-4 text-success" />
                ) : isNeutral ? (
                  <Minus className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-danger" />
                )}
              </motion.div>
            </AnimatePresence>
          </motion.div>
        </div>
        
        {/* Price */}
        <div className="mb-3">
          <motion.div
            className={cn(
              'font-mono tabular-nums',
              sizes.price
            )}
            animate={isUpdating ? { scale: [1, 1.05, 1] } : {}}
            transition={{ duration: 0.3 }}
          >
            <AnimatePresence mode="wait">
              <motion.span
                key={displayPrice}
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -20, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {formatCurrency(displayPrice)}
              </motion.span>
            </AnimatePresence>
          </motion.div>
          
          <div className={cn('flex items-center gap-2 mt-1', sizes.change)}>
            <span className={cn('font-medium', getPriceChangeColor(change))}>
              {formatCurrency(Math.abs(change))}
            </span>
            <span
              className={cn(
                'px-1.5 py-0.5 rounded font-medium',
                isPositive && 'bg-success/10 text-success',
                !isPositive && !isNeutral && 'bg-danger/10 text-danger',
                isNeutral && 'bg-muted text-muted-foreground'
              )}
            >
              {formatPercentage(changePercent)}
            </span>
          </div>
        </div>
        
        {/* Meta information */}
        {(high || low || volume) && (
          <div className={cn('grid grid-cols-3 gap-2 pt-3 border-t border-border/50', sizes.meta)}>
            {high && (
              <div>
                <div className="text-muted-foreground text-xs">High</div>
                <div className="font-medium">{formatCurrency(high)}</div>
              </div>
            )}
            {low && (
              <div>
                <div className="text-muted-foreground text-xs">Low</div>
                <div className="font-medium">{formatCurrency(low)}</div>
              </div>
            )}
            {volume && (
              <div>
                <div className="text-muted-foreground text-xs">Vol</div>
                <div className="font-medium">{formatNumber(volume, 0, true)}</div>
              </div>
            )}
          </div>
        )}
        
        {/* Live indicator */}
        <AnimatePresence>
          {animate && (
            <motion.div 
              className="absolute top-3 right-3 flex items-center gap-1"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0 }}
              transition={{ duration: 0.2 }}
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Activity className="h-2 w-2 text-success" />
              </motion.div>
              <span className="text-xs text-muted-foreground">Live</span>
            </motion.div>
          )}
        </AnimatePresence>
        </div>
      </Card>
    </motion.div>
  )
}

function formatNumber(value: number, decimals: number = 0, compact: boolean = false): string {
  if (compact && Math.abs(value) >= 1000) {
    const formatter = new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: decimals,
    })
    return formatter.format(value)
  }
  
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value)
}