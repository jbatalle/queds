<template>
  <div>
    <el-tabs value="first" class="demo-tabs">
      <el-tab-pane label="Wallet" name="first">
        <div class="row">
          <div class="col-lg-12 col-md-6 col-sm-6">
            <div class="row">
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="bottom">
                  <div>
                    <div class="popover-body">Cost of current wallet bought items</div>
                  </div>
                  <div slot="reference">
                    <stats-card type="warning"
                                icon="nc-icon nc-money-coins"
                                small-title="Cost"
                                :title="total_cost | toCurrency(base_currency)">
                    </stats-card>
                  </div>
                </el-popover>
              </div>
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="bottom">
                  <div>
                    <div class="popover-body">Current wallet value. Benefits vs cost and benefits from previous day
                    </div>
                  </div>
                  <div slot="reference">
                    <stats-card type="success"
                                icon="nc-icon nc-money-coins"
                                small-title="Wallet Value"
                                :title="total_value | toCurrency(base_currency)">
                      <div class="stats" slot="footer">
                        <i class="nc-icon nc-refresh-69"></i>
                        {{ this.current_benefits_percent }}% | Previous day:
                        {{ this.total_value - this.base_previous_value | toCurrency(base_currency) }}
                      </div>
                    </stats-card>
                  </div>
                </el-popover>
              </div>
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="bottom">
                  <div>
                    <div class="popover-body">Benefits in case of closing all operations with materialized w/l</div>
                  </div>
                  <div slot="reference">
                    <stats-card type="success"
                                icon="fa fa-chart-line"
                                small-title="Current W/L"
                                :title="total_current_benefits | toCurrency(base_currency)">

                      <div class="stats" slot="footer">
                        <i class="nc-icon nc-refresh-69"></i>
                        {{ this.benefits_percent }}%
                      </div>
                    </stats-card>
                  </div>
                </el-popover>
              </div>
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="bottom">
                  <div>
                    <div class="popover-body">Executed benefits over bought items. Only current open orders</div>
                  </div>
                  <div slot="reference">
                    <stats-card type="success"
                                icon="fa fa-chart-line"
                                small-title="Materialized W/L"
                                :title="total_benefits | toCurrency(base_currency)">
                    </stats-card>
                  </div>
                </el-popover>
              </div>
            </div>
          </div>
        </div>
        <div class="row">
          <div class="col-md-12">
            <div class="card">
              <div class="card-header">
                <div class="row">
                  <div class="col-md-6">
                    <h5 class="title">Wallet </h5>
                  </div>
                  <div class="col-md-6">
                    <div class="text-right mb-3">
                      <p-button type="info" size="sm" @click="reload">Reload</p-button>
                      <p-button type="warning" size="sm" @click="recalculate">Recalculate</p-button>
                    </div>
                  </div>
                </div>

                <!--p class="card-category">FX rate: {{ fx_rate }}</p-->
              </div>
              <div class="card-body table-full-width">
                <el-table :data="this.wallet" :default-sort="{property: 'win_lose', order: 'descending'}"
                          :cell-class-name="colorClass"
                          :cell-style="{padding: '0', height: '20px'}">
                  <el-table-column type="expand">
                    <template #default="props">
                      <div class="row">
                        <div class="col-lg-6 col-md-6 col-sm-6">
                          <el-table :data="props.row.children">
                            <el-table-column label="Date" prop="ticker.ticker"/>
                            <el-table-column label="Shares" prop="shares"/>
                            <el-table-column label="Price" prop="price">
                              <template slot-scope="scope">
                                {{ scope.row.price | toCurrency(scope.row.ticker.currency) }}
                              </template>
                            </el-table-column>
                            <el-table-column label="Cost" prop="cost">
                              <template slot-scope="scope">
                                {{ scope.row.cost | toCurrency(scope.row.ticker.currency) }}
                              </template>
                            </el-table-column>
                            <el-table-column label="Rate" prop="currency_rate">
                              <template slot-scope="scope">
                                {{ scope.row.transaction.currency_rate | toCurrency(scope.row.ticker.currency) }}
                              </template>
                            </el-table-column>
                            <!--el-table-column label="Broker" prop="broker"/-->
                          </el-table>
                        </div>
                        <div class="col-lg-6 col-md-6 col-sm-6">
                          <div :id="props.row.ticker.ticker"></div>
                          <VueTradingView :options="props.row"/>
                        </div>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column label="Symbol" property="ticker.ticker" sortable></el-table-column>
                  <el-table-column label="Shares" property="shares" width="100px"></el-table-column>
                  <el-table-column label="Price" property="price">
                    <template slot-scope="scope">
                      {{ scope.row.price | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Cost" property="cost">
                    <template slot-scope="scope">
                      {{ scope.row.cost | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="BE" property="break_even">
                    <template slot-scope="scope">
                      {{ scope.row.break_even | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Market price" property="current_price">
                    <template slot-scope="scope">
                      {{ scope.row.market.price | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Value" property="current_value" sortable>
                    <template slot-scope="scope">
                      {{ scope.row.current_value | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="W/L" property="win_lose" sortable>
                    <template slot-scope="scope">
                      {{ scope.row.win_lose | toCurrency(base_currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Change" property="market.price_change" sortable>
                    <template slot-scope="scope">
                      {{ scope.row.market.price_change | round(2) }}%
                    </template>
                  </el-table-column>
                  <el-table-column label="Pre" property="pre">
                    <template slot-scope="scope">
                      {{ scope.row.market.pre | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Pre change" property="market.pre_change" sortable>
                    <template slot-scope="scope">
                      {{ scope.row.market.pre_change | round(2) }}%
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
            <chart-card :chart-data="investChart"
                        :chart-options="investChart.options"
                        chart-type="Pie"
                        title="Investments"
                        description=""
                        :key="investKey">
              <template slot="header">
                <h5 class="title">Positions </h5>
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
                    <template slot-scope="scope">
                      {{ scope.row.cost | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Value" property="current_value">
                    <template slot-scope="scope">
                      {{ scope.row.current_value | toCurrency(scope.row.ticker.currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Base value" property="base_current_value">
                    <template slot-scope="scope">
                      {{ scope.row.base_current_value | toCurrency(base_currency) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Percentage" property="percentage" sortable>
                    <template slot-scope="scope">
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

import {Table, TableColumn, Tabs, TabPane, Popover} from 'element-ui';
import axios from "axios";
import StatsCard from "../../../UIComponents/Cards/StatsCard";
import ChartCard from 'src/components/UIComponents/Cards/ChartCard';
import VueTradingView from 'vue-trading-view/src/vue-trading-view';

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
  name: "Wallet",
  components: {
    Table, TableColumn, StatsCard, ChartCard, Tabs, TabPane,
    [Popover.name]: Popover, VueTradingView
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      fx_rate: 1,
      wallet: [],
      total_value: 0,
      total_current_benefits: 0,
      total_benefits: 0,
      total_cost: 0,
      current_benefits_percent: 0,
      benefits_percent: 0,
      base_previous_value: 0,
      investKey: 0,
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
          tooltips: tooltipOptions,
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
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/calculate").then(
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
      this.fx_rate = Number(res.data.close).toFixed(2);
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

      let bar = new Promise((resolve, reject) => {
        res.data.forEach(function (t, index, array) {
          t.children = t.open_orders;
          t['win_lose'] = t.current_benefit;
          t.symbol = t.ticker.ticker;
          t.container_id = t.ticker.ticker;
          t.style = "3";
          t.break_even = t.break_even * vm.fx_rate;

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
          vm.total_value += t.base_current_value;
          vm.base_previous_value += t.base_previous_value;

          if (index === array.length - 1) resolve();
        });
      });

      bar.then(() => {
        console.log("Win/Lose: " + (this.total_value - this.total_cost) + ". Current benefits: " + this.total_current_benefits);
        console.log("Final cost: " + (this.total_cost - this.total_benefits));
        this.wallet.forEach(function (t) {
          t['percentage'] = Number(parseFloat(t.base_current_value) / vm.total_value * 100).toFixed(2);
        });
        this.createInvestChart(this.total_value);

        // card stats
        this.current_benefits_percent = Number(this.total_value / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
        this.benefits_percent = Number((Number(this.total_value) + parseFloat(this.total_benefits)) / parseFloat(this.total_cost) * 100 - 100).toFixed(2);
      });
    },
    async getData() {
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/fx_rate").then(this.fillFxRate);
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/wallet").then(this.fillWallet);
    },
    colorClass(item) {
      if (item.column.property == 'market.price_change' || item.column.property == 'market.pre_change'
          || item.column.property == 'win_lose') {
        let objects = item.column.property.split('.')
        let value = 0;
        if (objects.length > 1){
          value =  objects.reduce((a, prop) => a[prop], item.row);
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

.red {
  color: red
}

.green {
  color: green
}
</style>
