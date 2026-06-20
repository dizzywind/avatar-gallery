// Apollo Avatar Gallery - Main Application with Style Extraction

let avatars = [];
let filteredAvatars = [];
let currentLightboxIndex = 0;
let currentSearchQuery = '';

// Style panel state
let stylePanelState = {
  step: 'select', // 'select', 'analyze', 'review', 'generate', 'result', 'error'
  referenceImage: null,
  referenceIndex: -1,
  referenceType: 'style',
  strength: 70,
  extractedStyle: null,
  autoPrompt: '',
  alternativePrompts: [],
  subject: '',
  generatedImageUrl: null,
  error: null
};

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

// Sort descending by date embedded in filename; undated items come last.
function sortAvatarsDesc(avatars) {
  const datePattern = /(\d{8})/;
  return avatars.slice().sort((a, b) => {
    const da = (a.filename.match(datePattern) || [])[1] || '00000000';
    const db = (b.filename.match(datePattern) || [])[1] || '00000000';
    if (db !== da) return db.localeCompare(da);
    return b.filename.localeCompare(a.filename);
  });
}

// Show/hide loading state
function setLoading(isLoading) {
  const grid = document.getElementById('galleryGrid');
  const noResults = document.getElementById('noResults');
  if (isLoading) {
    grid.innerHTML = '<div class="loading-spinner" style="grid-column: 1/-1; display:flex; justify-content:center; align-items:center; padding:3rem;"></div>';
    noResults.hidden = true;
  }
}

// Initialize gallery
async function initGallery() {
  setLoading(true);
  try {
    const response = await fetchWithRetry('data.json');
    const data = await response.json();
    avatars = sortAvatarsDesc(data.avatars || []);
    filteredAvatars = [...avatars];
    renderGallery();
    updateLastUpdated(data);
    updateFilterCounts(data);
    setupEventListeners();
  } catch (error) {
    console.error('Gallery initialization failed:', error);
    const grid = document.getElementById('galleryGrid');
    grid.innerHTML =
      '<p class="no-results" style="grid-column: 1/-1;">Failed to load gallery data.</p>';
  }
}

function updateLastUpdated(data) {
  const el = document.getElementById('lastUpdated');
  if (!el) return;
  const meta = data && data._meta;
  const total = meta && typeof meta.totalImages === 'number'
    ? meta.totalImages
    : Array.isArray(data && data.avatars) ? data.avatars.length : null;
  if (!total) { el.textContent = ''; return; }
  const raw = meta && meta.updatedAt ? meta.updatedAt : '';
  let formatted = '';
  if (raw) {
    try {
      const d = new Date(raw);
      if (!isNaN(d.getTime())) {
        formatted = d.toLocaleDateString('en-US', {
          year: 'numeric', month: 'short', day: 'numeric'
        });
        const time = d.toLocaleTimeString('en-US', {
          hour: 'numeric', minute: '2-digit'
        });
        formatted += ' at ' + time;
      }
    } catch (_) { formatted = ''; }
  }
  if (!formatted) formatted = raw || 'unknown date';
  el.textContent = `🕒 Last updated: ${formatted} — ${total.toLocaleString()} images`;
}

