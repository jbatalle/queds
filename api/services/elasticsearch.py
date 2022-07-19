from datetime import datetime
from elasticsearch import Elasticsearch


class ESClient:
    def __init__(self, host):
        self.es = Elasticsearch([{'host': host, 'port': 9200}])

    def save_comment(self, source, id, tickers, message, date):
        res = self.es.index(index='sw', doc_type=source, id=id,
                            body={
                                "ticker": tickers,
                                "message": message,
                                "timestamp": datetime.now(),
                                "date": date})
        if not res['created']:
            print(res)

    def get_last_page(self):
        f = {
            "size": 10,
            "sort": {"date": "desc"},
            "query": {
                "match_all": {}
            }
        }
        res = self.es.search(index="sw", doc_type="rankia", body=f)
        return res['hits']['hits'][0]["_id"].split("_")[0]

    def get_all_messages(self):
        res = self.es.search(index="sw", doc_type="rankia")
        for r in res['hits']['hits']:
            print(r['_source']['message'])

    def search_by_ticker(self, ticker):
        res = self.es.search(index="sw", body={'size': 100, "sort": {"date": "desc"}, "query": {"match": {'ticker': ticker}}})
        return res['hits']['hits']

    def search_comment(self, search_text):
        res = self.es.search(index="sw", body={
            "query": {
                "more_like_this": {
                    "fields": [
                        "message"
                    ],
                    "like_text": search_text,
                    "min_term_freq": 1,
                    "min_doc_freq": 1,
                    "max_query_terms": 12
                }
            }
        })

        # res = es.search(index="sw", body={"query": {"match": {'like_message': search_text}}})
        for r in res['hits']['hits']:
            print(f"M: {r['_source'].get('date', '')}: {r['_source']['message']}")
