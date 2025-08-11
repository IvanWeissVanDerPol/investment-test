import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { ThemeProvider, ThemeGradientBackground } from '@/components/theme/theme-provider'
import { NotificationProvider } from '@/components/ui/notification'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'TradeSys - Investment Analytics Platform',
  description: 'Modern investment analytics and trading signals platform with real-time market data.',
  keywords: ['trading', 'investment', 'analytics', 'signals', 'market data'],
  authors: [{ name: 'TradeSys Team' }],
  creator: 'TradeSys',
  publisher: 'TradeSys',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://tradesys.com',
    siteName: 'TradeSys',
    title: 'TradeSys - Investment Analytics Platform',
    description: 'Modern investment analytics and trading signals platform with real-time market data.',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'TradeSys Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TradeSys - Investment Analytics Platform',
    description: 'Modern investment analytics and trading signals platform with real-time market data.',
    images: ['/og-image.jpg'],
    creator: '@tradesys',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)" />
        <meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)" />
      </head>
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        <ThemeProvider
          defaultTheme="system"
          enableSystem
          storageKey="tradesys-theme"
        >
          <NotificationProvider>
            <ThemeGradientBackground />
            {children}
          </NotificationProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}