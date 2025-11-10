#!/usr/bin/env python3
"""
Zendesk Lead Generator REST API

FastAPI server providing endpoints for detection and lead management.

Endpoints:
- GET /health - Health check
- GET /leads - Get all leads (with filters)
- GET /lead/{domain} - Get specific lead
- POST /detect - Detect Zendesk for a domain
- GET /stats - Get database statistics
"""

import os
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from detect_zendesk import ZendeskDetector
from enrichment import CompanyEnricher
from storage import LeadStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Zendesk Lead Generator API",
    description="REST API for detecting Zendesk usage and managing leads",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
detector = ZendeskDetector()
enricher = CompanyEnricher(
    clearbit_api_key=os.getenv('CLEARBIT_API_KEY'),
    us_only=True
)
storage = LeadStorage()

logger.info("API initialized")


# Request/Response Models

class DetectRequest(BaseModel):
    """Request model for /detect endpoint."""
    domain: str = Field(..., description="Company domain to detect")
    enrich: bool = Field(True, description="Enable company enrichment")
    use_playwright: bool = Field(False, description="Force Playwright detection")
    use_cloudscraper: bool = Field(False, description="Enable cloudscraper")


class LeadResponse(BaseModel):
    """Response model for lead data."""
    domain: str
    company_name: Optional[str] = None
    detected_zendesk: bool
    zendesk_score: int
    signals: dict
    employees: Optional[int] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    linkedin_url: Optional[str] = None
    enriched_at: Optional[str] = None
    detection_timestamp: Optional[str] = None
    blocked_by_waf: bool
    original_status_code: Optional[int] = None
    detection_method: Optional[str] = None
    error: Optional[str] = None


class StatsResponse(BaseModel):
    """Response model for statistics."""
    total_leads: int
    zendesk_detected: int
    blocked_by_waf: int
    us_companies: int
    enriched: int
    methods: dict


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    version: str
    components: dict


# Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status of all components
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "detector": "ok",
            "enricher": "ok" if enricher else "disabled",
            "storage": "ok",
            "database": "ok"
        }
    }


@app.get("/leads", response_model=List[LeadResponse])
async def get_leads(
    detected_only: bool = Query(False, description="Only return Zendesk-detected leads"),
    us_only: bool = Query(False, description="Only return US companies"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get all leads with optional filtering.

    Args:
        detected_only: Only return detected leads
        us_only: Only return US companies
        limit: Maximum results
        offset: Pagination offset

    Returns:
        List of leads
    """
    try:
        leads = storage.get_all_leads(
            detected_only=detected_only,
            us_only=us_only
        )

        # Apply pagination
        paginated = leads[offset:offset + limit]

        logger.info(f"Retrieved {len(paginated)} leads (total: {len(leads)})")
        return paginated

    except Exception as e:
        logger.error(f"Failed to retrieve leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lead/{domain}", response_model=LeadResponse)
async def get_lead(domain: str):
    """
    Get a specific lead by domain.

    Args:
        domain: Company domain

    Returns:
        Lead data

    Raises:
        404 if lead not found
    """
    try:
        lead = storage.get_lead(domain)

        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead not found: {domain}")

        logger.info(f"Retrieved lead: {domain}")
        return lead

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve lead {domain}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect", response_model=LeadResponse)
async def detect_zendesk(
    request: DetectRequest,
    background_tasks: BackgroundTasks
):
    """
    Detect Zendesk usage for a domain.

    Performs detection and optionally enrichment, saves to database.

    Args:
        request: Detection request with domain and options

    Returns:
        Detection and enrichment results
    """
    try:
        domain = request.domain.strip()

        logger.info(f"Detecting Zendesk for {domain}")

        # Initialize detector with custom options if provided
        if request.use_playwright or request.use_cloudscraper:
            custom_detector = ZendeskDetector(
                use_playwright=request.use_playwright,
                use_cloudscraper=request.use_cloudscraper
            )
            detection_result = custom_detector.detect(domain)
        else:
            detection_result = detector.detect(domain)

        # Prepare lead data
        lead_data = {
            'domain': domain,
            'detected_zendesk': detection_result.get('detected', False),
            'zendesk_score': detection_result.get('score', 0),
            'signals': detection_result.get('signals', {}),
            'detection_timestamp': detection_result.get('timestamp'),
            'blocked_by_waf': detection_result.get('blocked_by_waf', False),
            'original_status_code': detection_result.get('original_status_code'),
            'original_headers': detection_result.get('original_headers'),
            'detection_method': detection_result.get('method', 'unknown'),
            'error': detection_result.get('error')
        }

        # Enrichment (if enabled and not blocked)
        if request.enrich and not lead_data['blocked_by_waf']:
            enriched = enricher.enrich(domain)

            if enriched:
                lead_data.update(enriched)
                logger.info(f"{domain}: Enriched successfully")
            else:
                logger.warning(f"{domain}: Enrichment failed or filtered")

        # Save to database in background
        background_tasks.add_task(storage.save_lead, lead_data)

        logger.info(f"{domain}: Detection complete - detected={lead_data['detected_zendesk']}, "
                   f"score={lead_data['zendesk_score']}")

        return lead_data

    except Exception as e:
        logger.error(f"Detection failed for {request.domain}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get database statistics.

    Returns:
        Statistics about stored leads
    """
    try:
        stats = storage.get_stats()

        logger.info("Retrieved database statistics")
        return stats

    except Exception as e:
        logger.error(f"Failed to retrieve stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/lead/{domain}")
async def delete_lead(domain: str):
    """
    Delete a lead from database.

    Args:
        domain: Company domain

    Returns:
        Success message
    """
    try:
        lead = storage.get_lead(domain)

        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead not found: {domain}")

        # Note: You would implement delete method in storage.py
        # For now, return not implemented

        raise HTTPException(status_code=501, detail="Delete not implemented yet")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete lead {domain}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/blocked", response_model=List[LeadResponse])
async def get_blocked_leads():
    """
    Get all leads that were blocked by WAF.

    Returns:
        List of blocked leads
    """
    try:
        blocked = storage.get_blocked_leads()

        logger.info(f"Retrieved {len(blocked)} blocked leads")
        return blocked

    except Exception as e:
        logger.error(f"Failed to retrieve blocked leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Run server

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", 8000))

    logger.info(f"Starting API server on port {port}")

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
