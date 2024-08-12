from pprint import pprint
from elasticsearch import Elasticsearch
from fuzz.utils.pdf_utils import get_file_documents, process_pdf_files_to_dest
from fuzz.utils.file_utils import get_pdf_files_paths_list
from PDF_Fuzz.settings import ASSETS_DIR, IMAGES_DIR
import os
from timeit import default_timer as timer


class Search:
    PDF_INDEX = "pdf_contents_doc"
    es = None

    @classmethod
    def connect(cls):
        if cls.es is None:
            ES = os.environ.get("ELASTIC_ADDRESS")
            cls.es = Elasticsearch(f"http://{ES}:9200")
            client_info = cls.es.info()
            print("Connected to Elasticsearch")
            pprint(client_info.body)

    @classmethod
    def create_index(cls, index=None):
        if index is None:
            index = cls.PDF_INDEX
        cls.es.indices.delete(index=index, ignore_unavailable=True)
        resp = cls.es.indices.create(index=index)
        print("Created index", resp)

    def insert_document(self, index, document):
        if index is None:
            index = self.PDF_INDEX
        return self.es.index(index=index, document=document)

    @classmethod
    def insert_documents(cls, index, documents):
        if index is None:
            index = cls.PDF_INDEX
        operations = []
        for document in documents:
            operations.append({"index": {"_index": index}})
            operations.append(document)
        print(f"Trying to insert {len(operations)/2} docs ...")
        if len(documents) == 0:
            print("Skipping: check file validity!")
            return

        resp = cls.es.bulk(operations=operations)

        return resp

    @classmethod
    def reindex(cls, index=None):
        """
        NOTE: When indexing a very large number of documents it would be best to divide the list of documents in smaller sets and import each set separately.
        TODO: 1. File indexation + processing
        todo: 2. Parallelize
        todo: 3. Non destructive reindexation (Reindex only non indexed files)
        """
        if index is None:
            index = cls.PDF_INDEX

        cls.create_index()

        print("Reindexation signal!")

        process_pdf_files_to_dest

        file_list = get_pdf_files_paths_list(ASSETS_DIR)
        # print('files ', file_list)
        print(20 * "-")
        for file in file_list:
            if not os.access(os.path.join(IMAGES_DIR, file.stem), os.R_OK):
                print(f"processing '{file}'")
                start = timer()

                process_pdf_files_to_dest(IMAGES_DIR, [file])

                end = timer()
                print(f"Took: {end - start}")

            print(f"Indexing '{file}'")
            start = timer()
            documents = get_file_documents(file)
            end = timer()
            cls.insert_documents(index, documents)

            print(f"Took: {end - start}")
            print(20 * "-")

        # TODO: Send File processing tasks instead

    @classmethod
    def get_all_documents(cls, index=None):
        if index is None:
            index = cls.PDF_INDEX
        return cls.es.search(index=index, query={"match_all": {}})

    @classmethod
    def get_all_aggregated_matchs(cls, index=None):
        if index is None:
            index = cls.PDF_INDEX

        aggs = {"path-agg": {"terms": {"field": "file_path.keyword"}}}
        results = cls.es.search(
            index=index,
            query={"match": {"content": "BACk"}},
            aggs=aggs,
        )

        aggs_result = {
            "Paths": {
                bucket["key"]: bucket["doc_count"]
                for bucket in results["aggregations"]["path-agg"]["buckets"]
            }
        }

        return aggs_result

    @classmethod
    def get_matching_keyword(cls, keyword):
        query = {"match": {"content": keyword}}
        results = cls.es.search(
            index=cls.PDF_INDEX,
            query=query,
            fields=["file_path", "page_id", "page_number"],
        )
        return results

    def search(self, **args):
        return self.es.search(self.PDF_INDEX, **args)
