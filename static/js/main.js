document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() { alert.style.display = 'none'; }, 300);
        }, 5000);
    });

    // AJAX cart add from product list
    document.querySelectorAll('form[action*="cart/add"]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.closest('.col-md-6, .col-md-8')) {
                // Only AJAX for quick-add buttons on product list, not detail page
                return;
            }
            e.preventDefault();
            const btn = form.querySelector('button[type="submit"]');
            const origHTML = btn.innerHTML;
            btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
            btn.disabled = true;

            fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update cart badge in navbar
                    const badge = document.querySelector('.badge-christmas');
                    if (badge) {
                        badge.textContent = data.cart_total_items;
                    }
                    btn.innerHTML = '<i class="fa fa-check"></i> Added';
                    setTimeout(() => { btn.innerHTML = origHTML; btn.disabled = false; }, 1500);
                }
            })
            .catch(() => {
                btn.innerHTML = origHTML;
                btn.disabled = false;
            });
        });
    });

    // Lazy load images
    if ('IntersectionObserver' in window) {
        const imgObserver = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    imgObserver.unobserve(img);
                }
            });
        });
        document.querySelectorAll('img[data-src]').forEach(function(img) {
            imgObserver.observe(img);
        });
    }
});
