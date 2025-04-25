<template>
  <div>
    <div class="row">
      <!-- Portfolio Value Card -->
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top" content="Value of your portfolio based on current prices">
          <template #reference>
            <stats-card type="success" icon="nc-icon nc-money-coins" small-title="Portfolio Value"
                        :title="$filters.toCurrency(total_wallet_value, base_currency)">
              <template #footer>
                <div class="stats">
                  <i class="nc-icon nc-chart-bar-32"></i>
                  Cost: {{ $filters.toCurrency(total_wallet_cost, base_currency) }} |
                  Unrealized Profit: {{ $filters.toCurrency(total_unrealized_profit, base_currency) }} ({{ $filters.round(total_unrealized_profit_percentage) }}%)
                </div>
              </template>
            </stats-card>
          </template>
        </el-popover>
      </div>

      <!-- Realized Gains Card -->
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top" title="Realized Profit from Closed Operations">
          <template #reference>
              <stats-card type="success" icon="nc-icon nc-globe" small-title="Closed positions"
                          :title="$filters.toCurrency(total_gain, base_currency)">
                <template #footer>
                    <div class="stats">
                      <i class="nc-icon nc-check-2"></i>
                      Realized Gains YTD: {{ $filters.toCurrency(realized_gains_ytd, base_currency) }}
                      <!--Avg Gain per Position: {{ $filters.toCurrency(average_gain_per_position, base_currency) }}-->
                  </div>
                  </template>
              </stats-card>
          </template>
        </el-popover>
      </div>

      <!-- Total P/L Card -->
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top" title="Total Profit including Open and Closed Positions">
          <template #reference>
            <stats-card type="success" icon="fa fa-chart-line" small-title="Total P/L" :title="$filters.toCurrency(totalPL, base_currency)">
              <template #footer>
                <div class="stats">
                  <i class="nc-icon nc-chart-pie-36"></i>
                  ROI: {{ $filters.round(roi) }}% |
                  Realized Profit: {{ $filters.round(total_realized_profit) }}%
                </div>
              </template>
            </stats-card>
          </template>
        </el-popover>
      </div>

      <!-- Available Fiat Card -->
      <div class="col-lg-3 col-md-6 col-sm-6">
        <el-popover trigger="hover" placement="top" title="Available Fiat">
          <template #reference>
            <stats-card type="success" icon="nc-icon nc-bank" small-title="Fiat"
                        :title="$filters.toCurrency(fiat, base_currency)">
              <template #footer>
                <div class="stats">
                  <i class="nc-icon nc-money-coins"></i>
                  Liquidity Ratio: {{ $filters.round(liquidity_ratio) }}%
                </div>
              </template>
            </stats-card>
          </template>
        </el-popover>
      </div>
    </div>

    <!-- Portfolio Summary Table -->
    <div class="row mb-4">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            <h4 class="card-title">Portfolio Summary</h4>
          </div>
          <div class="card-body">
            <div class="table-responsive">
              <table class="table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Value ({{ base_currency }})</th>
                    <th>Cost ({{ base_currency }})</th>
                    <th>Unrealized P/L ({{ base_currency }})</th>
                    <th>Realized Gains ({{ base_currency }})</th>
                    <th>Realized Gains YTD ({{ base_currency }})</th>
                    <th>Total P/L  ({{ base_currency }})</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Brokers</strong></td>
                    <td>{{ $filters.toCurrency(broker_wallet_value, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(broker_wallet_cost, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(broker_unrealized_profit, base_currency) }} ({{ $filters.round((broker_unrealized_profit / broker_wallet_cost) * 100) }}%)</td>
                    <td>{{ $filters.toCurrency(broker_gain, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(broker_realized_gains_ytd, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(total_wallet_gain, base_currency) }}</td>
                  </tr>
                  <tr>
                    <td><strong>Crypto</strong></td>
                    <td>{{ $filters.toCurrency(crypto_wallet_value, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(crypto_wallet_cost, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(crypto_unrealized_profit, base_currency) }} ({{ $filters.round((crypto_unrealized_profit / crypto_wallet_cost) * 100) }}%)</td>
                    <td>{{ $filters.toCurrency(crypto_gain, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(crypto_realized_gains_ytd, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(total_crypto_gain, base_currency) }}</td>
                  </tr>
                  <tr class="table-success">
                    <td><strong>Total</strong></td>
                    <td>{{ $filters.toCurrency(total_wallet_value, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(total_wallet_cost, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(total_unrealized_profit, base_currency) }} ({{ $filters.round(total_unrealized_profit_percentage) }}%)</td>
                    <td>{{ $filters.toCurrency(total_gain, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(realized_gains_ytd, base_currency) }}</td>
                    <td>{{ $filters.toCurrency(totalPL, base_currency) }}</td>
                  </tr>
                  <tr>
                    <td><strong>Fiat Balance</strong></td>
                    <td colspan="7">{{ $filters.toCurrency(fiat, base_currency) }}</td>
                  </tr>
                  <tr class="table-info">
                    <td><strong>Total Portfolio</strong></td>
                    <td colspan="7">{{ $filters.toCurrency(total_wallet_value + fiat, base_currency) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <!-- Portfolio Distribution Chart -->
      <div class="col-md-4">
        <chart-card
          v-if="distributionChart?.labels?.length > 0"
          :chart-data="distributionChart"
          :chart-options="distributionChart.options"
          chart-type="Pie"
          title="Wallet Distribution (Brokers vs. Exchanges)"
          :key="distributionKey"
        >
          <template #header>
            <h5 class="title">Wallet Distribution</h5>
          </template>
        </chart-card>
      </div>

      <!-- Distribution by account -->
      <div class="col-md-4">
        <chart-card
          v-if="accountDistributionChart?.labels?.length > 0"
          :chart-data="accountDistributionChart"
          :chart-options="accountDistributionChart.options"
          chart-type="Pie"
          title="Wallet Distribution by Account"
          :key="accountDistributionKey"
        >
          <template #header>
            <h5 class="title">Wallet by Account</h5>
          </template>
        </chart-card>
      </div>

      <div class="col-md-4">
        <chart-card
          v-if="totalChart?.labels?.length > 0"
          :chart-data="totalChart"
          :chart-options="totalChart.options"
          chart-type="Pie"
          title="Total"
          :key="totalKey">
          <template #header>
            <h5 class="title">Total Portfolio</h5>
          </template>
        </chart-card>
      </div>

      <!-- Account Distribution Bar Chart -->
      <div class="col-md-6">
        <chart-card
          v-if="accountBarChart?.labels?.length > 0"
          :chart-data="accountBarChart"
          :chart-options="accountBarChart.options"
          chart-type="Bar"
          title="Wallet Distribution by Account"
          :key="accountBarChartKey"
        >
          <template #header>
            <h5 class="title">Wallet by Account (Bar)</h5>
          </template>
        </chart-card>
      </div>

      <!-- Performance Over Time (Portfolio Growth) -->
      <div class="col-md-6">
        <chart-card
          v-if="performanceChart?.labels?.length > 0"
          :chart-data="performanceChart"
          :chart-options="performanceChart.options"
          chart-type="Line"
          title="Portfolio Growth Over Time"
          :key="performanceKey"
        >
          <template #header>
            <h5 class="title">Portfolio Growth</h5>
          </template>
        </chart-card>
      </div>
    </div>
  </div>
</template>

<script>
import ChartCard from '@/components/UIComponents/Cards/ChartCard.vue';
import axios from "axios";
import { ElPopover } from 'element-plus';
import { round } from "../filters";


export default {
  components: {
    ChartCard,
    ElPopover
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency') || 'EUR',
      fx_rate: 1,
      total_assets: [],
      accounts: [],
      brokerAccounts: [],
      exchangeAccounts: [],
      totalKey: 0,
      distributionKey: 0,
      accountDistributionKey: 0,
      accountBarChartKey: 0,
      performanceKey: 0,

      // Chart data placeholders
      distributionChart: { labels: [], datasets: [] },
      accountDistributionChart: { labels: [], datasets: [] },
      accountBarChart: { labels: [], datasets: [] },
      performanceChart: {
        labels: [],
        datasets: [],
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: false
            }
          }
        }
      },

      // global stats
      fiat: 0,
      total_wallet_value: 0,
      total_wallet_cost: 0,
      total_realized_profit: 0,
      total_unrealized_profit: 0,
      total_gain: 0,
      total_unrealized_profit_percentage: 0,
      roi: 0,
      liquidity_ratio: 0,
      realized_gains_ytd: 0,

      // broker vars
      broker_gain: 0,
      broker_wallet_value: 0,
      broker_wallet_cost: 0,
      broker_realized_profit: 0,
      broker_unrealized_profit: 0,
      broker_unrealized_profit_percentage: 0,
      broker_realized_gains_ytd: 0,
      broker_invested: 0,
      total_wallet_gain: 0,

      // crypto vars
      crypto_gain: 0,
      crypto_wallet_value: 0,
      crypto_wallet_cost: 0,
      crypto_unrealized_profit: 0,
      crypto_realized_profit: 0,
      crypto_realized_gains_ytd: 0,
      crypto_invested: 0,
      total_crypto_gain: 0,

      total_invested: 0,

      buy: 0,
      sell: 0,
      loaded: false,
      totalChart: {
        labels: [],
        datasets: [
          {
            label: "Assets",
            backgroundColor: [],
            data: [],
          },
        ],
        options: {
          tooltips: {
            backgroundColor: "rgba(0,0,0,0.5)",
            fontColor: "#fff",
            titleFontColor: "#fff",
            yPadding: 6,
            xPadding: 6,
            caretSize: 8,
            cornerRadius: 6,
            xOffset: 10,
          },
          legend: { display: true },
        },
      },
      investChart: {
        labels: [],
        datasets: [
          {
            label: "Brokers",
            backgroundColor: [],
            data: [],
          },
        ],
        options: {
          tooltips: {
            backgroundColor: "rgba(0,0,0,0.5)",
            fontColor: "#fff",
            titleFontColor: "#fff",
            yPadding: 6,
            xPadding: 6,
            caretSize: 8,
            cornerRadius: 6,
            xOffset: 10,
          },
          legend: { display: true },
        },
      },
    }
  },
  computed: {
    totalPL() {
      return this.total_wallet_value + this.total_gain - this.total_invested;
    },
    totalROI() {
      return (((this.total_wallet_value + this.total_gain) / this.total_invested) - 1) * 100;
    },
  },
  async mounted() {
    this.totalChart = {
      "options": {},
      "datasets": [{"data": [1, 99]}]
    }
    await this.getData();
    this.setupPerformanceChart();
  },
  methods: {
    calc_percentage(partial_balance, total) {
      return (parseFloat(partial_balance) / total * 100).toFixed(2);
    },
    fillBrokers(broker_account) {
      broker_account.virtual_balance = 0;
      this.brokerAccounts.push(broker_account);
      return broker_account;
    },
    fillExchanges(account) {
      account.virtual_balance = 0;
      this.exchangeAccounts.push(account);
      return account;
    },
    createDistributionChart() {
      console.log("Create distribution chart");
      const brokerValue = this.brokerAccounts.reduce((acc, broker) => acc + broker.virtual_balance, 0);
      const exchangeValue = this.exchangeAccounts.reduce((acc, exchange) => acc + exchange.virtual_balance, 0);
      console.log("Broker value", brokerValue);
      console.log("Exchange value", exchangeValue);

      this.distributionChart = {
        labels: ["Brokers", "Exchanges", "Fiat"],
        datasets: [
          {
            backgroundColor: ["#FF6384", "#36A2EB", "#5cc305"],
            data: [brokerValue, exchangeValue, this.fiat],
          },
        ],
        options: {
          responsive: true,
          legend: { display: true },
        },
      };
      this.distributionKey++;
    },
    // Distribution by individual accounts
    createAccountDistributionChart() {
      const accounts = [...this.brokerAccounts, ...this.exchangeAccounts];

      this.accountDistributionChart = {
        labels: accounts.map((account) => account.name),
        datasets: [
          {
            label: "Wallet Distribution",
            backgroundColor: accounts.map(() => {
              const r = Math.floor(Math.random() * 255);
              const g = Math.floor(Math.random() * 255);
              const b = Math.floor(Math.random() * 255);
              return `rgb(${r}, ${g}, ${b})`;
            }),
            data: accounts.map((account) => account.virtual_balance),
          },
        ],
        options: {
          responsive: true,
          legend: { display: true },
        },
      };
      this.accountDistributionKey++;

      // Create Bar chart version
      this.accountBarChart = {
        labels: accounts.map((account) => account.name),
        datasets: [
          {
           // label: "Balance2",
            backgroundColor: accounts.map(() => {
              const r = Math.floor(Math.random() * 255);
              const g = Math.floor(Math.random() * 255);
              const b = Math.floor(Math.random() * 255);
              return `rgb(${r}, ${g}, ${b})`;
            }),
            data: accounts.map((account) => account.virtual_balance),
          },
        ],
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: true
            }
          },
          plugins: {
            legend: {display: false},
          },
        },
      };
      this.accountBarChartKey++;
    },
    createPortfolioChart() {
      // shows distribution of assets in the portfolio by Broker/Exchange or Fiat
      console.log("Create Portfolio chart");
      console.log(this.total_assets);
      this.loaded = true;
      this.totalChart = {
        labels: this.total_assets.map((asset) => asset.currency),
        datasets: [
          {
            //label: this.total_assets.map(asset => asset.currency),
            backgroundColor: this.total_assets.map(() => {
              const r = Math.floor(Math.random() * 255);
              const g = Math.floor(Math.random() * 255);
              const b = Math.floor(Math.random() * 255);
              return `rgb(${r}, ${g}, ${b})`;
            }),
            data: this.total_assets.map((asset) => (asset.amount * asset.price)),
          },
        ],
        options: {
          responsive: true,
          legend: {display: false},
          plugins: {
            legend: {display: false},
          },
        },
      }
      this.totalKey++;
    },
    setupPerformanceChart() {
      // Sample data for portfolio growth over time
      // In production, this should use real historical data
      const today = new Date();
      const dates = [];
      const values = [];

      // Generate 12 months of data points
      for (let i = 11; i >= 0; i--) {
        const date = new Date(today);
        date.setMonth(today.getMonth() - i);
        dates.push(date.toLocaleDateString('default', { month: 'short', year: 'numeric' }));

        // Generate a sample growth trend - replace with real historical data
        const baseValue = this.total_wallet_value > 0 ? this.total_wallet_value * 0.7 : 1000;
        const randomGrowth = Math.random() * 0.05 - 0.02; // -2% to +3% random change
        const growthFactor = 1 + (i * 0.02) + randomGrowth; // Progressive growth plus random noise
        values.push(baseValue * growthFactor);
      }

      this.performanceChart = {
        labels: dates,
        datasets: [{
          label: 'Portfolio Value',
          borderColor: '#4acccd',
          pointBackgroundColor: '#4acccd',
          pointRadius: 3,
          pointHoverRadius: 5,
          fill: false,
          borderWidth: 2,
          data: values
        }],
        options: {
          responsive: true,
          scales: {
            y: {
              beginAtZero: false,
              ticks: {
                callback: (value) => {
                  return this.$filters?.toCurrency
                    ? this.$filters.toCurrency(value, this.base_currency)
                    : value;
                }
              }
            }
          },
          tooltips: {
            callbacks: {
              label: (tooltipItem) => {
                return this.$filters?.toCurrency
                  ? this.$filters.toCurrency(tooltipItem.yLabel, this.base_currency)
                  : tooltipItem.yLabel;
              }
            }
          }
        }
      };
      this.performanceKey++;
    },
    processStockStats(res) {
      let wallet = res.data;
      this.broker_wallet_value += wallet.reduce((acc, asset) => acc + asset.base_current_value, 0);
      this.broker_wallet_cost += wallet.reduce((acc, asset) => acc + asset.base_cost, 0);
      this.broker_unrealized_profit += wallet.reduce((acc, asset) => acc + asset.current_benefit, 0);
      if (this.total_invested > 0) {
        this.broker_realized_profit = (this.broker_gain / this.total_invested) * 100;
      } else {
        this.broker_realized_profit = 0;
      }

      this.total_wallet_gain = this.broker_wallet_value + this.broker_gain - this.broker_invested;

      console.log("-------------- Broker stats --------------");
      console.log("Broker value: " + this.broker_wallet_value);
      console.log("Stats gain: ", this.broker_gain); // IRS
      console.log("Broker invested: ", this.broker_invested);
      console.log("Broker cost: ", this.broker_wallet_cost);
      console.log("Realized gains ytd: ", this.broker_realized_gains_ytd);
      console.log("Total wallet gain: ", this.total_wallet_gain);

      console.log("Wallet P/L: ", this.broker_wallet_value - this.broker_wallet_cost);
      // TODO: which P/L is correct?
      console.log("Total P/L: ", this.broker_wallet_value + this.broker_gain - this.total_invested);
      console.log("Total P/L: ", this.broker_wallet_value - this.broker_wallet_cost + this.broker_gain);
      console.log("Realized Profit: ", this.broker_realized_profit);
      console.log("Unrealized Profit: ", this.broker_unrealized_profit);

      //  {{ $filters.round((((wallet_value + gain) / total_invested) - 1) * 100) }}%
      //this.roi = (this.wallet_value + this.total_invested) / this.total_invested;
      this.roi = (((this.broker_wallet_value + this.gain) / this.total_invested) - 1) * 100;

      console.log("Broker accounts", this.accounts);
      this.accounts.forEach(account => {
        // Iterate over wallets and sum the amount*current_price_eur for each open order
        // if open orders are not correctly created, we'll have a mismatch between total_wallet value and charts
        wallet.forEach(w => {
          // Check if any open_orders belong to this account
          w.open_orders.forEach(order => {
            if (order.transaction.account_id === account.id) {
              // Add wallet amount to the virtual_balance of the account
              // console.log(w.market !== null);
              if (Object.keys(w.market).length !== 0) {
                if (w.ticker.currency != 'EUR') {
                  account.virtual_balance += order.shares * w.market.price * this.fx_rate;
                } else {
                  account.virtual_balance += order.shares * w.market.price;
                }
              }
            }
          });
        });
      });
    },
    fillStats(res) {
      let resStatus = res.status === 200;
      let stats = res.data;
      // this.buy += stats.buy;
      // this.sell += stats.sell;
      this.broker_invested += stats.buy + stats.sell + stats.gain;
      this.broker_gain += stats.gain;
      this.broker_realized_gains_ytd += stats.current_year_gain;
    },
    fillCryptoStats(res) {
      let stats = res.data;
      // this.buy += stats.buy;
      // this.sell += stats.sell;
      this.crypto_invested += stats.buy + stats.sell + stats.gain;
      this.crypto_gain += stats.gain;
      this.crypto_realized_gains_ytd += stats.current_year_gain;
    },
    fillTotalStats() {
      console.log("-------------- Full stats --------------");
      this.fiat = this.brokerAccounts.reduce((acc, broker) => acc + (broker.balance || 0), 0) +
                this.exchangeAccounts.reduce((acc, exchange) => acc + (exchange.balance || 0), 0);

      this.total_gain = this.broker_gain + this.crypto_gain;
      this.total_wallet_value = this.broker_wallet_value + this.crypto_wallet_value;
      this.liquidity_ratio = (this.fiat / (this.total_wallet_value + this.fiat)) * 100;

      this.total_wallet_cost = this.broker_wallet_cost + this.crypto_wallet_cost;
      this.total_invested = this.broker_invested + this.crypto_invested;
      let benefits = this.total_wallet_value - this.total_invested;

      this.total_realized_profit = this.broker_realized_profit + this.crypto_realized_profit;
      this.total_unrealized_profit = this.broker_unrealized_profit + this.crypto_unrealized_profit;
      this.total_unrealized_profit_percentage = (this.total_unrealized_profit / this.total_wallet_cost) * 100;
      this.roi = (((this.total_wallet_value + this.total_gain) / this.total_invested) - 1) * 100;
      this.realized_gains_ytd = this.broker_realized_gains_ytd + this.crypto_realized_gains_ytd;

      console.log("Fiat: " + this.fiat);
      console.log("total_gain: " + this.total_gain);
      console.log("Current Wallet value: " + this.total_wallet_value);
      console.log("Current Wallet cost: " + this.total_wallet_cost);
      console.log("Current benefits: " + benefits);
      console.log("Total realized profit: " + this.total_realized_profit);
      console.log("Total Unrealized profit %: " + this.total_unrealized_profit_percentage);

      this.createPortfolioChart();
      this.createDistributionChart();
      this.createAccountDistributionChart();
    },
    processCryptoStats(assets, prices) {
      let crypto_wallet_cost = 0;
      let crypto_wallet_value = 0;

      assets.forEach(asset => {
        const price = prices.eur[asset.currency];
        crypto_wallet_value += asset.amount * (1/price || 0);
        //TODO: get account associated to that order an increment the virtual_balance
        asset.open_orders.forEach(order => {
          let cost_price = 0
          if (order.user_price !== 0) {
            // cost_price = (order.order.type === 0 && order.user_price) ? order.user_price: (1/order.user_price);
            cost_price = order.user_price;
          }
          crypto_wallet_cost += order.amount * (cost_price || 0) + order.order.fee;
          if (crypto_wallet_cost > 100000){
            console.log("BIG wallet cost", asset.currency, crypto_wallet_cost, order);
          }
          if (!isNaN(price) && price > 0) {
                this.exchangeAccounts.find(e => e.id === order.order.account_id).virtual_balance += order.amount * (1/price || 0);
          }
        });
        if (asset) this.total_assets.push(asset);
      });

      this.crypto_wallet_value += crypto_wallet_value;
      this.crypto_wallet_cost += crypto_wallet_cost;
      this.crypto_realized_profit = (this.crypto_gain / this.total_invested) * 100;
      this.crypto_unrealized_profit += this.crypto_wallet_value - this.crypto_wallet_cost;
      this.total_crypto_gain = this.crypto_wallet_value + this.crypto_gain - this.crypto_invested;
      //this.crypto_unrealized_profit += assets.reduce((acc, asset) => acc + (asset.current_benefit || 0), 0);

      console.log("-------------- Crypto stats --------------");
      console.log("Crypto value: " + this.crypto_wallet_value);
      console.log("Crypto gain: ", this.crypto_gain); // IRS
      console.log("Crypto invested: ", this.crypto_invested);
      console.log("Crypto cost: ", this.crypto_wallet_cost);
      console.log("Crypto realized gains ytd: ", this.crypto_realized_gains_ytd);
      console.log("Total Crypto gain: ", this.total_Crypto_gain);

      console.log("Crypto P/L: ", this.crypto_wallet_value - this.crypto_wallet_cost);
      console.log("Crypto P/L: ", this.crypto_wallet_value + this.crypto_gain - this.total_invested);
      console.log("Crypto P/L: ", this.crypto_wallet_value - this.crypto_wallet_cost + this.crypto_gain);
      console.log("Crypto Realized Profit: ", this.crypto_realized_profit);
      console.log("Unrealized Profit: ", this.crypto_unrealized_profit);

      //this.accounts.forEach(account => {
      this.exchangeAccounts.forEach(account => {
        // Iterate over wallets and sum the amount*current_price_eur for each open order
        assets.forEach(w => {
          // Check if any open_orders belong to this account
          if (w.open_orders && Array.isArray(w.open_orders)) {
            w.open_orders.forEach(order => {
              if (order.order && order.order.account_id === account.id) {
                // Add wallet amount to the virtual_balance of the account
                if (!isNaN(w.current_price_eur)) {
                  account.virtual_balance += order.amount * w.current_price_eur;
                }
              }
            });
          }
        });
      });
    },
    fillAccounts(res) {
      this.accounts = res.data;
      let vm = this;

      vm.accounts.forEach((account) => {
        let asset;
        if (account.entity_type === 1) {
          asset = this.fillBrokers(account);
        } else if (account.entity_type === 3) {
          asset = this.fillExchanges(account);
        }
        // if (asset) this.total_assets.push(asset);
      });
    },
    fillFxRate(res) {
      let resStatus = res.status === 200;
      this.fx_rate = Number(res.data).toFixed(2);
    },
    async getData() {
      try {
        // Fetch the exchange rate and accounts in parallel
        const initialRequests = [
          axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/fx_rate").then(this.fillFxRate),
          axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts").then(this.fillAccounts),
          axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/stats").then(this.fillStats),
          axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/stats").then(this.fillCryptoStats)
        ];
        await Promise.all(initialRequests);

        // These requests depend on stats but can run in parallel with each other
        const walletRequests = [
          // Stock wallet request
          axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/wallet").then(this.processStockStats),

          // Crypto wallet requests (assets followed by prices)
          axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/wallet/assets")
            .then(assetsRes => {
              const assets = assetsRes.data;
              const currencies = assets.map(item => item.currency).filter(Boolean);

              return axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/wallet/prices", {
                currencies: currencies
              })
              .then(pricesRes => {
                const prices = pricesRes.data;
                this.processCryptoStats(assets, prices);
              });
            })
        ];

    // Wait for all wallet requests to complete
    await Promise.all(walletRequests);

    // Final step after all data is loaded
    this.fillTotalStats();
    console.log("All data loaded");
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    }
  },
}
</script>

<style>
.table-responsive {
  overflow-x: auto;
}

.card {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.card-header {
  background-color: #f9f9f9;
  border-bottom: 1px solid #eee;
  padding: 15px 20px;
}

.card-body {
  padding: 20px;
}

.table {
  width: 100%;
  margin-bottom: 0;
}

.table th, .table td {
  padding: 12px 8px;
  vertical-align: middle;
}

.table-success {
  background-color: rgba(92, 195, 5, 0.1);
}

.table-info {
  background-color: rgba(54, 162, 235, 0.1);
}
</style>