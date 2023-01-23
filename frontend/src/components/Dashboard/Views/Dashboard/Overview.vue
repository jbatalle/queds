<template>
  <div>
    <div class="row">
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top">
          <div>
            <div class="popover-body">Value of your portfolio taking into account current prices</div>
          </div>
          <div slot="reference">
            <stats-card type="success"
                        icon="nc-icon nc-money-coins"
                        small-title="Portfolio value"
                        :title="total_value | toCurrency(base_currency)"
            >
              <div class="stats" slot="footer">
                <i class="nc-icon nc-refresh-69"></i>
                Current invests: {{ total_invested | toCurrency(base_currency) }}
              </div>
            </stats-card>
          </div>
        </el-popover>
      </div>
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top">
          <div>
            <div class="popover-body">Materialized gain</div>
          </div>
          <div slot="reference">
            <stats-card type="success"
                        icon="nc-icon nc-globe"
                        small-title="Gain"
                        :title="gain | toCurrency(base_currency)">
              <div class="stats" slot="footer">
                <i class="nc-icon nc-refresh-69"></i>
                Total buy: {{ buy | toCurrency(base_currency) }}. Total sell: {{ -sell | toCurrency(base_currency) }}
              </div>
            </stats-card>
          </div>
        </el-popover>
      </div>
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top">
          <div>
            <div class="popover-body">Future gains. Materialized gains + portfolio value</div>
          </div>
          <div slot="reference">
            <stats-card type="success"
                        icon="fa fa-chart-line"
                        small-title="W/L"
                        :title="(total_value + gain - total_invested) | toCurrency(base_currency)">
              <div class="stats" slot="footer">
                <i class="nc-icon nc-refresh-69"></i>
                {{ (((total_value + gain) / total_invested) - 1) * 100 | round }}%
              </div>
            </stats-card>
          </div>
        </el-popover>
      </div>
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top">
          <div>
            <div class="popover-body">Total fiat available in accounts</div>
          </div>
          <div slot="reference">
            <stats-card type="success"
                        icon="nc-icon nc-money-coins"
                        small-title="Fiat"
                        :title="fiat | toCurrency(base_currency)">
            </stats-card>
          </div>
        </el-popover>
      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <chart-card :chart-data="totalChart"
                    :chart-options="totalChart.options"
                    chart-type="Pie"
                    title="Banks"
                    :key="totalKey">
          <template slot="header">
            <h5 class="card-title">Total Portfolio</h5>
          </template>
        </chart-card>
      </div>
      <div class="col-md-4">
        <chart-card :chart-data="investChart"
                    :chart-options="investChart.options"
                    chart-type="Pie"
                    title="Investments"
                    description=""
                    :key="investKey">
          <template slot="header">
            <h5 class="card-title">Invested</h5>
          </template>
        </chart-card>
      </div>
      <div class="col-md-4">
      </div>
    </div>
  </div>
