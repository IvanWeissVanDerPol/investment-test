import { config, isProduction, isDevelopment } from './environment'

export interface PerformanceMetric {
  name: string
  value: number
  timestamp: number
  url: string
  environment: string
}

export interface ErrorReport {
  message: string
  stack?: string
  url: string
  userAgent: string
  timestamp: number
  userId?: string
  environment: string
}

class MonitoringService {
  private static instance: MonitoringService
  private performanceObserver?: PerformanceObserver
  private errorQueue: ErrorReport[] = []
  private metricsQueue: PerformanceMetric[] = []
  private isInitialized = false

  static getInstance(): MonitoringService {
    if (!MonitoringService.instance) {
      MonitoringService.instance = new MonitoringService()
    }
    return MonitoringService.instance
  }

  async init() {
    if (this.isInitialized || typeof window === 'undefined') return

    try {
      // Initialize error reporting
      this.initErrorReporting()
      
      // Initialize performance monitoring
      this.initPerformanceMonitoring()
      
      // Initialize user session tracking
      this.initSessionTracking()
      
      // Initialize Vercel Analytics (if available)
      await this.initVercelAnalytics()
      
      // Initialize Sentry (if configured)
      await this.initSentry()
      
      this.isInitialized = true
      console.log('🔍 Monitoring service initialized')
    } catch (error) {
      console.warn('⚠️ Failed to initialize monitoring:', error)
    }
  }

  private initErrorReporting() {
    window.addEventListener('error', (event) => {
      this.reportError({
        message: event.message,
        stack: event.error?.stack,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: Date.now(),
        environment: config.app.environment,
      })
    })

    window.addEventListener('unhandledrejection', (event) => {
      this.reportError({
        message: `Unhandled Promise Rejection: ${event.reason}`,
        stack: event.reason?.stack,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: Date.now(),
        environment: config.app.environment,
      })
    })
  }

  private initPerformanceMonitoring() {
    if (!('PerformanceObserver' in window)) return

    // Core Web Vitals
    this.observeWebVitals()
    
    // Navigation timing
    this.observeNavigation()
    
    // Resource timing
    this.observeResources()
  }

