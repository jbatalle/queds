<template>
  <div>
    <div class="row">
      <div class="col-lg-12 col-md-6 col-sm-6">
        <div class="row">
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Current wallet value given market price
                </div>
              </div>
              <template #reference>
                <stats-card type="success"
                            icon="nc-icon nc-money-coins"
                            small-title="Wallet Value"
                            :title="$filters.toCurrency(wallet_value, base_currency)">
                  <template #footer>
                    <div class="stats">
                      <i class="nc-icon nc-refresh-69"></i>
                      Total cost: {{ $filters.toCurrency(this.total_cost, base_currency) }}
                    </div>
                  </template>
                </stats-card>
              </template>
            </el-popover>
          </div>
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Profit / loses for the current wallet</div>
              </div>
              <template #reference>
                <stats-card type="success"
                            icon="fa fa-chart-line"
                            small-title="Current P/L"
                            :title="`${$filters.toCurrency(total_current_benefits + total_benefits, base_currency)} (${this.benefits_percent}%)`">
                  <template #footer>
                    <div class="stats">
                      <i class="nc-icon nc-refresh-69"></i>
                      Realized: {{ $filters.toCurrency(total_benefits, base_currency) }} - Unrealized:
                      {{ $filters.toCurrency(this.total_current_benefits, base_currency) }}
                    </div>
                  </template>
                </stats-card>
              </template>
            </el-popover>
          </div>
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Wallet daily changes (last 24h)</div>
              </div>
              <template #reference>
                <stats-card type="success"
                            icon="fa fa-chart-line"
                            small-title="Daily P/L"
                            :title="$filters.toCurrency((this.wallet_value - this.base_previous_value ), base_currency)">
                  <template #footer>
                    <div class="stats">
                      <i class="nc-icon nc-refresh-69"></i>
                      Daily change: {{ this.daily_benefits_percent }}%
                    </div>
                  </template>
                  <div class="stats" slot="footer">
                    <i class="nc-icon nc-refresh-69"></i>

                  </div>
                </stats-card>
              </template>
            </el-popover>
          </div>
        </div>
      </div>
    </div>
    <el-tabs class="demo-tabs" type="card" v-model="activeName">
      <el-tab-pane class="sidebar-wrapper" label="Wallet" name="first">
        <div class="row">
          <balance-table :base_currency="base_currency" :wallet="wallet" :loading="loading" type="broker"
                         @recalculate="recalculate" @reload="reload"/>
        </div>
      </el-tab-pane>
      <el-tab-pane label="Distribution" name="second">
        <balance-dist :wallet="wallet" :wallet_value="wallet_value" type="broker"/>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script>
import axios from "axios";
import BalanceTable from "@/components/Dashboard/Views/BalanceTable.vue";
import BalanceDist from "@/components/Dashboard/Views/BalanceDist.vue";

