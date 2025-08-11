export type Environment = 'development' | 'staging' | 'production'

interface BaseConfig {
  app: {
    name: string
    version: string
    environment: Environment
    debug: boolean
    url: string
  }
  api: {
    baseUrl: string
    timeout: number
    retries: number
    version: string
  }
  websocket: {
    url: string
    reconnectInterval: number
    maxReconnectAttempts: number
  }
  features: {
    analytics: boolean
    errorReporting: boolean
    realTimeData: boolean
    darkMode: boolean
    notifications: boolean
  }
  monitoring: {
    sentry?: {
      dsn?: string
      environment: string
      tracesSampleRate: number
    }
    vercel?: {
      analyticsId?: string
    }
  }
  performance: {
    enableSWR: boolean
    cacheTimeout: number
    maxCacheSize: number
    enableServiceWorker: boolean
  }
}

const baseConfig: Omit<BaseConfig, 'app'> = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 10000,
    retries: 3,
    version: 'v1',
  },
  websocket: {
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
  },
  features: {
    analytics: true,
    errorReporting: true,
    realTimeData: true,
    darkMode: true,
    notifications: true,
  },
  monitoring: {
    sentry: {
      dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
      environment: process.env.NEXT_PUBLIC_APP_ENV || 'development',
      tracesSampleRate: 0.1,
    },
    vercel: {
      analyticsId: process.env.NEXT_PUBLIC_VERCEL_ANALYTICS_ID,
    },
  },
  performance: {
    enableSWR: true,
    cacheTimeout: 300000, // 5 minutes
    maxCacheSize: 100,
    enableServiceWorker: true,
  },
}

const developmentConfig: BaseConfig = {
  ...baseConfig,
  app: {
    name: 'TradeSys (Development)',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0-dev',
    environment: 'development',
    debug: true,
    url: 'http://localhost:3000',
  },
  api: {
    ...baseConfig.api,
    timeout: 30000, // Longer timeout for development
  },
  features: {
    ...baseConfig.features,
    errorReporting: false, // Disable error reporting in dev
  },
  monitoring: {
    ...baseConfig.monitoring,
    sentry: {
      ...baseConfig.monitoring.sentry,
      tracesSampleRate: 1.0, // Full tracing in development
    },
  },
  performance: {
    ...baseConfig.performance,
    cacheTimeout: 60000, // Shorter cache in development
    enableServiceWorker: false, // Disable SW in development
  },
}

const stagingConfig: BaseConfig = {
  ...baseConfig,
  app: {
    name: 'TradeSys (Staging)',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0-staging',
    environment: 'staging',
    debug: false,
    url: process.env.NEXT_PUBLIC_APP_URL || 'https://staging.tradesys.com',
  },
  api: {
    ...baseConfig.api,
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://api-staging.tradesys.com',
  },
  websocket: {
    ...baseConfig.websocket,
    url: process.env.NEXT_PUBLIC_WS_URL || 'wss://api-staging.tradesys.com/ws',
  },
  monitoring: {
    ...baseConfig.monitoring,
    sentry: {
      ...baseConfig.monitoring.sentry,
      tracesSampleRate: 0.5,
    },
  },
}

const productionConfig: BaseConfig = {
  ...baseConfig,
  app: {
    name: 'TradeSys',
    version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
    environment: 'production',
    debug: false,
    url: process.env.NEXT_PUBLIC_APP_URL || 'https://tradesys.com',
  },
  api: {
    ...baseConfig.api,
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://api.tradesys.com',
    timeout: 5000, // Shorter timeout for production
  },
  websocket: {
    ...baseConfig.websocket,
    url: process.env.NEXT_PUBLIC_WS_URL || 'wss://api.tradesys.com/ws',
    reconnectInterval: 1000, // Faster reconnection in production
  },
  performance: {
    ...baseConfig.performance,
    cacheTimeout: 600000, // 10 minutes cache in production
    maxCacheSize: 200,
  },
}

function getEnvironment(): Environment {
  const env = process.env.NEXT_PUBLIC_APP_ENV as Environment
  return env || 'development'
}

function getConfig(): BaseConfig {
  const environment = getEnvironment()
  
  switch (environment) {
    case 'production':
      return productionConfig
    case 'staging':
      return stagingConfig
    case 'development':
    default:
      return developmentConfig
  }
}

export const config = getConfig()

// Environment utilities
export const isDevelopment = config.app.environment === 'development'
export const isStaging = config.app.environment === 'staging'
export const isProduction = config.app.environment === 'production'
export const isClient = typeof window !== 'undefined'
export const isServer = !isClient

// Feature flags
export const features = config.features

// API utilities
export const apiConfig = {
  baseURL: config.api.baseUrl,
  timeout: config.api.timeout,
  headers: {
    'Content-Type': 'application/json',
    'X-Client-Version': config.app.version,
    'X-Client-Environment': config.app.environment,
  },
}

// WebSocket configuration
export const wsConfig = {
  url: config.websocket.url,
  options: {
    reconnectInterval: config.websocket.reconnectInterval,
    maxReconnectAttempts: config.websocket.maxReconnectAttempts,
  },
}

// Monitoring configuration
export const monitoringConfig = config.monitoring

export default config