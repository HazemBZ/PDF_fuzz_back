from django.core.management.base import BaseCommand, CommandError
from fuzz.search import Search
import traceback

class Command(BaseCommand):
    help = "Reindex pdf documents"

    def add_arguments(self, *args, **kwargs):
        pass
    
    def handle(self, *args, **options):
        try:
            Search.reindex()
        except Exception as err:
            traceback.print_tb(err.__traceback__)
            raise CommandError("Failed to reindex!")
        else:
            self.stdout.write(
                    self.style.SUCCESS('Reindexation succeeded')
                )

            
        