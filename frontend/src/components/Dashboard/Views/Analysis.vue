<template>
  <div>
    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-body">
            <template>
              <div class="row">
                <div class="col-md-12">
                  <el-button
                      v-for="item in watchlists"
                      :key="item.name"
                      type="primary"
                      @click="get_watchlist(item)"
                  >{{ item.name }}
                  </el-button>
                  <el-button type="primary" @click="getWallet()">Wallet</el-button>
                  <el-button type="info" @click="dialogVisible = true">Add watchlist</el-button>
                </div>
                <div class="col-md-12">
                </div>
              </div>
            </template>
          </div>
        </div>
        <el-dialog
            title="Add watchlist"
            :visible.sync="dialogVisible"
            width="30%" :close-on-press-escape="true"
            :before-close="handleClose">
          <el-input placeholder="Insert watchlist name" v-model="add_watchlist"></el-input>
          <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="addWatchlist">Confirm</el-button>
      </span>
        </el-dialog>
      </div>
    </div>
    <div class="row">
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <div class="row">
              <div class="col-md-6">
                <el-input placeholder="Input symbol" v-model="input"></el-input>
              </div>
              <div class="col-md-6">
                <div class="text-right mb-3">
                  <el-button @click="addSymbol(input)" type="primary" :disabled="current_watchlist == undefined">Add
                    symbol
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          <div class="card-body table-full-width">
            <el-table
                :data="watchlist.filter(data => !search || data.symbol.toLowerCase().includes(search.toLowerCase()))"
                :default-sort="{property: 'ticker.ticker', order: 'descending'}"
                max-height="650"
              :cell-style="{padding: '0', height: '20px'}">
              <el-table-column label="Symbol" property="ticker.ticker">
                <template slot="header" slot-scope="scope">
                  <el-input
                      v-model="search"
                      size="mini"
                      placeholder="Symbol search"/>
                </template>
                <template slot-scope="scope">
                  <a @click="handleClick(scope.$index, scope.row)">{{ scope.row.symbol }}</a>
                </template>
              </el-table-column>
              <el-table-column label="Time" property="market_time"></el-table-column>
              <el-table-column label="Change" property="price_change" sortable>
                    <template slot-scope="scope">
                      {{ scope.row.price_change | round(2) }}%
                    </template>
              </el-table-column>
              <el-table-column label="Price" property="price"></el-table-column>
              <el-table-column label="High" property="high"></el-table-column>
              <el-table-column label="Low" property="low"></el-table-column>
              <el-table-column
                  fixed="right"
                  class-name="td-actions"
                  label="Actions">
                <template slot-scope="props">
                  <p-button type="info" size="sm" icon @click="onProFeature()"  :disabled="current_watchlist == undefined">
                    <i class="fa fa-bell"></i>
                  </p-button>
                  <p-button type="danger" size="sm" icon @click="onProFeature()"  :disabled="current_watchlist == undefined">
                    <i class="fa fa-times"></i>
                  </p-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card" style="padding: 5px">
          <VueTradingView :key=componentKey :options="options"/>
        </div>
        <!--div class="card">
          <div class="card-body table-responsive table-full-width">
            <el-table :data="comments">
              <el-table-column label="Date" property="date"></el-table-column>
              <el-table-column label="Source" property="source"></el-table-column>
              <el-table-column label="Message" property="message" sortable></el-table-column>
            </el-table>
          </div>
        </div-->
      </div>
    </div>
  </div>
</template>
<script>
import axios from "axios";
// import VueTradingView from 'vue-trading-view';
import {Table, TableColumn, Input, Button, Dialog, Tabs, TabPane} from 'element-ui'
import VueTradingView from 'vue-trading-view/src/vue-trading-view';
import Vue from 'vue'

Vue.use(Table);
Vue.use(TableColumn);
Vue.use(Input);
Vue.use(Button);
Vue.use(Dialog);
Vue.use(Tabs);
Vue.use(TabPane);
//Vue.use(Tab);
export default {
  name: "Analysis",
  components: {
    VueTradingView, Tabs, TabPane
  },
  data() {
    return {
      add_watchlist: '',
      dialogVisible: false,
      current_watchlist: undefined,
      wallet: false,
      watchlists: [],
      watchlist: [],
      input: '',
      search: '',
      options: {},
      comments: [],
      componentKey: 0,
    };
  },
  created() {
    this.getData();
  },
  methods: {
    fillWatchlists(res) {
      let resStatus = res.status === 200 ? true : false;
      this.watchlists = res.data;
    },
    fillWatchlist(res) {
      let resStatus = res.status === 200 ? true : false;
      this.watchlist = res.data;
      this.watchlist.forEach(function (s) {
        s.market_time = s.market_time.split(' ')[0];
      });
      console.log(res.data);
    },
    fillComments(res) {
      let resStatus = res.status === 200 ? true : false;
      this.comments = res.data;
    },
    async getWallet() {
      this.wallet = true;
      this.current_watchlist = undefined;
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/analysis/watchlist/0").then(this.fillWatchlist);
    },
    async getData() {
      await this.getWallet();
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/analysis/watchlist").then(this.fillWatchlists);
    },
    async get_watchlist(item) {
      this.current_watchlist = item;
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/analysis/watchlist/" + item.id).then(this.fillWatchlist);
    },
    async handleClick(id, row) {
      this.options.symbol = row.symbol;
      this.componentKey += 1;
      await axios.get(process.env.VUE_APP_BACKEND_URL + "/analysis/comments/" + row.symbol).then(this.fillComments);
    }, handleClose(done) {
      this.dialogVisible = false;
    },
    async addWatchlist(done) {

      this.dialogVisible = false
      let data = {
        "name": this.add_watchlist
      };
      let vm = this;
      await axios.post(process.env.VUE_APP_BACKEND_URL + "/analysis/watchlist", data)
          .then(function (r) {
            vm.getData();
          }).catch(function (r) {
            console.log(r)
          });

      this.add_watchlist = ""
    },
    async addSymbol(input) {
      let data = {
        "ticker": input
      }
      let vm = this;
      await axios.post(process.env.VUE_APP_BACKEND_URL + "/analysis/watchlist/" + this.current_watchlist.id, data)
          .then(function (r) {
            // vm.getData();
            vm.get_watchlist({id: vm.current_watchlist.id})
          }).catch(function (r) {
            console.log(r)
          });
    }
  },
};
</script>
<style>

</style>
