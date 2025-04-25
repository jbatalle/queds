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
                    Realized: {{ $filters.toCurrency(total_benefits, base_currency) }} - Unrealized: {{ $filters.toCurrency(this.total_current_benefits, base_currency) }}
                  </div>
                  </template>
                </stats-card>
              </template>
            </el-popover>
          </div>
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Wallet daily changes</div>
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
                         @recalculate="recalculate" @reload="reload"
          />
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
      total_value: 0,
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
    fillWallet(res) {
      this.wallet = res.data;
      let vm = this;
      this.wallet = []
      this.total_cost = 0;
      this.total_current_benefits = 0;  // wallet benefits taking into account if we sell the wallet right now
      this.total_benefits = 0;  // executed benefits from the wallet
      this.wallet_value = 0;  // current wallet value given the current market price
      this.base_previous_value = 0;  // wallet value from previous day

      let bar = new Promise((resolve, reject) => {
        res.data.forEach(function (t, index, array) {
          t.children = t.open_orders;
          t.symbol = t.ticker.ticker; // change here the symbol by trading_view symbol
          t.container_id = t.ticker.ticker;
          t.style = "3";
          // if no current_change, fx_rate not required
          // if (t.current_value == t.shares * t.market.price) {
          if (t.ticker.currency != 'EUR') {
            t.break_even = t.break_even * vm.fx_rate;
          }

          t.children.forEach(function (c) {
            c.ticker = {
              "ticker": c.transaction.value_date.split(' ')[0],
              "currency": t.ticker.currency
            }
            c.id = t.id + "_" + c.id;
            c.price = c.transaction.price;
          });
          vm.wallet.push(t);

          // update global stats
          vm.total_cost += t.base_cost;
          vm.total_benefits += t.benefits;
          vm.total_current_benefits += t.current_benefit;
          vm.wallet_value += t.base_current_value;
          // console.log(t.symbol + " - " + t.base_current_value + " Total wallet value: " + vm.wallet_value + "€ -");
          vm.base_previous_value += t.base_previous_value;

          if (index === array.length - 1) resolve();
        });
      });

      // - wallet_value -> DONE
      // - unrealized gains/loses -> total_current_benefits
      // - realized gains/loses -> total_benefits
      // TODO: from /stats endpoint because we look for closed orders and from benefits
      // console.log("Base previous_value: ", this.base_previous_value);
      console.log("Wallet value: ", this.wallet_value);
      console.log("Total current benefits", this.total_current_benefits);
      console.log("Total benefits: ", this.total_benefits);
      console.log("Total benefits + current benefits", this.total_benefits + this.total_current_benefits);
      bar.then(() => {
        console.log("Win/Lose: " + (this.wallet_value - this.total_cost) + ". Current benefits: " + this.total_current_benefits);
        console.log("Final cost: " + (this.total_cost - this.total_benefits));
        this.wallet.forEach(function (t) {
          t['percentage'] = Number(parseFloat(t.base_current_value) / vm.wallet_value * 100).toFixed(2);
        });

        // card stats
        this.current_benefits_percent = Number(this.wallet_value / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
        this.benefits_percent = Number((Number(this.wallet_value) + parseFloat(this.total_benefits)) / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
        // calc percentage for the day
        this.daily_benefits_percent = Number((Number(this.wallet_value) - parseFloat(this.base_previous_value)) / parseFloat(this.base_previous_value) * 100).toFixed(2);
      });
      this.loading = false;
    },
    fillStats(res) {
      let resStatus = res.status === 200;
      let stats = res.data;
      let total_invested = stats.buy + stats.sell + stats.gain;
      this.gain = this.wallet_value + stats.gain - total_invested;
      console.log("Full stats");
      console.log("Stats gain: ", stats.gain);
      console.log("Stats buy: ", stats.buy);
      console.log("Stats sell: ", stats.sell);

      console.log("Total invested: ", total_invested);
      console.log("Gain: ", this.gain);
    },
    async getData() {
      this.loading = true;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/fx_rate").then(this.fillFxRate);
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/wallet").then(this.fillWallet);
      //await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/stats").then(this.fillStats);
    },
  },
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
