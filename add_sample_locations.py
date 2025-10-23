#!/usr/bin/env python3
"""
Script to add sample location data to existing job postings for testing the map functionality.
Run this after creating some job postings to add latitude/longitude coordinates.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/rithvikpadigala/Downloads/jobfinder2340-main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder2340.settings')
django.setup()

from jobs.models import JobPosting

# Sample locations with coordinates (city, latitude, longitude)
SAMPLE_LOCATIONS = [
    ("New York, NY", 40.7128, -74.0060),
    ("San Francisco, CA", 37.7749, -122.4194),
    ("Los Angeles, CA", 34.0522, -118.2437),
    ("Chicago, IL", 41.8781, -87.6298),
    ("Austin, TX", 30.2672, -97.7431),
    ("Seattle, WA", 47.6062, -122.3321),
    ("Boston, MA", 42.3601, -71.0589),
    ("Denver, CO", 39.7392, -104.9903),
    ("Miami, FL", 25.7617, -80.1918),
    ("Portland, OR", 45.5152, -122.6784),
]

def add_sample_locations():
    """Add sample location data to job postings that don't have coordinates."""
    jobs_without_coords = JobPosting.objects.filter(
        latitude__isnull=True, 
        longitude__isnull=True
    )
    
    print(f"Found {jobs_without_coords.count()} job postings without coordinates.")
    
    for i, job in enumerate(jobs_without_coords):
        if i < len(SAMPLE_LOCATIONS):
            location, lat, lng = SAMPLE_LOCATIONS[i]
            job.location = location
            job.latitude = lat
            job.longitude = lng
            job.save()
            print(f"Updated job '{job.title}' with location: {location}")
        else:
            # If we run out of sample locations, use a default
            job.latitude = 39.8283  # Center of US
            job.longitude = -98.5795
            job.save()
            print(f"Updated job '{job.title}' with default coordinates")
    
    print("Sample location data added successfully!")

if __name__ == "__main__":
    add_sample_locations()
