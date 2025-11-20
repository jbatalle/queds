from finance_reader.entities.csv_reader import BrokerCSVProcessor
from models.dtos.broker_dtos import Transaction, Ticker
from datetime import datetime
from collections import defaultdict
import requests
import csv
from io import StringIO

AUTO_FX_FEE = 0.0025  # 0.25%


class Degiro(BrokerCSVProcessor):


    def __init__(self):
        super().__init__()

    def _get_exchanges(self):
        headers = {
            "cache-control": "no-cache",
            "origin": "https://trader.degiro.nl",
            "pragma": "no-cache",
            "referer": "https://trader.degiro.nl/login/es",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
        }
        # url = "https://trader.degiro.nl/product_search/config/dictionary/"
        url = "https://trader.degiro.nl/productsearch/secure/v1/config/dictionary"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            exchanges = {str(e['id']): e for e in response.json().get('exchanges', [])}
            return exchanges
        except Exception as e:
            self.log.error(f"Error fetching Degiro exchanges: {e}")
            return {}


    def process_csv(self, csv_data, account):
        self.log.info(f"Processing Degiro CSV file for account {account.id}")
        reader = csv.reader(StringIO(csv_data), delimiter=',', quotechar='"')
        rows = list(reader)
        if not rows:
            self.log.error("CSV data is empty.")
            return [], []

        headers = rows[0]
        try:
            precio_idx = headers.index('Precio')
            currency_idx = precio_idx + 1
        except ValueError as e:
            self.log.error(f"Missing expected columns in CSV: {e}")
            return [], []

        exchanges = self._get_exchanges()
        exchanges2 = {e.get('hiqAbbr'): e for e in exchanges.values()}

        orders = []
        transactions = []
        self.log.info(f"Found {len(rows)-1} transactions in CSV file. Parsing...")
        for row in reversed(rows[1:]):
            data = dict(zip(headers, row))
            t = Transaction()
            try:
                shares = int(data.get('Número', '0'))
            except Exception:
                self.log.error(f"Error parsing shares: {data}")
                continue
            t.type = Transaction.Type.BUY if shares > 0 else Transaction.Type.SELL
            t.shares = abs(shares)
            try:
                t.price = float(data.get('Precio', '0').replace('"', '').replace("'", '').replace(",", "."))
            except Exception:
                self.log.error(f"Error parsing price: {data}")
                continue
            t.name = data.get('Producto', '')

            t.ticker = Ticker()
            t.ticker.name = t.name
            t.ticker.ticker = None
            t.ticker.isin = data.get('ISIN', '')
            price_currency = row[currency_idx] if len(row) > currency_idx else ''
            t.ticker.currency = price_currency
            t.ticker.exchange = data.get('Bolsa de', '')
            try:
                t.ticker.exchange = exchanges2.get(data.get('Bolsa de', ''), {}).get('micCode', t.ticker.exchange)
            except Exception:
                self.log.warning(f"Unable to detect the exchange for ticker {t.name} - {t.ticker.isin}. {data.get('Bolsa de')} - {data.get('Centro de ejecución')}")

            t.ticker.active = Ticker.Status.ACTIVE
            try:
                date = datetime.strptime(data.get('Fecha', '') + "T" + data.get('Hora', ''), "%d-%m-%YT%H:%M")
            except Exception:
                self.log.error(f"Error parsing date/time: {data}")
                continue
            t.value_date = date
            t.external_id = data.get('ID Orden') or f"{t.value_date}_{t.ticker.isin}_{t.shares}_{t.price}"

            fee_str = data.get('Costes de transacción', '')
            t.fee = float(fee_str.replace('"', '').replace("'", '').replace(",", ".")) if fee_str else 0
            change_rate_str = data.get('Tipo de cambio', '')
            change_rate = float(change_rate_str.replace('"', '').replace("'", '').replace(",", ".")) if change_rate_str else 0
            t.currency_rate = 1 / (change_rate if change_rate else 1)
            t.currency = price_currency

            valor_str = data.get('Valor', '')
            if change_rate and valor_str:
                try:
                    t.exchange_fee = round(float(valor_str.replace('"', '').replace("'", '').replace(",", ".")) * AUTO_FX_FEE, 2)
                except Exception:
                    self.log.error(f"Error parsing exchange fee: {data}")

            # check HOUR in order to identify split
            if t.type == Transaction.Type.BUY and not data.get('ID Orden'):
                t.type = Transaction.Type.SPLIT_BUY
            elif t.type == Transaction.Type.SELL and not data.get('ID Orden'):
                t.type = Transaction.Type.SPLIT_SELL

            if data.get('Bolsa de') == 'OTC':
                t.type = Transaction.Type.OTC_BUY
            orders.append(t)

        orders = merge_orders(orders)
        self.log.info(f"Processed {len(orders)} orders for account {account.id}")
        return orders, transactions


def merge_orders(orders):
    grouped = defaultdict(list)
    for order in orders:
        grouped[order.external_id].append(order)

    merged = []
    for order_id, group in grouped.items():
        total_shares = sum(o.shares for o in group)
        avg_price = sum(o.price * o.shares for o in group) / total_shares if total_shares else 0
        total_fee = sum(o.fee for o in group)
        merged_order = group[0]
        merged_order.shares = total_shares
        merged_order.price = avg_price
        merged_order.fee = total_fee
        merged.append(merged_order)
    return merged