export default {
  name: "Portfolio",
  components: {
    BalanceTable, BalanceDist
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      activeName: 'first',
      fx_rate: 1,
      loading: true,
      wallet: [],
      //total_value: 0,
      wallet_value: 0,
      total_current_benefits: 0,
      total_benefits: 0,
      total_cost: 0,
      current_benefits_percent: 0,
      daily_benefits_percent: 0,
      benefits_percent: 0,
      base_previous_value: 0,
      investKey: 0,
      gain: 0,
    };
  },
  created() {
    this.getData();
  },
  methods: {
    async recalculate() {
      let vm = this;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/calculate").then(
          vm.$notify({
            message: 'Recalculating balances/taxes!',
            type: 'info',
          })
      );
    },
    async reload() {
      await this.getData();
    },
    fillFxRate(res) {
      let resStatus = res.status === 200;
      this.fx_rate = Number(res.data).toFixed(2);
    },
    async getData() {
      this.loading = true;

      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/fx_rate").then(this.fillFxRate);
      try {
        await this.loadWalletAssets();
        await this.loadPricesAndUpdateWallet();
      } catch (err) {
        console.error("Wallet error:", err);
        this.$notify({message: 'Error loading wallet data.', type: 'error'});
      }

      this.loading = false;
    },

    async loadWalletAssets() {
      // Load wallet assets (no prices yet)
      const walletRes = await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/wallet/assets");

      // Initialize wallet arrays and counters
      this.wallet = [];
      this.total_cost = 0;
      this.total_current_benefits = 0;
      this.total_benefits = 0;
      this.wallet_value = 0;
      this.base_previous_value = 0;

      // Process wallet items partially
      const vm = this;
      const walletItems = walletRes.data.map(t => {
        // Process children (open orders)
        if (t.open_orders) {
          t.children = t.open_orders.map(c => {
            return {
              ...c,
              ticker: {
                "id": t.ticker.id,
                "ticker": c.transaction.value_date.split(' ')[0],
                "currency": t.ticker.currency
              },
              id: t.id + "_" + c.id,
              price: (c.transaction.type == 0 && c.transaction.price) ? c.transaction.price || 0 : (1 / c.transaction.price || 0),
              price_eur: c.user_price,
              cost: c.shares * c.transaction.price,
              //current_price_currency: c.transaction.symbol.split('/')[1]
            };
          });
        } else {
          t.children = [];
        }

        return {
          ...t,
          ticker: {"id": t.ticker.id, "ticker": t.ticker.ticker, "isin": t.ticker.isin, "name": t.ticker.name, "yahoo": t.ticker.ticker_yahoo, "currency": t.ticker.currency},
          symbol: t.ticker.ticker,
          container_id: t.ticker.ticker,
          base_current_value: t.current_value * this.fx_rate || 0,
          style: "3",
          current_price: null,
          current_value: null,
          previous_day_value: null,
          current_benefit: null,
          loading: true // mark as loading prices
        };
      });//.filter(t => t.currency !== undefined);

      this.wallet = walletItems;
      this.loading = false; // Allow UI to be interactive while prices load
    },

    async loadPricesAndUpdateWallet() {
      // Load prices async, don't block UI
      let tickers = this.wallet.map(item => {return { ticker: item.ticker.ticker, ticker_yahoo: item.ticker.yahoo};}).filter(Boolean); // removes undefined/null values
      const priceRes = await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/stock/wallet/prices", {
        tickers: tickers
      });

      const prices = priceRes.data;
      this.mergeWalletWithPrices(prices);
    },

    mergeWalletWithPrices(prices) {
      const vm = this;

      // Reset global stats before recalculating
      this.total_cost = 0;
      this.total_current_benefits = 0;
      this.total_benefits = 0;
      this.wallet_value = 0;
      this.base_previous_value = 0;

      this.wallet = this.wallet.map(t => {
        let item_fx = 1
        if (t.ticker.currency != 'EUR') {
          item_fx = this.fx_rate;
        }
        if (t.ticker.currency != 'EUR') {
          // the break_even is in EUR, we need to convert it to the ticker currency
          t.break_even = t.break_even / vm.fx_rate;
        }
        let priceData = prices[t.symbol];
        let current_value = 0;
        let previous_day_value = 0;

        if (priceData !== undefined) {
          //const priceData = this.calculatePriceData(t, prices_eur, prices_usd, prices_btc);
          t.current_value = t.shares * priceData.price;
          t.previous_day_value = t.shares * priceData.previous_close;
          //  r.shares * (item['market'].get('previous_close', 0) or 0)
          t.base_current_value = t.current_value * item_fx;
          t.base_previous_value = t.previous_day_value * item_fx;
          t.day_change = t.base_current_value-t.base_previous_value;
          t.current_price = priceData.price;
          t.price_change = previous_day_value;
          t.pre = priceData.pre;
          t.pre_change = priceData.pre_change;
        }

        t.current_benefit = t.base_current_value - t.base_cost;//(t.price * t.shares);

        // Update global stats (similar to the loop in fillWallet)
        vm.total_cost += t.price * t.shares;
        vm.wallet_value += t.base_current_value;
        vm.total_benefits += t.benefits || 0;
        vm.total_current_benefits += t.current_benefit;
        vm.base_previous_value += t.base_previous_value;

        return {
          ...t,
          loading: false // price is now loaded
        };
      });

      this.wallet = this.wallet.map(t => {
        t.percentage = Number(parseFloat(t.base_current_value) / this.wallet_value * 100);
        return t;
      });

      // Calculate card stats
      this.current_benefits_percent = Number(this.wallet_value / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
      if (this.total_cost > 0) {
        this.benefits_percent = Number((Number(this.wallet_value) + parseFloat(this.total_benefits)) / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
      } else {
        this.benefits_percent = 0;
      }
      if (this.base_previous_value > 0) {
        this.daily_benefits_percent = Number((Number(this.wallet_value) - parseFloat(this.base_previous_value)) / parseFloat(this.base_previous_value) * 100).toFixed(2);
      } else {
        this.daily_benefits_percent = 0;
      }

      console.log("Wallet_value: " + this.wallet_value);
      console.log("Total_cost: " + this.total_cost);
      console.log("Base_previous_value: " + this.base_previous_value);
      console.log("Win/Lose: " + (this.wallet_value - this.total_cost) + ". Current benefits: " + this.total_current_benefits);
      console.log("Final cost: " + (this.total_cost - this.total_benefits));
    },

    calculatePriceData(item, prices_eur, prices_usd, prices_btc) {
      let current_price = 0;
      let current_price_eur = 0;
      let current_price_currency = '';

      if (prices_eur[item.currency]) {
        current_price = 1 / prices_eur[item.currency];
        current_price_eur = current_price;
        current_price_currency = 'eur';
      } else if (prices_usd[item.currency]) {
        current_price = 1 / prices_usd[item.currency];
        current_price_eur = current_price * prices_eur['USD'];
        current_price_currency = 'usd';
      } else if (prices_btc[item.currency]) {
        current_price = 1 / prices_btc[item.currency];
        current_price_eur = current_price * prices_eur['BTC'];
        current_price_currency = 'btc';
      }

      return {
        current_price,
        current_price_eur,
        current_price_currency
      };
    },
  }
};
</script>
<style>
.Chart {
  max-width: 200px;
  padding: 20px;
  /* box-shadow: 0px 0px 20px 2px rgba(0, 0, 0, 0.4); */
  border-radius: 20px;
  margin: 50px 0;
}

.el-tabs__item.is-active {
  background-color: #ffffff;
  color: #3cab79 !important;
}

.el-tabs__item:hover {
  background-color: #ffffff;
  color: #3cab79 !important;
}
</style>
