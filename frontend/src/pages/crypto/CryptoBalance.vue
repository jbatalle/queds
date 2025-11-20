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
          <balance-table :base_currency="base_currency" :wallet="wallet" :loading="loading" type="exchange"
                         @recalculate="recalculate" @reload="reload"/>
        </div>
      </el-tab-pane>
      <el-tab-pane label="Distribution" name="second">
        <balance-dist :wallet="wallet" :wallet_value="wallet_value" type="exchange"/>
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
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/calculate").then(
          vm.$notify({
            message: 'Recalculating balances/taxes!',
            type: 'info',
          })
      );
    },
    async reload() {
      await this.getData();
    },
    async getData() {
      this.loading = true;

      try {
        await this.loadWalletAssets();
        await this.loadPricesAndUpdateWallet();
      } catch (err) {
        this.$notify({message: 'Error loading wallet data.', type: 'error'});
      }

      this.loading = false;
    },

    async loadWalletAssets() {
      // Load wallet assets (no prices yet)
      const walletRes = await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/wallet/assets");

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
                "ticker": c.order.value_date.split(' ')[0],
              },
              id: t.id + "_" + c.id,
              price: (c.order.type == 0 && c.order.price) ? c.order.price || 0 : (1 / c.order.price || 0),
              price_eur: c.user_price,
              cost: c.amount * c.order.price,
              current_price_currency: c.order.symbol.split('/')[1]
            };
          });
        } else {
          t.children = [];
        }

        return {
          ...t,
          ticker: {"ticker": t.currency, "name": t.currency},
          symbol: t.currency + "USD",
          container_id: t.currency + "USD",
          base_current_value: t.current_value || 0,
          style: "3",
          current_price: null,
          current_value: null,
          previous_day_value: null,
          current_benefit: null,
          loading: true // mark as loading prices
        };
      }).filter(t => t.currency !== undefined);

      this.wallet = walletItems;
      this.loading = false; // Allow UI to be interactive while prices load
    },

    async loadPricesAndUpdateWallet() {
      // Load prices async, don't block UI
      const currencies = this.wallet.map(item => item.currency).filter(Boolean);
      const priceRes = await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/wallet/prices", {
        currencies: currencies
      });

      const prices = priceRes.data;
      this.mergeWalletWithPrices(prices);
    },

    mergeWalletWithPrices(prices) {
      const prices_eur = prices.eur || {};
      const prices_usd = prices.usd || {};
      const prices_btc = prices.btc || {};
      const changes_24h = prices.changes_24h || {};
      const vm = this;

      // Reset global stats before recalculating
      this.total_cost = 0;
      this.total_current_benefits = 0;
      this.total_benefits = 0;
      this.wallet_value = 0;
      this.base_previous_value = 0;

      this.wallet = this.wallet.map(t => {
        const priceData = this.calculatePriceData(t, prices_eur, prices_usd, prices_btc);
        const current_value = t.amount * priceData.current_price;
        let previous_day_value = 0;
        if (changes_24h[t.currency] !== undefined) {
          previous_day_value = t.amount * (1 / (changes_24h[t.currency]));
        }
        const current_benefit = current_value - (t.price * t.amount);

        // Update global stats
        console.log("CAlculating", t.price, t.amount, vm.total_cost);
        vm.total_cost += t.price * t.amount;
        vm.wallet_value += current_value;
        vm.total_benefits += t.benefits || 0;
        vm.total_current_benefits += current_benefit;
        vm.base_previous_value += previous_day_value;

        return {
          ...t,
          ...priceData,
          current_value,
          previous_day_value,
          current_benefit,
          loading: false // price is now loaded
        };
      });

      // Calculate percentages for each wallet item
      this.wallet.forEach(t => {
        t.percentage = Number(parseFloat(t.current_value) / this.wallet_value * 100).toFixed(2);
        t.base_current_value = Number(parseFloat(t.current_value)).toFixed(2);
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
