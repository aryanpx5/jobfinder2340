# Job Map Feature

This document describes the interactive job map functionality that has been added to JobFinder2340.

## Overview

The job map feature allows users to view job postings on an interactive map, making it easier to explore job opportunities by location. The map displays job postings as markers with popup information and detailed job views.

## Features

### 1. Interactive Map
- Uses Leaflet.js for the interactive map
- OpenStreetMap tiles for map display
- Responsive design that works on desktop and mobile
- Automatic map bounds adjustment to show all job markers

### 2. Job Markers
- Each job posting appears as a marker on the map
- Markers show basic job information in popups
- Click markers to view detailed job information
- Only shows jobs with valid latitude/longitude coordinates

### 3. Job Details Modal
- Detailed view of job information
- Salary information, location, skills, and description
- Direct link to apply for the job
- Remote work and visa sponsorship indicators

### 4. API Endpoint
- RESTful API endpoint at `/api/job_map/`
- Returns job data as JSON for map markers
- Filters for active, approved jobs with coordinates

## Technical Implementation

### Database Changes
- Added `latitude` and `longitude` fields to `JobPosting` model
- Both fields are optional (null=True, blank=True)
- Migration created: `0006_jobposting_latitude_jobposting_longitude.py`

### New Files
- `templates/jobs/job_map.html` - Map view template
- `add_sample_locations.py` - Script to add sample location data

### Modified Files
- `jobs/models.py` - Added latitude/longitude fields
- `jobs/views.py` - Added map view and API endpoint
- `jobs/urls.py` - Added map routes
- `jobs/forms.py` - Added coordinate fields to job posting form
- `templates/base.html` - Added map link to navigation

### URL Routes
- `/job_map/` - Main map view
- `/api/job_map/` - API endpoint for job data

## Usage

### For Job Seekers
1. Navigate to "Job Map" from the main navigation
2. View all available job postings on the interactive map
3. Click on markers to see job details
4. Use the "Apply Now" button to apply for jobs

### For Recruiters
1. When creating job postings, include latitude and longitude coordinates
2. Use the form fields to specify exact location coordinates
3. Jobs with coordinates will automatically appear on the map

## Adding Location Data

### Manual Entry
When creating or editing job postings, recruiters can enter:
- Location text (e.g., "New York, NY")
- Latitude (e.g., 40.7128)
- Longitude (e.g., -74.0060)

### Sample Data Script
Run the provided script to add sample location data to existing job postings:

```bash
python3 add_sample_locations.py
```

This script adds coordinates for major US cities to job postings that don't have location data.

## Map Features

### Interactive Elements
- **Zoom**: Mouse wheel or zoom controls
- **Pan**: Click and drag to move around the map
- **Markers**: Click to see job popup information
- **Details**: Click "View Details" for full job information

### Responsive Design
- Works on desktop, tablet, and mobile devices
- Map adjusts to screen size
- Touch-friendly controls for mobile users

## Browser Compatibility

The map feature uses modern web technologies:
- Leaflet.js 1.9.4
- Bootstrap 5.1.3
- Modern JavaScript (ES6+)

Compatible with:
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Future Enhancements

Potential improvements for the map feature:
1. **Geocoding**: Automatic coordinate lookup from location text
2. **Clustering**: Group nearby markers for better performance
3. **Filters**: Filter jobs by salary, skills, or other criteria on the map
4. **Directions**: Integration with mapping services for directions
5. **Heat Maps**: Show job density in different areas
6. **User Location**: Detect and center map on user's location

## Troubleshooting

### No Jobs Showing on Map
- Ensure job postings have latitude and longitude values
- Check that jobs are active and approved
- Verify coordinates are not (0, 0)

### Map Not Loading
- Check internet connection (requires external map tiles)
- Verify JavaScript is enabled
- Check browser console for errors

### Location Data Issues
- Use decimal degrees format for coordinates
- Latitude: -90 to 90
- Longitude: -180 to 180
- Use online tools to convert addresses to coordinates

## Dependencies

The map feature requires:
- Django 3.2+
- Leaflet.js (loaded from CDN)
- Bootstrap 5.1.3 (already included)
- Modern web browser with JavaScript enabled

No additional Python packages are required beyond the existing Django installation.