  private observeWebVitals() {
    try {
      // Largest Contentful Paint (LCP)
      new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1]
        this.reportMetric('LCP', lastEntry.startTime)
      }).observe({ type: 'largest-contentful-paint', buffered: true })

      // First Input Delay (FID)
      new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry: any) => {
          this.reportMetric('FID', entry.processingStart - entry.startTime)
        })
      }).observe({ type: 'first-input', buffered: true })

      // Cumulative Layout Shift (CLS)
      new PerformanceObserver((list) => {
        let clsValue = 0
        const entries = list.getEntries()
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value
          }
        })
        this.reportMetric('CLS', clsValue)
      }).observe({ type: 'layout-shift', buffered: true })
    } catch (error) {
      console.warn('Web Vitals monitoring failed:', error)
    }
  }

  private observeNavigation() {
    if (!('navigation' in performance.getEntriesByType('navigation')[0])) return

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    
    // Time to First Byte (TTFB)
    this.reportMetric('TTFB', navigation.responseStart - navigation.fetchStart)
    
    // DOM Content Loaded
    this.reportMetric('DCL', navigation.domContentLoadedEventEnd - navigation.fetchStart)
    
    // Load Event
    this.reportMetric('Load', navigation.loadEventEnd - navigation.fetchStart)
  }

  private observeResources() {
    new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach((entry) => {
        if (entry.name.includes('.js') || entry.name.includes('.css')) {
          this.reportMetric('Resource Load', entry.duration, entry.name)
        }
      })
    }).observe({ type: 'resource', buffered: true })
  }

  private initSessionTracking() {
    const sessionId = this.getOrCreateSessionId()
    const userId = this.getUserId()
    
    // Track page views
    this.trackPageView({
      url: window.location.href,
      title: document.title,
      sessionId,
      userId,
      timestamp: Date.now(),
    })
    
    // Track user engagement
    this.trackUserEngagement()
  }

  private async initVercelAnalytics() {
    if (!config.monitoring.vercel?.analyticsId) return

    try {
      const { inject } = await import('@vercel/analytics')
      inject({
        mode: isProduction ? 'production' : 'development',
      })
      console.log('📊 Vercel Analytics initialized')
    } catch (error) {
      console.warn('Failed to initialize Vercel Analytics:', error)
    }
  }

  private async initSentry() {
    if (!config.monitoring.sentry?.dsn || !config.features.errorReporting) return

    try {
      const Sentry = await import('@sentry/nextjs')
      
      Sentry.init({
        dsn: config.monitoring.sentry.dsn,
        environment: config.monitoring.sentry.environment,
        tracesSampleRate: config.monitoring.sentry.tracesSampleRate,
        debug: isDevelopment,
        beforeSend(event) {
          // Filter out known non-critical errors
          if (event.exception?.values?.[0]?.value?.includes('ResizeObserver')) {
            return null
          }
          return event
        },
      })
      
      console.log('🐛 Sentry initialized')
    } catch (error) {
      console.warn('Failed to initialize Sentry:', error)
    }
  }

  reportMetric(name: string, value: number, url?: string) {
    const metric: PerformanceMetric = {
      name,
      value: Math.round(value),
      timestamp: Date.now(),
      url: url || window.location.href,
      environment: config.app.environment,
    }

    this.metricsQueue.push(metric)
    
    // Send metrics in batches
    if (this.metricsQueue.length >= 10) {
      this.flushMetrics()
    }

    // Log important metrics in development
    if (isDevelopment && ['LCP', 'FID', 'CLS', 'TTFB'].includes(name)) {
      console.log(`📈 ${name}: ${value}${name === 'CLS' ? '' : 'ms'}`)
    }
  }

  reportError(error: ErrorReport) {
    this.errorQueue.push(error)
    
    // Send errors immediately
    this.flushErrors()
    
    if (isDevelopment) {
      console.error('🚨 Error reported:', error)
    }
  }

  trackPageView(data: any) {
    if (isDevelopment) {
      console.log('👁️ Page view:', data)
    }
    
    // Send to analytics service
    this.sendToAnalytics('page_view', data)
  }

  trackUserEngagement() {
    let startTime = Date.now()
    let isActive = true
    
    // Track time on page
    const trackEngagement = () => {
      if (isActive) {
        const timeOnPage = Date.now() - startTime
        this.sendToAnalytics('engagement', {
          timeOnPage,
          url: window.location.href,
          timestamp: Date.now(),
        })
      }
    }
    
    // Track when user becomes inactive
    window.addEventListener('blur', () => {
      isActive = false
      trackEngagement()
    })
    
    // Track when user becomes active
    window.addEventListener('focus', () => {
      isActive = true
      startTime = Date.now()
    })
    
    // Track before page unload
    window.addEventListener('beforeunload', trackEngagement)
  }

  private async flushMetrics() {
    if (this.metricsQueue.length === 0) return

    try {
      await this.sendToAnalytics('metrics', {
        metrics: [...this.metricsQueue],
        timestamp: Date.now(),
      })
      this.metricsQueue = []
    } catch (error) {
      console.warn('Failed to send metrics:', error)
    }
  }

  private async flushErrors() {
    if (this.errorQueue.length === 0) return

    try {
      await this.sendToAnalytics('errors', {
        errors: [...this.errorQueue],
        timestamp: Date.now(),
      })
      this.errorQueue = []
    } catch (error) {
      console.warn('Failed to send errors:', error)
    }
  }

  private async sendToAnalytics(type: string, data: any) {
    if (!config.features.analytics) return

    try {
      // Send to your analytics endpoint
      await fetch('/api/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type,
          data,
          timestamp: Date.now(),
          environment: config.app.environment,
        }),
      })
    } catch (error) {
      // Fail silently for analytics
      if (isDevelopment) {
        console.warn('Analytics request failed:', error)
      }
    }
  }

  private getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('session_id')
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('session_id', sessionId)
    }
    return sessionId
  }

  private getUserId(): string | undefined {
    return localStorage.getItem('user_id') || undefined
  }
}

export const monitoring = MonitoringService.getInstance()

// Export utilities for manual tracking
export const trackEvent = (eventName: string, properties?: Record<string, any>) => {
  monitoring.sendToAnalytics('event', {
    name: eventName,
    properties,
    timestamp: Date.now(),
  })
}

export const trackError = (error: Error | string, context?: Record<string, any>) => {
  const errorData: ErrorReport = {
    message: typeof error === 'string' ? error : error.message,
    stack: typeof error === 'object' ? error.stack : undefined,
    url: window.location.href,
    userAgent: navigator.userAgent,
    timestamp: Date.now(),
    environment: config.app.environment,
  }
  
  monitoring.reportError({ ...errorData, ...context })
}

export default monitoring