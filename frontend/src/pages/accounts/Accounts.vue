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
    <span slot="footer" class="dialog-footer"></span>
  </el-dialog>
  <el-dialog title="Read account" v-model="readDialogVisible" width="60%" :close-on-press-escape="true"
             :before-close="handleReadClose">
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
                          placeholder="passphrase"
                          v-model="read.encrypt_password">
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
    <template #footer>
      <span slot="footer" class="dialog-footer">
        <el-button @click="deleteDialogVisible = false">Cancel</el-button>
        <el-button type="danger" @click="deleteAccount">Delete</el-button>
      </span>
    </template>
  </el-dialog>
  <el-dialog title="Upload CSV" v-model="uploadDialogVisible" width="60%" :close-on-press-escape="true"
             :before-close="handleUploadClose">
    <div class="card-body">
      <form>
        <el-upload
            action=""
            ref="uploadRef"
            :http-request="uploadAction"
            class="upload-demo"
            drag
            :limit="1"
            :auto-upload="false"
        >
          <el-icon class="el-icon--upload">
            <!--upload-filled/-->
          </el-icon>
          <el-button type="primary">Select file</el-button>
          <template #tip>
            <div class="el-upload__tip text-red" v-if="upload_ko">
              Error uploading file: {{ upload_ko }}
            </div>
            <div class="el-upload__tip text-green" v-if="upload_ok">
              File uplodaded correctly!
            </div>
          </template>
        </el-upload>
        <div class="clearfix"></div>
      </form>
    </div>
    <template #footer>
      <span slot="footer" class="dialog-footer">
        <el-button @click="uploadDialogVisible = false">Close</el-button>
        <el-button type="success" @click="submitCSV">Upload</el-button>
      </span>
    </template>
  </el-dialog>
  <div class="row">
    <div class="col-md-12">
      <account-table
          title="Broker accounts"
          :accounts="brokerAccounts"
          :table-columns="tableColumns"
          :account-type="1"
          @open-create-dialog="openCreateDialog"
          @open-read-dialog="openReadDialog"
          @open-delete-dialog="openDeleteDialog"
          @open-upload-dialog="openUploadDialog"
      >
      </account-table>
    </div>
    <div class="col-md-12">
      <account-table
          title="Exchange accounts"
          :accounts="exchangeAccounts"
          :table-columns="tableColumns"
          :account-type="3"
          @open-create-dialog="openCreateDialog"
          @open-read-dialog="openReadDialog"
          @open-delete-dialog="openDeleteDialog"
          @open-upload-dialog="openUploadDialog"
      >
      </account-table>
    </div>
  </div>
    </div>
</template>
<script>
import axios from "axios";
import ChartCard from '@/components/UIComponents/Cards/ChartCard.vue'
import StatsCard from "@/components/UIComponents/Cards/StatsCard.vue";
import AccountTable from "@/pages/accounts/AccountTable.vue";
import {ref} from 'vue'
import {nextTick} from 'vue';

const uploadRef = ref()
export default {
  components: {
    ChartCard,
    StatsCard,
    AccountTable
  },
  data() {
    return {
      tableColumns: [
        {label: "Name", prop: "name"},
        {label: "Type", prop: "entity_name"},
        {label: "Fiat", prop: "balance", slot: "balance"},
        {label: "Value", prop: "virtual_balance", slot: "virtual_balance"},
        {label: "Last update", prop: "updated_on"}
      ],
      credential: {
        "currency": "EUR",
        "parameters": {},
        "entity": {}
      },
      errors: {},
      dialogVisible: false,
      readDialogVisible: false,
      deleteDialogVisible: false,
      uploadDialogVisible: false,
      delete_account: undefined,
      read: {
        account_id: undefined,
        encrypt_password: "",
      },
      upload: {
        account: undefined,
        file: null
      },
      upload_ko: false,
      upload_ok: false,
      exchangeAccounts: [],
      brokerAccounts: [],
      crowdAccounts: [],
      entities: [],
      entity_credentials: [],
      loading: false
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
    async openUploadDialog(id, account) {
      this.upload_ko = false;
      this.upload_ok = false;
      this.uploadDialogVisible = true;
      this.upload.account = account;
    },
    async readAccount() {
      this.loading = true;
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
      this.loading = false;
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
        await axios.put(import.meta.env.VITE_APP_BACKEND_URL + "/entities/accounts/" + this.credential['id'], data).then(function (res) {
        });
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
    handleUploadClose() {
      this.uploadDialogVisible = false;
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
    },
    async processUpload(res) {
      let res_status = res.status === 200;
      if (res_status) {
        this.upload_ok = true;
      } else {
        this.upload_ko = res.response.data.message;
      }
    },
    async submitCSV() {
      this.upload_ko = false;
      this.upload_ok = false;
      await this.$nextTick();
      await this.$refs.uploadRef.submit()
    },
    async uploadAction(option) {
      let d = {
        "account_id": this.upload.account.id,
        "file": option.file
      }
      await axios.postForm(import.meta.env.VITE_APP_BACKEND_URL + "/entities/upload_csv", d).then(this.processUpload).catch(this.processUpload);
      await this.$refs.uploadRef.clearFiles();
    }
  }
}
</script>
<style>
.example-showcase .el-loading-mask {
  z-index: 9;
}

.text-red {
  --un-text-opacity: 1;
  color: rgba(248, 113, 113, var(--un-text-opacity));
}

.text-green {
  --un-text-opacity: 1;
  color: green;
}
</style>
