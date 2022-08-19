<template>
  <div>
    <div class="row">
      <div class="col-lg-4 col-md-6 col-sm-6">
        <stats-card type="success"
                    icon="fa fa-chart-line"
                    small-title="Win/Loses"
                    :title="benefits.toString()">
        </stats-card>
      </div>
      <div class="col-lg-4 col-md-6 col-sm-6">
        <stats-card type="danger"
                    icon="nc-icon nc-money-coins"
                    small-title="Fees"
                    :title="fees.toString()">
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
                  <el-select class="select-default" v-model="tax_year" placeholder="Year">
                    <el-option
                        class="select-default"
                        v-for="item in years" :key="item" :label="item" :value="item">
                    </el-option>
                  </el-select>
                </div>
              </div>
            </div>
          </div>
          <div class="card-body table-full-width">
            <el-table name="tax_items" :data="this.closedOrders" :default-sort="{property: 'id', order: 'descending'}"
                      row-key="id" :cell-class-name="testClass" default-expand-all
                      :cell-style="{padding: '0', height: '20px'}">
              <el-table-column label="Symbol" property="pair"></el-table-column>
              <el-table-column label="Date" property="value_date" sortable></el-table-column>
              <el-table-column label="Amount" property="amount">
                <template slot-scope="scope">
                  {{ scope.row.amount | toCurrency(scope.row.source_currency, 8) }}
                </template>
              </el-table-column>
              <el-table-column label="Price" property="price">
                <template slot-scope="scope">
                  {{ scope.row.price | toCurrency(scope.row.target_currency, 8) }}
                </template>
              </el-table-column>
              <el-table-column label="Fees" property="fee">
                <template slot-scope="scope">
                  {{ scope.row.fee | toCurrency(scope.row.target_currency, 8) }}
                </template>
              </el-table-column>
              <el-table-column label="Cost" property="cost">
                <template slot-scope="scope">
                  {{ scope.row.cost | toCurrency(scope.row.target_currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Benefits" property="benefits">
                <template slot-scope="scope">
                  {{ scope.row.benefits | toCurrency(scope.row.target_currency) }}
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

import {Table, TableColumn, Select, Option} from 'element-ui'
import axios from "axios";
import StatsCard from "../../../UIComponents/Cards/StatsCard";

export default {
  name: "Taxes",
  components: {
    Table, TableColumn, StatsCard,
    [Select.name]: Select,
    [Option.name]: Option,
  },
  data() {
    return {
      closedOrders: [],
      years: [2019, 2020, 2021, 2022],
      tax_year: new Date().getFullYear() - 1,
      value: 0,
      benefits: 0,
      fees: 0
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
    },
    async getData() {
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/crypto/tax?year=" + this.tax_year).then(this.fillTaxes);
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
.red {
  color: red
}

.green {
  color: green
}
</style>
