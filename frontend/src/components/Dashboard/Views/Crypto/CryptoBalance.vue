<template>
  <div>
    <el-tabs value="first" class="demo-tabs">
      <el-tab-pane label="Wallet" name="first">
        <div class="row">
          <div class="col-lg-12 col-md-6 col-sm-6">
            <div class="row">
              <div class="col-lg-4 col-md-6 col-sm-6">
                <stats-card type="warning"
                            icon="nc-icon nc-money-coins"
                            small-title="Cost"
                            :title="total_cost | toCurrency(base_currency)">
                </stats-card>
              </div>
              <div class="col-lg-4 col-md-6 col-sm-6">
                <stats-card type="success"
                            icon="nc-icon nc-money-coins"
                            small-title="Wallet Value"
                            :title="value | toCurrency(base_currency)">
                </stats-card>
              </div>
              <div class="col-lg-4 col-md-6 col-sm-6">
                <stats-card type="success"
                            icon="nc-icon nc-globe"
                            small-title="Current W/L"
                            :title="benefits | toCurrency(base_currency)">
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
                    <h5 class="title">Balance</h5>
                  </div>
                  <div class="col-md-6">
                    <div class="text-right mb-3">
                      <p-button type="info" size="sm" @click="reload">Reload</p-button>
                      <p-button type="warning" size="sm" @click="recalculate">Recalculate</p-button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body table-full-width">
                <el-table :data="this.wallet" :default-sort="{property: 'win_lose', order: 'descending'}"
                          :cell-class-name="testClass" :cell-style="{padding: '0', height: '20px'}">
                  <el-table-column label="Coin" property="currency" width="100px" sortable></el-table-column>
                  <el-table-column label="Balance" property="amount">
                    <template slot-scope="scope">
                      {{ scope.row.amount | toCurrency(scope.row.currency, 8) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Price ($/€)" property="price">
                    <template slot-scope="scope">
                      {{ scope.row.price | toCurrency(scope.row.current_price_currency, 8) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Cost (€)" property="cost">
                    <template slot-scope="scope">
                      {{ scope.row.cost | toCurrency(scope.row.current_price_currency, 8) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Market price" property="current_price">
                    <template slot-scope="scope">
                      {{ scope.row.current_price | toCurrency(scope.row.current_price_currency, 8) }}
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
                          :cell-class-name="testClass">
                  <el-table-column label="Symbol" property="currency" width="100px" sortable></el-table-column>
                  <el-table-column label="cost" property="cost">
                    <template slot-scope="scope">
                      {{ scope.row.cost | toCurrency(scope.row.current_price_currency, 8) }}
                    </template>
                  </el-table-column>
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

import {Table, TableColumn, Tabs, TabPane} from 'element-ui'
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
    Table, TableColumn, StatsCard, ChartCard, Tabs, TabPane
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      wallet: [],
      value: 0,
      benefits: 0,
      total_cost: 0,
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
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/crypto/calculate").then(
          vm.$notify({
            message: 'Recalculating balances/taxes!',
            type: 'info',
          })
      );
    },
    async reload() {
      await this.getData();
    },
    createInvestChart(wallet_value) {
      this.investChart.labels = this.wallet.map(el => el.currency);
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
      this.total_cost = 0;
      this.benefits = 0;
      this.value = 0;

      res.data.forEach(function (t) {
        console.log(t);
        vm.total_cost += t.price * t.amount;
        vm.wallet.push(t)
      });

      let wallet_value = Number(this.wallet.reduce((a, b) => a + b.amount, 0)).toFixed(2);
      this.createInvestChart(wallet_value);

      this.wallet.forEach(function (t) {
        t['percentage'] = Number(t.current_value / wallet_value * 100).toFixed(2);
      });
    },
    async getData() {
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/crypto/wallet").then(this.fillWallet);
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

.red {
  color: red
}

.green {
  color: green
}
</style>
