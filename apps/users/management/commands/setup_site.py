from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from decouple import config


class Command(BaseCommand):
    help = "Ensure that the Django Site object matching SITE_ID exists to prevent allauth 500 errors"

    def handle(self, *args, **options):
        site_id = getattr(settings, 'SITE_ID', 1)
        raw_url = config('SITE_URL', default='http://localhost:8000')
        domain = raw_url.replace('https://', '').replace('http://', '').strip('/')
        name = config('SITE_NAME', default='Smart Library Management System')

        # If a different Site already owns this domain, rename it to avoid unique constraint violations
        existing_with_domain = Site.objects.filter(domain=domain).exclude(id=site_id).first()
        if existing_with_domain:
            existing_with_domain.domain = f"inactive-{existing_with_domain.id}.local"
            existing_with_domain.save()

        site = Site.objects.filter(id=site_id).first()
        if not site:
            # Check if site ID 1 exists, or create matching site_id
            site = Site.objects.create(id=site_id, domain=domain, name=name)
            self.stdout.write(self.style.SUCCESS(f"Created Site [ID={site_id}] with domain '{domain}'."))
        else:
            if domain not in ['localhost:8000', '127.0.0.1:8000', 'example.com'] or site.domain in ['example.com']:
                site.domain = domain
                site.name = name
                site.save()
                self.stdout.write(self.style.SUCCESS(f"Updated Site [ID={site_id}] to domain '{domain}'."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Site [ID={site_id}] exists with domain '{site.domain}'."))
