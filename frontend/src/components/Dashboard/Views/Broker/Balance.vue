<template>
  <div>
    <!--el-tabs class="demo-tabs" type="border-card" v-model="activeName">
      <el-tab-pane class="sidebar-wrapper" label="Wallet" name="first"-->
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
    <el-tabs class="demo-tabs" type="border-card" v-model="activeName">
      <el-tab-pane class="sidebar-wrapper" label="Wallet" name="first">
        <div class="row">
          <div class="col-md-12">
            <div class="card">
              <div class="card-header">
                <div class="row">
                  <div class="col-md-6">
                    <h5 class="title">Wallet </h5>
                  </div>
                  <div class="col-md-6">
                    <div class="flex text-right mb-3 gap-4">
                      <el-input class="input-sm" placeholder="Search" v-model="search" width="40%" style="width: 40%;">
                        <template #suffix>
                          <el-icon class="el-input__icon"></el-icon>
                          <i class="nc-icon nc-zoom-split"></i>
                        </template>
                      </el-input>
                      <span></span>
                      <el-button type="primary" size="small" @click="reload">Reload</el-button>
                      <el-button type="warning" size="small" @click="recalculate">Recalculate</el-button>
                    </div>
                  </div>
                </div>

                <!--p class="card-category">FX rate: {{ fx_rate }}</p-->
              </div>
              <div class="card-body table-full-width">
                <el-table v-loading="loading"
                          :data="this.wallet.filter(data => !search || data.ticker.ticker.toLowerCase().includes(search.toLowerCase())
                    || data.ticker.name.toLowerCase().includes(search.toLowerCase()))"
                          :default-sort="{property: 'win_lose', order: 'descending'}"
                          :cell-class-name="colorClass"
                          :cell-style="{padding: '0', height: '20px'}">
                  <el-table-column type="expand" fixed>
                    <template #default="props">
                      <div class="row">
                        <div class="col-lg-6 col-md-6 col-sm-12">
                          <el-table :data="props.row.children">
                            <el-table-column label="Date" prop="ticker.ticker"/>
                            <el-table-column label="Shares" prop="shares"/>
                            <el-table-column label="Price" prop="price">
                              <template v-slot:default="scope">
                                {{ $filters.toCurrency(scope.row.price, scope.row.ticker.currency) }}
                              </template>
                            </el-table-column>
                            <el-table-column label="Cost" prop="cost">
                              <template v-slot:default="scope">
                                {{ $filters.toCurrency(scope.row.cost, scope.row.ticker.currency) }}
                              </template>
                            </el-table-column>
                            <el-table-column label="Rate" prop="currency_rate">
                              <template v-slot:default="scope">
                                {{
                                  $filters.toCurrency(scope.row.transaction.currency_rate, scope.row.ticker.currency)
                                }}
                              </template>
                            </el-table-column>
                            <!--el-table-column label="Broker" prop="broker"/-->
                          </el-table>
                        </div>
                        <div class="col-lg-6 col-md-6 col-sm-12" style="height: 500px">
                          <div :id="props.row.ticker.ticker"></div>
                          <VueTradingView :options="props.row"/>
                        </div>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column label="Symbol" property="ticker.ticker" sortable fixed></el-table-column>
                  <el-table-column label="Shares" property="shares" width="100px"></el-table-column>
                  <el-table-column label="Price" property="price">
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.price, scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Cost (w. fees)" property="cost">
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.cost, scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="BEP" property="break_even">
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.break_even, scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Current price" property="current_price">
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.market.price, scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Value" property="current_value" sortable>
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.current_value, scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="W/L" property="win_lose" sortable>
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.win_lose, base_currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Day Change" property="market.price_change" sortable>
                    <template v-slot:default="scope"><!-- v-if="scope.row.market.price_change"-->
                      {{ $filters.round(scope.row.market.price_change, 2) }}%
                    </template>
                  </el-table-column>
                  <el-table-column label="Pre" property="market.pre_change">
                    <template v-slot:default="scope"><!-- v-if="scope.row.market.pre"-->
                      {{ $filters.toCurrency(scope.row.market.pre, scope.row.ticker.currency) }}
                      ({{ $filters.round(scope.row.market.pre_change, 2) }}%)
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="Distribution" name="second">
        <div class="row">
          <div class="col-md-6">
            <chart-card v-if="investChart && investChart.labels.length > 0"
                        :chart-data="investChart"
                        :chart-options="investChart.options"
                        chart-type="Pie"
                        description=""
                        :key="investKey">
              <template #header>
                <h5 class="title">Distribution </h5>
              </template>
            </chart-card>
          </div>
          <div class="col-md-6">
            <div class="card">
              <div class="card-header">
                <div class="row">
                  <div class="col-md-6">
                    <h5 class="title">Positions </h5>
                  </div>
                </div>
              </div>
              <div class="card-body table-responsive table-full-width">
                <el-table :data="this.wallet" :default-sort="{property: 'percentage', order: 'descending'}"
                          :cell-class-name="colorClass">
                  <el-table-column label="Symbol" property="ticker.ticker" width="100px" sortable></el-table-column>
                  <el-table-column label="cost" property="cost">
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.cost, scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Value" property="current_value">
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.current_value, scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Base value" property="base_current_value">
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.base_current_value, base_currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Percentage" property="percentage" sortable>
                    <template v-slot:default="scope">
                      {{ scope.row.percentage }}%
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script>

