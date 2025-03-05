// Main JavaScript for Chess Tournament Explorer

document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const monthSelect = document.getElementById('month');
    const yearSelect = document.getElementById('year');
    const categorySelect = document.getElementById('category');
    const searchInput = document.getElementById('search-input');
    const searchClearBtn = document.getElementById('search-clear-btn');
    const searchButton = document.getElementById('search-btn');
    const tournamentsContainer = document.getElementById('tournaments-container');
    const tournamentsList = document.getElementById('tournaments-list');
    const loadingIndicator = document.getElementById('loading');
    const noResultsMessage = document.getElementById('no-results');
    const tournamentCardTemplate = document.getElementById('tournament-card-template');
    const paginationContainer = document.getElementById('pagination-container');
    const paginationInfo = document.getElementById('pagination-info');
    const pageNumbers = document.getElementById('page-numbers');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageNumberTemplate = document.getElementById('page-number-template');

    // State variables
    let currentPage = 1;
    let totalPages = 1;
    let pageSize = 12;
    let currentFilters = {};

    // Initialize the application
    init();

    // Initialize the application
    async function init() {
        // Load filter options
        await Promise.all([
            loadMonths(),
            loadYears(),
            loadCategories()
        ]);

        // Load initial tournament data
        await loadTournaments();

        // Set up event listeners
        searchButton.addEventListener('click', handleSearch);
        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });
        searchClearBtn.addEventListener('click', clearSearch);
        prevPageBtn.addEventListener('click', goToPrevPage);
        nextPageBtn.addEventListener('click', goToNextPage);
    }

    // Clear search field
    function clearSearch() {
        searchInput.value = '';
        if (currentFilters.search) {
            delete currentFilters.search;
            handleSearch();
        }
    }

    // Load months for the filter
    async function loadMonths() {
        try {
            const response = await fetch('/api/months');
            const data = await response.json();
            
            if (data.status === 'success' && Array.isArray(data.data)) {
                // Clear existing options except the default
                clearSelectOptions(monthSelect);
                
                // Add month options
                data.data.forEach(month => {
                    const option = document.createElement('option');
                    option.value = month;
                    option.textContent = month;
                    monthSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading months:', error);
        }
    }

    // Load years for the filter
    async function loadYears() {
        try {
            const response = await fetch('/api/years');
            const data = await response.json();
            
            if (data.status === 'success' && Array.isArray(data.data)) {
                // Clear existing options except the default
                clearSelectOptions(yearSelect);
                
                // Add year options
                data.data.forEach(year => {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    yearSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading years:', error);
        }
    }

    // Load categories for the filter
    async function loadCategories() {
        try {
            const response = await fetch('/api/categories');
            const data = await response.json();
            
            if (data.status === 'success' && Array.isArray(data.data)) {
                // Clear existing options except the default
                clearSelectOptions(categorySelect);
                
                // Add category options
                data.data.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    categorySelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    // Clear select options except the first one (default)
    function clearSelectOptions(selectElement) {
        const defaultOption = selectElement.options[0];
        selectElement.innerHTML = '';
        selectElement.appendChild(defaultOption);
    }

    // Handle search button click
    async function handleSearch() {
        // Reset to first page when searching
        currentPage = 1;
        
        // Update filters
        currentFilters = {
            month: monthSelect.value,
            year: yearSelect.value,
            category: categorySelect.value,
        };
        
        // Add search query if not empty
        const searchQuery = searchInput.value.trim();
        if (searchQuery) {
            currentFilters.search = searchQuery;
        }
        
        // Load tournaments with new filters
        await loadTournaments(currentFilters);
    }

    // Go to previous page
    async function goToPrevPage() {
        if (currentPage > 1) {
            currentPage--;
            await loadTournaments(currentFilters);
        }
    }

    // Go to next page
    async function goToNextPage() {
        if (currentPage < totalPages) {
            currentPage++;
            await loadTournaments(currentFilters);
        }
    }

    // Go to specific page
    async function goToPage(page) {
        if (page >= 1 && page <= totalPages) {
            currentPage = page;
            await loadTournaments(currentFilters);
        }
    }

    // Load tournament data with optional filters
    async function loadTournaments(filters = {}) {
        try {
            // Show loading indicator
            showLoading(true);
            
            // Build query string from filters
            const queryParams = new URLSearchParams();
            
            // Add all filters to query params
            Object.entries(filters).forEach(([key, value]) => {
                if (value) queryParams.append(key, value);
            });
            
            // Add pagination params
            queryParams.append('page', currentPage);
            queryParams.append('page_size', pageSize);
            
            // Fetch tournaments
            const url = `/api/tournaments${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
            const response = await fetch(url);
            const data = await response.json();
            
            // Clear current tournaments
            tournamentsList.innerHTML = '';
            
            if (data.status === 'success') {
                // Update pagination information
                if (data.meta) {
                    updatePagination(data.meta);
                }
                
                // Display tournaments
                if (Array.isArray(data.data) && data.data.length > 0) {
                    displayTournaments(data.data);
                    showNoResults(false);
                } else {
                    showNoResults(true);
                }
            } else {
                showNoResults(true);
            }
        } catch (error) {
            console.error('Error loading tournaments:', error);
            showNoResults(true);
        } finally {
            // Hide loading indicator
            showLoading(false);
        }
    }

    // Update pagination controls
    function updatePagination(meta) {
        const total = meta.total;
        currentPage = meta.page;
        pageSize = meta.page_size;
        totalPages = meta.pages;
        
        // Update info text
        const startItem = (currentPage - 1) * pageSize + 1;
        const endItem = Math.min(currentPage * pageSize, total);
        paginationInfo.textContent = `Showing ${startItem}-${endItem} of ${total} tournaments`;
        
        // Enable/disable prev/next buttons
        prevPageBtn.disabled = currentPage <= 1;
        nextPageBtn.disabled = currentPage >= totalPages;
        
        // Generate page number buttons
        pageNumbers.innerHTML = '';
        
        // Determine which page numbers to show
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        // Adjust start page if necessary
        if (endPage - startPage < 4 && startPage > 1) {
            startPage = Math.max(1, endPage - 4);
        }
        
        // Add first page and ellipsis if necessary
        if (startPage > 1) {
            addPageNumberButton(1);
            if (startPage > 2) {
                addEllipsis();
            }
        }
        
        // Add page number buttons
        for (let i = startPage; i <= endPage; i++) {
            addPageNumberButton(i);
        }
        
        // Add ellipsis and last page if necessary
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                addEllipsis();
            }
            addPageNumberButton(totalPages);
        }
    }

    // Add page number button
    function addPageNumberButton(pageNum) {
        const pageButton = document.importNode(pageNumberTemplate.content, true).querySelector('button');
        pageButton.textContent = pageNum;
        pageButton.classList.toggle('bg-blue-500', pageNum === currentPage);
        pageButton.classList.toggle('text-white', pageNum === currentPage);
        pageButton.addEventListener('click', () => goToPage(pageNum));
        pageNumbers.appendChild(pageButton);
    }

    // Add ellipsis to pagination
    function addEllipsis() {
        const ellipsis = document.createElement('span');
        ellipsis.textContent = '...';
        ellipsis.className = 'px-3 py-1 text-gray-500';
        pageNumbers.appendChild(ellipsis);
    }

    // Display tournaments in the list
    function displayTournaments(tournaments) {
        tournaments.forEach(tournament => {
            // Clone the template
            const tournamentCard = document.importNode(tournamentCardTemplate.content, true).querySelector('.tournament-card');
            
            // Fill in the tournament details
            tournamentCard.querySelector('.tournament-name').textContent = tournament.name;
            
            // Set date info
            const dateText = `${tournament.month} ${tournament.year}`;
            tournamentCard.querySelector('.tournament-date').textContent = dateText;
            
            // Set location if available
            if (tournament.city || tournament.country) {
                const locationParts = [];
                if (tournament.city) locationParts.push(tournament.city);
                if (tournament.country) locationParts.push(tournament.country);
                tournamentCard.querySelector('.tournament-location').textContent = locationParts.join(', ');
            } else {
                tournamentCard.querySelector('.tournament-location').textContent = 'Location not specified';
            }
            
            // Set tournament type badge if available
            const typeBadge = tournamentCard.querySelector('.tournament-type-badge');
            if (tournament.tournament_type) {
                typeBadge.textContent = tournament.tournament_type;
            } else {
                typeBadge.style.display = 'none';
            }
            
            // Set category badge if available
            const categoryBadge = tournamentCard.querySelector('.tournament-category-badge');
            if (tournament.category) {
                categoryBadge.textContent = tournament.category;
            } else {
                categoryBadge.style.display = 'none';
            }
            
            // Set website URL if available
            const urlLink = tournamentCard.querySelector('.tournament-url');
            if (tournament.website_url) {
                urlLink.href = tournament.website_url;
            } else {
                urlLink.href = '#';
            }
            
            // Add the card to the list
            tournamentsList.appendChild(tournamentCard);
        });
    }

    // Show or hide loading indicator
    function showLoading(show) {
        loadingIndicator.classList.toggle('hidden', !show);
    }

    // Show or hide no results message
    function showNoResults(show) {
        noResultsMessage.classList.toggle('hidden', !show);
    }
}); 