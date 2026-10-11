/**
 * LifeTrace AI — Analytics Charts
 */

document.addEventListener('DOMContentLoaded', () => {
  if (typeof Chart === 'undefined') return;

  // Set default Chart.js styling for dark mode
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.08)';

  // 1. Task Status Doughnut Chart
  const statusCtx = document.getElementById('taskStatusChart');
  if (statusCtx && window.analyticsData) {
    const d = window.analyticsData.task_metrics;
    new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: ['Completed', 'In Progress', 'Pending', 'Overdue'],
        datasets: [{
          data: [d.completed, d.in_progress, d.pending, d.overdue],
          backgroundColor: ['#10b981', '#38bdf8', '#f59e0b', '#ef4444'],
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 12, padding: 16 }
          }
        },
        cutout: '72%'
      }
    });
  }

  // 2. Weekly Task Trend Chart
  const trendCtx = document.getElementById('taskTrendChart');
  if (trendCtx && window.analyticsData) {
    const d = window.analyticsData.task_metrics;
    new Chart(trendCtx, {
      type: 'bar',
      data: {
        labels: d.days_labels,
        datasets: [
          {
            label: 'Completed Tasks',
            data: d.completed_by_day,
            backgroundColor: '#6366f1',
            borderRadius: 6
          },
          {
            label: 'New Tasks Created',
            data: d.created_by_day,
            backgroundColor: 'rgba(255, 255, 255, 0.12)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            ticks: { precision: 0 }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12 }
          }
        }
      }
    });
  }

  // 3. Payment Balance Bar Chart
  const paymentCtx = document.getElementById('paymentBalanceChart');
  if (paymentCtx && window.analyticsData) {
    const p = window.analyticsData.payment_metrics;
    new Chart(paymentCtx, {
      type: 'bar',
      data: {
        labels: ['Money Lent (You gave)', 'Money Borrowed (You took)'],
        datasets: [
          {
            label: 'Outstanding Balance (₹)',
            data: [p.lent_outstanding, p.borrowed_outstanding],
            backgroundColor: ['#10b981', '#f59e0b'],
            borderRadius: 6
          },
          {
            label: 'Settled / Repaid (₹)',
            data: [p.lent_recovered, p.borrowed_repaid],
            backgroundColor: ['rgba(16, 185, 129, 0.3)', 'rgba(245, 158, 11, 0.3)'],
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12 }
          }
        }
      }
    });
  }

  // 4. Categories Distribution Chart
  const catCtx = document.getElementById('categoryDistributionChart');
  if (catCtx && window.analyticsData) {
    const d = window.analyticsData.task_metrics;
    if (d.categories_labels.length > 0) {
      new Chart(catCtx, {
        type: 'polarArea',
        data: {
          labels: d.categories_labels,
          datasets: [{
            data: d.categories_values,
            backgroundColor: [
              'rgba(99, 102, 241, 0.7)',
              'rgba(139, 92, 246, 0.7)',
              'rgba(6, 182, 212, 0.7)',
              'rgba(16, 185, 129, 0.7)',
              'rgba(245, 158, 11, 0.7)',
              'rgba(239, 68, 68, 0.7)'
            ],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { boxWidth: 12, padding: 12 }
            }
          }
        }
      });
    }
  }
});