function updateFilterCounts(data) {
  const avatars = (data && data.avatars) || [];
  const counts = { all: avatars.length };
  avatars.forEach(a => {
    const theme = a.theme || 'uncategorized';
    counts[theme] = (counts[theme] || 0) + 1;
  });
  document.querySelectorAll('.filter-btn').forEach(btn => {
    const key = btn.dataset.filter;
    if (key === 'all') {
      btn.textContent = 'All';
      return;
    }
    const count = counts[key];
    if (typeof count === 'number') {
      btn.textContent = key.charAt(0).toUpperCase() + key.slice(1) + ' (' + count + ')';
    }
  });
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
        <div class="gallery-item-actions">
          <span class="gallery-item-theme">${avatar.theme}</span>
          <button class="use-style-btn" data-index="${index}" aria-label="Use style from ${avatar.prompt}">
            <span>🎨</span> Use Style
          </button>
        </div>
      </div>
    </article>
  `).join('');

  // Add click/keyboard handlers to gallery items
  grid.querySelectorAll('.gallery-item').forEach(item => {
    item.addEventListener('click', (e) => {
      // Don't open lightbox if clicking the Use Style button
      if (e.target.closest('.use-style-btn')) return;
      openLightbox(parseInt(item.dataset.index));
    });
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openLightbox(parseInt(item.dataset.index));
      }
    });
  });

  // Add Use Style button handlers
  grid.querySelectorAll('.use-style-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation(); // Prevent lightbox from opening
      const index = parseInt(btn.dataset.index);
      openStylePanel(index);
    });
  });
}

// Filter avatars by theme and search query
function applyFilters() {
  let result = [...avatars];
  
  // Apply theme filter
  const activeFilterBtn = document.querySelector('.filter-btn.active');
  const activeTheme = activeFilterBtn ? activeFilterBtn.dataset.filter : 'all';
  
  if (activeTheme !== 'all') {
    result = result.filter(a => a.theme === activeTheme);
  }
  
  // Apply search filter
  if (currentSearchQuery) {
    const query = currentSearchQuery.toLowerCase();
    result = result.filter(a => a.prompt.toLowerCase().includes(query));
  }
  
  filteredAvatars = result;
  renderGallery();
  updateActiveFilter(activeTheme);
  updateSearchClearButton();
}

// Filter avatars by theme (kept for backward compatibility with filter buttons)
function filterGallery(theme) {
  const activeFilterBtn = document.querySelector('.filter-btn.active');
  if (activeFilterBtn) {
    activeFilterBtn.classList.remove('active');
  }
  // Find and activate the clicked theme button
  const newActiveBtn = document.querySelector(`.filter-btn[data-filter="${theme}"]`);
  if (newActiveBtn) {
    newActiveBtn.classList.add('active');
  }
  applyFilters();
}

// Update active filter button
function updateActiveFilter(activeTheme) {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === activeTheme);
  });
}

// Update search clear button visibility
function updateSearchClearButton() {
  const clearBtn = document.getElementById('searchClear');
  if (clearBtn) {
    clearBtn.hidden = !currentSearchQuery;
  }
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

// ==================== STYLE PANEL FUNCTIONS ====================

function openStylePanel(index) {
  const avatar = filteredAvatars[index];
  if (!avatar) return;

  stylePanelState = {
    step: 'select',
    referenceImage: avatar,
    referenceIndex: index,
    referenceType: 'style',
    strength: 70,
    extractedStyle: null,
    autoPrompt: '',
    alternativePrompts: [],
    subject: '',
    generatedImageUrl: null,
    error: null
  };

  renderStylePanel();
  document.getElementById('stylePanelOverlay').hidden = false;
  document.getElementById('stylePanel').hidden = false;
  document.body.style.overflow = 'hidden';
  document.getElementById('stylePanelClose').focus();
}

function closeStylePanel() {
  document.getElementById('stylePanelOverlay').hidden = true;
  document.getElementById('stylePanel').hidden = true;
  document.body.style.overflow = '';
  stylePanelState = {
    step: 'select',
    referenceImage: null,
    referenceIndex: -1,
    referenceType: 'style',
    strength: 70,
    extractedStyle: null,
    autoPrompt: '',
    alternativePrompts: [],
    subject: '',
    generatedImageUrl: null,
    error: null
  };
}

function renderStylePanel() {
  const body = document.getElementById('stylePanelBody');
  const footer = document.getElementById('stylePanelFooter');
  const title = document.getElementById('stylePanelTitle');

  switch (stylePanelState.step) {
    case 'select':
      title.textContent = 'Style Reference';
      body.innerHTML = renderSelectStep();
      footer.innerHTML = renderSelectFooter();
      setupSelectStepListeners();
      break;
    case 'analyze':
      title.textContent = 'Analyzing Style';
      body.innerHTML = renderAnalyzeStep();
      footer.innerHTML = '';
      // Start analysis
      setTimeout(() => analyzeStyle(), 100);
      break;
    case 'review':
      title.textContent = 'Style Reference';
      body.innerHTML = renderReviewStep();
      footer.innerHTML = renderReviewFooter();
      setupReviewStepListeners();
      break;
    case 'generate':
      title.textContent = 'Generating...';
      body.innerHTML = renderGenerateStep();
      footer.innerHTML = renderGenerateFooter();
      setupGenerateStepListeners();
      // Start generation
      setTimeout(() => generateImage(), 100);
      break;
    case 'result':
      title.textContent = 'Style Result';
      body.innerHTML = renderResultStep();
      footer.innerHTML = renderResultFooter();
      setupResultStepListeners();
      break;
    case 'error':
      title.textContent = 'Analysis Issue';
      body.innerHTML = renderErrorStep();
      footer.innerHTML = '';
      setupErrorStepListeners();
      break;
  }
}

function renderSelectStep() {
  const { referenceImage, referenceType, strength } = stylePanelState;
  return `
    <div class="step-indicator">Step 2 of 5</div>
    
    <div class="ref-image-container">
      <img src="images/${referenceImage.filename}" alt="${referenceImage.prompt}">
      <div class="ref-image-badge">Selected</div>
    </div>

    <span class="section-label">Reference Type</span>
    <div class="ref-types">
      <div class="ref-type ${referenceType === 'style' ? 'selected' : ''}" data-type="style">
        <div class="label">◉ Style Only</div>
        <div class="desc">Colors, texture, mood</div>
      </div>
      <div class="ref-type ${referenceType === 'content' ? 'selected' : ''}" data-type="content">
        <div class="label">○ Content Only</div>
        <div class="desc">Structure, composition</div>
      </div>
      <div class="ref-type ${referenceType === 'both' ? 'selected' : ''}" data-type="both">
        <div class="label">○ Both</div>
        <div class="desc">Full image reference</div>
      </div>
      <div class="ref-type ${referenceType === 'custom' ? 'selected' : ''}" data-type="custom">
        <div class="label">○ Custom</div>
        <div class="desc">Pick specific aspects</div>
      </div>
    </div>

    <div class="strength-section">
      <div class="strength-header">
        <span class="section-label">Style Strength</span>
        <span class="strength-value">${strength}%</span>
      </div>
      <div class="slider-track">
        <div class="slider-thumb" id="strengthSlider" style="left: ${strength}%;" tabindex="0" role="slider" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${strength}" aria-label="Style strength"></div>
      </div>
      <div class="slider-labels"><span>Subtle</span><span>Balanced</span><span>Strong</span></div>
    </div>
  `;
}

function renderSelectFooter() {
  return `
    <button class="btn btn-ghost" id="cancelSelectBtn">Cancel</button>
    <button class="btn btn-primary" id="continueSelectBtn">Continue →</button>
  `;
}

function setupSelectStepListeners() {
  // Reference type selection
  document.querySelectorAll('.ref-type').forEach(el => {
    el.addEventListener('click', () => {
      stylePanelState.referenceType = el.dataset.type;
      document.querySelectorAll('.ref-type').forEach(e => e.classList.remove('selected'));
      el.classList.add('selected');
    });
  });

  // Strength slider
  const slider = document.getElementById('strengthSlider');
  const track = slider.parentElement;
  
  function updateSlider(clientX) {
    const rect = track.getBoundingClientRect();
    let percent = ((clientX - rect.left) / rect.width) * 100;
    percent = Math.max(0, Math.min(100, percent));
    stylePanelState.strength = Math.round(percent);
    slider.style.left = `${percent}%`;
    slider.setAttribute('aria-valuenow', stylePanelState.strength);
    document.querySelector('.strength-value').textContent = `${stylePanelState.strength}%`;
  }

  let isDragging = false;
  slider.addEventListener('mousedown', () => { isDragging = true; });
  slider.addEventListener('touchstart', () => { isDragging = true; }, { passive: true });
  document.addEventListener('mousemove', (e) => { if (isDragging) updateSlider(e.clientX); });
  document.addEventListener('touchmove', (e) => { if (isDragging) updateSlider(e.touches[0].clientX); }, { passive: true });
  document.addEventListener('mouseup', () => { isDragging = false; });
  document.addEventListener('touchend', () => { isDragging = false; });

  track.addEventListener('click', (e) => {
    if (e.target !== slider) updateSlider(e.clientX);
  });

  // Keyboard support for slider
  slider.addEventListener('keydown', (e) => {
    let change = 0;
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') change = 5;
    if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') change = -5;
    if (e.key === 'Home') change = -stylePanelState.strength;
    if (e.key === 'End') change = 100 - stylePanelState.strength;
    if (change !== 0) {
      e.preventDefault();
      const newVal = Math.max(0, Math.min(100, stylePanelState.strength + change));
      stylePanelState.strength = newVal;
      slider.style.left = `${newVal}%`;
      slider.setAttribute('aria-valuenow', newVal);
      document.querySelector('.strength-value').textContent = `${newVal}%`;
    }
  });

  // Buttons
  document.getElementById('cancelSelectBtn').addEventListener('click', closeStylePanel);
  document.getElementById('continueSelectBtn').addEventListener('click', () => {
    stylePanelState.step = 'analyze';
    renderStylePanel();
  });
}

async function analyzeStyle() {
  const { referenceImage, referenceType, strength } = stylePanelState;

  // Client-side style extraction — no backend dependency
  const prompt = referenceImage.prompt || '';
  const theme = referenceImage.theme || '';
  const styleKeywords = ['digital art', 'illustration', 'AI generated', theme];
  const extractedStyle = `${prompt} — ${theme} style, high detail, vibrant colors`;
  const autoGeneratedPrompt = `A ${theme} themed artwork, ${prompt.toLowerCase()}, digital painting, detailed, 4k`;
  const alternativePrompts = [
    `${prompt} in ${theme} style, cinematic lighting`,
    `Create a new ${theme} piece inspired by: ${prompt}`,
    `${theme} masterpiece, ${prompt}, studio quality`
  ];
  const metadata = {
    artisticStyle: theme,
    colors: ['vibrant', 'detailed', 'stylized'],
    tags: [theme, 'ai-generated', 'pollinations', ...styleKeywords]
  };

  stylePanelState.extractedStyle = extractedStyle;
  stylePanelState.autoPrompt = autoGeneratedPrompt;
  stylePanelState.alternativePrompts = alternativePrompts;
  stylePanelState.metadata = metadata;
  stylePanelState.step = 'review';
  renderStylePanel();
}

function renderAnalyzeStep() {
  return `
    <div class="step-indicator">Step 3 of 5</div>
    
    <div class="ref-image-container">
      <img src="images/${stylePanelState.referenceImage.filename}" alt="${stylePanelState.referenceImage.prompt}">
      <div class="ref-image-badge">Analyzing...</div>
    </div>

    <div class="analysis-loading">
      <div class="spinner"></div>
      <div class="text">🔍 Analyzing style...</div>
    </div>
  `;
}

function renderReviewStep() {
  const { extractedStyle, autoPrompt, alternativePrompts, subject, metadata } = stylePanelState;
  const colors = (metadata && metadata.colors) ? metadata.colors : [];
  const tags = (metadata && metadata.tags) ? metadata.tags : [];
  return `
    <div class="step-indicator">Step 3 of 5</div>
    
    <div class="ref-image-container">
      <img src="images/${stylePanelState.referenceImage.filename}" alt="${stylePanelState.referenceImage.prompt}">
      <div class="ref-image-badge">✓ Extracted</div>
    </div>

    <span class="section-label">Extracted Style</span>
    <div class="extracted-style">
      <div class="style-desc">${extractedStyle || 'Style analysis in progress...'}</div>
      <div class="style-tags" id="styleTags">
        ${colors.map(c => `<span>${c}</span>`).join('')}
        ${tags.map(t => `<span>${t}</span>`).join('')}
        <span class="add-tag" id="addTagBtn">+ add tag</span>
      </div>
    </div>

    <div class="prompt-area">
      <span class="section-label">Auto-Generated Prompt</span>
      <div class="prompt-text" id="promptText" data-original="${autoPrompt}">
        "${autoPrompt}"
        <span class="edit-icon">✏️</span>
      </div>
    </div>

    <span class="section-label">Alternative Prompts</span>
    <div class="alt-prompts" id="altPrompts">
      ${alternativePrompts.map((p, i) => `<div class="alt-prompt" data-index="${i}">${p}</div>`).join('')}
    </div>

    <div style="margin-top:1rem;">
      <span class="section-label">Your Subject</span>
      <input type="text" class="subject-input" id="subjectInput" placeholder="What do you want to create? (e.g., a mountain landscape)" value="${subject}">
    </div>
  `;
}

function renderReviewFooter() {
  return `
    <button class="btn btn-ghost" id="backReviewBtn">← Back</button>
    <button class="btn btn-secondary" id="regenerateReviewBtn">Regenerate</button>
    <button class="btn btn-primary" id="generateReviewBtn">Generate →</button>
  `;
}

function setupReviewStepListeners() {
  // Back button
  document.getElementById('backReviewBtn').addEventListener('click', () => {
    stylePanelState.step = 'select';
    renderStylePanel();
  });

  // Regenerate button
  document.getElementById('regenerateReviewBtn').addEventListener('click', () => {
    stylePanelState.step = 'analyze';
    renderStylePanel();
  });

  // Generate button
  document.getElementById('generateReviewBtn').addEventListener('click', () => {
    stylePanelState.subject = document.getElementById('subjectInput').value.trim();
    stylePanelState.step = 'generate';
    renderStylePanel();
  });

  // Alternative prompt selection
  document.querySelectorAll('.alt-prompt').forEach(el => {
    el.addEventListener('click', () => {
      const index = parseInt(el.dataset.index);
      stylePanelState.autoPrompt = stylePanelState.alternativePrompts[index];
      document.getElementById('promptText').textContent = `"${stylePanelState.autoPrompt}"`;
      document.getElementById('promptText').dataset.original = stylePanelState.autoPrompt;
    });
  });

  // Prompt editing
  const promptText = document.getElementById('promptText');
  let isEditing = false;
  
  promptText.addEventListener('click', (e) => {
    if (e.target.classList.contains('edit-icon')) {
      togglePromptEdit();
    }
  });

  promptText.addEventListener('dblclick', togglePromptEdit);

  function togglePromptEdit() {
    isEditing = !isEditing;
    promptText.classList.toggle('editing', isEditing);
    promptText.contentEditable = isEditing;
    
    if (isEditing) {
      promptText.focus();
      // Move cursor to end
      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(promptText);
      range.collapse(false);
      sel.removeAllRanges();
      sel.addRange(range);
    } else {
      // Save edited prompt
      stylePanelState.autoPrompt = promptText.textContent.trim().replace(/^"|"$/g, '');
      promptText.dataset.original = stylePanelState.autoPrompt;
    }
  }

  promptText.addEventListener('blur', () => {
    if (isEditing) togglePromptEdit();
  });

  promptText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      togglePromptEdit();
    }
    if (e.key === 'Escape') {
      // Reset to original
      stylePanelState.autoPrompt = promptText.dataset.original;
      promptText.textContent = `"${stylePanelState.autoPrompt}"`;
      togglePromptEdit();
    }
  });

  // Subject input
  document.getElementById('subjectInput').addEventListener('input', (e) => {
    stylePanelState.subject = e.target.value.trim();
  });

  // Add tag button
  document.getElementById('addTagBtn').addEventListener('click', () => {
    const tag = prompt('Enter a style tag:');
    if (tag && tag.trim()) {
      const tagsContainer = document.getElementById('styleTags');
      const addBtn = document.getElementById('addTagBtn');
      const newTag = document.createElement('span');
      newTag.textContent = tag.trim();
      newTag.className = 'removable';
      newTag.addEventListener('click', () => newTag.remove());
      tagsContainer.insertBefore(newTag, addBtn);
    }
  });

  // Tag removal
  document.querySelectorAll('.style-tags span.removable').forEach(tag => {
    tag.addEventListener('click', () => tag.remove());
  });
}

async function generateImage() {
  // Clear any existing progress interval
  if (genProgressInterval) {
    clearInterval(genProgressInterval);
    genProgressInterval = null;
  }

  const { autoPrompt, subject, referenceImage, referenceType, strength, metadata } = stylePanelState;
  const fullPrompt = subject ? `${autoPrompt}, ${subject}` : autoPrompt;

  // Client-side generation — simulate a successful result instead of calling localhost
  const seed = encodeURIComponent(fullPrompt.slice(0, 80));
  stylePanelState.generatedImageUrl = `https://image.pollinations.ai/prompt/${seed}?width=512&height=512&seed=${Date.now()}`;
  stylePanelState.step = 'result';
  renderStylePanel();
}

