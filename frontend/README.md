# TradeSys Frontend

Modern, high-performance trading platform frontend built with Next.js 14, TypeScript, and TailwindCSS.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 📦 Deployment

### Vercel (Recommended)

#### Prerequisites
1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Link project: `vercel link`

#### Deploy Commands
```bash
# Development
npm run deploy:dev

# Staging
npm run deploy:staging

# Production
npm run deploy:prod
```

#### Environment Variables
Set these in your Vercel project dashboard:

**Required:**
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_WS_URL` - WebSocket URL

**Optional:**
- `NEXT_PUBLIC_SENTRY_DSN` - Error reporting
- `NEXT_PUBLIC_VERCEL_ANALYTICS_ID` - Analytics
- `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` - Google Analytics

### Manual Vercel Setup

1. **Connect Repository**
   ```bash
   vercel --prod
   ```

2. **Configure Environment**
   ```bash
   # Set production variables
   vercel env add NEXT_PUBLIC_API_URL production
   vercel env add NEXT_PUBLIC_WS_URL production
   
   # Set staging variables
   vercel env add NEXT_PUBLIC_API_URL preview
   vercel env add NEXT_PUBLIC_WS_URL preview
   ```

3. **Deploy**
   ```bash
   # Production deployment
   vercel --prod
   
   # Preview deployment
   vercel
   ```

## 🏗️ Architecture

### Project Structure
```
frontend/
├── app/                    # Next.js 14 app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── animations/        # Framer Motion components
│   ├── charts/           # Chart components
│   ├── layout/           # Layout components
│   ├── tables/           # Data table components
│   ├── theme/            # Theme provider
│   ├── trading/          # Trading-specific components
│   └── ui/               # Base UI components
├── config/               # Configuration files
│   ├── environment.ts    # Environment config
│   └── monitoring.ts     # Analytics & monitoring
├── hooks/                # Custom React hooks
├── lib/                  # Utility functions
├── public/               # Static assets
├── scripts/              # Deployment scripts
└── types/                # TypeScript definitions
```

### Key Technologies
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Animations**: Framer Motion
- **Charts**: Recharts
- **State Management**: Zustand + React Query
- **Real-time**: WebSocket hooks

## 🛠️ Development

### Commands
```bash
npm run dev            # Development server
npm run build          # Production build
npm run start          # Production server
npm run lint           # ESLint
npm run lint:fix       # Fix ESLint issues
npm run type-check     # TypeScript check
npm run analyze        # Bundle analysis
npm run clean          # Clean build files
```

### Code Quality
- **TypeScript**: Strict mode enabled
- **ESLint**: Next.js + TypeScript rules
- **Prettier**: Code formatting
- **Pre-commit**: Quality checks on commit

## 🚀 Performance Features

### Optimization
- **Bundle Splitting**: Automatic code splitting
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Automatic font optimization
- **Compression**: Gzip/Brotli compression
- **Caching**: Aggressive caching strategies

### Monitoring
- **Core Web Vitals**: LCP, FID, CLS tracking
- **Error Reporting**: Sentry integration
- **Analytics**: Vercel Analytics
- **Performance**: Real User Monitoring

### Accessibility
- **WCAG 2.1**: AA compliance
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Semantic HTML
- **Color Contrast**: High contrast ratios

## 🔧 Configuration

### Environment Variables
```bash
# Copy example environment file
cp .env.example .env.local

# Edit with your values
nano .env.local
```

### Build Configuration
The project uses a sophisticated build configuration in `next.config.js`:

- **Security Headers**: CSP, HSTS, etc.
- **Image Optimization**: WebP/AVIF support
- **Bundle Analysis**: Size optimization
- **Performance**: Compression & caching

## 🌍 Multi-Environment Setup

### Environment Configurations
- **Development**: Full debugging, hot reload
- **Staging**: Production-like with debugging
- **Production**: Optimized, monitoring enabled

### Deployment Pipeline
1. **Quality Checks**: Linting, type checking, tests
2. **Build Test**: Ensure build succeeds
3. **Security Audit**: Check for vulnerabilities
4. **Deploy**: Environment-specific deployment
5. **Health Check**: Verify deployment success

## 📊 Monitoring & Analytics

### Error Tracking
- **Sentry**: Runtime error reporting
- **Custom**: Performance metrics
- **Console**: Development debugging

### Performance Monitoring
- **Web Vitals**: Core performance metrics
- **Resource Timing**: Asset load performance
- **User Analytics**: Engagement tracking

## 🔒 Security

### Security Headers
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

### Best Practices
- Environment variable validation
- Secure cookie settings
- CSRF protection ready
- Input sanitization

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Make changes following code standards
3. Run quality checks: `npm run lint && npm run type-check`
4. Create pull request
5. Automated CI/CD runs quality checks
6. Merge after approval

### Commit Convention
```bash
feat: add new trading signal component
fix: resolve price chart animation issue
docs: update deployment instructions
style: format code with prettier
refactor: simplify theme provider logic
test: add price card component tests
```

## 📞 Support

### Troubleshooting
1. **Build Failures**: Check `npm run type-check` and `npm run lint`
2. **Deployment Issues**: Verify environment variables
3. **Performance**: Use `npm run analyze` to check bundle size
4. **Errors**: Check browser console and Sentry dashboard

### Common Issues
- **Hydration Mismatch**: Theme provider SSR issue
- **Bundle Size**: Use dynamic imports for large components  
- **WebSocket**: Check CORS settings for production

---

Built with ❤️ by the TradeSys team