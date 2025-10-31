# Alignment Attempt Tracking and Azure Logging

This document describes the new features added to track alignment attempts and integrate Azure Application Insights logging.

## Features Added

### 1. Alignment Attempt Tracking

The system now tracks all alignment verification attempts and provides detailed information about the verification process:

- **Real-time Progress Display**: Shows the current attempt number during certificate generation
- **Attempt Count Reporting**: Displays how many attempts were made (e.g., "Attempts: 3/150")
- **Best Certificate Selection**: When max attempts is reached without perfect alignment, the system automatically selects and provides the certificate with the closest/best alignment instead of failing completely

#### How It Works

1. During certificate generation, the alignment verifier attempts to match field positions with the reference certificate
2. Each attempt is tracked with its alignment metrics
3. If perfect alignment is achieved, the certificate is provided immediately
4. If max attempts is reached without perfect alignment:
   - The system compares all attempts
   - Selects the certificate with the smallest alignment difference
   - Provides that certificate to the user with a warning message
   - Logs indicate "Used Best Available" status

#### UI Display

The GOONJ certificate generation page now shows:
- Progress bar during alignment verification
- Current attempt number (e.g., "Verifying alignment... (attempt 25/150)")
- Final result showing total attempts made
- Special notification when best available certificate is used

Example output:
```
🎯 Alignment Verification
Status: ⚠️ Used Best Available
Message: MAX ATTEMPTS REACHED: Using best alignment from 3 attempts. Max difference: 0.0015 px (tolerance: 0.01 px)
Attempts: 150/150
Note: Maximum attempts reached. Using certificate with best alignment (closest match to reference).
Best Attempt: #3 with 0.0015 px difference
```

### 2. Azure Application Insights Integration

Azure Application Insights logging has been integrated for cloud-based monitoring and diagnostics.

#### Configuration

Add to your `.env` file:

```bash
# Azure Application Insights - for logging and monitoring
# Get these values from Azure Portal > Application Insights > Overview
# You need either APPINSIGHTS_INSTRUMENTATION_KEY or APPINSIGHTS_CONNECTION_STRING

APPINSIGHTS_INSTRUMENTATION_KEY=your-instrumentation-key-here
# OR
APPINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key;IngestionEndpoint=https://...
```

#### Features

1. **Automatic Log Collection**: All application logs are automatically sent to Azure Application Insights when configured
2. **Request Tracking**: HTTP requests and responses are tracked with timing information
3. **Exception Tracking**: Unhandled exceptions are automatically logged with stack traces
4. **Custom Event Tracking**: Alignment verification events and certificate generation metrics are logged

#### Developer Dashboard

A new Azure logs status panel has been added to the Developer Logs page (`/developer/logs`):

- **Status Display**: Shows whether Azure Application Insights is configured and active
- **Configuration Details**: Displays instrumentation key (masked) and handler status
- **Quick Access**: Button to check Azure logs status at any time

To view detailed logs:
1. Configure Azure Application Insights (see above)
2. Navigate to `/developer/logs`
3. Click "Azure Logs Status" button
4. Access full logs and analytics in the Azure Portal under Application Insights

#### Viewing Logs in Azure Portal

1. Go to Azure Portal (portal.azure.com)
2. Navigate to your Application Insights resource
3. Click on "Logs" in the left sidebar
4. Query logs using Kusto Query Language (KQL)

Example queries:

```kql
// View all logs from the last hour
traces
| where timestamp > ago(1h)
| order by timestamp desc

// View alignment verification events
traces
| where message contains "Alignment verification"
| order by timestamp desc

// View failed alignment attempts
traces
| where message contains "failed" and message contains "alignment"
| order by timestamp desc

// View certificate generation success rate
requests
| where name contains "generate_certificate"
| summarize SuccessRate = 100.0 * countif(success == true) / count() by bin(timestamp, 1h)
```

## Dependencies Added

The following dependencies have been added to `requirements.txt`:

```
opencensus-ext-azure        # Azure Application Insights integration
opencensus-ext-flask        # Flask middleware for Azure tracking
```

## Code Changes

### Modified Files