</template>
<script>
import ChartCard from 'src/components/UIComponents/Cards/ChartCard';
import StatsCard from 'src/components/UIComponents/Cards/StatsCard';
import axios from "axios";
import PieChart from "../../../UIComponents/Charts/PieChart";
import {Popover} from 'element-ui'

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
  components: {
    StatsCard,
    ChartCard,
    PieChart,
    [Popover.name]: Popover,
  },
  created() {
    this.getData()
  },
  methods: {
    calc_percentage(partial_balance, total) {
      return (parseFloat(partial_balance) / total * 100).toFixed(2)
    },
    fillBrokers(broker_account) {
      broker_account.virtual_balance = Number(broker_account.virtual_balance).toFixed(2);
      this.brokerAccounts.push(broker_account)
      return broker_account;
    },
    fillExchanges(account) {
      this.exchangeAccounts.push(account)
      return account;
    },
    fillTotal() {
      this.wallet_value = Number(this.brokerAccounts.reduce((a, b) => parseFloat(a) + parseFloat(b['virtual_balance']), 0)).toFixed(2);

      let benefits = this.total_value - this.total_invested;
      console.log("Current benefits: " + benefits);
      // this.total_value = Number(this.brokerAccounts.reduce((a, b) => parseFloat(a) + parseFloat(b['virtual_balance']), 0)).toFixed(2);
      this.fiat += this.brokerAccounts.reduce((a, b) => a + b['balance'], 0);
      this.fiat += this.exchangeAccounts.reduce((a, b) => a + b['balance'], 0);

      this.createPortfolioChart();
      this.createInvestChart();
    },
    createInvestChart() {
      this.investChart.labels = this.brokerAccounts.map(function (el) {
        return el.name;
      });
      this.investChart.datasets[0].backgroundColor = this.brokerAccounts.map(function (el) {
        var r = Math.floor(Math.random() * 255);
        var g = Math.floor(Math.random() * 255);
        var b = Math.floor(Math.random() * 255);
        return "rgb(" + r + "," + g + "," + b + ")";
      });
      this.investChart.datasets[0].data = this.brokerAccounts.map(el => this.calc_percentage(el.virtual_balance, this.wallet_value));
      this.investKey += 1;
    },
    createPortfolioChart() {
      this.totalChart.labels = this.total_assets.map(function (el) {
        return el.name;
      });
      this.totalChart.datasets[0].backgroundColor = this.total_assets.map(function (el) {
        var r = Math.floor(Math.random() * 255);
        var g = Math.floor(Math.random() * 255);
        var b = Math.floor(Math.random() * 255);
        return "rgb(" + r + "," + g + "," + b + ")";
      });
      this.totalChart.datasets[0].data = this.total_assets.map(el => this.calc_percentage(el.virtual_balance, this.wallet_value));
      this.totalKey += 1;
    },
    fillWallet(res) {
      let wallet = res.data;
      this.total_value += wallet.reduce((a, b) => a + (b.base_current_value), 0);
      this.roi = (this.total_value + this.total_invested) / this.total_invested;
    },
    fillCryptoWallet(res) {
      let wallet = res.data;
      this.total_value += wallet.reduce((a, b) => a + (b.current_value), 0);
      this.roi = (this.total_value + this.total_invested) / this.total_invested;
    },
    fillStats(res) {
      let resStatus = res.status === 200;
      let stats = res.data;
      //this.total_invested = stats.invested;
      this.buy = stats.buy;
      this.sell = stats.sell;
      this.total_invested = this.buy + this.sell + stats.gain;
      this.gain = stats.gain;
    },
    fillAccounts(res) {
      let resStatus = res.status === 200;
      this.accounts = res.data;

      let vm = this;
      let bar = new Promise((resolve, reject) => {
        vm.accounts.forEach((p, index, array) => {
          let asset = undefined;
          if (p.entity_type === 1) {
            asset = vm.fillBrokers(p);
          } else if (p.entity_type === 3) {
            asset = vm.fillExchanges(p);
          }
          if (asset != undefined) {
            vm.total_assets.push(asset);
          }
          if (index === array.length - 1) resolve();
        });
      });
      bar.then(() => {
        this.fillTotal();
      });
    },
    fillFxRate(res) {
      let resStatus = res.status === 200;
      this.fx_rate = Number(res.data.close).toFixed(2);
    },
    async getData() {
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/fx_rate").then(this.fillFxRate);
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/stats").then(this.fillStats);
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/wallet").then(this.fillWallet);
      // await axios.get(process.env.VUE_APP_BACKEND_URL + "/crypto/wallet").then(this.fillCryptoWallet);
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/entities/accounts").then(this.fillAccounts);
    }
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      fx_rate: 1,
      total_assets: [],
      brokerAccounts: [],
      exchangeAccounts: [],
      totalKey: 0,
      investKey: 0,
      componentKey2: 0,
      fiat: 0,
      gain: 0,
      total_value: 0,
      wallet_value: 0,
      total_invested: 0,
      buy: 0,
      sell: 0,
      totalChart: {
        labels: [],
        datasets: [{
          label: "Banks",
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
      bankChart: {
        labels: [],
        datasets: [{
          label: "Banks",
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
    }
  },
}
</script>
<style>

</style>
