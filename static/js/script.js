/**
 * The Recipe Table - Culinary Atelier Master JavaScript
 * Final Visual & Interactive Polish for Floating Editorial Navbar
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log('🍳 The Savor Table Navigation System loaded.');

  initCulinaryThemeSwitch();
  initExpandableSearch();
  initUserProfileDropdown();
  initMobileNavDrawer();
  initKeyboardAccessibility();
  initFavoriteInteractions();
});

/**
 * 1. Food-Themed Culinary Light/Dark Theme Switch System
 */
function initCulinaryThemeSwitch() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  applyThemeUI(currentTheme);

  const themeBtns = document.querySelectorAll('.culinary-theme-switch .theme-option-btn');
  themeBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const selectedTheme = btn.getAttribute('data-theme-val');
      setTheme(selectedTheme);
    });
  });

  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      if (!localStorage.getItem('savortable_theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('savortable_theme', theme);
  applyThemeUI(theme);
}

function applyThemeUI(theme) {
  const isDark = theme === 'dark';
  const switches = document.querySelectorAll('.culinary-theme-switch');

  switches.forEach(sw => {
    const dayBtn = sw.querySelector('[data-theme-val="light"]');
    const nightBtn = sw.querySelector('[data-theme-val="dark"]');

    if (dayBtn && nightBtn) {
      if (isDark) {
        dayBtn.classList.remove('active');
        dayBtn.setAttribute('aria-checked', 'false');
        nightBtn.classList.add('active');
        nightBtn.setAttribute('aria-checked', 'true');
        sw.classList.add('is-dark');
      } else {
        nightBtn.classList.remove('active');
        nightBtn.setAttribute('aria-checked', 'false');
        dayBtn.classList.add('active');
        dayBtn.setAttribute('aria-checked', 'true');
        sw.classList.remove('is-dark');
      }
    }
  });
}

/**
 * 6. Progressive Enhancement for Favorites & Collections Toggle
 */
function initFavoriteInteractions() {
  document.addEventListener('submit', async (e) => {
    const form = e.target.closest('.favorite-action-form, .remove-favorite-form');
    if (!form) return;

    e.preventDefault();

    const actionUrl = form.getAttribute('action');
    const recipeId = form.getAttribute('data-recipe-id');
    const submitBtn = form.querySelector('button[type="submit"]');

    if (!actionUrl) return;

    try {
      const response = await fetch(actionUrl, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/json'
        }
      });

      if (response.status === 401) {
        const data = await response.json().catch(() => ({}));
        showToast(data.message || 'Please log in to save recipes.', '⚠️');
        setTimeout(() => {
          window.location.href = data.redirect || '/login';
        }, 1200);
        return;
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        showToast(data.message || 'An error occurred.', '⚠️');
        return;
      }

      const result = await response.json();
      if (result.status === 'success') {
        const isFavorite = result.is_favorite;

        // 1. If inside Recipe Details Page action bar
        const detailsBtn = form.querySelector('.favorite-toggle-btn');
        if (detailsBtn) {
          if (isFavorite) {
            detailsBtn.classList.remove('btn-outline-dark');
            detailsBtn.classList.add('btn-terracotta');
            detailsBtn.setAttribute('data-is-favorite', 'true');
            detailsBtn.innerHTML = '<span>♥ Saved</span>';
            form.setAttribute('action', `/recipes/${recipeId}/unfavorite`);
          } else {
            detailsBtn.classList.remove('btn-terracotta');
            detailsBtn.classList.add('btn-outline-dark');
            detailsBtn.setAttribute('data-is-favorite', 'false');
            detailsBtn.innerHTML = '<span>♡ Save Recipe</span>';
            form.setAttribute('action', `/recipes/${recipeId}/favorite`);
          }
        }

        // 2. If clicking heart icon on recipe cards
        const heartBtn = form.querySelector('.favorite-heart-btn');
        if (heartBtn) {
          if (isFavorite) {
            heartBtn.classList.add('liked');
          } else {
            heartBtn.classList.remove('liked');
          }
        }

        // 3. If removing from Collections Page
        const collectionCard = form.closest('.collection-card-item');
        if (collectionCard && !isFavorite) {
          collectionCard.style.transition = 'all 0.3s ease';
          collectionCard.style.opacity = '0';
          collectionCard.style.transform = 'scale(0.95)';
          setTimeout(() => {
            collectionCard.remove();
            const remainingCards = document.querySelectorAll('.collection-card-item');
            if (remainingCards.length === 0) {
              location.reload(); // Reload to render empty state cleanly
            }
          }, 300);
        }

        showToast(result.message, isFavorite ? '❤️' : 'ℹ️');
      }
    } catch (err) {
      console.error('Favorite toggle failed:', err);
      // Fallback: submit standard form if fetch fails
      form.submit();
    }
  });
}

