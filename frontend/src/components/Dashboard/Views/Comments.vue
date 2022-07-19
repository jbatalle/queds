<template>
  <div class="row">
    <div class="col-md-12">
      <div class="card">
        <div class="card-body">
          <div class="col-sm-12 mt-12">
            <!--          <el-table
                :data="watchlist.filter(data => !search || data.symbol.toLowerCase().includes(search.toLowerCase()))"
                :default-sort="{property: 'symbol', order: 'descending'}">-->
            <el-table class="table-striped"
                      :data="comments"
                      border :cell-style="{padding: '0', height: '20px'}">
              <el-table-column label="Date" property="date"></el-table-column>
              <el-table-column label="Source" property="source"></el-table-column>
              <el-table-column label="Ticker" property="tickers"></el-table-column>
              <el-table-column label="Message" property="message" sortable></el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import axios from "axios";
import {Table, TableColumn, Input, Button, Dialog} from 'element-ui'
import Vue from 'vue'

const tableColumns = ['symbol', 'market_time', 'price_change', 'price', 'high', 'low']
Vue.use(Table);
Vue.use(TableColumn);
Vue.use(Input);
Vue.use(Button);
Vue.use(Dialog);
export default {
  name: "Analysis",
  components: {

  },
  //extends: LTable,
  data() {
    return {
      add_watchlist: '',
      dialogVisible: false,
      current_watchlist: {},
      watchlists: [],
      watchlist: [],
      search: '',
      options: {},
      comments: [],
      componentKey: 0,
    };
  },
  created() {
    this.getComments();
  },
  methods: {
    fillComments(res) {
      let resStatus = res.status === 200 ? true : false;
      this.comments = res.data;
      console.log(this.comments)
    },
    async getComments() {
      console.log("Get comments");
      this.componentKey += 1;

      await axios.get(process.env.VUE_APP_BACKEND_URL + "/analysis/comments").then(this.fillComments);

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
</style>
