import os
import logging
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from datetime import datetime
from dotenv import load_dotenv

from ..models.tournament import Tournament

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SchachinterScraper:
    """
    Service class for scraping the Schachinter.net website.
    This is a simplified version that uses requests and BeautifulSoup directly.
    """
    
    def __init__(self):
        """
        Initialize the scraper with configuration from environment variables.
        """
        self.base_url = os.getenv("TARGET_URL", "https://www.schachinter.net/")
        self.user_agent = os.getenv("USER_AGENT", "Mozilla/5.0")
        
        # Set up headers for requests
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        logger.info("Initialized simple scraper with requests and BeautifulSoup")
    
    async def fetch_page(self) -> Optional[Dict[str, Any]]:
        """
        Fetch HTML content from Schachinter.net using requests.
        
        Returns:
            Dictionary with page content or None if request failed
        """
        try:
            logger.info(f"Fetching {self.base_url} using requests")
            
            # Make the request
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            logger.info(f"Successfully fetched {self.base_url}, content length: {len(html_content)}")
            
            # Extract links
            soup = BeautifulSoup(html_content, 'lxml')
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            
            # Return in a format similar to what we'd expect from crawl4ai
            return {
                "status": "completed",
                "pages": [{
                    "url": self.base_url,
                    "html": html_content,
                    "text": soup.get_text(),
                    "links": links
                }]
            }
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {self.base_url}: {str(e)}")
            return None
    
    async def parse_tournaments(self, crawl_result: Dict[str, Any]) -> List[Tournament]:
        """
        Parse the page content to extract tournament information.
        
        Args:
            crawl_result: Dictionary containing page content
            
        Returns:
            List of Tournament objects
        """
        if not crawl_result or "pages" not in crawl_result or not crawl_result["pages"]:
            logger.error("Invalid or empty crawl result")
            return []
        
        tournaments = []
        
        # Get the main page content
        main_page = next((page for page in crawl_result["pages"] if page["url"] == self.base_url), None)
        if not main_page:
            logger.error("Main page not found in crawl result")
            return []
        
        html_content = main_page.get("html", "")
        if not html_content:
            logger.error("No HTML content found in crawl result")
            return []
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract the current year from the website
        current_year = datetime.now().year
        
        # Try to find year information on the page
        year_match = re.search(r'(\d{4})', html_content)
        if year_match:
            current_year = int(year_match.group(1))
        
        # Month sections - these are the main containers for tournament information
        month_blocks = self._extract_month_blocks(soup)
        
        for month_name, month_content in month_blocks.items():
            # Extract tournament names within this month
            tournament_names = self._extract_tournament_names(month_content)
            
            for tournament_name in tournament_names:
                # Create tournament object
                tournament = Tournament(
                    name=tournament_name,
                    month=month_name,
                    year=current_year,
                    is_international=self._determine_if_international(tournament_name),
                    city=self._extract_city(tournament_name),
                    country="Germany",  # Default, will be overridden if international
                    tournament_type=self._determine_tournament_type(tournament_name),
                    category=self._determine_category(tournament_name, month_content)
                )
                
                # If it's international, try to extract the country
                if tournament.is_international:
                    country = self._extract_country(tournament_name)
                    if country:
                        tournament.country = country
                
                tournaments.append(tournament)
        
        logger.info(f"Extracted {len(tournaments)} tournaments")
        return tournaments
    
    def _extract_month_blocks(self, soup: BeautifulSoup) -> Dict[str, BeautifulSoup]:
        """
        Extract content blocks for each month.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary mapping month names to their content blocks
        """
        month_blocks = {}
        
        # Look for month indicators - this is site-specific and needs analysis
        # Common German month names
        german_months = ["Januar", "Februar", "März", "April", "Mai", "Juni", 
                        "Juli", "August", "September", "Oktober", "November", "Dezember"]
        
        # Also look for abbreviated months
        english_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Find month sections based on text content
        for month in german_months + english_months:
            month_elements = soup.find_all(string=lambda text: text and month in text)
            for element in month_elements:
                parent = element.parent
                # Try to get the nearest content section
                section = self._find_section_for_month(parent, month)
                if section:
                    # Standardize month name to English
                    std_month = self._standardize_month_name(month)
                    month_blocks[std_month] = section
        
        return month_blocks
    
    def _find_section_for_month(self, element, month: str) -> Optional[BeautifulSoup]:
        """
        Find the content section for a given month starting from the element.
        
        Args:
            element: Starting element
            month: Month name to search for
            
        Returns:
            BeautifulSoup object representing the section, or None
        """
        # Try to find a parent div or section that contains this month
        current = element
        for _ in range(3):  # Look up to 3 levels up
            if current and current.find_all(text=True, recursive=True):
                return current
            if current:
                current = current.parent
        
        # If no clear section found, return the original element
        return element
    
    def _standardize_month_name(self, month: str) -> str:
        """
        Convert German or abbreviated month names to standard English names.
        
        Args:
            month: Month name in German or abbreviated form
            
        Returns:
            Standardized month name in English
        """
        month_mapping = {
            "Januar": "January",
            "Februar": "February", 
            "März": "March",
            "April": "April",
            "Mai": "May",
            "Juni": "June",
            "Juli": "July",
            "August": "August",
            "September": "September",
            "Oktober": "October",
            "November": "November",
            "Dezember": "December",
            "Jan": "January",
            "Feb": "February",
            "Mar": "March",
            "Apr": "April",
            "May": "May",
            "Jun": "June",
            "Jul": "July",
            "Aug": "August",
            "Sep": "September",
            "Oct": "October",
            "Nov": "November",
            "Dec": "December"
        }
        
        return month_mapping.get(month, month)
    
    def _extract_tournament_names(self, section: BeautifulSoup) -> List[str]:
        """
        Extract tournament names from a month section.
        
        Args:
            section: BeautifulSoup object of the month section
            
        Returns:
            List of tournament names
        """
        tournament_names = []
        
        # Look for typical tournament name patterns
        # Names are likely to be in links, strong/b tags, or headings
        for element in section.find_all(['a', 'strong', 'b', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = element.get_text(strip=True)
            if text and len(text) > 3 and text not in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                # Filter out month names themselves
                if not any(month in text for month in ["Januar", "Februar", "März", "April", "Mai", "Juni", 
                                                     "Juli", "August", "September", "Oktober", "November", "Dezember"]):
                    tournament_names.append(text)
        
        # Also look for text that might be tournament names based on pattern
        for element in section.find_all(text=True):
            text = element.strip()
            if text and len(text) > 10:  # Reasonably long text
                # Look for typical tournament name patterns
                if re.search(r'(Open|Championship|Tournament|Cup|Masters|Schach|Turnier)', text, re.IGNORECASE):
                    tournament_names.append(text)
        
        # Remove duplicates while preserving order
        seen = set()
        return [name for name in tournament_names if not (name in seen or seen.add(name))]
    
    def _determine_if_international(self, tournament_name: str) -> bool:
        """
        Determine if a tournament is international based on its name.
        
        Args:
            tournament_name: Name of the tournament
            
        Returns:
            True if the tournament appears to be international, False otherwise
        """
        international_keywords = [
            "International", "World", "European", "Europe", "FIDE", 
            "International", "Weltmeisterschaft", "Europameisterschaft"
        ]
        
        return any(keyword.lower() in tournament_name.lower() for keyword in international_keywords)
    
    def _extract_city(self, tournament_name: str) -> Optional[str]:
        """
        Extract the city from the tournament name if possible.
        
        Args:
            tournament_name: Name of the tournament
            
        Returns:
            City name or None if not found
        """
        # List of common German cities
        common_cities = [
            "Berlin", "Hamburg", "München", "Köln", "Frankfurt", "Stuttgart", 
            "Düsseldorf", "Leipzig", "Dortmund", "Essen", "Dresden", "Bremen",
            "Hannover", "Nürnberg", "Duisburg", "Bochum", "Wuppertal", "Bonn",
            "Mannheim", "Karlsruhe", "Münster", "Wiesbaden", "Augsburg"
        ]
        
        # Check if any of the common cities are in the tournament name
        for city in common_cities:
            if city in tournament_name:
                return city
        
        # Try to extract with regex patterns common for tournament naming
        city_match = re.search(r'in\s+([A-Z][a-zäöüß]+(?:\s+[A-Z][a-zäöüß]+)?)', tournament_name)
        if city_match:
            return city_match.group(1)
        
        return None
    
    def _extract_country(self, tournament_name: str) -> Optional[str]:
        """
        Extract the country from the tournament name for international tournaments.
        
        Args:
            tournament_name: Name of the tournament
            
        Returns:
            Country name or None if not found
        """
        # List of common European countries
        common_countries = [
            "Germany", "France", "Spain", "Italy", "Netherlands", "Belgium",
            "Austria", "Switzerland", "Denmark", "Sweden", "Norway", "Finland",
            "Poland", "Czech Republic", "Hungary", "Romania", "Bulgaria",
            "Greece", "Portugal", "Ireland", "UK", "United Kingdom"
        ]
        
        # Check if any of the common countries are in the tournament name
        for country in common_countries:
            if country in tournament_name:
                return country
        
        # Default to Germany for most tournaments
        return "Germany"
    
    def _determine_tournament_type(self, tournament_name: str) -> str:
        """
        Determine the type of tournament based on its name.
        
        Args:
            tournament_name: Name of the tournament
            
        Returns:
            Tournament type (Standard, Rapid, Blitz, etc.)
        """
        if re.search(r'(Rapid|Schnell)', tournament_name, re.IGNORECASE):
            return "Rapid"
        elif re.search(r'Blitz', tournament_name, re.IGNORECASE):
            return "Blitz"
        elif re.search(r'(Online|Internet)', tournament_name, re.IGNORECASE):
            return "Online"
        else:
            return "Standard"  # Default to standard
    
    def _determine_category(self, tournament_name: str, section: BeautifulSoup) -> str:
        """
        Determine the category of the tournament.
        
        Args:
            tournament_name: Name of the tournament
            section: BeautifulSoup section containing the tournament
            
        Returns:
            Tournament category (Open, Youth, Women, etc.)
        """
        name_lower = tournament_name.lower()
        if re.search(r'(junior|jugend|youth|u\d+)', name_lower):
            return "Youth"
        elif re.search(r'(women|frauen|damen)', name_lower):
            return "Women"
        elif re.search(r'(senior|senioren)', name_lower):
            return "Senior"
        elif re.search(r'(team|mannschaft|verein)', name_lower):
            return "Team"
        else:
            return "Open"  # Default to open
    
    async def scrape(self) -> List[Tournament]:
        """
        Main scraping method that orchestrates the entire scraping process.
        
        Returns:
            List of Tournament objects
        """
        logger.info(f"Starting to scrape {self.base_url}")
        
        # Step 1: Fetch the page
        crawl_result = await self.fetch_page()
        if not crawl_result:
            logger.error("Failed to fetch the main page")
            return []
        
        # Step 2: Parse the results
        tournaments = await self.parse_tournaments(crawl_result)
        logger.info(f"Scraping completed, found {len(tournaments)} tournaments")
        
        return tournaments 