/**
 * System Status Floating Widget
 * 
 * Displays real-time system status with metrics:
 * - Template availability
 * - SMTP configuration
 * - Engine status
 * - Active jobs count
 * - System latency
 */

(function() {
  'use strict';
  
  // Configuration
  const POLL_INTERVAL = 5000; // 5 seconds
  const API_ENDPOINT = '/goonj/api/system-status';
  
  // State
  let isMinimized = false;
  let pollInterval = null;
  
  // Status color mapping
  const STATUS_COLORS = {
    operational: '#10b981', // green
    degraded: '#f59e0b',    // amber
    error: '#ef4444'        // red
  };
  
  // Create widget HTML
  function createWidget() {
    const widget = document.createElement('div');
    widget.id = 'system-status-widget';
    widget.className = 'system-status-widget';
    widget.innerHTML = `
      <div class="status-header">
        <span class="status-title">System Status</span>
        <button class="status-toggle" aria-label="Toggle widget" title="Minimize/Maximize">
          <span class="toggle-icon">−</span>
        </button>
      </div>
      <div class="status-content">
        <div class="status-indicator">
          <div class="status-dot" id="status-dot"></div>
          <span class="status-text" id="status-text">Checking...</span>
        </div>
        <div class="status-metrics">
          <div class="metric">
            <span class="metric-icon">📄</span>
            <span class="metric-label">Template:</span>
            <span class="metric-value" id="metric-template">—</span>
          </div>
          <div class="metric">
            <span class="metric-icon">✉️</span>
            <span class="metric-label">SMTP:</span>
            <span class="metric-value" id="metric-smtp">—</span>
          </div>
          <div class="metric">
            <span class="metric-icon">⚡</span>
            <span class="metric-label">Latency:</span>
            <span class="metric-value" id="metric-latency">—</span>
          </div>
          <div class="metric">
            <span class="metric-icon">📊</span>
            <span class="metric-label">Active Jobs:</span>
            <span class="metric-value" id="metric-jobs">—</span>
          </div>
        </div>
        <div class="status-updated" id="status-updated">Never updated</div>
      </div>
    `;
    
    document.body.appendChild(widget);
    
    // Attach event listeners
    const toggleBtn = widget.querySelector('.status-toggle');
    toggleBtn.addEventListener('click', toggleWidget);
    
    // Make widget draggable (optional enhancement)
    makeWidgetDraggable(widget);
  }
  
  // Toggle widget minimized state
  function toggleWidget() {
    const widget = document.getElementById('system-status-widget');
    const content = widget.querySelector('.status-content');
    const toggleIcon = widget.querySelector('.toggle-icon');
    
    isMinimized = !isMinimized;
    
    if (isMinimized) {
      content.style.display = 'none';
      toggleIcon.textContent = '+';
      widget.classList.add('minimized');
    } else {
      content.style.display = 'block';
      toggleIcon.textContent = '−';
      widget.classList.remove('minimized');
    }
  }
  
  // Update widget with status data
  function updateWidget(data) {
    // Update main status
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    const status = data.engine_status || 'error';
    statusDot.style.backgroundColor = STATUS_COLORS[status];
    statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusText.style.color = STATUS_COLORS[status];
    
    // Update metrics
    document.getElementById('metric-template').textContent = data.template_exists ? '✓ OK' : '✗ Missing';
    document.getElementById('metric-template').style.color = data.template_exists ? '#10b981' : '#ef4444';
    
    // Update SMTP metric with tooltip showing reason if disabled
    const smtpMetric = document.getElementById('metric-smtp');
    if (data.smtp_configured) {
      smtpMetric.textContent = '✓ OK';
      smtpMetric.style.color = '#10b981';
      smtpMetric.title = data.smtp_status_details?.message || 'SMTP configured';
    } else {
      smtpMetric.textContent = '✗ Disabled';
      smtpMetric.style.color = '#f59e0b';
      // Set tooltip with detailed reason
      if (data.smtp_status_details) {
        smtpMetric.title = data.smtp_status_details.message || 'SMTP not configured';
      } else {
        smtpMetric.title = 'SMTP not configured';
      }
    }
    
    document.getElementById('metric-latency').textContent = `${data.latency_ms || 0}ms`;
    document.getElementById('metric-latency').style.color = data.latency_ms < 100 ? '#10b981' : data.latency_ms < 500 ? '#f59e0b' : '#ef4444';
    
    document.getElementById('metric-jobs').textContent = data.active_jobs_count || 0;
    document.getElementById('metric-jobs').style.color = data.active_jobs_count > 0 ? '#3b82f6' : '#6b7280';
    
    // Update timestamp
    if (data.last_updated) {
      const date = new Date(data.last_updated);
      const timeStr = date.toLocaleTimeString();
      document.getElementById('status-updated').textContent = `Updated: ${timeStr}`;
    }
  }
  
  // Fetch status from API
  async function fetchStatus() {
    try {
      const response = await fetch(API_ENDPOINT);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      updateWidget(data);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      // Update widget with error state
      updateWidget({
        engine_status: 'error',
        template_exists: false,
        smtp_configured: false,
        latency_ms: 0,
        active_jobs_count: 0,
        last_updated: new Date().toISOString()
      });
    }
  }
  
  // Make widget draggable (simple implementation)
  function makeWidgetDraggable(widget) {
    const header = widget.querySelector('.status-header');
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    
    header.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);
    
    function dragStart(e) {
      if (e.target.closest('.status-toggle')) return;
      
      initialX = e.clientX - widget.offsetLeft;
      initialY = e.clientY - widget.offsetTop;
      isDragging = true;
      widget.style.cursor = 'grabbing';
    }
    
    function drag(e) {
      if (!isDragging) return;
      
      e.preventDefault();
      currentX = e.clientX - initialX;
      currentY = e.clientY - initialY;
      
      widget.style.left = currentX + 'px';
      widget.style.top = currentY + 'px';
      widget.style.right = 'auto';
      widget.style.bottom = 'auto';
    }
    
    function dragEnd() {
      isDragging = false;
      widget.style.cursor = 'default';
    }
  }
  
  // Initialize widget
  function init() {
    createWidget();
    fetchStatus(); // Initial fetch
    pollInterval = setInterval(fetchStatus, POLL_INTERVAL);
  }
  
  // Cleanup on page unload
  window.addEventListener('beforeunload', function() {
    if (pollInterval) {
      clearInterval(pollInterval);
    }
  });
  
  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
