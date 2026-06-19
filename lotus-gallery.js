// Lotus Gallery - Dedicated Lotus Theme Gallery

let lotusAvatars = [];

// Utility: fetch with retry
async function fetchWithRetry(url, options = {}, retries = 3, delay = 500) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response;
    } catch (error) {
      if (attempt === retries) throw error;
      console.warn(`Fetch attempt ${attempt} failed, retrying in ${delay}ms...`, error);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

// Show/hide loading state
function setLoading(isLoading) {
  const grid = document.getElementById('lotusGalleryGrid');
  const noResults = document.getElementById('noResults');
  if (isLoading) {
    grid.innerHTML = '<div class="loading-spinner" style="grid-column: 1/-1; display:flex; justify-content:center; align-items:center; padding:3rem;"></div>';
    noResults.hidden = true;
  }
}

// Initialize lotus gallery
async function initLotusGallery() {
  setLoading(true);
  try {
    const response = await fetchWithRetry('data.json');
    const data = await response.json();
    // Filter for lotus theme only
    lotusAvatars = data.avatars.filter(a => a.theme === 'lotus');
    renderLotusGallery();
    setupLightboxListeners();
  } catch (error) {
    console.error('Lotus gallery initialization failed:', error);
    const grid = document.getElementById('lotusGalleryGrid');
    grid.innerHTML = '<p class="no-results" style="grid-column: 1/-1;">Failed to load lotus gallery data.</p>';
  }
}

// Render lotus gallery grid
function renderLotusGallery() {
  const grid = document.getElementById('lotusGalleryGrid');
  const noResults = document.getElementById('noResults');

  if (lotusAvatars.length === 0) {
    grid.innerHTML = '';
    noResults.hidden = false;
    return;
  }

  noResults.hidden = true;
  grid.innerHTML = lotusAvatars.map((avatar, index) => `
    <article class="gallery-item" data-index="${index}" data-theme="${avatar.theme}" tabindex="0" role="listitem">
      <img src="images/${avatar.filename}" alt="${avatar.prompt}" loading="lazy">
      <div class="gallery-item-overlay">
        <div class="gallery-item-title">${avatar.prompt}</div>
        <div class="gallery-item-actions">
          <span class="gallery-item-theme">${avatar.theme}</span>
        </div>
      </div>
    </article>
  `).join('');

  // Add click/keyboard handlers to gallery items
  grid.querySelectorAll('.gallery-item').forEach(item => {
    item.addEventListener('click', () => {
      openLightbox(parseInt(item.dataset.index));
    });
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openLightbox(parseInt(item.dataset.index));
      }
    });
  });
}

// Lightbox functions
let currentLightboxIndex = 0;

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
  const avatar = lotusAvatars[currentLightboxIndex];
  if (!avatar) return;

  document.getElementById('lightboxImage').src = `images/${avatar.filename}`;
  document.getElementById('lightboxImage').alt = avatar.prompt;
  document.getElementById('lightboxTitle').textContent = avatar.prompt;
  document.getElementById('lightboxPrompt').textContent = avatar.prompt;
  document.getElementById('lightboxTheme').textContent = avatar.theme;
}

function navigateLightbox(direction) {
  currentLightboxIndex = (currentLightboxIndex + direction + lotusAvatars.length) % lotusAvatars.length;
  updateLightbox();
}

// Setup lightbox event listeners
function setupLightboxListeners() {
  // Close button
  document.getElementById('lightboxClose').addEventListener('click', closeLightbox);
  
  // Navigation buttons
  document.getElementById('lightboxPrev').addEventListener('click', () => navigateLightbox(-1));
  document.getElementById('lightboxNext').addEventListener('click', () => navigateLightbox(1));
  
  // Click outside to close
  document.getElementById('lightbox').addEventListener('click', (e) => {
    if (e.target.id === 'lightbox') closeLightbox();
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
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initLotusGallery);