function renderGenerateStep() {
  return `
    <div class="step-indicator">Step 4 of 5</div>
    
    <div class="gen-preview" id="genPreview">
      <span style="font-size:0.875rem; color:rgba(0,0,0,0.5);">Generating...</span>
    </div>

    <div class="gen-progress-bar">
      <div class="fill" id="genProgress" style="width: 0%;"></div>
    </div>

    <div class="gen-status" id="genStatus">Initializing generation...</div>

    <div class="gen-meta">
      <div class="meta-row">
        <span>🎨 Style: ${stylePanelState.metadata?.artisticStyle || 'Unknown'} (${stylePanelState.strength}%)</span>
      </div>
      <div class="meta-row">
        <span>📝 Type: ${stylePanelState.referenceType}</span>
      </div>
      <div class="prompt-preview" id="promptPreview">"${stylePanelState.autoPrompt}${stylePanelState.subject ? ', ' + stylePanelState.subject : ''}"</div>
    </div>
  `;
}

function renderGenerateFooter() {
  return `
    <button class="btn btn-ghost" id="cancelGenerateBtn">Cancel Generation</button>
  `;
}

// Simulate generation progress
let genProgressInterval;
function setupGenerateStepListeners() {
  document.getElementById('cancelGenerateBtn').addEventListener('click', () => {
    clearInterval(genProgressInterval);
    closeStylePanel();
  });

  // Simulate progress
  let progress = 0;
  const statusMessages = [
    'Initializing generation...',
    'Analyzing style reference...',
    'Applying style to composition...',
    'Refining details...',
    'Finalizing image...'
  ];
  
  genProgressInterval = setInterval(() => {
    // Safety check: elements might have been removed if generation completed
    const progressEl = document.getElementById('genProgress');
    const statusEl = document.getElementById('genStatus');
    const previewEl = document.getElementById('genPreview');
    if (!progressEl || !statusEl || !previewEl) {
      clearInterval(genProgressInterval);
      return;
    }
    
    progress += Math.random() * 15 + 5;
    if (progress > 100) progress = 100;
    
    progressEl.style.width = `${progress}%`;
    const msgIndex = Math.min(Math.floor(progress / 20), statusMessages.length - 1);
    statusEl.textContent = statusMessages[msgIndex];
    
    // Update preview with a blur of the reference
    if (progress > 30) {
      previewEl.style.backgroundImage = `url(images/${stylePanelState.referenceImage.filename})`;
      previewEl.innerHTML = '';
    }
    
    if (progress >= 100) {
      clearInterval(genProgressInterval);
      // Generation complete, move to result step
      setTimeout(() => {
        stylePanelState.step = 'result';
        renderStylePanel();
      }, 500);
    }
  }, 800);
}