1. **`app/utils/iterative_alignment_verifier.py`**
   - Added tracking of all attempts in `all_attempts` list
   - Added `best_attempt` selection when max attempts reached
   - Added `used_best_available` flag in return value
   - Modified to return best certificate instead of failing completely

2. **`app/routes/goonj.py`**
   - Modified to accept "best available" certificates when max attempts reached
   - Added `used_best_available` and `best_attempt` to alignment status
   - Changed behavior to provide certificate with warning instead of failing

3. **`app/templates/goonj.html`**
   - Added real-time progress display with attempt counter
   - Added progress bar during alignment verification
   - Enhanced success handler to show "Used Best Available" status
   - Added display of best attempt information

4. **`app/templates/developer/logs.html`**
   - Added Azure logs status panel
   - Added "Azure Logs Status" button
   - Added `checkAzureLogs()` JavaScript function

5. **`app/routes/developer.py`**
   - Added `/api/azure-logs` endpoint
   - Returns Azure configuration status and handler information

6. **`app/__init__.py`**
   - Added Azure Application Insights initialization
   - Added Azure log handler to root logger
   - Added Flask middleware for request tracking

7. **`config.py`**
   - Added `APPINSIGHTS_INSTRUMENTATION_KEY` config
   - Added `APPINSIGHTS_CONNECTION_STRING` config

8. **`.env.example`**
   - Added Azure Application Insights configuration section
   - Added documentation for connection string and instrumentation key

## Testing

A comprehensive test suite has been added in `test_alignment_tracking.py`:

```bash
python test_alignment_tracking.py
```

Tests verify:
- ✅ Perfect alignment match (single attempt)
- ✅ Best certificate selection when max attempts reached
- ✅ Tracking of all attempts with metrics
- ✅ Field position extraction and comparison

## Usage Examples

### Example 1: Successful Alignment (First Attempt)

```
Status: ✅ Passed
Attempts: 1/150
Max Difference: 0.0000 px (tolerance: 0.01 px)
```

### Example 2: Successful Alignment (Multiple Attempts)

```
Status: ✅ Passed
Attempts: 47/150
Max Difference: 0.0089 px (tolerance: 0.01 px)
```

### Example 3: Max Attempts Reached - Using Best Available

```
Status: ⚠️ Used Best Available
Attempts: 150/150
Max Difference: 0.0156 px (tolerance: 0.01 px)
Note: Maximum attempts reached. Using certificate with best alignment.
Best Attempt: #89 with 0.0156 px difference
```

## Benefits

1. **Improved User Experience**: Users receive a certificate even when perfect alignment isn't achieved within max attempts
2. **Better Transparency**: Users can see how many attempts were made and understand the alignment quality
3. **Cloud Monitoring**: Azure integration enables professional monitoring and diagnostics
4. **Better Debugging**: Developers can track alignment issues and performance in real-time
5. **Production Ready**: Azure Application Insights provides enterprise-grade observability

## Configuration Tips

### For Development
- Azure logging is optional - the app works fine without it
- Set `ALIGNMENT_MAX_ATTEMPTS=10` for faster testing
- Use local logs in `/developer/logs` for quick debugging

### For Production
- Enable Azure Application Insights for comprehensive monitoring
- Set `ALIGNMENT_MAX_ATTEMPTS=150` for best quality
- Monitor alignment metrics in Azure Portal
- Set up alerts for repeated alignment failures

## Security Notes

- Instrumentation keys are masked in the developer dashboard
- Connection strings are not exposed in API responses
- Logs are sanitized before sending to Azure
- No sensitive user data is logged

## Troubleshooting

### Azure Logs Not Appearing

1. Verify `APPINSIGHTS_INSTRUMENTATION_KEY` or `APPINSIGHTS_CONNECTION_STRING` is set in `.env`
2. Check `/developer/api/azure-logs` endpoint shows `configured: true`
3. Wait a few minutes - logs may have ingestion delay
4. Check Azure Portal for ingestion errors

### Best Available Certificate Quality

If you're frequently getting "best available" instead of perfect alignment:
1. Increase `ALIGNMENT_MAX_ATTEMPTS` in `.env` (default: 150)
2. Relax `ALIGNMENT_TOLERANCE_PX` if needed (default: 0.01)
3. Check the template and font rendering consistency
4. Review Azure logs for patterns in alignment failures
