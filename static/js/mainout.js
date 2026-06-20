// AssetLinkAfrica Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle
  const hamburger = document.querySelector('.hamburger');
  const navMenu = document.querySelector('.nav-menu');
  
  if (hamburger) {
    hamburger.addEventListener('click', function() {
      navMenu.classList.toggle('active');
    });
  }

  // Search form handler
  const searchForm = document.getElementById('searchForm');
  if (searchForm) {
    searchForm.addEventListener('submit', function(e) {
      e.preventDefault();
      handleSearch();
    });
  }

  // Filter listings on featured section
  const assetType = document.getElementById('assetType');
  const transactionType = document.getElementById('transactionType');
  
  if (assetType) {
    assetType.addEventListener('change', filterListings);
  }
  if (transactionType) {
    transactionType.addEventListener('change', filterListings);
  }
});

// Handle search functionality
function handleSearch() {
  const assetType = document.getElementById('assetType')?.value || 'all';
  const transactionType = document.getElementById('transactionType')?.value || 'all';
  const location = document.getElementById('location')?.value || '';
  const priceRange = document.getElementById('priceRange')?.value || 'all';

  // Build query string
  const params = new URLSearchParams();
  if (assetType !== 'all') params.append('type', assetType);
  if (transactionType !== 'all') params.append('transaction', transactionType);
  if (location) params.append('location', location);
  if (priceRange !== 'all') params.append('price', priceRange);

  // Redirect to listings page with filters
  window.location.href = `/listings/?${params.toString()}`;
}

// Filter featured listings
function filterListings() {
  const assetType = document.getElementById('assetType')?.value || 'all';
  const transactionType = document.getElementById('transactionType')?.value || 'all';
  const cards = document.querySelectorAll('.listing-card');

  cards.forEach(card => {
    let show = true;
    
    if (assetType !== 'all' && card.dataset.type !== assetType) {
      show = false;
    }
    
    if (transactionType !== 'all' && card.dataset.transaction !== transactionType) {
      show = false;
    }

    card.style.display = show ? 'block' : 'none';
  });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});
