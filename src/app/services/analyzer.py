import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import json
from anthropic import Anthropic
import re
from pydantic import BaseModel, Field

from ..models.tournament import Tournament

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class TournamentAnalysisResult(BaseModel):
    """Schema for tournament analysis result."""
    name: str = Field(..., description="Name of the tournament")
    month: str = Field(..., description="Month when the tournament takes place")
    year: int = Field(..., description="Year when the tournament takes place")
    is_international: bool = Field(..., description="Whether the tournament is international or national")
    city: Optional[str] = Field(None, description="City where the tournament takes place")
    country: Optional[str] = Field(None, description="Country where the tournament takes place")
    tournament_type: Optional[str] = Field(None, description="Type of tournament (Standard, Rapid, Blitz, etc.)")
    category: Optional[str] = Field(None, description="Category (Open, Women, Senior, Youth, etc.)")
    description: Optional[str] = Field(None, description="Additional information or description")


class TournamentAnalyzer:
    """
    Service class for analyzing tournament information using Anthropic.
    """
    
    def __init__(self):
        """
        Initialize the analyzer with API key from environment variables.
        """
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("Anthropic API key not set. AI analysis will not be available.")
        else:
            # Create Anthropic client with only the API key
            try:
                self.client = Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {str(e)}")
                logger.warning("AI analysis will not be available")
                self.api_key = None
            
            # Setup the prompt template
            self.prompt_template = """
            You are an expert in chess tournaments. You are tasked with analyzing information about a chess tournament to extract and infer detailed information.
            
            Here's what I know about the tournament:
            Name: {tournament_name}
            Month: {month}
            Year: {year}
            
            Please analyze this information and provide more details about the tournament.
            Infer the following:
            1. Whether the tournament is international or national
            2. The city where it takes place (if mentioned or can be inferred)
            3. The country (default to Germany unless clearly international)
            4. The type of tournament (Standard, Rapid, Blitz, etc.)
            5. The category (Open, Women, Senior, Youth, etc.)
            6. A brief description or any additional information that can be inferred
            
            Be precise and concise. If you can't infer something with reasonable confidence, don't guess.
            
            Return your analysis as valid JSON with the following schema:
            {{
                "name": string,
                "month": string,
                "year": integer,
                "is_international": boolean,
                "city": string or null,
                "country": string or null,
                "tournament_type": string or null,
                "category": string or null,
                "description": string or null
            }}
            
            Respond with ONLY the JSON, no explanations or additional text.
            """
    
    async def analyze_tournament(self, tournament: Tournament) -> Optional[Tournament]:
        """
        Analyze a tournament using Anthropic and enhance its information.
        
        Args:
            tournament: Tournament object to analyze
            
        Returns:
            Enhanced Tournament object or None if analysis failed
        """
        if not self.api_key:
            logger.warning("Skipping AI analysis - API key not configured")
            return tournament
        
        try:
            # Prepare the prompt
            prompt = self.prompt_template.format(
                tournament_name=tournament.name,
                month=tournament.month,
                year=tournament.year
            )
            
            # Get response from Anthropic
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0,
                system="You analyze chess tournament information and return structured data as requested. Always respond with valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            
            # Extract the JSON part
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no code block, try to extract JSON directly
                json_str = response_text.strip()
            
            # Clean up any remaining markdown artifacts
            json_str = re.sub(r'```.*?```', '', json_str, flags=re.DOTALL)
            
            # Parse the result
            try:
                result_dict = json.loads(json_str)
                analysis_result = TournamentAnalysisResult(**result_dict)
                
                # Update the tournament with new information
                enhanced_tournament = tournament.copy()
                
                # Only update fields if they were empty or if the AI is more confident
                if not tournament.is_international:
                    enhanced_tournament.is_international = analysis_result.is_international
                
                if not tournament.city and analysis_result.city:
                    enhanced_tournament.city = analysis_result.city
                
                if analysis_result.country and tournament.country == "Germany" and analysis_result.is_international:
                    enhanced_tournament.country = analysis_result.country
                
                if not tournament.tournament_type and analysis_result.tournament_type:
                    enhanced_tournament.tournament_type = analysis_result.tournament_type
                
                if not tournament.category and analysis_result.category:
                    enhanced_tournament.category = analysis_result.category
                
                if analysis_result.description:
                    enhanced_tournament.description = analysis_result.description
                
                logger.info(f"Successfully enhanced tournament information for: {tournament.name}")
                return enhanced_tournament
                
            except Exception as e:
                logger.error(f"Error parsing AI response: {str(e)}")
                logger.debug(f"Problematic response: {response_text}")
                return tournament
                
        except Exception as e:
            logger.error(f"Error during AI analysis: {str(e)}")
            return tournament
    
    async def analyze_tournaments(self, tournaments: List[Tournament]) -> List[Tournament]:
        """
        Analyze a list of tournaments using AI and enhance their information.
        
        Args:
            tournaments: List of Tournament objects to analyze
            
        Returns:
            List of enhanced Tournament objects
        """
        if not self.api_key:
            logger.warning("Skipping AI analysis - API key not configured")
            return tournaments
        
        enhanced_tournaments = []
        
        for tournament in tournaments:
            enhanced_tournament = await self.analyze_tournament(tournament)
            enhanced_tournaments.append(enhanced_tournament)
        
        logger.info(f"Enhanced {len(enhanced_tournaments)} tournaments with AI analysis")
        return enhanced_tournaments 