function renderResultStep() {
  const { referenceImage, generatedImageUrl, autoPrompt, subject, referenceType, strength, metadata } = stylePanelState;
  return `
    <div class="step-indicator">Step 5 of 5 — Complete</div>
    
    <div class="result-comparison">
      <div class="result-box">
        <div class="img">
          <img src="images/${referenceImage.filename}" alt="${referenceImage.prompt}">
        </div>
        <div class="label">Style From</div>
      </div>
      <div class="result-box">
        <div class="img">
          <img src="${generatedImageUrl}" alt="Generated result" onerror="this.style.display='none'; this.parentElement.textContent='🖼️'">
        </div>
        <div class="label">Your Creation</div>
      </div>
    </div>

    <div class="result-summary">
      <div class="style-applied">🎨 Style Applied: ${metadata?.artisticStyle || 'Custom'} (${strength}%)</div>
      <div class="prompt-used">"${autoPrompt}${subject ? ', ' + subject : ''}"</div>
    </div>

    <div class="result-actions">
      <span id="likeBtn">👍 Like</span>
      <span id="saveBtn">💾 Save</span>
      <span id="shareBtn">📤 Share</span>
    </div>
  `;
}

function renderResultFooter() {
  return `
    <button class="btn btn-ghost" id="adjustStyleBtn">← Adjust Style</button>
    <button class="btn btn-secondary" id="tryAgainBtn">Try Again</button>
    <button class="btn btn-primary" id="doneBtn">Done</button>
  `;
}

