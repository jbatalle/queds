<template>
  <div>
    <div class="row">
        <div class="col-md-6">
        <el-tabs type="card" editable class="demo-tabs" @edit="handleTabsEdit" @tab-click="handleTabClick">
          <el-tab-pane class="sidebar-wrapper" v-for="item in watchlists" :key="item.id" :label="item.name"
                       :name="item.name" @tab-click="get_watchlist(item)">
            <div class="card">
              <div class="card-header">
                <div class="row">
                  <div class="col-md-6">
                    <el-input placeholder="Input symbol" v-model="input"></el-input>
                  </div>
                  <div class="col-md-6">
                    <div class="text-right mb-3">
                      <el-button @click="addSymbol(input)" type="primary" :disabled="current_watchlist == undefined">Add symbol</el-button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body table-full-width">
                <el-table
                    :data="watchlist.filter(data => !search || data.symbol.toLowerCase().includes(search.toLowerCase()))"
                    :default-sort="{ property: 'ticker.ticker', order: 'descending' }" max-height="650"
                    :cell-style="{ padding: '0', height: '20px' }">
                  <el-table-column label="Symbol" property="ticker.ticker">
                    <template #header>
                      <el-input v-model="search" size="mini" placeholder="Symbol search"/>
                    </template>
                    <template v-slot:default="scope">
                      <a @click="handleClick(scope.$index, scope.row)">{{ scope.row.symbol }}</a>
                    </template>
                  </el-table-column>
                  <el-table-column label="Time" property="market_time"></el-table-column>
                  <el-table-column label="Change" property="price_change" sortable>
                    <template v-slot:default="scope">
                      {{ $filters.toCurrency(scope.row.price_change) }}
                    </template>
                  </el-table-column>
                  <el-table-column label="Price" property="price"></el-table-column>
                  <el-table-column label="High" property="high"></el-table-column>
                  <el-table-column label="Low" property="low"></el-table-column>
                  <el-table-column fixed="right" class-name="td-actions" label="Actions">
                    <template v-slot:default="props">
                      <el-button type="info" size="small" icon @click="onProFeature()"
                                 :disabled="current_watchlist == undefined">
                        <i class="fa fa-bell"></i>
                      </el-button>
                      <el-button type="danger" size="small" icon @click="openDeleteDialog(props.row)"
                                 :disabled="current_watchlist == undefined">
                        <i class="fa fa-times"></i>
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
          </div>
        <div class="col-md-6">
          <div class="card" style="padding: 5px; border-radius: revert;">
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
    <el-dialog title="Delete watchlist" v-model="deleteDialogVisible" width="60%" :close-on-press-escape="true"
               :before-close="handleDeleteClose">
      <div class="card-body">
        <form>
          <div class="row" v-if="delete_watchlist">
            <div class="col-md-12">
              <div class="form-group">
                <h4>Are you sure you want to delete this list?</h4>
                <ul>
                  <li>{{ delete_watchlist.name }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div class="clearfix"></div>
        </form>
      </div>
      <template #footer>
      <span slot="footer" class="dialog-footer">
        <el-button @click="deleteDialogVisible = false">Cancel</el-button>
        <el-button type="danger" @click="deleteWatchlistForm">Delete</el-button>
      </span>
      </template>
    </el-dialog>

    <el-dialog title="Read account" v-model="readDialogVisible" width="60%" :close-on-press-escape="true"
               :before-close="handleReadClose" v-loading="loading">
      <div v-loading="loading">
        <div class="card-body">
          <form>
            <div class="row">
              <div class="col-md-12">
                <div class="form-group2">
                  <div class="sub-title my-2 text-sm text-gray-600">
                    Insert a passphrase for credential encryption
                  </div>
                  <el-input type="password"
                            label="Insert a passphrase for credential encryption"
                            placeholder="passphrase">
                  </el-input>
                </div>
              </div>
            </div>
            <div class="clearfix"></div>
          </form>
        </div>
        <footer class="el-dialog__footer">
          <el-button @click="readDialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="readAccount">Read</el-button>
        </footer>
      </div>
    </el-dialog>

    <el-dialog title="Add watchlist" v-model="dialogVisible" width="40%" :close-on-press-escape="true"
               :before-close="handleClose">
      <div class="card-body">
        <form>
          <div class="row">
            <div class="col-md-12">
              <div class="form-group2">
                <div class="sub-title my-2 text-sm text-gray-600">
                  Insert the watchlist name
                </div>
                <el-input type="text" label="" v-model="add_watchlist"></el-input>
              </div>
            </div>
          </div>
          <div class="clearfix"></div>
        </form>
      </div>
      <footer class="el-dialog__footer">
        <el-button @click="readDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="addWatchlist">Confirm</el-button>
      </footer>
    </el-dialog>
  </div>
</template>
<script>
import axios from "axios";
import VueTradingView from 'vue-trading-view/src/';

export default {
  name: "Analysis",
  components: {
    VueTradingView//, Tabs, TabPane
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
      state1: '',
      deleteDialogVisible: false,
      delete_watchlist: undefined,
      tableData: [
        {name: "Row 1", tags: ["tag1", "tag2"]},
        {name: "Row 2", tags: ["tag2", "tag3"]},
        // Add more rows as needed
      ],
      filteredData: [],
      filterTag: "",
      dynamicTags: ['Tag 1', 'Tag 2', 'Tag 3'],
      inputVisible: false,
      inputValue: ''
    };
  },
  created() {
    this.getData();
  },
  methods: {
    async handleTabClick(tab, a) {
      this.watchlist = [];
      let watchlist = this.watchlists.filter((w) => w.name == tab.props.name);
      await this.get_watchlist(watchlist[0]);
    },
    handleDeleteClose() {
      this.deleteDialogVisible = false;
    },
    async openDeleteDialog(a) {
      await this.deleteTickerWatchlist(this.current_watchlist, a);
      await this.get_watchlist(this.current_watchlist);
    },
    async handleTabsEdit(targetName, action) {
      console.log("Handle Tabs edit", action, targetName)
      if (action === 'add') {
        this.dialogVisible = true;
      } else if (action === 'remove') {
        let watchlist = this.watchlists.filter((w) => w.name == targetName);
        this.deleteDialogVisible = true;
        this.delete_watchlist = watchlist[0];
      }
    },
    async deleteWatchlistForm() {
      let vm = this;
      console.log(this.delete_watchlist);
      await this.deleteWatchlist(this.delete_watchlist).then(function (d) {
        vm.$notify({
          message: 'Watchlist deleted correctly',
          type: 'info',
        });
        vm.getData();
      }).catch(_ => {
        vm.$notify({
          message: 'Unable to delete the watchlist',
          type: 'warning',
        });
      });
      this.deleteDialogVisible = false;
      this.delete_watchlist = undefined;
    },
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
    },
    fillComments(res) {
      let resStatus = res.status === 200 ? true : false;
      this.comments = res.data;
    },
    async getWallet() {
      this.wallet = true;
      this.current_watchlist = undefined;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/analysis/watchlist/0").then(this.fillWatchlist);
    },
    async getData() {
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/analysis/watchlist").then(this.fillWatchlists);
      await this.getWallet();
    },
    async get_watchlist(item) {
      console.log(this.watchlists)
      console.log(item);
      this.current_watchlist = item;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/analysis/watchlist/" + item.id).then(this.fillWatchlist);
    },
    async handleClick(id, row) {
      this.options.symbol = row.symbol;
      this.componentKey += 1;
    }, handleClose(done) {
      this.dialogVisible = false;
    },
    async addWatchlist(done) {
      this.dialogVisible = false
      let data = {
        "name": this.add_watchlist
      };
      let vm = this;
      await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/analysis/watchlist", data)
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
      this.input = "";
      let vm = this;
      await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/analysis/watchlist/" + this.current_watchlist.id, data)
          .then(function (r) {
            // vm.getData();
            vm.get_watchlist({id: vm.current_watchlist.id})
          }).catch(function (r) {
            console.log(r)
          });
    },
    async deleteWatchlist(watchlist) {
      console.log("delete list " + watchlist.id)
      let vm = this;
      await axios.delete(import.meta.env.VITE_APP_BACKEND_URL + "/analysis/watchlist/" + watchlist.id)
          .then(function (r) {
            console.log(r);
          }).catch(function (r) {
            console.log(r)
          });
    },
    async deleteTickerWatchlist(watchlist, ticker) {
      console.log("delete ticker" + watchlist.id + " " + ticker.id)
      let vm = this;
      await axios.delete(import.meta.env.VITE_APP_BACKEND_URL + "/analysis/watchlist/" + watchlist.id + "/" + ticker.id)
          .then(function (r) {
            console.log(r);
          }).catch(function (r) {
            console.log(r)
          });
    },
    andleClose(tag) {
      this.dynamicTags.splice(this.dynamicTags.indexOf(tag), 1);
    },

    showInput() {
      this.inputVisible = true;
      this.$nextTick(_ => {
        this.$refs.saveTagInput.$refs.input.focus();
      });
    },

    handleInputConfirm() {
      let inputValue = this.inputValue;
      if (inputValue) {
        this.dynamicTags.push(inputValue);
      }
      this.inputVisible = false;
      this.inputValue = '';
    }, filterTable() {
      console.log(this.filterTag);
      console.log(this.filterTag === "");
      console.log(this.filterTag == "");
      console.log(this.filterTag == undefined);
      if (this.filterTag === "") {
        this.filteredData = this.tableData;
        return;
      }
      console.log("FIlter table");
      console.log(this.filterTag)
      const filteredData = this.tableData.filter(row => {
        return row.tags.includes(this.filterTag);
      });
      console.log(this.tableData);
      console.log(filteredData);
      this.$refs.tagTable.setCurrentRow(null);
      this.$refs.tagTable.clearSort();
      this.filteredData = filteredData;
    },
    handleSelect(item) {
      console.log("handle selectg " + item);
    },
    querySearch(queryString, cb) {
      console.log("query search");
      console.log(queryString);
      console.log(this.tableData);
      const results = this.tableData;
      cb(results);
    }, createFilter(queryString) {
      return this.tableData;
    }
  },
};
</script>
<style>
.demo-tabs {
  border-radius: inherit;
}

.el-tabs__item.is-active {
  background-color: #ffffff;
  color: #3cab79 !important;
}

.el-tabs__item:hover {
  background-color: #ffffff;
  color: #3cab79 !important;
}
</style>
