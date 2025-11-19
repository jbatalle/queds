<template>
  <div class="row">
    <div class="col-md-6">
      <chart-card v-if="investChart && investChart.labels.length > 0"
                  :chart-data="investChart"
                  :chart-options="{ cutout: '65%', plugins: { legend: { position: 'bottom' }}}"
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
          <el-table :data="wallet" :default-sort="{property: 'percentage', order: 'descending'}"
                    :cell-class-name="colorClass">
            <el-table-column label="Symbol" property="ticker.ticker" width="100px" sortable></el-table-column>
            <el-table-column label="cost" property="cost">
              <template v-slot:default="scope">
              <span v-if="type==='broker'">
                {{ $filters.toCurrency(scope.row.cost, scope.row.ticker.currency) }}
              </span>
                <span v-else>
                {{ $filters.toCurrency(scope.row.cost, scope.row.current_price_currency, 2) }}
              </span>
              </template>
            </el-table-column>
            <el-table-column label="Value" property="current_value">
              <template v-slot:default="scope">
                        <span v-if="type==='broker'">
                          {{ $filters.toCurrency(scope.row.current_value, scope.row.ticker.currency) }}
                        </span>
                <span v-else>
                          {{ $filters.toCurrency(scope.row.current_value, scope.row.current_price_currency, 2) }}
                        </span>
              </template>
            </el-table-column>
            <el-table-column label="Base value" property="base_current_value" sortable>
              <template v-slot:default="scope">
                {{ $filters.toCurrency(scope.row.base_current_value, base_currency) }}
              </template>
            </el-table-column>
            <el-table-column label="Percentage" property="percentage" sortable>
              <template v-slot:default="scope">
                {{ scope.row.percentage !== undefined && scope.row.percentage !== null ? Number(scope.row.percentage).toFixed(2) : '0.00' }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import StatsCard from "@/components/UIComponents/Cards/StatsCard.vue";
import ChartCard from '@/components/UIComponents/Cards/ChartCard.vue';

export default {
  props: {
    base_currency: String,
    wallet: Array,
    loading: Boolean,
    type: String,
    total_value: Number,
    wallet_value: Number,
  },
  components: {StatsCard, ChartCard},
  emits: ['recalculate', 'reload'],
  data: () => ({
    filter_accounts: new Set(),
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
        tooltips: {},
        legend: {display: true}
      },
    },
  }),
  watch: {
    wallet: {
      handler(val) {
        this.createInvestChart(this.wallet_value);
      },
      deep: true
    },
  },
  computed: {},
  methods: {
    createInvestChart(wallet_value) {
      if (this.type === 'broker') {
        this.investChart.labels = this.wallet.map(el => el.ticker.ticker);
      } else {
        this.investChart.labels = this.wallet.map(el => el.currency);
      }
      this.investChart.datasets[0].backgroundColor = this.wallet.map(function (el) {
        let r = Math.floor(Math.random() * 255);
        let g = Math.floor(Math.random() * 255);
        let b = Math.floor(Math.random() * 255);
        return "rgb(" + r + "," + g + "," + b + ")";
      });

      if (this.type === 'broker') {
        this.investChart.datasets[0].data = this.wallet.map(el => Number(el.base_current_value / wallet_value * 100).toFixed(2));
      } else {
        this.investChart.datasets[0].data = this.wallet.map(el => Number(el.current_value / wallet_value * 100).toFixed(2));
      }
      this.investKey += 1;
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
}
</script>

<style scoped>
.Chart {
  max-width: 200px;
  padding: 20px;
  /* box-shadow: 0px 0px 20px 2px rgba(0, 0, 0, 0.4); */
  border-radius: 20px;
  margin: 50px 0;
}
</style>
