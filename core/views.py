from django.shortcuts import render, redirect
from .models import JobListing
from .scrapers import scrape_timesjobs, scrape_careerindia

def home(request):
    jobs = None
    
    if request.method == 'POST':
        # 1. Get User Input
        designation = request.POST.get('designation')
        location = request.POST.get('location')
        
        # 2. Run Scrapers
        # Note: In a real production app, this should be a Celery task (Async).
        # For this interview test, running it synchronously is acceptable.
        data_1 = scrape_timesjobs(designation, location)
        data_2 = scrape_careerindia(designation, location)
        
        all_scraped_jobs = data_1 + data_2
        
        # 3. Save to Database (Avoid Duplicates)
        # We clear old results for this demo to keep it simple
        JobListing.objects.all().delete() 
        
        for job in all_scraped_jobs:
            JobListing.objects.create(
                title=job['title'],
                company=job['company'],
                location=job['location'],
                source=job['source'],
                link=job['link']
            )
            
        return redirect('results')

    return render(request, 'search.html')
def results(request):
    # Fetch all jobs from DB
    jobs = JobListing.objects.all().order_by('-created_at')
    return render(request, 'results.html', {'jobs': jobs})