import {ElPopover, ElTable, ElTableColumn, ElTabPane, ElTabs, ElIcon} from 'element-plus';
import axios from "axios";
import StatsCard from "@/components/UIComponents/Cards/StatsCard.vue";
import ChartCard from '@/components/UIComponents/Cards/ChartCard.vue';
import VueTradingView from 'vue-trading-view/src/';

const tooltipOptions = {
  tooltipFillColor: "rgba(0,0,0,0.5)",
  tooltipFontFamily: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
  tooltipFontSize: 14,
  tooltipFontStyle: "normal",
  tooltipFontColor: "#fff",
  tooltipTitleFontFamily: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
  tooltipTitleFontSize: 14,
  tooltipTitleFontStyle: "bold",
  tooltipTitleFontColor: "#fff",
  tooltipYPadding: 6,
  tooltipXPadding: 6,
  tooltipCaretSize: 8,
  tooltipCornerRadius: 6,
  tooltipXOffset: 10,
};
export default {
  name: "Portfolio",
  components: {
    //ElTable, ElTableColumn,
    StatsCard, ChartCard, //, ElTabs, ElTabPane, ElIcon, ElPopover,
    VueTradingView
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      activeName: 'first',
      fx_rate: 1,
      loading: true,
      search: '',
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
      investChart: {
        labels: [],
        datasets: [{
          label: "Brokers",
          pointRadius: 2,
          pointHoverRadius: 1,
          backgroundColor: [],
          borderWidth: 0,
          data: []
        }],
        options: {
          tooltips: {},
          legend: {display: true}
        },
      },
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
    createInvestChart(wallet_value) {
      this.investChart.labels = this.wallet.map(el => el.ticker.ticker);
      this.investChart.datasets[0].backgroundColor = this.wallet.map(function (el) {
        let r = Math.floor(Math.random() * 255);
        let g = Math.floor(Math.random() * 255);
        let b = Math.floor(Math.random() * 255);
        return "rgb(" + r + "," + g + "," + b + ")";
      });

      this.investChart.datasets[0].data = this.wallet.map(el => Number(el.base_current_value / wallet_value * 100).toFixed(2));
      this.investKey += 1;
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
          t['win_lose'] = t.current_benefit;
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
        this.createInvestChart(this.total_value);

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
    colorClass(item) {
      if (item.column.property == 'market.price_change' || item.column.property == 'market.pre_change'
          || item.column.property == 'win_lose') {
        let objects = item.column.property.split('.')
        let value = 0;
        if (objects.length > 1) {
          value = objects.reduce((a, prop) => a[prop], item.row);
        } else {
          value = item.row[item.column.property]
        }
        if (parseFloat(value) > 0)
          return "green";
        else
          return "red"
      } else
        return "black"
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
</style>
