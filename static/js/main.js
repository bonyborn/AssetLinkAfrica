// ======================================
// ASSETLINKAFRICA MAIN JAVASCRIPT FILE
// ======================================

document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const assetType = document.getElementById('assetType').value;
            const transactionType = document.getElementById('transactionType').value;
            const location = document.getElementById('location').value;
            const priceRange = document.getElementById('priceRange').value;
            
            // Store search params in localStorage
            localStorage.setItem('searchParams', JSON.stringify({
                assetType, transactionType, location, priceRange
            }));
            
            // Redirect to listings page
            window.location.href = 'listings.html';
        });
    }

    // Load search params on listings page
    if (window.location.pathname.includes('listings.html')) {
        const searchParams = localStorage.getItem('searchParams');
        if (searchParams) {
            const params = JSON.parse(searchParams);
            // Apply filters
            if (document.getElementById('filterAssetType')) {
                document.getElementById('filterAssetType').value = params.assetType;
                document.getElementById('filterTransactionType').value = params.transactionType;
                document.getElementById('filterLocation').value = params.location;
                document.getElementById('filterPriceRange').value = params.priceRange;
                
                // Trigger filter
                filterListings(params.assetType, params.transactionType, params.priceRange, params.location);
            }
            localStorage.removeItem('searchParams');
        }
    }

    // Filter functionality
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const assetType = document.getElementById('filterAssetType').value;
            const transactionType = document.getElementById('filterTransactionType').value;
            const priceRange = document.getElementById('filterPriceRange').value;
            const location = document.getElementById('filterLocation').value;
            
            filterListings(assetType, transactionType, priceRange, location);
        });
        
        filterForm.addEventListener('reset', () => {
            setTimeout(() => {
                filterListings('all', 'all', 'all', '');
            }, 100);
        });
    }

    // Filter featured listings
    const assetType = document.getElementById('assetType');
    const transactionType = document.getElementById('transactionType');
    
    if (assetType) {
        assetType.addEventListener('change', filterListings);
    }
    if (transactionType) {
        transactionType.addEventListener('change', filterListings);
    }

    // Sort functionality
    const sortBy = document.getElementById('sortBy');
    if (sortBy) {
        sortBy.addEventListener('change', () => {
            const sortValue = sortBy.value;
            const listingsGrid = document.querySelector('.listings-grid');
            const listings = Array.from(document.querySelectorAll('.listing-card'));
            
            listings.sort((a, b) => {
                if (sortValue === 'price-low') {
                    return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                } else if (sortValue === 'price-high') {
                    return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
                }
                return 0;
            });
            
            listings.forEach(listing => listingsGrid.appendChild(listing));
        });
    }

    // Booking form handling
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        const daysInput = bookingForm.querySelector('input[type="number"]');
        const totalSpan = document.querySelector('.total-amount');
        const pricePerDay = 5000; // This should come from the listing data
        
        function updateTotal() {
            if (daysInput && totalSpan) {
                const days = daysInput.value;
                const total = days * pricePerDay;
                totalSpan.textContent = `Ksh${total}`;
            }
        }
        
        if (daysInput) daysInput.addEventListener('input', updateTotal);
        
        bookingForm.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Booking request sent! You will receive a confirmation email shortly.');
            bookingForm.reset();
            if (totalSpan) totalSpan.textContent = 'Ksh5000';
        });
    }

    // Dashboard tab switching
    if (window.location.pathname.includes('dashboard.html')) {
        // Set active tab from localStorage or default
        const activeTab = localStorage.getItem('activeDashboardTab') || 'overview';
        
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.dataset.tab === activeTab) {
                link.classList.add('active');
            }
            
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabId = link.dataset.tab;
                
                // Update active states
                document.querySelectorAll('.nav-link').forEach(nav => nav.classList.remove('active'));
                link.classList.add('active');
                
                document.querySelectorAll('.dashboard-tab').forEach(tab => tab.classList.remove('active'));
                document.getElementById(tabId).classList.add('active');
                
                // Save to localStorage
                localStorage.setItem('activeDashboardTab', tabId);
            });
        });
    }

    // Modal functionality
    const modal = document.getElementById('addListingModal');
    const btn = document.querySelector('.btn-add-listing');
    const span = document.getElementsByClassName('close')[0];

    function showAddListingModal() {
        if (modal) modal.style.display = 'block';
    }

    if (btn) {
        btn.onclick = showAddListingModal;
    }

    if (span) {
        span.onclick = function() {
            if (modal) modal.style.display = 'none';
        }
    }

    window.onclick = function(event) {
        if (modal && event.target == modal) {
            modal.style.display = 'none';
        }
    }

    // Form validation
    function validateForm(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.style.borderColor = '#f44336';
                isValid = false;
            } else {
                input.style.borderColor = '#ddd';
            }
        });
        
        return isValid;
    }

    // Add validation to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!validateForm(form)) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    });

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

}); // End DOMContentLoaded

