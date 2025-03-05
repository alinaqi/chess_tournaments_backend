#!/usr/bin/env python3
"""
Test script for crawl4ai functionality.
"""
import crawl4ai
import asyncio
import logging
import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def test_crawl4ai():
    """
    Test crawl4ai functionality by crawling a simple website.
    """
    try:
        logger.info("Initializing crawl4ai WebCrawler...")
        
        # Test if async version is available
        if hasattr(crawl4ai, 'AsyncWebCrawler'):
            logger.info("Using AsyncWebCrawler")
            crawler = crawl4ai.AsyncWebCrawler()
            
            # Try to use the arun method
            logger.info("Trying to crawl using arun method...")
            try:
                result = await crawler.arun(
                    url="https://www.example.com",
                    extract_text=True,
                    extract_html=True,
                    verbose=True
                )
                
                logger.info(f"Crawl completed successfully")
                logger.info(f"URL: {result.url}")
                logger.info(f"Title: {result.title}")
                logger.info(f"Text length: {len(result.text or '')}")
                logger.info(f"HTML length: {len(result.html or '')}")
                
                # Try to extract some content
                if result.text:
                    logger.info(f"First 100 chars of text: {result.text[:100]}...")
                
            except Exception as e:
                logger.error(f"Error using arun method: {str(e)}")
                
                # Try to use the start method to start the server
                logger.info("Trying to start the server...")
                try:
                    # Start the server
                    await crawler.start()
                    logger.info("Server started successfully")
                    
                    # Wait a bit for the server to initialize
                    await asyncio.sleep(2)
                    
                    # Now try to use the REST API
                    import requests
                    response = requests.post(
                        "http://localhost:11235/crawl",
                        json={
                            "urls": "https://www.example.com",
                            "extract_text": True,
                            "extract_html": True
                        }
                    )
                    
                    if response.status_code == 200:
                        task_id = response.json().get("task_id")
                        logger.info(f"Crawl job submitted, task_id: {task_id}")
                        
                        # Poll for results
                        for _ in range(10):  # Try for up to 10 times
                            await asyncio.sleep(1)
                            result_response = requests.get(f"http://localhost:11235/task/{task_id}")
                            if result_response.status_code == 200:
                                result = result_response.json()
                                if result.get("status") == "completed":
                                    logger.info(f"Crawl completed: {result}")
                                    break
                                elif result.get("status") == "failed":
                                    logger.error(f"Crawl failed: {result}")
                                    break
                                else:
                                    logger.info(f"Crawl in progress: {result.get('status')}")
                            else:
                                logger.error(f"Failed to get task status: {result_response.status_code}")
                    else:
                        logger.error(f"Failed to submit crawl job: {response.status_code}")
                except Exception as e:
                    logger.error(f"Error starting server or using REST API: {str(e)}")
        else:
            logger.info("Using WebCrawler")
            crawler = crawl4ai.WebCrawler()
            
            # Try to use the run method
            logger.info("Trying to crawl using run method...")
            try:
                result = crawler.run(
                    url="https://www.example.com",
                    extract_text=True,
                    extract_html=True,
                    verbose=True
                )
                
                logger.info(f"Crawl completed successfully")
                logger.info(f"URL: {result.url}")
                logger.info(f"Title: {result.title}")
                logger.info(f"Text length: {len(result.text or '')}")
                logger.info(f"HTML length: {len(result.html or '')}")
            except Exception as e:
                logger.error(f"Error using run method: {str(e)}")
        
        logger.info("Crawl4ai test completed")
        
    except Exception as e:
        logger.error(f"Error testing crawl4ai: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(test_crawl4ai())
    except KeyboardInterrupt:
        logger.info("Test stopped by user") 