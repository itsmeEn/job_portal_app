from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

class Command(BaseCommand):
    help = 'Updates the default site domain and name'

    def handle(self, *args, **options):
        site = Site.objects.get(id=settings.SITE_ID)
        site.domain = settings.SITE_DOMAIN
        site.name = settings.SITE_NAME
        site.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated site domain to {site.domain} and name to {site.name}')
        ) 