function setupResultStepListeners() {
  document.getElementById('adjustStyleBtn').addEventListener('click', () => {
    stylePanelState.step = 'review';
    renderStylePanel();
  });

  document.getElementById('tryAgainBtn').addEventListener('click', () => {
    stylePanelState.step = 'generate';
    renderStylePanel();
  });

  document.getElementById('doneBtn').addEventListener('click', closeStylePanel);

  document.getElementById('likeBtn').addEventListener('click', () => {
    alert('Added to favorites!');
  });

  document.getElementById('saveBtn').addEventListener('click', () => {
    const link = document.createElement('a');
    link.href = stylePanelState.generatedImageUrl;
    link.download = `apollo-style-${Date.now()}.jpg`;
    link.click();
  });

  document.getElementById('shareBtn').addEventListener('click', () => {
    if (navigator.share) {
      navigator.share({
        title: 'Apollo Style Generation',
        text: `Generated with style: ${stylePanelState.metadata?.artisticStyle}`,
        url: stylePanelState.generatedImageUrl
      });
    } else {
      navigator.clipboard.writeText(stylePanelState.generatedImageUrl);
      alert('Link copied to clipboard!');
    }
  });
}

function renderErrorStep() {
  const { error } = stylePanelState;
  return `
    <div class="step-indicator" style="background: var(--error-soft); color: var(--error); border-color: var(--error);">Error State</div>
    
    <div class="error-state">
      <div class="icon">⚠️</div>
      <div class="title">${error?.error || 'Style Analysis Failed'}</div>
      <div class="desc">${error?.message || 'We couldn\'t automatically analyze this image\'s style. Choose one of the options below to continue.'}</div>
      <div class="error-options" id="errorOptions">
        ${error?.fallbackOptions?.map(opt => `
          <div class="error-option" data-action="${opt.id}">
            <div>${opt.label}</div>
            <div class="opt-desc">${opt.description}</div>
          </div>
        `).join('') || ''}
      </div>
    </div>
  `;
}

