from finance_reader.entities.csv_reader import BrokerCSVProcessor
from models.dtos.broker_dtos import Transaction, Ticker
from datetime import datetime
from collections import defaultdict
import requests
import csv
from io import StringIO

AUTO_FX_FEE = 0.0025  # 0.25%


class Degiro(BrokerCSVProcessor):

    # Field mappings for different languages
    FIELD_MAPPINGS = {
        'date': ['Fecha', 'Date'],
        'time': ['Hora', 'Time'],
        'product': ['Producto', 'Product'],
        'isin': ['ISIN', 'ISIN'],
        'exchange': ['Bolsa de', 'Reference'],
        'execution_venue': ['Centro de ejecución', 'Venue'],
        'shares': ['Número', 'Quantity'],
        'price': ['Precio', 'Price'],
        'currency_price': ['Divisa Precio', 'Local value'],  # Next column after Precio
        'value': ['Valor', 'Value'],
        'currency_value': ['Divisa Valor', 'Value Currency'],
        'exchange_rate': ['Tipo de cambio', 'Exchange rate'],
        'transaction_costs': ['Costes de transacción', 'Transaction and/or third'],
        'total': ['Total', 'Total'],
        'order_id': ['ID Orden', 'Order ID'],
    }

    def __init__(self):
        super().__init__()
        self.field_indices = {}

    def _detect_field_indices(self, headers):
        """Detect which language is used and map field names to column indices."""
        field_indices = {}
        
        for field_key, possible_names in self.FIELD_MAPPINGS.items():
            for name in possible_names:
                if name in headers:
                    field_indices[field_key] = headers.index(name)
                    break
        
        # Special handling for currency column (next to price)
        if 'price' in field_indices:
            field_indices['currency_price'] = field_indices['price'] + 1
        
        return field_indices

    def _get_field_value(self, row, field_key, default=''):
        """Safely get a field value from a row using the detected indices."""
        if field_key in self.field_indices:
            idx = self.field_indices[field_key]
            if idx < len(row):
                return row[idx]
        return default

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
        self.field_indices = self._detect_field_indices(headers)
        
        # Verify required fields are present
        required_fields = ['price', 'shares', 'product', 'date', 'time']
        missing_fields = [f for f in required_fields if f not in self.field_indices]
        if missing_fields:
            self.log.error(f"Missing required columns in CSV: {missing_fields}")
            return [], []

        exchanges = self._get_exchanges()
        exchanges2 = {e.get('hiqAbbr'): e for e in exchanges.values()}

        orders = []
        transactions = []
        self.log.info(f"Found {len(rows)-1} transactions in CSV file. Parsing...")
        for row in reversed(rows[1:]):
            t = Transaction()
            try:
                shares_str = self._get_field_value(row, 'shares', '0')
                shares = int(shares_str)
            except Exception:
                self.log.error(f"Error parsing shares: {row}")
                continue
            t.type = Transaction.Type.BUY if shares > 0 else Transaction.Type.SELL
            t.shares = abs(shares)
            try:
                price_str = self._get_field_value(row, 'price', '0')
                t.price = float(price_str.replace('"', '').replace("'", '').replace(",", "."))
            except Exception:
                self.log.error(f"Error parsing price: {row}")
                continue
            t.name = self._get_field_value(row, 'product', '')

            t.ticker = Ticker()
            t.ticker.name = t.name
            t.ticker.ticker = None
            t.ticker.isin = self._get_field_value(row, 'isin', '')
            price_currency = self._get_field_value(row, 'currency_price', '')
            t.ticker.currency = price_currency
            exchange_name = self._get_field_value(row, 'exchange', '')
            t.ticker.exchange = exchange_name
            try:
                t.ticker.exchange = exchanges2.get(exchange_name, {}).get('micCode', t.ticker.exchange)
            except Exception:
                execution_venue = self._get_field_value(row, 'execution_venue', '')
                self.log.warning(f"Unable to detect the exchange for ticker {t.name} - {t.ticker.isin}. {exchange_name} - {execution_venue}")

            t.ticker.active = Ticker.Status.ACTIVE
            try:
                date_str = self._get_field_value(row, 'date', '')
                time_str = self._get_field_value(row, 'time', '')
                date = datetime.strptime(date_str + "T" + time_str, "%d-%m-%YT%H:%M")
            except Exception:
                self.log.error(f"Error parsing date/time: {row}")
                continue
            t.value_date = date
            order_id = self._get_field_value(row, 'order_id', '')
            t.external_id = order_id or f"{t.value_date}_{t.ticker.isin}_{t.shares}_{t.price}"

            fee_str = self._get_field_value(row, 'transaction_costs', '')
            t.fee = float(fee_str.replace('"', '').replace("'", '').replace(",", ".")) if fee_str else 0
            change_rate_str = self._get_field_value(row, 'exchange_rate', '')
            change_rate = float(change_rate_str.replace('"', '').replace("'", '').replace(",", ".")) if change_rate_str else 0
            t.currency_rate = 1 / (change_rate if change_rate else 1)
            t.currency = price_currency

            valor_str = self._get_field_value(row, 'value', '')
            if change_rate and valor_str:
                try:
                    t.exchange_fee = round(float(valor_str.replace('"', '').replace("'", '').replace(",", ".")) * AUTO_FX_FEE, 2)
                except Exception:
                    self.log.error(f"Error parsing exchange fee: {row}")

            # check HOUR in order to identify split
            if t.type == Transaction.Type.BUY and not order_id:
                t.type = Transaction.Type.SPLIT_BUY
            elif t.type == Transaction.Type.SELL and not order_id:
                t.type = Transaction.Type.SPLIT_SELL

            if exchange_name == 'OTC':
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