/**
 * 2. Expandable Editorial Search Interaction
 */
function initExpandableSearch() {
  const searchWrapper = document.getElementById('navSearchWrapper');
  const searchTrigger = document.getElementById('navSearchTrigger');
  const searchInput = document.getElementById('navSearchInput');

  if (searchTrigger && searchWrapper && searchInput) {
    searchTrigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isExpanded = searchWrapper.classList.toggle('expanded');
      searchTrigger.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
      if (isExpanded) {
        searchInput.focus();
      }
    });

    // Dismiss search when clicking outside
    document.addEventListener('click', (e) => {
      if (!searchWrapper.contains(e.target) && searchWrapper.classList.contains('expanded')) {
        searchWrapper.classList.remove('expanded');
        searchTrigger.setAttribute('aria-expanded', 'false');
      }
    });
  }
}

/**
 * 3. User Profile Dropdown Toggle
 */
function initUserProfileDropdown() {
  const wrapper = document.getElementById('userProfileDropdown');
  const chipBtn = document.getElementById('userChipBtn');

  if (chipBtn && wrapper) {
    chipBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isActive = wrapper.classList.toggle('active');
      chipBtn.setAttribute('aria-expanded', isActive ? 'true' : 'false');
    });

    // Dismiss profile dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!wrapper.contains(e.target) && wrapper.classList.contains('active')) {
        wrapper.classList.remove('active');
        chipBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }
}

/**
 * 4. Mobile Off-Canvas Navigation Drawer with Body Scroll Lock
 */
function initMobileNavDrawer() {
  const trigger = document.getElementById('mobileMenuTrigger');
  const panel = document.getElementById('mobileNavPanel');
  const closeBtn = document.getElementById('mobilePanelClose');
  const overlay = document.getElementById('mobilePanelOverlay');
  const mobileLinks = document.querySelectorAll('.mobile-link');

  if (trigger && panel) {
    const openMenu = () => {
      panel.classList.add('open');
      panel.setAttribute('aria-hidden', 'false');
      trigger.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden'; // Lock body scrolling
    };

    const closeMenu = () => {
      panel.classList.remove('open');
      panel.setAttribute('aria-hidden', 'true');
      trigger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = ''; // Unlock body scrolling
    };

    trigger.addEventListener('click', openMenu);
    if (closeBtn) closeBtn.addEventListener('click', closeMenu);
    if (overlay) overlay.addEventListener('click', closeMenu);

    // Auto-close mobile drawer when clicking any navigation link
    mobileLinks.forEach(link => {
      link.addEventListener('click', closeMenu);
    });
  }
}

/**
 * 5. Global Keyboard Accessibility & Escape Key Handlers
 */
function initKeyboardAccessibility() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      // 1. Close mobile drawer if open
      const panel = document.getElementById('mobileNavPanel');
      if (panel && panel.classList.contains('open')) {
        panel.classList.remove('open');
        panel.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        const trigger = document.getElementById('mobileMenuTrigger');
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
      }

      // 2. Close profile dropdown if open
      const profileWrapper = document.getElementById('userProfileDropdown');
      if (profileWrapper && profileWrapper.classList.contains('active')) {
        profileWrapper.classList.remove('active');
        const chipBtn = document.getElementById('userChipBtn');
        if (chipBtn) chipBtn.setAttribute('aria-expanded', 'false');
      }

      // 3. Close expandable search if open
      const searchWrapper = document.getElementById('navSearchWrapper');
      if (searchWrapper && searchWrapper.classList.contains('expanded')) {
        searchWrapper.classList.remove('expanded');
        const searchTrigger = document.getElementById('navSearchTrigger');
        if (searchTrigger) searchTrigger.setAttribute('aria-expanded', 'false');
      }
    }
  });
}

/**
 * Toast Notification System
 */
function showToast(message, icon = '✨') {
  const container = document.getElementById('toast-container') || createToastContainer();
  
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toast-container';
  container.className = 'toast-container';
  document.body.appendChild(container);
  return container;
}

/**
 * Favorite Heart Micro-Interaction
 */
function toggleHeart(btn) {
  btn.classList.toggle('liked');
  if (btn.classList.contains('liked')) {
    btn.innerHTML = '♥';
    btn.style.color = '#ef4444';
    showToast('Saved to your favorites collection!', '❤️');
  } else {
    btn.innerHTML = '♥';
    btn.style.color = 'var(--text-muted)';
    showToast('Removed from favorites.', '💔');
  }
}
