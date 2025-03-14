import re
import requests
import base64
from datetime import datetime, timedelta


class ZincClient:
    def __init__(self, host, user, password):
        self.client = requests.Session()
        bas64encoded_creds = base64.b64encode(bytes(user + ":" + password, "utf-8")).decode("utf-8")
        self.client.headers = {
            "Authorization": "Basic " + bas64encoded_creds
        }
        self.base_url = f"http://{host}:4080"

    def get_last_items(self):
        indexes = self.get_indexes()
        items = []
        now = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        for index in indexes:
            data = {
                "max_results": 100,
                "sort_fields": ["-@date"],
                "query": {
                    "match_all": {},
                    "start_time": now
                }
            }
            res = self.client.post(f"{self.base_url}/api/{index}/_search", json=data)
            d = res.json()
            if not d['hits']['hits']:
                continue
            items.extend(d['hits']['hits'])
        return items

    def get_indexes(self):
        res = self.client.get(f"{self.base_url}/api/index")
        if res.status_code != 200:
            print(f"Error: {res.text}")
        return list(res.json().keys())

    def get_last_page(self, index):
        data = {
            "max_results": 10,
            "sort_fields": ["-@timestamp"],
            "query": {
                "match_all": {}
            }
        }
        res = self.client.post(f"{self.base_url}/api/{index}/_search", json=data)
        d = res.json()
        return d['hits']['hits'][0]['_id'].split("_")[0]

    def get_last_post(self, index, thread_id):
        data = {
            "max_results": 1,
            "search_type": "querystring",
            "sort_fields": ["-@timestamp"],
            "query": {
                "term": f"thread_id:{thread_id}"
            }
        }
        res = self.client.post(f"{self.base_url}/api/{index}/_search", json=data)
        d = res.json()
        if not d['hits']['hits']:
            return
        return d['hits']['hits'][0]['_source']['post_id']

    def get_last_post_page(self, index, thread_id):
        data = {
            "max_results": 1,
            "search_type": "querystring",
            "sort_fields": ["-@timestamp"],
            "query": {
                "term": f"thread_id:{thread_id}"
            }
        }
        res = self.client.post(f"{self.base_url}/api/{index}/_search", json=data)
        d = res.json()
        if 'hits' not in res.json():
            return None, None
        if not d['hits']['hits']:
            return None, None
        if 'page' not in d['hits']['hits'][0]['_source']:
            return None, None
        post = d['hits']['hits'][0]['_source']['post_id']
        return post.split("_")

    def search_by_ticker(self, index, ticker):
        match = ' '.join([f"ticker.{q}:{ticker}" for q in range(0, 30)])
        data = {
            "max_results": 1000,
            "search_type": "querystring",
            "sort_fields": ["-@timestamp"],
            "query": {
                "term": match
            }
        }
        res = self.client.post(f"{self.base_url}/api/{index}/_search", json=data)
        d = res.json()
        if not d['hits']['hits']:
            print("NOT FOUND!")
            return
        for r in d['hits']['hits']:
            print(f"M: {r['_source'].get('date', '')}: {r['_source']['message']}")

    def search_by_ticker_using_el(self, index, ticker):
        ticker = "BRQS"
        data = {'size': 100, "sort": {"date": "desc"}, "query": {"match": {'ticker': ticker}}}
        res = self.client.post(f"{self.base_url}/es/{index}/_search", json=data)
        d = res.json()
        for r in d['hits']['hits']:
            print(f"M: {r['_source'].get('date', '')}: {r['_source']['message']}")

    def get_last_messages(self, index):
        data = {
            "max_results": 1,
            "sort_fields": ["-@date"],
            "query": {
                "match_all": {}
            }
        }
        res = self.client.post(f"{self.base_url}/api/{index}/_search", json=data)
        d = res.json()
        return d['hits']['hits']
