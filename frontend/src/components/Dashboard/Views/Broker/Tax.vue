<template>
  <div>
    <div class="row">
      <div class="col-lg-4 col-md-6 col-sm-6">
        <stats-card type="success"
                    icon="fa fa-chart-line"
                    small-title="Win/Loses"
                    :title="$filters.toCurrency(benefits, base_currency)">
        </stats-card>
      </div>
      <div class="col-lg-4 col-md-6 col-sm-6">
        <stats-card type="success"
                    icon="nc-icon nc-money-coins"
                    small-title="Dividends"
                    :title="$filters.toCurrency(dividends, base_currency)">
        </stats-card>
      </div>
      <div class="col-lg-4 col-md-6 col-sm-6">
        <stats-card type="danger"
                    icon="nc-icon nc-money-coins"
                    small-title="Fees"
                    :title="$filters.toCurrency(fees, base_currency)">
        </stats-card>
      </div>
    </div>
    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            <div class="row">
              <div class="col-md-6">
                <h5 class="title">Taxes</h5>
              </div>
              <div class="col-md-6">
                <div class="pull-right">
                  <el-select class="m-2" v-model="tax_year" placeholder="Year" style="width: 100px">
                    <el-option v-for="item in years" :key="item" :label="item" :value="item">
                    </el-option>
                  </el-select>
                </div>
              </div>
            </div>
          </div>
          <div class="card-body table-full-width">
            <el-table v-loading="loading" name="tax_items" :data="this.closedOrders"
                      :default-sort="{property: 'id', order: 'descending'}"
                      row-key="id" :cell-class-name="colorClass" default-expand-all
                      :cell-style="{padding: '0', height: '20px'}">
              <el-table-column label="Symbol">
                <template v-slot:default="scope">
                  <el-tooltip :content="scope.row.name" placement="top">
                    <span type="info">{{ scope.row.ticker.ticker }}</span>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column label="ISIN" property="ticker.isin"></el-table-column>
              <el-table-column label="Date" property="value_date" sortable></el-table-column>
              <el-table-column label="Shares" property="shares" width="100px"></el-table-column>
              <el-table-column label="Price">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.price, scope.row.currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Fees" property="fees">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.fees, base_currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Currency Rate" property="rate">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.price, base_currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Cost" property="cost">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.cost, base_currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Benefits" property="benefits">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.benefits, base_currency) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>

import {ElTable, ElTableColumn, ElSelect, ElOption, ElTooltip, ElTag, ElIcon, ElInput} from 'element-plus';
import StatsCard from "@/components/UIComponents/Cards/StatsCard.vue";
import axios from "axios";


export default {
  name: "Taxes",
  components: {
    ElTable, ElTableColumn, StatsCard,
    ElSelect,
    ElOption,
    ElTooltip,
    ElIcon,
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      closedOrders: [],
      years: Array.from({length: 5}, (v, k) => new Date().getFullYear() - k).sort(),
      tax_year: new Date().getFullYear() - 1,
      dividends: 0,
      benefits: 0,
      fees: 0,
      loading: true
    };
  },
  watch: {
    tax_year: {
      handler(val) {
        this.getData();
      },
      deep: true
    }
  },
  created() {
    this.getData();
  },
  methods: {
    fillTaxes(res) {
      this.closedOrders = res.data;
      this.benefits = 0;
      this.fees = 0;
      let vm = this;
      this.closedOrders.forEach(function (s) {
        s.fees = s.fee + s.exchange_fee;
        s.cost = s.shares * s.price * s.currency_rate + s.fees;
        if (s.currency_rate === 0) {
          s.currency_rate = "-";
        }

        //TODO: sum fees of children items
        //s.benefits = Number(s.shares * s.price *s.currency_rate + s.fees).toFixed(2);
        s.benefits = s.cost;
        s.value_date = s.value_date.split(' ')[0];

        s.children.forEach(function (c) {
          c.id = s.id + "_" + c.id;
          c.shares = -c.shares;
          c.name = "";
          c.ticker = {ticker: "", currency: s.currency};
          c.value_date = c.value_date.split(' ')[0];
          c.fees = c.partial_fee; //c.fee + c.exchange_fee;
          s.benefits += c.price * c.shares * c.currency_rate + c.partial_fee;
          c.cost = c.shares * c.price * c.currency_rate + c.partial_fee;
          s.fees += c.fees;
        });
        vm.benefits += s.benefits;
        vm.fees += s.fees;
      });
      this.loading = false;
    },
    async getData() {
      this.loading = true;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/tax?year=" + this.tax_year).then(this.fillTaxes);
    },
    colorClass(item) {
      if (item.column.property == 'benefits' || item.column.property == 'shares') {
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
.red {
  color: red
}

.green {
  color: green
}
</style>
