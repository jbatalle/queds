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
                          type="exchange"
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
      years: Array.from({length: 5}, (v, k) => new Date().getFullYear()-k).sort(),
      tax_year: new Date().getFullYear() - 1,
      value: 0,
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
        console.log(s);
        vm.fees += s.fee;
        s.fees = s.fee;
        s.cost = s.amount * s.price - s.fee;
        vm.fees = Number((vm.fees).toFixed(2));
        //TODO: sum fees of children items
        s.benefits_net = s.amount * s.price;
        s.benefits = Number((s.amount * s.price - s.fees).toFixed(2));
        s.value_date = s.value_date.split(' ')[0];
        //s.source_currency = s.pair.split("/")[0];
        s.target_currency = s.pair.split("/")[1];

        s.children.forEach(function (c) {
          c.id = s.id + "_" + c.id;
          c.name = "";
          c.target_currency = s.pair.split("/")[1];
          c.value_date = c.value_date.split(' ')[0];
          c.fees = c.fee + c.exchange_fee;
          s.benefits_net -= c.price * c.amount;
          s.benefits -= (c.price * c.amount + c.partial_fee); //- (c.fees/(s.shares/c.shares));
          s.benefits = Number((s.benefits).toFixed(2));
          c.fees = Number(c.fees).toFixed(2);
        });
        //s.cost = Number(s.cost).toFixed(2);
        vm.benefits += s.benefits;
        vm.benefits = Number((vm.benefits).toFixed(2));
      });
      this.loading = false;
    },
    async getData() {
      this.loading = true;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/crypto/tax?year=" + this.tax_year).then(this.fillTaxes);
    },
    testClass(item) {
      if (item.column.property == 'benefits') {
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
</style>
