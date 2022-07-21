<template>
  <div>
    <el-tabs value="first" class="demo-tabs">
      <el-tab-pane label="Wallet" name="first">
        <div class="row">
          <div class="col-lg-12 col-md-6 col-sm-6">
            <div class="row">
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="top">
                  <div>
                    <div class="popover-body">Cost of current wallet bought items</div>
                  </div>
                  <div slot="reference">
                    <stats-card type="warning"
                                icon="nc-icon nc-money-coins"
                                small-title="Cost"
                                :title="cost.toString()">
                    </stats-card>
                  </div>
                </el-popover>
              </div>
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="top">
                  <div>
                    <div class="popover-body">Current wallet value</div>
                  </div>
                  <div slot="reference">
                    <stats-card type="success"
                                icon="nc-icon nc-money-coins"
                                small-title="Wallet Value"
                                :title="value.toString()">
                      <div class="stats" slot="footer">
                        <i class="nc-icon nc-refresh-69"></i>
                        {{ this.current_benefits_percent }}
                      </div>
                    </stats-card>
                  </div>
                </el-popover>
              </div>
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="top">
                  <div>
                    <div class="popover-body">Benefits in case of closing all operations with materialized w/l</div>
                  </div>
                  <div slot="reference">
                    <stats-card type="success"
                                icon="fa fa-chart-line"
                                small-title="Current W/L"
                                :title="current_benefits.toString()">

                      <div class="stats" slot="footer">
                        <i class="nc-icon nc-refresh-69"></i>
                        {{ this.benefits_percent }}
                      </div>
                    </stats-card>
                  </div>
                </el-popover>
              </div>
              <div class="col-lg-3 col-md-6 col-sm-6">
                <el-popover trigger="hover"
                            placement="top">
                  <div>
                    <div class="popover-body">Executed benefits over bought items. Only open orders</div>
                  </div>
                  <div slot="reference">
                    <stats-card type="success"
                                icon="fa fa-chart-line"
                                small-title="Materialized W/L"
                                :title="benefits.toString()">
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
                          row-key="id" :cell-class-name="testClass" :default-expand-all="false"
                          :cell-style="{padding: '0', height: '20px'}">
                  <el-table-column label="Symbol" property="ticker.ticker" sortable></el-table-column>
                  <el-table-column label="Shares" property="shares" width="100px"></el-table-column>
                  <el-table-column label="Price" property="price"></el-table-column>
                  <el-table-column label="Cost" property="cost"></el-table-column>
                  <el-table-column label="BE" property="break_even"></el-table-column>
                  <el-table-column label="Value" property="current_value" sortable></el-table-column>
                  <el-table-column label="W/L" property="win_lose" sortable></el-table-column>
                  <el-table-column label="Market price" property="current_price"></el-table-column>
                  <el-table-column label="Change" property="price_change_percent" sortable></el-table-column>
                  <el-table-column label="Pre" property="current_pre"></el-table-column>
                  <el-table-column label="Pre change" property="pre_change_percent" sortable></el-table-column>
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
                          :cell-class-name="testClass">
                  <el-table-column label="Symbol" property="ticker.ticker" width="100px" sortable></el-table-column>
                  <el-table-column label="cost" property="cost"></el-table-column>
                  <el-table-column label="Value" property="current_value"></el-table-column>
                  <el-table-column label="Percentage" property="percentage" sortable></el-table-column>
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
    [Popover.name]: Popover,
  },
  data() {
    return {
      fx_rate: 1,
      wallet: [],
      value: 0,
      current_benefits: 0,
      benefits: 0,
      cost: 0,
      current_benefits_percent: 0,
      benefits_percent: 0,
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
      this.getData();
    },
    fillFxRate(res) {
      let resStatus = res.status === 200 ? true : false;
      this.fx_rate = Number(res.data.close).toFixed(2);
    },
    createInvestChart(wallet_value) {
      this.investChart.labels = this.wallet.map(el => el.ticker.ticker);
      this.investChart.datasets[0].backgroundColor = this.wallet.map(function (el) {
        var r = Math.floor(Math.random() * 255);
        var g = Math.floor(Math.random() * 255);
        var b = Math.floor(Math.random() * 255);
        return "rgb(" + r + "," + g + "," + b + ")";
      });

      this.investChart.datasets[0].data = this.wallet.map(el => Number(el.cost / wallet_value * 100).toFixed(2));
      this.investKey += 1;
    },
    fillWallet(res) {
      let resStatus = res.status === 200 ? true : false;
      this.wallet = res.data;
      var vm = this;
      this.wallet = []
      this.cost = 0;
      this.current_benefits = 0;  // taking into account if we sell the wallet right now
      this.benefits = 0;
      this.value = 0;
      this.idx = 0;
      var bar = new Promise((resolve, reject) => {
        let testt_list = [];
        res.data.forEach(function (t, index, array) {
          t.children = t.open_orders;
          t['cost_eur'] = 0;
          if (vm.idx == 2) {
            //return;
          }
          vm.idx += 1
          t.children.forEach(function (c) {
            let shares = c.shares;
            c.ticker = {
              "ticker": c.transaction.value_date.split(' ')[0]
            }
            c.price = c.transaction.price;
            c.id = t.id + "_" + c.id;
            c.cost = c.shares * c.transaction.price;
            c.cost_eur = c.cost * c.transaction.currency_rate - c.transaction.fee - c.transaction.exchange_fee;
            t['cost_eur'] += c.cost_eur;
            c.price = c.transaction.price + t.ticker.currency;
            c.cost = Number((c.cost).toFixed(2)) + t.ticker.currency;
          });

          // update wallet item
          t['current_value'] = Number((t.shares * t.market.price || 0).toFixed(2)) + t.ticker.currency;
          let current_benefit = 0;
          if (t.ticker.currency == '€') {
            current_benefit = (t.shares * t.market.price || 0) - t.cost_eur + t.benefits + t.fees;
            vm.value += t.shares * t.market.price || 0;
          } else {
            current_benefit = (t.shares * t.market.price || 0) * vm.fx_rate - t.cost_eur + t.benefits + t.fees;
            vm.value += (t.shares * t.market.price || 0) * vm.fx_rate;
          }

          vm.current_benefits += current_benefit; //+ t.benefits;

          t['win_lose'] = Number(current_benefit).toFixed(2) + "€";
          t['current_price'] = Number((t.market.price || 0).toFixed(2)) + t.ticker.currency
          t['price_change_percent'] = Number((t.market.price_change || 0).toFixed(2)) + "%";
          t['current_pre'] = Number((t.market.pre || 0).toFixed(2)) + t.ticker.currency
          t['pre_change_percent'] = Number((t.market.price_change || 0).toFixed(2)) + "%";
          t['break_even'] = Number((t.break_even || 0).toFixed(2)) + t.ticker.currency
          t['price'] = Number((t.price).toFixed(2)) + t.ticker.currency;
          t['cost'] = Number((t.cost || 0).toFixed(2)) + t.ticker.currency

          vm.wallet.push(t);

          // update global stats
          vm.cost += t.cost_eur;
          vm.benefits += Number((t.benefits).toFixed(2));

          if (index === array.length - 1) resolve();
        });
      });

      bar.then(() => {
        console.log("Win/Lose: " + (this.value - this.cost) + ". Current benefits: "+ this.current_benefits);
        console.log("Final cost: " + (this.cost - this.benefits));

        this.cost = Number((this.cost).toFixed(2))  + "€";
        this.value = Number((this.value).toFixed(2))  + "€";
        this.current_benefits = Number(this.current_benefits).toFixed(2)  + "€";
        this.benefits = Number((this.benefits).toFixed(2))  + "€";

        let wallet_value = Number(this.wallet.reduce((a, b) => a + parseFloat(b.current_value), 0)).toFixed(2);
        this.wallet.forEach(function (t) {
          t['percentage'] = Number(parseFloat(t.current_value) / wallet_value * 100).toFixed(2);
        });

        this.current_benefits_percent = Number(wallet_value / parseFloat(this.cost) * 100 - 100).toFixed(2)  + "%";
        this.benefits_percent = Number((Number(wallet_value) + parseFloat(this.benefits)) / parseFloat(this.cost) * 100 - 100).toFixed(2)  + "%";
        this.createInvestChart(wallet_value);
      });
    },
    async getData() {
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/fx_rate").then(this.fillFxRate);
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/wallet").then(this.fillWallet);
    },
    testClass(item) {
      if (item.column.property == 'pre_price_change_percent' || item.column.property == 'current_price_change_percent'
          || item.column.property == 'win_lose') {
        if (parseInt(item.row[item.column.property]) > 0)
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

.btn-to-top {
  width: 50px;
  height: 30px;
  font-size: 22px;
  line-height: 22px;
}

.red {
  color: red
}

.green {
  color: green
}
</style>
