#!/usr/bin/env node

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const ENVIRONMENTS = {
  development: {
    branch: 'main',
    alias: ['dev.tradesys.com'],
    env: 'development'
  },
  staging: {
    branch: 'staging',
    alias: ['staging.tradesys.com'],
    env: 'staging'
  },
  production: {
    branch: 'main',
    alias: ['tradesys.com', 'www.tradesys.com'],
    env: 'production'
  }
}

class DeploymentManager {
  constructor() {
    this.environment = process.argv[2] || 'development'
    this.config = ENVIRONMENTS[this.environment]
    
    if (!this.config) {
      console.error(`❌ Invalid environment: ${this.environment}`)
      console.log(`Available environments: ${Object.keys(ENVIRONMENTS).join(', ')}`)
      process.exit(1)
    }
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString()
    const prefix = {
      info: '📋',
      success: '✅',
      warning: '⚠️',
      error: '❌',
      deploy: '🚀'
    }[type] || '📋'
    
    console.log(`${prefix} [${timestamp}] ${message}`)
  }

  exec(command, description) {
    this.log(description, 'info')
    try {
      const result = execSync(command, { 
        encoding: 'utf8', 
        stdio: ['inherit', 'pipe', 'inherit'] 
      })
      this.log(`✓ ${description} completed`, 'success')
      return result
    } catch (error) {
      this.log(`✗ ${description} failed: ${error.message}`, 'error')
      throw error
    }
  }

  validateEnvironment() {
    this.log('Validating environment...', 'info')
    
    // Check if Vercel CLI is installed
    try {
      execSync('vercel --version', { stdio: 'ignore' })
    } catch {
      this.log('Vercel CLI not found. Installing...', 'warning')
      this.exec('npm install -g vercel', 'Installing Vercel CLI')
    }

    // Check if required env vars exist for production
    if (this.environment === 'production') {
      const requiredEnvVars = [
        'NEXT_PUBLIC_API_URL',
        'NEXT_PUBLIC_WS_URL'
      ]
      
      const missing = requiredEnvVars.filter(varName => !process.env[varName])
      if (missing.length > 0) {
        this.log(`Missing required environment variables: ${missing.join(', ')}`, 'error')
        throw new Error('Environment validation failed')
      }
    }

    this.log('Environment validation passed', 'success')
  }

  runPreDeployChecks() {
    this.log('Running pre-deployment checks...', 'info')
    
    // Type checking
    this.exec('npm run type-check', 'Type checking')
    
    // Linting
    this.exec('npm run lint', 'Linting code')
    
    // Build test
    this.exec('npm run build', 'Testing build')
    
    // Security audit
    try {
      this.exec('npm audit --audit-level=high', 'Security audit')
    } catch (error) {
      this.log('Security vulnerabilities found. Review and fix before deploying.', 'warning')
      if (this.environment === 'production') {
        throw error
      }
    }

    this.log('Pre-deployment checks completed', 'success')
  }

  generateBuildInfo() {
    const buildInfo = {
      timestamp: new Date().toISOString(),
      environment: this.environment,
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      branch: this.getCurrentBranch(),
      commit: this.getCurrentCommit(),
      deployer: this.getDeployerInfo()
    }

    fs.writeFileSync(
      path.join(__dirname, '../public/build-info.json'),
      JSON.stringify(buildInfo, null, 2)
    )

    this.log(`Build info generated for ${buildInfo.version}`, 'success')
    return buildInfo
  }

  getCurrentBranch() {
    try {
      return execSync('git branch --show-current', { encoding: 'utf8' }).trim()
    } catch {
      return 'unknown'
    }
  }

  getCurrentCommit() {
    try {
      return execSync('git rev-parse --short HEAD', { encoding: 'utf8' }).trim()
    } catch {
      return 'unknown'
    }
  }

  getDeployerInfo() {
    try {
      const name = execSync('git config user.name', { encoding: 'utf8' }).trim()
      const email = execSync('git config user.email', { encoding: 'utf8' }).trim()
      return `${name} <${email}>`
    } catch {
      return 'unknown'
    }
  }

  deploy() {
    this.log(`Starting deployment to ${this.environment}...`, 'deploy')
    
    let deployCommand = 'vercel'
    
    if (this.environment === 'production') {
      deployCommand += ' --prod'
    }

    // Add environment variables
    deployCommand += ` --env NEXT_PUBLIC_APP_ENV=${this.config.env}`
    
    // Add aliases for staging/production
    if (this.config.alias && this.config.alias.length > 0) {
      this.config.alias.forEach(alias => {
        deployCommand += ` --alias ${alias}`
      })
    }

    const deployResult = this.exec(deployCommand, `Deploying to ${this.environment}`)
    
    // Extract deployment URL
    const urlMatch = deployResult.match(/https:\/\/[^\s]+/)
    const deploymentUrl = urlMatch ? urlMatch[0] : 'unknown'
    
    this.log(`Deployment completed: ${deploymentUrl}`, 'success')
    return deploymentUrl
  }

  runPostDeployChecks(deploymentUrl) {
    this.log('Running post-deployment checks...', 'info')
    
    // Health check
    try {
      const healthCheck = `curl -f -s ${deploymentUrl}/api/health || echo "Health check failed"`
      this.exec(healthCheck, 'Health check')
    } catch {
      this.log('Health check endpoint not available (this is expected if no API routes exist)', 'warning')
    }

    // Performance check
    if (this.environment === 'production') {
      this.log('Consider running Lighthouse audit for performance validation', 'info')
    }

    this.log('Post-deployment checks completed', 'success')
  }

  async run() {
    try {
      this.log(`🚀 Starting deployment pipeline for ${this.environment}`, 'deploy')
      
      this.validateEnvironment()
      this.runPreDeployChecks()
      
      const buildInfo = this.generateBuildInfo()
      const deploymentUrl = this.deploy()
      
      this.runPostDeployChecks(deploymentUrl)
      
      this.log(`🎉 Deployment successful!`, 'success')
      this.log(`Environment: ${this.environment}`, 'info')
      this.log(`URL: ${deploymentUrl}`, 'info')
      this.log(`Version: ${buildInfo.version}`, 'info')
      this.log(`Commit: ${buildInfo.commit}`, 'info')
      
    } catch (error) {
      this.log(`Deployment failed: ${error.message}`, 'error')
      process.exit(1)
    }
  }
}

// Add package.json scripts validation
function validatePackageScripts() {
  const packagePath = path.join(__dirname, '../package.json')
  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
  
  const requiredScripts = ['build', 'lint', 'type-check']
  const missingScripts = requiredScripts.filter(script => !packageJson.scripts[script])
  
  if (missingScripts.length > 0) {
    console.error(`❌ Missing required scripts in package.json: ${missingScripts.join(', ')}`)
    process.exit(1)
  }
}

// Run the deployment
if (require.main === module) {
  validatePackageScripts()
  const deployment = new DeploymentManager()
  deployment.run()
}

module.exports = DeploymentManager