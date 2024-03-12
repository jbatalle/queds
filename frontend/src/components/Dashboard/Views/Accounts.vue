<template>
  <div>
    <el-dialog title="Adding account" v-model="dialogVisible" width="60%" :close-on-press-escape="true"
               :before-close="handleClose">
      <div class="card-body">
        <form>
          <div class="row">
            <div class="col-md-4">
              <p>Account type</p>
              <el-select
                  label="Account type"
                  v-model="credential.entity"
                  :class="errors.entity ? 'select-danger' : ''"
                  placeholder="Select account">
                <el-option
                    :error="errors.entity ? errors.entity : ''"
                    v-for="item in entities"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id">
                </el-option>
              </el-select>
            </div>
            <div class="col-md-4">
              <p>Currency</p>
              <el-select
                  label="Currency"
                  v-model="credential.currency"
                  :class="errors.currency ? 'select-danger' : ''"
                  placeholder="Currency">
                <el-option
                    :error="errors.currency ? errors.currency : ''"
                    v-for="item in ['EUR', 'USD']"
                    :key="item"
                    :label="item"
                    :value="item">
                </el-option>
              </el-select>
            </div>
            <div class="col-md-4">
                <p>Account name</p>
              <el-input type="text"
                        label="Account name"
                        placeholder="Account name"
                        :error="errors.name ? errors.name : ''"
                        v-model="credential.name">
              </el-input>
            </div>
          </div>
          <div class="clearfix"></div>
          <div class="row" v-if="credential.entity">
            <div class="col-md-12">
              <div class="form-group2">
                <h4>Insert credentials</h4>
                <el-input v-bind="$attrs"
                          v-for="{ cred_type, mode, id } in entity_credentials"
                          :key="id"
                          :type="mode"
                          class="w-100 m-2"
                          :name="cred_type"
                          :placeholder="cred_type"
                          :error="errors.parameters ? errors.parameters : ''"
                          v-model="credential.parameters[id]">
                </el-input>
              </div>
            </div>
          </div>
          <div class="row" v-if="credential.entity">
            <div class="col-md-12">
              <div class="form-group2">
                <div class="sub-title my-2 text-sm text-gray-600">
                  Insert a passphrase for credential encryption
                </div>
                <el-input type="password"
                          class="w-100 m-2"
                          label="Insert a passphrase for credential encryption"
                          placeholder="passphrase"
                          :error="errors.encrypt_password ? errors.encrypt_password : ''"
                          v-model="credential.encrypt_password"
                          autocomplete="one-time-code">
                </el-input>
              </div>
            </div>
          </div>
          <div class="clearfix"></div>
        </form>
      </div>
      <template #footer>
      <span class="dialog-footer">

        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="addAccount" :disabled="$isDemo == 1">Confirm</el-button>
      </span>
    </template>
      <span slot="footer" class="dialog-footer">
      </span>
    </el-dialog>
    <el-dialog title="Read account" v-model="readDialogVisible" width="60%" :close-on-press-escape="true"
               :before-close="handleReadClose">
      <div class="card-body">
        <form>
          <div class="row">
            <div class="col-md-12">
              <div class="form-group">
                <div class="sub-title my-2 text-sm text-gray-600">
                  Insert a passphrase for credential encryption
                </div>
                <el-input type="password"
                          label="Insert a passphrase for credential encryption"
                          placeholder="passphrase"
                          v-model="read.encrypt_password">
                </el-input>
              </div>
            </div>
          </div>
          <div class="clearfix"></div>
        </form>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="readDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="readAccount">Read</el-button>
      </span>
    </el-dialog>
    <el-dialog title="Delete account" v-model="deleteDialogVisible" width="60%" :close-on-press-escape="true"
               :before-close="handleDeleteClose">
      <div class="card-body">
        <form>
          <div class="row" v-if="delete_account">
            <div class="col-md-12">
              <div class="form-group">
                <h4>Are you sure you want to delete this account?</h4>
                <ul>
                  <li>{{ delete_account.name }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div class="clearfix"></div>
        </form>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="deleteDialogVisible = false">Cancel</el-button>
        <el-button type="danger" @click="deleteAccount">Delete</el-button>
      </span>
    </el-dialog>

    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            <div class="row">
              <div class="col-md-6">
                <h5 class="title">Broker accounts </h5>
              </div>
              <div class="col-md-6">
                <div class="text-right mb-3">
                  <el-button type="primary" size="small" disabled>Read all</el-button>
                  <el-button type="primary" size="small" @click="openCreateDialog(1)">Add account</el-button>
                </div>
              </div>
            </div>
          </div>
          <div class="col-sm-12 mt-2">
            <el-table :data="brokerAccounts" stripe :cell-style="{padding: '0', height: '20px'}">
              <el-table-column label="Name" property="name"></el-table-column>
              <el-table-column label="Type" property="entity_name"></el-table-column>
              <el-table-column label="Fiat" property="balance">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.balance, scope.row.currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Value" property="virtual_balance">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.virtual_balance, scope.row.currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Last update" property="updated_on"></el-table-column>
              <el-table-column label="actions">
                <template v-slot:default="scope">
                  <el-tooltip content="Read" placement="top">
                    <el-button type="primary" aria-label="read" class="" @click="openReadDialog(scope.$index, scope.row)">
                      <i class="nc-icon nc-button-play"></i>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="Upload" placement="top">
                    <el-button type="success" aria-label="upload button" icon @click="" disabled>
                      <i class="nc-icon nc-cloud-upload-94"></i>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="Edit" placement="top">
                    <el-button type="warning" aria-label="read" icon @click="openCreateDialog(1, scope.row)">
                      <i class="nc-icon nc-settings-gear-65"></i>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip placement="top" content="Remove">
                    <el-button type="danger" aria-label="button" icon @click="openDeleteDialog(scope.row)">
                      <i class="nc-icon nc-simple-remove"></i>
                    </el-button>
                  </el-tooltip>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            <div class="row">
              <div class="col-md-6">
                <h5 class="title">Exchange accounts</h5>
              </div>
              <div class="col-md-6">
                <div class="text-right mb-3">
                  <el-button type="primary" size="small" disabled>Read all</el-button>
                  <el-button type="primary" size="small" @click="openCreateDialog(3)">Add account</el-button>
                </div>
              </div>
            </div>
          </div>
          <div class="col-sm-12 mt-2">
            <el-table :data="this.exchangeAccounts" stripe :cell-style="{padding: '0', height: '20px'}">
              <el-table-column label="Name" property="name"></el-table-column>
              <el-table-column label="Type" property="entity_name"></el-table-column>
              <el-table-column label="Fiat" property="balance">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.balance, scope.row.currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Value" property="virtual_balance">
                <template v-slot:default="scope">
                  {{ $filters.toCurrency(scope.row.virtual_balance, scope.row.currency) }}
                </template>
              </el-table-column>
              <el-table-column label="Last update" property="updated_on"></el-table-column>
              <el-table-column label="actions">
                <template v-slot:default="scope">
                  <el-tooltip content="Read" placement="top">
                    <el-button type="primary" aria-label="read" class="" @click="openReadDialog(scope.$index, scope.row)">
                      <i class="nc-icon nc-button-play"></i>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="Edit" placement="top">
                    <el-button type="warning" aria-label="read" icon @click="openCreateDialog(1, scope.row)">
                      <i class="nc-icon nc-settings-gear-65"></i>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip placement="top" content="Remove">
                    <el-button type="danger" aria-label="button" icon @click="openDeleteDialog(scope.row)">
                      <i class="nc-icon nc-simple-remove"></i>
                    </el-button>
                  </el-tooltip>
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
import axios from "axios";
import ChartCard from '@/components/UIComponents/Cards/ChartCard.vue'
import StatsCard from "@/components/UIComponents/Cards/StatsCard.vue";

export default {
  components: {
    ChartCard,
    StatsCard
  },
  data() {
    return {
      credential: {
        "currency": "EUR",
        "parameters": {},
        "entity": {}
      },
      errors: {},
      dialogVisible: false,
      readDialogVisible: false,
      deleteDialogVisible: false,
      delete_account: undefined,
      read: {
        account_id: undefined,
        encrypt_password: "",
      },
      exchangeAccounts: [],
      brokerAccounts: [],
      crowdAccounts: [],
      entities: [],
      entity_credentials: []
    }
  },
  created() {
    this.getData()
  },
  watch: {
    credential: {
      handler(val, oldVal) {
        this.errors = {};
      },
      deep: true
    },
    "credential.entity": {
      handler(entity) {
        if (entity !== undefined) {
          this.getAccountCredentialTypes(entity);
        }
      },
      deep: true
    },
    // "credential.entity": {
    //   handler(entity) {
    //     if (entity !== undefined) {
    //       this.getAccountCredentialTypes(entity);
    //     }
    //   },
    //   deep: true
    // },
    // "credential": {
    //   handler(val, oldVal) {
    //     this.errors = {};
    //   },
    //   deep: true
    // },
  },
  methods: {
    async deleteAccount() {
      let vm = this;
      await axios.delete(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts/" + this.delete_account.id).then(function (d) {
        vm.$notify({
          message: 'Account deleted correctly',
          type: 'info',
        });
        vm.getData();
      }).catch(_ => {
        vm.$notify({
          message: 'Unable to delete the account',
          type: 'warning',
        });
      });
      this.deleteDialogVisible = false;
      this.delete_account_id = undefined;
    },
    async openDeleteDialog(account) {
      this.deleteDialogVisible = true;
      this.delete_account = account;
    },
    async openReadDialog(id, account) {
      this.readDialogVisible = true;
      this.read.account_id = account.id;
    },
    async readAccount() {
      let data = {
        "encrypt_password": this.read.encrypt_password
      }
      this.read.encrypt_password = undefined;
      var vm = this;
      await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts/" + this.read.account_id + "/read", data).then(function (d) {
        vm.$notify({
          message: 'Reading account!',
          type: 'info',
        });
      }).catch(function (error) {
        console.log("Error reading the account!");
        vm.$notify({
          message: 'Unable to read the account',
          type: 'warning',
        });
      });
      this.readDialogVisible = false;
    },
    async addAccount(done) {
      console.log("Add or update account");
      this.errors = {};
      if (!this.credential.entity) {
        this.errors.entity = 'Choose an entity';
      }
      if (!this.credential.name) {
        //this.errors.push('The name of the account is required');
        this.errors.name = 'The name of the account is required';
      }
      if (!this.credential.currency) {
        this.errors.currency = 'The currency is required';
      }
      if (!this.credential.parameters.length && this.credential.id == undefined) {
        this.errors.parameters = 'Credentials are required';
      }
      if (!this.credential.encrypt_password && this.credential.id == undefined) {
        this.errors.encrypt_password = 'Encryption password is required';
      }

      if (Object.keys(this.errors).length) {
        console.log(this.errors)
        return;
      }

      let data = {
        "name": this.credential.name,
        "entity_id": this.credential.entity,
        "currency": this.credential.currency
      }
      let vm = this;
      if (this.credential['id'] != undefined) {
        console.log("Update account!");
        await axios.put(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts/" + this.credential['id'], data).then(function (res) {});
        if (this.credential.parameters.length) {
          console.log("Update credential!");
          await this.createCredential(this.credential);
        }
      } else {
        await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts", data).then(function (res) {
          vm.createCredential(res.data);
        });
      }
      this.dialogVisible = false;
    },
    async createCredential(account) {
      let parameters = []
      for (let key in this.credential.parameters) {
        parameters.push({
          "value": this.credential.parameters[key],
          "credential_type_id": Number(key)
        })
      }

      let data = {
        "parameters": parameters,
        "encrypt_password": this.credential.encrypt_password
      }
      await axios.post(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts/" + account.id + '/credentials', data).then(this.checkCredential);
      await this.getData()
    },
    checkCredential(res) {
      let res_status = res.status === 200 ? true : false;
      //console.log("Checking credential created");
    },
    async openCreateDialog(account_type, account = undefined) {
      this.dialogVisible = true;
      this.credential = {
        "parameters": [],
        "entity": undefined,
        "currency": undefined,
        "name": ""
      }
      if (account !== undefined) {
        this.credential["id"] = account.id;
        this.credential["entity"] = account.entity_id;
        this.credential["currency"] = account.currency;
        this.credential["name"] = account.name;
      }
      this.errors = [];
      this.entities = [];
      let vm = this;
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/entities/").then(function (res) {
        res.data.forEach(function (e) {
          if (e.type == account_type) {
            vm.entities.push(e);
          }
        });
      });
    },
    handleClose() {
      this.dialogVisible = false;
    },
    handleReadClose() {
      this.readDialogVisible = false;
    },
    handleDeleteClose() {
      this.deleteDialogVisible = false;
    },
    fillBrokers(broker_account) {
      this.brokerAccounts.push(broker_account);
      return broker_account;
    },
    fillExchanges(exchange_account) {
      this.exchangeAccounts.push(exchange_account);
      return exchange_account;
    },
    fillAccounts(res) {
      let res_status = res.status === 200 ? true : false;
      this.accounts = res.data;
      this.accounts.forEach(p => {
        if (p.entity_type == 1) {
          this.fillBrokers(p);
        } else if (p.entity_type == 3) {
          this.fillExchanges(p);
        }
        //p.balance = p.balance / 100;
      });
    },
    fillEntities(res) {
      let res_status = res.status === 200;
      this.entities = res.data;
    },
    fillCredentials(res) {
      let res_status = res.status === 200;
      console.log(res);
      console.log(res.data);
      console.log(this.entity_credentials);
      this.entity_credentials = res.data;
    },
    async getData() {
      this.brokerAccounts = [];
      this.exchangeAccounts = [];
      this.crowdAccounts = [];
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts").then(this.fillAccounts);
    },
    async getEntities() {
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/entities/").then(this.fillEntities);
    },
    async getAccountCredentialTypes(entity_id) {
      this.entity_credentials = [];
      await axios.get(import.meta.env.VITE_APP_BACKEND_URL + "/entities/" + entity_id + '/credentials').then(this.fillCredentials);
    }
  }
}
</script>
<style>
</style>
