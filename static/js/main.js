/**
 * KUMAR STORE - CLIENT APPLICATION SCRIPTS
 * Dynamic B2C/B2B Unit Switching, Live Cart Counters, Wishlist Toggle
 */

document.addEventListener('DOMContentLoaded', function () {
  initImageFallbacks();
  initUnitVariantSelectors();
  initQuantityCounters();
  initAddToCartButtons();
  initWishlistToggles();
  initCartPageInteractions();
});

// -------------------------------------------------------------
// 1. Static Image Fallback Support
// -------------------------------------------------------------
function initImageFallbacks() {
  document.querySelectorAll('img.product-img, img.card-img-top, img.fallback-capable').forEach(img => {
    img.addEventListener('error', function () {
      if (!this.dataset.fallbackApplied) {
        this.dataset.fallbackApplied = 'true';
        this.src = '/static/img/fallback.svg';
      }
    });
  });
}

// -------------------------------------------------------------
// 2. Unit Variant Selector - Dynamic Pricing & MOQ Adjustment
// -------------------------------------------------------------
function initUnitVariantSelectors() {
  document.querySelectorAll('.unit-select-box').forEach(select => {
    select.addEventListener('change', function () {
      const card = this.closest('.product-card') || this.closest('.product-detail-box');
      if (!card) return;

      const selectedOpt = this.options[this.selectedIndex];
      if (!selectedOpt) return;

      const price = parseFloat(selectedOpt.dataset.price || 0);
      const mrp = parseFloat(selectedOpt.dataset.mrp || 0);
      const moq = parseInt(selectedOpt.dataset.moq || 1, 10);
      const stock = parseInt(selectedOpt.dataset.stock || 0, 10);
      const unitId = selectedOpt.value;

      // Update price display
      const priceElem = card.querySelector('.current-price');
      if (priceElem) {
        priceElem.textContent = '₹ ' + price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      }

      // Update MRP display
      const mrpElem = card.querySelector('.mrp-price');
      if (mrpElem) {
        if (mrp > price) {
          mrpElem.textContent = '₹ ' + mrp.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
          mrpElem.style.display = 'inline';
        } else {
          mrpElem.style.display = 'none';
        }
      }

      // Update discount tag
      const discountTag = card.querySelector('.discount-tag');
      if (discountTag) {
        if (mrp > price) {
          const discountPct = Math.round(((mrp - price) / mrp) * 100);
          discountTag.textContent = discountPct + '% OFF';
          discountTag.style.display = 'inline-block';
        } else {
          discountTag.style.display = 'none';
        }
      }

      // Update stock badge & Add to cart button state
      const stockTag = card.querySelector('.stock-tag');
      const addBtn = card.querySelector('.add-cart-btn');
      const qtyGroup = card.querySelector('.qty-counter-group');
      const qtyInput = card.querySelector('.qty-input');

      // Reset card action controls: show Add button, hide counter
      if (qtyGroup) {
        qtyGroup.style.display = 'none';
      }

      if (stock <= 0) {
        if (stockTag) {
          stockTag.className = 'stock-tag stock-out';
          stockTag.textContent = 'Out of Stock';
        }
        if (addBtn) {
          addBtn.disabled = true;
          addBtn.style.display = 'inline-flex';
          addBtn.innerHTML = '<i class="bi bi-x-circle me-1"></i> Sold Out';
        }
      } else if (stock < 10) {
        if (stockTag) {
          stockTag.className = 'stock-tag stock-low';
          stockTag.textContent = 'Low Stock (' + stock + ' left)';
        }
        if (addBtn) {
          addBtn.disabled = false;
          addBtn.style.display = 'inline-flex';
          addBtn.innerHTML = '<i class="bi bi-cart-plus me-1"></i> Add to Cart';
        }
      } else {
        if (stockTag) {
          stockTag.className = 'stock-tag stock-in';
          stockTag.textContent = 'In Stock';
        }
        if (addBtn) {
          addBtn.disabled = false;
          addBtn.style.display = 'inline-flex';
          addBtn.innerHTML = '<i class="bi bi-cart-plus me-1"></i> Add to Cart';
        }
      }

      // Update MOQ indicator
      const moqIndicator = card.querySelector('.moq-indicator');
      if (moqIndicator) {
        if (moq > 1) {
          moqIndicator.textContent = 'Min Order (MOQ): ' + moq + ' units';
          moqIndicator.style.display = 'inline-block';
        } else {
          moqIndicator.style.display = 'none';
        }
      }

      // Sync quantity input min & default value with MOQ
      if (qtyInput) {
        qtyInput.min = moq;
        qtyInput.value = moq;
        qtyInput.dataset.unitId = unitId;
      }

      // Store selected unit_id on the Add to Cart button
      if (addBtn) {
        addBtn.dataset.unitId = unitId;
      }
    });

    // Trigger initial change event to ensure clean render
    select.dispatchEvent(new Event('change'));
  });
}

