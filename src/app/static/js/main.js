// Main JavaScript for Chess Tournament Explorer

document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const monthSelect = document.getElementById('month');
    const yearSelect = document.getElementById('year');
    const categorySelect = document.getElementById('category');
    const searchButton = document.getElementById('search-btn');
    const tournamentsContainer = document.getElementById('tournaments-container');
    const tournamentsList = document.getElementById('tournaments-list');
    const loadingIndicator = document.getElementById('loading');
    const noResultsMessage = document.getElementById('no-results');
    const tournamentCardTemplate = document.getElementById('tournament-card-template');

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
        await loadTournaments({
            month: monthSelect.value,
            year: yearSelect.value,
            category: categorySelect.value
        });
    }

    // Load tournament data with optional filters
    async function loadTournaments(filters = {}) {
        try {
            // Show loading indicator
            showLoading(true);
            
            // Build query string from filters
            const queryParams = new URLSearchParams();
            Object.entries(filters).forEach(([key, value]) => {
                if (value) queryParams.append(key, value);
            });
            
            // Fetch tournaments
            const url = `/api/tournaments${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
            const response = await fetch(url);
            const data = await response.json();
            
            // Clear current tournaments
            tournamentsList.innerHTML = '';
            
            if (data.status === 'success' && Array.isArray(data.data)) {
                // Display tournaments
                if (data.data.length > 0) {
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