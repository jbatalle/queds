<template>
  <div>
    <div class="row">
      <div class="col-lg-12 col-md-6 col-sm-6">
        <div class="row">
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Current wallet value. So, sum of the value for each investment
                </div>
              </div>
              <template #reference>
                <stats-card type="success"
                            icon="nc-icon nc-money-coins"
                            small-title="Wallet Value"
                            :title="$filters.toCurrency(total_value, base_currency)">
                  <div class="stats" slot="footer">
                    <!--i class="nc-icon nc-refresh-69"></i-->
                  </div>
                </stats-card>
              </template>
            </el-popover>
          </div>
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Total benefits or loses for all the accounts</div>
              </div>
              <template #reference>
                <stats-card type="success"
                            icon="fa fa-chart-line"
                            small-title="Total B/L"
                            :title="$filters.toCurrency(gain, base_currency)">
                  <div class="stats" slot="footer">
                    <i class="nc-icon nc-refresh-69"></i>
                    {{ this.benefits_percent }}%
                  </div>
                </stats-card>
              </template>
            </el-popover>
          </div>
          <div class="col-lg-4 col-md-6 col-sm-6">
            <el-popover trigger="hover" placement="bottom">
              <div>
                <div class="popover-body">Daily changes</div>
              </div>
              <template #reference>
                <stats-card type="success"
                            icon="fa fa-chart-line"
                            small-title="Daily B/L"
                            :title="$filters.toCurrency((this.total_value - this.base_previous_value ), base_currency)">
                  <div class="stats" slot="footer">
                    <i class="nc-icon nc-refresh-69"></i>
                    {{ this.daily_benefits_percent }}%
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
        <balance-dist :wallet="wallet" :total_value="total_value" type="broker"/>
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
      console.log("Fill fx rate")
      let resStatus = res.status === 200;
      this.fx_rate = Number(res.data).toFixed(2);
    },
    fillWallet(res) {
      this.wallet = res.data;
      let vm = this;
      this.wallet = []
      this.total_cost = 0;
      this.total_current_benefits = 0;  // taking into account if we sell the wallet right now
      this.total_benefits = 0;
      this.total_value = 0;
      this.base_previous_value = 0;
      console.log("current fx_rate: " + this.fx_rate);

      let bar = new Promise((resolve, reject) => {
        res.data.forEach(function (t, index, array) {
          t.children = t.open_orders;
          //t['win_lose'] = t.current_benefit;
          t.symbol = t.ticker.ticker; // change here the symbol by trading_view symbol
          t.container_id = t.ticker.ticker;
          t.style = "3";
          // if no current_change, fx_rate not required
          //if (t.current_value == t.shares * t.market.price) {
          if (t.ticker.currency == 'EUR') {
            console.log(t);
          } else {
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
          // console.log(t.benefits);
          vm.total_benefits += t.benefits;
          vm.total_current_benefits += t.current_benefit;
          vm.total_value += t.base_current_value;
          // console.log("Total value: " + vm.total_value + " - " + t.base_current_value);
          vm.base_previous_value += t.base_previous_value;

          if (index === array.length - 1) resolve();
        });
      });

      console.log(this.base_previous_value);
      console.log(this.total_value);
      console.log(this.total_current_benefits);
      console.log(this.total_benefits);
      console.log(this.total_benefits + this.total_current_benefits);
      bar.then(() => {
        console.log("Win/Lose: " + (this.total_value - this.total_cost) + ". Current benefits: " + this.total_current_benefits);
        console.log("Final cost: " + (this.total_cost - this.total_benefits));
        this.wallet.forEach(function (t) {
          t['percentage'] = Number(parseFloat(t.base_current_value) / vm.total_value * 100).toFixed(2);
        });
        // console.log("Emit event to generate chart")
        //this.$emit('createInvestChart', this.total_value)
        // this.createInvestChart2(this.total_value);

        // card stats
        console.log(this.total_value);
        console.log(this.total_cost);
        this.current_benefits_percent = Number(this.total_value / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
        this.benefits_percent = Number((Number(this.total_value) + parseFloat(this.total_benefits)) / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
        // calc percentage for the day
        this.daily_benefits_percent = Number((Number(this.total_value) - parseFloat(this.base_previous_value)) / parseFloat(this.base_previous_value) * 100).toFixed(2);
      });
      this.loading = false;
    },
    fillStats(res) {
      let resStatus = res.status === 200;
      let stats = res.data;
      let total_invested = stats.buy + stats.sell + stats.gain;
      this.gain = this.total_value + stats.gain - total_invested;
      console.log("FIUll stats");
      console.log(this.gain);
    },
    async getData() {
      this.loading = true;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/fx_rate").then(this.fillFxRate);
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/wallet").then(this.fillWallet);
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/stats").then(this.fillStats);
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
