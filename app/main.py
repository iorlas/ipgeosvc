import os
from fastapi import FastAPI, HTTPException, Request
from geoip2.database import Reader
from geoip2.errors import AddressNotFoundError
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel, Field
from fastapi.middleware.gzip import GZipMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load GeoIP2 database
geoip_reader = Reader(os.environ.get("GEOLITE2_CITY_DATABASE", "GeoLite2-City.mmdb"))

app = FastAPI(middleware=[Middleware(GZipMiddleware, minimum_size=1000)])

# CORS configuration
origins = ["*"]  # Adjust as needed for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GeoIPResponse(BaseModel):
    ip: str
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field(None, description="Country name")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    continent: Optional[str] = Field(None, description="Continent name")
    timezone: Optional[str] = Field(None, description="Timezone")
    postal_code: Optional[str] = Field(None, description="Postal code")
    region: Optional[str] = Field(None, description="Region name")


@app.get("/geo", response_model=GeoIPResponse, response_model_exclude_none=True)
@app.get("/geo/{ip}", response_model=GeoIPResponse, response_model_exclude_none=True)
async def get_ip_location(request: Request, ip: str | None = None):
    if ip is None:
        ip = request.client.host

    try:
        response = geoip_reader.city(ip)
        return {
            "ip": ip,
            "city": response.city.name,
            "country": response.country.name,
            "latitude": response.location.latitude,
            "longitude": response.location.longitude,
            "continent": response.continent.name,
            "timezone": response.location.time_zone,
            "postal_code": response.postal.code,
            "region": response.subdivisions[0].name if response.subdivisions else None,
        }
    except AddressNotFoundError:
        raise HTTPException(status_code=404, detail=f"IP address '{ip}' not found")
    except Exception as e:
        logger.exception(f"Error processing IP address: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
