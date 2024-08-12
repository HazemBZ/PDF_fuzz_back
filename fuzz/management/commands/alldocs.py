from django.core.management.base import BaseCommand, CommandError
from fuzz.search import Search
import traceback
from pprint import pprint

class Command(BaseCommand):
    help = "All pdf indexed documents"

    def add_arguments(self, *args, **kwargs):
        pass
    
    def handle(self, *args, **options):
        try:
            res = Search.get_all_documents()
            pprint(res)
        except Exception as err:
            traceback.print_tb(err.__traceback__)
            raise CommandError("Failed to find documents!")
        else:
            self.stdout.write(
                    self.style.SUCCESS("Documents found")
                )

            
        