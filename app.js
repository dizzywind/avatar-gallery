// Apollo Avatar Gallery - Main Application

let avatars = [];
let filteredAvatars = [];
let currentLightboxIndex = 0;

// Initialize gallery
async function initGallery() {
  try {
    const response = await fetch('data.json');
    if (!response.ok) throw new Error('Failed to load data.json');
    const data = await response.json();
    avatars = data.avatars;
    filteredAvatars = [...avatars];
    renderGallery();
    setupEventListeners();
  } catch (error) {
    console.error('Gallery initialization failed:', error);
    document.getElementById('galleryGrid').innerHTML =
      '<p class="no-results" style="grid-column: 1/-1;">Failed to load gallery data.</p>';
  }
}

// Render gallery grid
function renderGallery() {
  const grid = document.getElementById('galleryGrid');
  const noResults = document.getElementById('noResults');

  if (filteredAvatars.length === 0) {
    grid.innerHTML = '';
    noResults.hidden = false;
    return;
  }

  noResults.hidden = true;
  grid.innerHTML = filteredAvatars.map((avatar, index) => `
    <article class="gallery-item" data-index="${index}" data-theme="${avatar.theme}" tabindex="0" role="listitem">
      <img src="images/${avatar.filename}" alt="${avatar.prompt}" loading="lazy">
      <div class="gallery-item-overlay">
        <div class="gallery-item-title">${avatar.prompt}</div>
        <span class="gallery-item-theme">${avatar.theme}</span>
      </div>
    </article>
  `).join('');

  // Add click/keyboard handlers to gallery items
  grid.querySelectorAll('.gallery-item').forEach(item => {
    item.addEventListener('click', () => openLightbox(parseInt(item.dataset.index)));
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openLightbox(parseInt(item.dataset.index));
      }
    });
  });
}

// Filter avatars by theme
function filterGallery(theme) {
  if (theme === 'all') {
    filteredAvatars = [...avatars];
  } else {
    filteredAvatars = avatars.filter(a => a.theme === theme);
  }
  renderGallery();
  updateActiveFilter(theme);
}

// Update active filter button
function updateActiveFilter(activeTheme) {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === activeTheme);
  });
}

// Lightbox functions
function openLightbox(index) {
  currentLightboxIndex = index;
  updateLightbox();
  document.getElementById('lightbox').hidden = false;
  document.body.style.overflow = 'hidden';
  document.getElementById('lightboxClose').focus();
}

function closeLightbox() {
  document.getElementById('lightbox').hidden = true;
  document.body.style.overflow = '';
}

function updateLightbox() {
  const avatar = filteredAvatars[currentLightboxIndex];
  if (!avatar) return;

  document.getElementById('lightboxImage').src = `images/${avatar.filename}`;
  document.getElementById('lightboxImage').alt = avatar.prompt;
  document.getElementById('lightboxTitle').textContent = avatar.prompt;
  document.getElementById('lightboxPrompt').textContent = avatar.prompt;
  document.getElementById('lightboxTheme').textContent = avatar.theme;
}

function navigateLightbox(direction) {
  currentLightboxIndex = (currentLightboxIndex + direction + filteredAvatars.length) % filteredAvatars.length;
  updateLightbox();
}

// Event listeners
function setupEventListeners() {
  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => filterGallery(btn.dataset.filter));
  });

  // Lightbox controls
  document.getElementById('lightboxClose').addEventListener('click', closeLightbox);
  document.getElementById('lightboxPrev').addEventListener('click', () => navigateLightbox(-1));
  document.getElementById('lightboxNext').addEventListener('click', () => navigateLightbox(1));

  // Lightbox background click to close
  document.getElementById('lightbox').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeLightbox();
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    if (document.getElementById('lightbox').hidden) return;

    switch (e.key) {
      case 'Escape':
        closeLightbox();
        break;
      case 'ArrowLeft':
        navigateLightbox(-1);
        break;
      case 'ArrowRight':
        navigateLightbox(1);
        break;
    }
  });

  // Touch swipe support for lightbox
  let touchStartX = 0;
  const lightbox = document.getElementById('lightbox');

  lightbox.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
  }, { passive: true });

  lightbox.addEventListener('touchend', (e) => {
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartX - touchEndX;
    if (Math.abs(diff) > 50) {
      navigateLightbox(diff > 0 ? 1 : -1);
    }
  }, { passive: true });
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initGallery);