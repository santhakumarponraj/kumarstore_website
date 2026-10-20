/**
 * KUMAR STORE - ADMIN DASHBOARD JAVASCRIPT
 */

document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts after 5 seconds
  setTimeout(function () {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    });
  }, 5000);

  // Status transition confirmation
  document.querySelectorAll('.order-status-select').forEach(function (select) {
    select.addEventListener('change', function () {
      const form = this.closest('form');
      if (form) {
        if (confirm(`Change order status to "${this.value}"?`)) {
          form.submit();
        } else {
          // Revert back
          this.value = this.dataset.currentStatus;
        }
      }
    });
  });

  // Table search filter helper
  const tableSearchInput = document.getElementById('admin-table-search');
  if (tableSearchInput) {
    tableSearchInput.addEventListener('input', function () {
      const term = this.value.toLowerCase();
      const rows = document.querySelectorAll('.filterable-table tbody tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  }
});