// -------------------------------------------------------------
// 3. Interactive Quantity Adjustment (+ / - Counter)
// -------------------------------------------------------------
function initQuantityCounters() {
  document.querySelectorAll('.qty-counter-group').forEach(group => {
    const minusBtn = group.querySelector('.qty-minus');
    const plusBtn = group.querySelector('.qty-plus');
    const input = group.querySelector('.qty-input');
    const card = group.closest('.product-card');

    if (!minusBtn || !plusBtn || !input) return;

    plusBtn.addEventListener('click', function (e) {
      e.preventDefault();
      let current = parseInt(input.value || 1, 10);
      let max = parseInt(input.max || 9999, 10);
      if (current < max) {
        let newVal = current + 1;
        input.value = newVal;

        // If on product card, sync update to cart
        if (card) {
          const unitSelect = card.querySelector('.unit-select-box');
          const unitId = input.dataset.unitId || (unitSelect ? unitSelect.value : null);
          if (unitId) {
            fetch('/api/cart/update', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ unit_id: unitId, quantity: newVal })
            })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                updateCartBadge(data.cart_count);
              } else {
                showToast(data.error || 'Could not update cart', 'error');
                if (data.min_qty) input.value = data.min_qty;
              }
            })
            .catch(err => console.error(err));
          }
        }
      }
    });

    minusBtn.addEventListener('click', function (e) {
      e.preventDefault();
      let min = parseInt(input.min || 1, 10);
      let current = parseInt(input.value || min, 10);

      if (current > min) {
        let newVal = current - 1;
        input.value = newVal;

        // If on product card, sync update to cart
        if (card) {
          const unitSelect = card.querySelector('.unit-select-box');
          const unitId = input.dataset.unitId || (unitSelect ? unitSelect.value : null);
          if (unitId) {
            fetch('/api/cart/update', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ unit_id: unitId, quantity: newVal })
            })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                updateCartBadge(data.cart_count);
              } else {
                showToast(data.error || 'Could not update cart', 'error');
              }
            })
            .catch(err => console.error(err));
          }
        }
      } else {
        // Value is at or below minimum -> Remove from cart and switch back to Add button!
        if (card) {
          const unitSelect = card.querySelector('.unit-select-box');
          const unitId = input.dataset.unitId || (unitSelect ? unitSelect.value : null);
          const addBtn = card.querySelector('.add-cart-btn');

          if (unitId) {
            fetch('/api/cart/remove', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ unit_id: unitId })
            })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                updateCartBadge(data.cart_count);
                showToast('Item removed from cart', 'info');

                // Hide counter, show add button
                group.style.display = 'none';
                if (addBtn) {
                  addBtn.style.display = 'inline-flex';
                  addBtn.innerHTML = '<i class="bi bi-cart-plus me-1"></i> Add to Cart';
                }
                input.value = min;
              }
            })
            .catch(err => console.error(err));
          }
        }
      }
    });

    input.addEventListener('change', function () {
      let min = parseInt(this.min || 1, 10);
      let max = parseInt(this.max || 9999, 10);
      let val = parseInt(this.value, 10);
      if (isNaN(val) || val < min) val = min;
      if (val > max) val = max;
      this.value = val;
    });
  });
}

// -------------------------------------------------------------
// 4. AJAX Add to Cart
// -------------------------------------------------------------
function initAddToCartButtons() {
  document.querySelectorAll('.add-cart-btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const card = this.closest('.product-card') || this.closest('.product-detail-box');
      if (!card) return;

      const unitSelect = card.querySelector('.unit-select-box');
      let unitId = this.dataset.unitId;
      if (!unitId && unitSelect) {
        unitId = unitSelect.value;
      }

      const qtyGroup = card.querySelector('.qty-counter-group');
      const qtyInput = card.querySelector('.qty-input');
      const quantity = qtyInput ? parseInt(qtyInput.value, 10) : 1;

      if (!unitId) {
        showToast('Please select a unit variant', 'error');
        return;
      }

      // UI loading state
      const origHtml = this.innerHTML;
      this.disabled = true;
      this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Adding...';

      fetch('/api/cart/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ unit_id: unitId, quantity: quantity })
      })
      .then(res => res.json())
      .then(data => {
        this.disabled = false;
        this.innerHTML = origHtml;

        if (data.success) {
          showToast(data.message || 'Added to cart!', 'success');
          updateCartBadge(data.cart_count);

          // Product Card UI Behavior:
          // add-cart-btn becomes hidden, qty-counter-group becomes visible
          if (card.classList.contains('product-card')) {
            this.style.display = 'none';
            if (qtyGroup) {
              qtyGroup.style.display = 'inline-flex';
            }
            if (qtyInput) {
              qtyInput.value = data.quantity || quantity;
              qtyInput.dataset.unitId = unitId;
            }
          }
        } else {
          showToast(data.error || 'Failed to add item to cart', 'error');
        }
      })
      .catch(err => {
        this.disabled = false;
        this.innerHTML = origHtml;
        console.error('Add to cart error:', err);
        showToast('Network error, please try again', 'error');
      });
    });
  });
}

