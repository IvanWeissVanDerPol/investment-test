# Portfolio Maintenance Guide

## 📅 Regular Tasks

### Weekly (Mondays)
- [ ] Check portfolio performance in `tracking/portfolio-tracker-2025-Q3.md`
- [ ] Review any alerts or notifications from brokers
- [ ] Update transaction log if any trades were made

### Monthly (1st of each month)
- [ ] Review asset allocation vs. targets
- [ ] Document any significant market events
- [ ] Update performance metrics
- [ ] Run backup of all portfolio files

### Quarterly (Jan 1, Apr 1, Jul 1, Oct 1)
- [ ] Rebalance portfolio to target allocations
- [ ] Archive old tracker: `tools\archive_old_trackers.ps1`
- [ ] Create new quarterly tracker in `tracking/`
- [ ] Review and update investment strategy if needed

## 🔄 Rebalancing Process

1. **Review Current Allocation**
   - Check current vs. target allocations
   - Identify any significant deviations (>5% from target)

2. **Calculate Trades**
   - Sell over-weighted assets
   - Buy under-weighted assets
   - Consider tax implications

3. **Execute Trades**
   - Place orders during market hours
   - Use limit orders for better price control
   - Document all trades in the tracker

4. **Update Documentation**
   - Update portfolio tracker with new allocations
   - Document reasons for any strategic changes
   - Save trade confirmations

## 💾 Backup Procedure

1. **Local Backup**
   ```powershell
   # Run this from project root
   $backupDir = "$env:USERPROFILE\Documents\ivan_backup_$(Get-Date -Format 'yyyyMMdd')"
   New-Item -ItemType Directory -Path $backupDir -Force
   Copy-Item -Path .\* -Destination $backupDir -Recurse -Force
   ```

2. **Cloud Backup**
   - Sync project folder with your preferred cloud storage
   - Ensure sensitive data is encrypted

## 🛠️ Troubleshooting

### Common Issues
- **Missing Files**: Check `archive/` directory
- **Tracking Errors**: Verify calculations in the tracker
- **Access Issues**: Refer to `quick-reference.md` for credentials

### Getting Help
- For technical issues: [Your IT Support Contact]
- For investment advice: [Your Financial Advisor]
- For broker-specific questions: [Broker Support Contacts]

## 📈 Performance Review

### Key Metrics to Track
- Total portfolio value
- Year-to-date return
- Risk-adjusted returns (Sharpe ratio)
- Sector allocation
- Geographic exposure

### Review Questions
- Are we meeting our investment objectives?
- Has our risk tolerance changed?
- Are there new investment opportunities to consider?
- Do we need to adjust our strategy?
