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
        <stats-card type="success"
                    icon="nc-icon nc-money-coins"
                    small-title="Dividends"
                    :title="value.toString()">
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
              <el-table-column label="Symbol">
                <template #default="scope">
                  <el-tooltip :content="scope.row.name" placement="top">
                    <span type="info">{{ scope.row.ticker.ticker }}</span>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column label="ISIN" property="ticker.isin"></el-table-column>
              <el-table-column label="Date" property="value_date" sortable></el-table-column>
              <el-table-column label="Shares" property="shares" width="100px"></el-table-column>
              <el-table-column label="Price ($/€)" property="price"></el-table-column>
              <el-table-column label="Fees" property="fees"></el-table-column>
              <el-table-column label="Cost" property="cost"></el-table-column>
              <el-table-column label="Benefits" property="benefits"></el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>

import {Table, TableColumn, Select, Option, Tooltip, Icon} from 'element-ui'
import axios from "axios";
import StatsCard from "../../../UIComponents/Cards/StatsCard";

export default {
  name: "Taxes",
  components: {
    Table, TableColumn, StatsCard,
    [Select.name]: Select,
    [Option.name]: Option,
    [Tooltip.name]: Tooltip,
    [Icon.name]: Icon,
  },
  data() {
    return {
      closedOrders: [],
      years: [2019, 2020, 2021, 2022],
      tax_year: 2021,
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
      let resStatus = res.status === 200 ? true : false;
      this.closedOrders = res.data;
      this.benefits = 0;
      this.fees = 0;
      let vm = this;
      this.closedOrders.forEach(function (s) {
        vm.fees += s.fee + s.exchange_fee;
        s.fees = s.fee + s.exchange_fee;
        s.cost = s.shares * s.price - s.fee - s.exchange_fee;
        s.cost_eur = s.shares * s.price * s.currency_rate + s.fee + s.exchange_fee;
        s.sell = 0;
        vm.fees = Number((vm.fees).toFixed(2));

        //TODO: sum fees of children items
        //s.benefits = Number(s.shares * s.price *s.currency_rate + s.fees).toFixed(2);
        s.benefits = s.cost_eur;
        s.value_date = s.value_date.split(' ')[0];
        s.fees = Number(s.fees).toFixed(2);
        s.children.forEach(function (c) {
          c.id = s.id + "_" + c.id;
          c.name = "";
          c.ticker = {ticker: ""};
          c.value_date = c.value_date.split(' ')[0];
          c.fees = c.fee + c.exchange_fee;
          s.benefits -= Number(c.price * c.shares *c.currency_rate - c.partial_fee).toFixed(2); //- (c.fees/(s.shares/c.shares));
          c.cost = Number(c.shares * c.price * c.currency_rate - c.fee - c.exchange_fee).toFixed(2) + "€";
          c.fees = Number(c.fees).toFixed(2);
          c.price = c.price + c.currency;
        });
        s.cost = Number(s.cost_eur).toFixed(2);
        vm.benefits += s.benefits;

        s.price = s.price + s.currency;
        s.cost = s.cost + "€";
        s.sell = s.sell + "€";
        s.benefits = Number(s.benefits).toFixed(2)+ "€";
        vm.benefits = Number((vm.benefits).toFixed(2));
      });
    },
    async getData() {
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/stock/tax?year=" + this.tax_year).then(this.fillTaxes);
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
.red {
  color: red
}

.green {
  color: green
}
</style>