// ======================================
// UTILITY FUNCTIONS (Outside DOMContentLoaded)
// ======================================

// Filter listings helper function
function filterListings(assetType, transactionType, priceRange, location) {
    const listings = document.querySelectorAll('.listing-card');
    
    listings.forEach(listing => {
        let show = true;
        const type = listing.dataset.type;
        const transaction = listing.dataset.transaction;
        const price = parseFloat(listing.dataset.price);
        const listingLocation = listing.querySelector('.location')?.textContent.toLowerCase() || '';
        
        if (assetType !== 'all' && type !== assetType) show = false;
        if (transactionType !== 'all' && transaction !== transactionType) show = false;
        
        if (priceRange !== 'all') {
            const [min, max] = priceRange.split('-');
            if (max) {
                if (price < parseFloat(min) || price > parseFloat(max)) show = false;
            } else {
                if (price < parseFloat(min.replace('+', ''))) show = false;
            }
        }
        
        if (location && !listingLocation.includes(location.toLowerCase())) show = false;
        
        listing.style.display = show ? 'block' : 'none';
    });
}

// Initialize login/register forms
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const tabs = document.querySelectorAll('.tab-btn');

if (loginForm && registerForm) {
    loginForm.classList.add('active');
    registerForm.classList.remove('active');
    tabs[0].classList.add('active');
    tabs[1].classList.remove('active');
}

function showRegister() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabs = document.querySelectorAll('.tab-btn');
    
    if (loginForm && registerForm) {
        loginForm.classList.remove('active');
        registerForm.classList.add('active');
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
    }
}

function handleLogin(event) {
    if (event) event.preventDefault();
    // Simulate login - redirect to dashboard
    window.location.href = 'dashboard.html';
}

function handleRegister(event) {
    if (event) event.preventDefault();
    alert('Registration successful! Please login.');
    showLogin();
}

function togglePassword(element) {
    const passwordInput = element.previousElementSibling;
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        element.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        passwordInput.type = 'password';
        element.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

function changeImage(element) {
    const mainImage = document.getElementById('mainImage');
    if (mainImage) {
        mainImage.src = element.src;
        document.querySelectorAll('.thumbnail').forEach(thumb => {
            thumb.classList.remove('active');
        });
        element.classList.add('active');
    }
}

function showLease() {
    const leasePrice = document.querySelector('.lease-price');
    const salePrice = document.querySelector('.sale-price');
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    
    if (leasePrice && salePrice) {
        leasePrice.classList.remove('hidden');
        salePrice.classList.add('hidden');
        if (toggleBtns[0]) toggleBtns[0].classList.add('active');
        if (toggleBtns[1]) toggleBtns[1].classList.remove('active');
    }
}

function showSale() {
    const leasePrice = document.querySelector('.lease-price');
    const salePrice = document.querySelector('.sale-price');
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    
    if (leasePrice && salePrice) {
        leasePrice.classList.add('hidden');
        salePrice.classList.remove('hidden');
        if (toggleBtns[0]) toggleBtns[0].classList.remove('active');
        if (toggleBtns[1]) toggleBtns[1].classList.add('active');
    }
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

    // Initialize login/register forms
    const loginFormInit = document.getElementById('loginForm');
    const registerFormInit = document.getElementById('registerForm');
    const tabsInit = document.querySelectorAll('.tab-btn');

    if (loginFormInit && registerFormInit) {
        loginFormInit.classList.add('active');
        registerFormInit.classList.remove('active');
        if (tabsInit[0]) tabsInit[0].classList.add('active');
        if (tabsInit[1]) tabsInit[1].classList.remove('active');
    }

console.log('AssetLinkAfrica frontend loaded successfully!');