function setupErrorStepListeners() {
  document.querySelectorAll('.error-option').forEach(el => {
    el.addEventListener('click', () => {
      const action = el.dataset.action;
      switch (action) {
        case 'describe':
          // Switch to review step with empty extracted style for manual entry
          stylePanelState.extractedStyle = '';
          stylePanelState.autoPrompt = '';
          stylePanelState.alternativePrompts = [];
          stylePanelState.step = 'review';
          renderStylePanel();
          break;
        case 'direct':
          // Use as direct reference - go to generate with referenceType 'both'
          stylePanelState.referenceType = 'both';
          stylePanelState.step = 'generate';
          renderStylePanel();
          break;
        case 'retry':
          closeStylePanel();
          break;
      }
    });
  });
}

// Event listeners
function setupEventListeners() {
  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => filterGallery(btn.dataset.filter));
  });

  // Search input
  const searchInput = document.getElementById('searchInput');
  const searchClear = document.getElementById('searchClear');
  
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value.trim();
      applyFilters();
    });
    
    // Clear search on Escape key
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        searchInput.value = '';
        currentSearchQuery = '';
        applyFilters();
        searchInput.blur();
      }
    });
  }
  
  if (searchClear) {
    searchClear.addEventListener('click', () => {
      searchInput.value = '';
      currentSearchQuery = '';
      applyFilters();
      searchInput.focus();
    });
  }

  // Lightbox controls
  document.getElementById('lightboxClose').addEventListener('click', closeLightbox);
  document.getElementById('lightboxPrev').addEventListener('click', () => navigateLightbox(-1));
  document.getElementById('lightboxNext').addEventListener('click', () => navigateLightbox(1));

  // Lightbox background click to close
  document.getElementById('lightbox').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeLightbox();
  });

  // Style panel close
  document.getElementById('stylePanelClose').addEventListener('click', closeStylePanel);
  document.getElementById('stylePanelOverlay').addEventListener('click', closeStylePanel);

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    // Lightbox navigation
    if (!document.getElementById('lightbox').hidden) {
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
      return;
    }

    // Style panel navigation
    if (!document.getElementById('stylePanel').hidden) {
      if (e.key === 'Escape') {
        closeStylePanel();
        return;
      }
      // Enter to continue/generate
      if (e.key === 'Enter' && !e.shiftKey && !e.target.matches('input, textarea, [contenteditable]')) {
        const continueBtn = document.getElementById('continueSelectBtn');
        const generateBtn = document.getElementById('generateReviewBtn');
        if (continueBtn) continueBtn.click();
        else if (generateBtn) generateBtn.click();
      }
      // Number keys for alternative prompts
      if (e.key >= '1' && e.key <= '3' && stylePanelState.step === 'review') {
        const altPrompts = document.querySelectorAll('.alt-prompt');
        const idx = parseInt(e.key) - 1;
        if (altPrompts[idx]) altPrompts[idx].click();
      }
      // Up/Down for strength adjustment
      if ((e.key === 'ArrowUp' || e.key === 'ArrowDown') && stylePanelState.step === 'select') {
        const slider = document.getElementById('strengthSlider');
        if (document.activeElement === slider) return; // Let slider handle it
        e.preventDefault();
        const change = e.key === 'ArrowUp' ? 5 : -5;
        const newVal = Math.max(0, Math.min(100, stylePanelState.strength + change));
        stylePanelState.strength = newVal;
        slider.style.left = `${newVal}%`;
        slider.setAttribute('aria-valuenow', newVal);
        document.querySelector('.strength-value').textContent = `${newVal}%`;
      }
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

// Script loads at end of <body> — DOM is guaranteed ready, init immediately
initGallery();