// -------------------------------------------------------------
// 5. Wishlist Heart Toggle Icon
// -------------------------------------------------------------
function initWishlistToggles() {
  document.querySelectorAll('.wishlist-btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const productId = this.dataset.productId;
      if (!productId) return;

      fetch('/api/wishlist/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          if (data.in_wishlist) {
            this.classList.add('active');
            this.innerHTML = '<i class="bi bi-heart-fill"></i>';
            showToast('Added to your wishlist!', 'success');
          } else {
            this.classList.remove('active');
            this.innerHTML = '<i class="bi bi-heart"></i>';
            showToast('Removed from your wishlist', 'info');
          }
          updateWishlistBadge(data.wishlist_count);
        } else {
          if (data.redirect) {
            window.location.href = data.redirect;
          } else {
            showToast(data.error || 'Please login to use wishlist', 'error');
          }
        }
      })
      .catch(err => {
        console.error('Wishlist error:', err);
        showToast('Error updating wishlist', 'error');
      });
    });
  });
}

// -------------------------------------------------------------
// 6. Cart Page Dynamic Interactions (Update / Remove / Coupon)
// -------------------------------------------------------------
function initCartPageInteractions() {
  // Cart item quantity update
  document.querySelectorAll('.cart-item-qty').forEach(input => {
    input.addEventListener('change', function () {
      const cartId = this.dataset.cartId;
      const quantity = parseInt(this.value, 10);
      if (!cartId || isNaN(quantity)) return;

      fetch('/api/cart/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_id: cartId, quantity: quantity })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          updateCartBadge(data.cart_count);
          // Reload or dynamically update summary
          window.location.reload();
        } else {
          showToast(data.error || 'Failed to update quantity', 'error');
          if (data.min_qty) {
            this.value = data.min_qty;
          }
        }
      })
      .catch(err => console.error(err));
    });
  });

  // Cart item remove
  document.querySelectorAll('.cart-item-remove').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const cartId = this.dataset.cartId;
      if (!cartId) return;

      if (!confirm('Remove this item from your cart?')) return;

      fetch('/api/cart/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart_id: cartId })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          updateCartBadge(data.cart_count);
          window.location.reload();
        } else {
          showToast(data.error || 'Failed to remove item', 'error');
        }
      })
      .catch(err => console.error(err));
    });
  });

  // Coupon Application
  const couponForm = document.getElementById('coupon-form');
  if (couponForm) {
    couponForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const codeInput = document.getElementById('coupon-code-input');
      const code = codeInput ? codeInput.value.trim() : '';
      if (!code) return;

      fetch('/api/coupon/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coupon_code: code })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast('Coupon applied: ' + data.message, 'success');
          setTimeout(() => window.location.reload(), 600);
        } else {
          showToast(data.error || 'Invalid coupon code', 'error');
        }
      })
      .catch(err => console.error(err));
    });
  }
}

// -------------------------------------------------------------
// Helper: Update Navbar Badges
// -------------------------------------------------------------
function updateCartBadge(count) {
  document.querySelectorAll('.live-cart-count').forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? 'inline-block' : 'none';
  });
}

function updateWishlistBadge(count) {
  document.querySelectorAll('.live-wishlist-count').forEach(el => {
    el.textContent = count;
    el.style.display = count > 0 ? 'inline-block' : 'none';
  });
}

// -------------------------------------------------------------
// Helper: Toast Notifications
// -------------------------------------------------------------
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container-custom');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container-custom';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'custom-toast';
  
  let icon = 'bi-info-circle-fill text-primary';
  if (type === 'success') icon = 'bi-check-circle-fill text-success';
  if (type === 'error') icon = 'bi-exclamation-triangle-fill text-danger';

  toast.innerHTML = `
    <i class="bi ${icon} fs-5"></i>
    <div class="flex-grow-1">${message}</div>
    <button type="button" class="btn-close ms-2" aria-label="Close"></button>
  `;

  toast.querySelector('.btn-close').addEventListener('click', () => toast.remove());
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
