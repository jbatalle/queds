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
            <taxes-table :base_currency="base_currency" :orders="closedOrders" :loading="loading"
                          type="broker"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>

import {ElTable} from 'element-plus';
import StatsCard from "@/components/UIComponents/Cards/StatsCard.vue";
import axios from "axios";
import TaxesTable from "@/components/Dashboard/Views/TaxesTable.vue";


export default {
  name: "Taxes",
  components: {
    ElTable, StatsCard,
    TaxesTable
  },
  data() {
    return {
      base_currency: localStorage.getItem('base_currency'),
      closedOrders: [],
      years: Array.from({length: 6}, (v, k) => new Date().getFullYear() - k).sort(),
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
        s.benefits = 0;
        //TODO: sum fees of children items
        //s.benefits = Number(s.shares * s.price *s.currency_rate + s.fees).toFixed(2);
        //s.benefits = s.cost;
        s.value_date = s.value_date; //.split(' ')[0];
        let sell_shares = 0;
        s.children.forEach(function (c) {
          c.id = s.id + "_" + c.id;
          c.shares = -c.shares;
          c.name = "";
          c.ticker = {ticker: "", currency: s.currency};
          c.value_date = c.value_date; //.split(' ')[0];
          c.fees = c.partial_fee; //c.fee + c.exchange_fee;
          s.benefits += c.price * c.shares * c.currency_rate + c.partial_fee;
          c.cost = c.shares * c.price * c.currency_rate + c.partial_fee;
          //s.fees += c.fees;
          sell_shares -= c.shares;
        });
        s.shares = sell_shares;
        s.cost = s.shares * s.price * s.currency_rate + s.fees;
        s.benefits += s.cost;
        vm.benefits += s.benefits;
        vm.fees += s.fees;
      });
      this.loading = false;
    },
    async getData() {
      this.loading = true;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/stock/tax?year=" + this.tax_year).then(this.fillTaxes);
    },
  },
};
</script>
<style>
</style>
