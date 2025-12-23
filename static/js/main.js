// Main JavaScript for ecommerce site

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.display = 'none';
        }, 5000);
    });
    
    // Cart functionality will be added here
    console.log('Ecommerce site loaded successfully');
});