<template>
  <div>
    <el-tabs value="first" class="demo-tabs">
      <el-tab-pane label="Wallet" name="first">
        <div class="row">
          <div class="col-lg-12 col-md-6 col-sm-6">
            <div class="row">
              <div class="col-lg-3 col-md-6 col-sm-6">
                <stats-card type="warning"
                            icon="nc-icon nc-money-coins"
                            small-title="Cost"
                            :title="cost.toString()">
                </stats-card>
              </div>
              <div class="col-lg-3 col-md-6 col-sm-6">
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
              <div class="col-lg-3 col-md-6 col-sm-6">
                        <el-popover trigger="hover"
                    placement="top">
          <div>
            <div class="popover-body">Current benefits plus materialized benefits</div>
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
                <stats-card type="success"
                            icon="fa fa-chart-line"
                            small-title="Materialized W/L"
                            :title="benefits.toString()">
                </stats-card>
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
                          row-key="id" :cell-class-name="testClass" :default-expand-all="false">
                  <el-table-column label="Symbol" property="ticker.ticker" sortable></el-table-column>
                  <el-table-column label="Shares" property="shares" width="100px"></el-table-column>
                  <el-table-column label="Price ($/€)" property="price"></el-table-column>
                  <el-table-column label="Cost (€)" property="cost"></el-table-column>
                  <el-table-column label="BE ($/€)" property="break_even"></el-table-column>
                  <el-table-column label="Value (€)" property="current_value" sortable></el-table-column>
                  <el-table-column label="W/L (€)" property="win_lose" sortable></el-table-column>
                  <el-table-column label="Market price" property="current_price"></el-table-column>
                  <el-table-column label="Change (%)" property="price_change_percent" sortable></el-table-column>
                  <el-table-column label="Pre" property="current_pre"></el-table-column>
                  <el-table-column label="Pre change (%)" property="pre_change_percent" sortable></el-table-column>
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
                <h5 class="card-title">Positions</h5>
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

      var bar = new Promise((resolve, reject) => {
        res.data.forEach(function (t, index, array) {

          t.children = t.open_orders;
          t.children.forEach(function(c) {
            let shares = c.shares;
            c.ticker = {
              "ticker": c.transaction.value_date.split(' ')[0]
            }
            c.price = c.transaction.price;
            c.id = t.id + "_" + c.id;
            c.cost = c.shares * c.transaction.price;
            c.price = c.transaction.price;
          });

          vm.cost += Number((t.price * t.shares).toFixed(2));
          vm.value += t.shares * t.market.price || 0
          vm.benefits += Number((t.benefits).toFixed(2));
          vm.benefits = Number((vm.benefits).toFixed(2));

          let current_benefit = (t.shares * t.market.price || 0) - t.shares * t.price;
          vm.current_benefits += Number((current_benefit + t.benefits).toFixed(2));
          vm.current_benefits = Number((vm.current_benefits).toFixed(2));

          // TODO: use user currency
          /*
                  // modify current_price using fx_rate
        var current_price_eur = current_price
        var be_eur = s.break_even
        if (ticker.currency == 'EUR') {
          ticker.currency = "€";
        } else if (ticker.currency == 'USD') {
          ticker.currency = "$";
        }
        if (ticker.currency != 'EUR') {
          current_price_eur = Number(current_price * vm.fx_rate).toFixed(2);
          be_eur = Number(s.break_even / vm.fx_rate).toFixed(2);
        }
        var w = {
          "symbol": ticker.ticker,
          "currency": ticker.currency,
          "cost": Number((s.shares * s.price + s.fees).toFixed(2)) + "€",
          "cost_eur": 0,
          "current_value": Number((s.shares * current_price_eur).toFixed(2)) + "€",
          "win_lose": Number((s.shares * current_price - s.shares * s.price + s.benefits + s.fees).toFixed(2)),
          "be": be_eur + ticker.currency,
        }*/

          vm.value = Number((vm.value).toFixed(2));

          t['current_value'] = Number((t.shares * t.market.price || 0).toFixed(2)) //+ "€"
          t['win_lose'] = Number((t.shares * t.market.price - t.shares * t.price + t.benefits + t.fees).toFixed(2)) + "€"
          t['current_price'] = Number((t.market.price || 0).toFixed(2)) + t.ticker.currency
          t['price_change_percent'] = Number((t.market.price_change || 0).toFixed(2))
          t['current_pre'] = Number((t.market.pre || 0).toFixed(2)) + t.ticker.currency
          t['pre_change_percent'] = Number((t.market.price_change || 0).toFixed(2))
          t['break_even'] = Number((t.break_even || 0).toFixed(2))
          t['price'] = Number((t.price).toFixed(2)) + t.ticker.currency;
          t['cost'] = Number((t.cost || 0).toFixed(2))

          vm.wallet.push(t);
          if (index === array.length - 1) resolve();
        });
      });
      this.cost = Number((this.cost).toFixed(2));

      bar.then(() => {
        let wallet_value = Number(this.wallet.reduce((a, b) => a + b.current_value, 0)).toFixed(2);
        this.wallet.forEach(function (t) {
          t['percentage'] = Number(t.current_value / wallet_value * 100).toFixed(2);
        });
        this.current_benefits_percent = Number(wallet_value / this.cost * 100 - 100).toFixed(2);
        this.benefits_percent = Number((Number(wallet_value) + this.benefits) / this.cost * 100 - 100).toFixed(2);
        this.createInvestChart(wallet_value);
      });
    },
    async getData() {
      //await axios.get(process.env.VUE_APP_BACKEND_URL + "/accounts/fx_rate").then(this.fillFxRate);
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
