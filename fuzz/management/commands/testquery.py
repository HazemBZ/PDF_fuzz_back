from django.core.management.base import BaseCommand, CommandError
from fuzz.search import Search
import traceback
from pprint import pprint
from itertools import groupby

class Command(BaseCommand):
    help = "Returns result of a es lookup"

    def add_arguments(self, *args, **kwargs):
        pass
    
    def handle(self, *args, **options):
        
        def build_image_name(path, count):
            print('path ', path)
            file_location = path.split('assets/')[1]
            file_location = f"/{count}_".join(file_location.split('/')).replace('.pdf', '.jpg')
            return f"http://localhost:8000/api/fuzz/image/path/{file_location}"
        
        try:
            res = Search.get_matching_keyword('back')['hits']['hits']
            
            formatted = []
            pprint(res)
            
            for key, items in groupby(res, lambda x: x['_source']['file_path']):
                match_group = {}
                
                match_group['file'] = key
                
                match_group['matchedImges'] = [build_image_name(key, item['_source']['page_id']) for item in items ]
                match_group['keyword'] = 'back'
                formatted.append(match_group)
                
            print(formatted)
        except Exception as err:
            traceback.print_tb(err.__traceback__)
            raise CommandError("Failed to find documents!")
        else:
            self.stdout.write(
                    self.style.SUCCESS("Documents found")
                )

            
        