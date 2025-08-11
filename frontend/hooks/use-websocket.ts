import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

interface UseWebSocketOptions {
  url: string
  reconnect?: boolean
  reconnectInterval?: number
  reconnectAttempts?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onMessage?: (message: WebSocketMessage) => void
}

export enum WebSocketState {
  CONNECTING = 0,
  OPEN = 1,
  CLOSING = 2,
  CLOSED = 3,
}

export function useWebSocket({
  url,
  reconnect = true,
  reconnectInterval = 3000,
  reconnectAttempts = 5,
  onOpen,
  onClose,
  onError,
  onMessage,
}: UseWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null)
  const reconnectCount = useRef(0)
  const reconnectTimeout = useRef<NodeJS.Timeout>()
  const [readyState, setReadyState] = useState<WebSocketState>(WebSocketState.CONNECTING)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url)
      
      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setReadyState(WebSocketState.OPEN)
        reconnectCount.current = 0
        onOpen?.()
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setReadyState(WebSocketState.CLOSED)
        onClose?.()
        
        if (reconnect && reconnectCount.current < reconnectAttempts) {
          reconnectTimeout.current = setTimeout(() => {
            reconnectCount.current++
            console.log(`Reconnecting... Attempt ${reconnectCount.current}`)
            connect()
          }, reconnectInterval)
        }
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        onError?.(error)
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [url, reconnect, reconnectInterval, reconnectAttempts, onOpen, onClose, onError, onMessage])

  const sendMessage = useCallback((data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type: 'client_message',
        data,
        timestamp: new Date().toISOString(),
      }
      ws.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current)
    }
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    sendMessage,
    lastMessage,
    readyState,
    connect,
    disconnect,
  }
}

// Market data specific WebSocket hook
export function useMarketWebSocket(symbols: string[]) {
  const [marketData, setMarketData] = useState<Record<string, any>>({})
  
  const { sendMessage, readyState } = useWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
    onOpen: () => {
      // Subscribe to symbols when connected
      sendMessage({
        type: 'subscribe',
        symbols,
      })
    },
    onMessage: (message) => {
      if (message.type === 'market_update') {
        setMarketData((prev) => ({
          ...prev,
          [message.data.symbol]: message.data,
        }))
      }
    },
  })

  const subscribe = useCallback((newSymbols: string[]) => {
    sendMessage({
      type: 'subscribe',
      symbols: newSymbols,
    })
  }, [sendMessage])

  const unsubscribe = useCallback((symbolsToRemove: string[]) => {
    sendMessage({
      type: 'unsubscribe',
      symbols: symbolsToRemove,
    })
  }, [sendMessage])

  return {
    marketData,
    subscribe,
    unsubscribe,
    isConnected: readyState === WebSocketState.OPEN,
  }
}