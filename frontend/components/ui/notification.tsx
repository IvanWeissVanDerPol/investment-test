"use client"

import React, { createContext, useContext, useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message?: string
  duration?: number
  persistent?: boolean
}

interface NotificationContextType {
  notifications: Notification[]
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function useNotification() {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider')
  }
  return context
}

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([])

  const addNotification = useCallback((notification: Omit<Notification, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newNotification: Notification = {
      ...notification,
      id,
      duration: notification.duration ?? 5000,
    }

    setNotifications((prev) => [...prev, newNotification])

    if (!notification.persistent && newNotification.duration) {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.duration)
    }
  }, [])

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  return (
    <NotificationContext.Provider
      value={{ notifications, addNotification, removeNotification, clearNotifications }}
    >
      {children}
      <NotificationContainer />
    </NotificationContext.Provider>
  )
}

function NotificationContainer() {
  const { notifications, removeNotification } = useNotification()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  )
}

interface NotificationItemProps {
  notification: Notification
  onClose: () => void
}

function NotificationItem({ notification, onClose }: NotificationItemProps) {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const colors = {
    success: 'border-success/20 bg-success/10 text-success',
    error: 'border-danger/20 bg-danger/10 text-danger',
    warning: 'border-warning/20 bg-warning/10 text-warning',
    info: 'border-primary/20 bg-primary/10 text-primary',
  }

  const Icon = icons[notification.type]

  return (
    <div
      className={cn(
        'pointer-events-auto min-w-[320px] max-w-md rounded-lg border p-4 shadow-lg backdrop-blur-sm',
        'animate-fade-in transition-all duration-300',
        colors[notification.type]
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="font-medium text-sm">{notification.title}</p>
          {notification.message && (
            <p className="mt-1 text-sm opacity-90">{notification.message}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 rounded-md p-1 hover:bg-background/20 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

// Standalone notification functions for imperative usage
let notificationApi: NotificationContextType | null = null

export function setNotificationApi(api: NotificationContextType) {
  notificationApi = api
}

export const notify = {
  success: (title: string, message?: string, options?: Partial<Notification>) => {
    notificationApi?.addNotification({
      type: 'success',
      title,
      message,
      ...options,
    })
  },
  error: (title: string, message?: string, options?: Partial<Notification>) => {
    notificationApi?.addNotification({
      type: 'error',
      title,
      message,
      ...options,
    })
  },
  warning: (title: string, message?: string, options?: Partial<Notification>) => {
    notificationApi?.addNotification({
      type: 'warning',
      title,
      message,
      ...options,
    })
  },
  info: (title: string, message?: string, options?: Partial<Notification>) => {
    notificationApi?.addNotification({
      type: 'info',
      title,
      message,
      ...options,
    })
  },
}