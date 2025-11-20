<template>
  <el-dialog title="Upload CSV" v-model="dialogVisible" width="60%" :close-on-press-escape="true"
             :before-close="handleDeleteClose">
    <div class="card-body">
      <form>
        <el-upload
            class="upload-demo"
            :on-preview="handlePreview"
            :limit="3"
            :auto-upload="false"
        >
          <el-button type="primary">Select file</el-button>
        </el-upload>
        <div class="clearfix"></div>
      </form>
    </div>
    <template #footer>
      <span slot="footer" class="dialog-footer">
        <el-button @click="closeUploadDialog = false">Cancel</el-button>
        <el-button type="success" @click="submitCSV">Upload</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import  UploadInstance from 'element-plus'
import { ref } from 'vue'

export default {
  props: {
    account: Object,
    visible: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dialogVisible: this.visible,
      uploadRef: null,
      formData: {
        accountId: null,
        csvFile: null,
      },
      uploadUrl: '/api/upload_csv', // Replace with your actual upload endpoint URL
    };
  },
  watch: {
    visible(newVal) {
      this.dialogVisible = newVal;
      this.resetFormData();
    },
  },
  methods: {
    resetFormData() {
      this.formData.accountId = null;
      this.formData.csvFile = null;
      this.$refs.csvUpload.clearFiles(); // Clear uploaded file after closing dialog
    },
    handleDrop(files) {
      this.formData.csvFile = files[0]; // Assign the first dropped file
    },
    handlePreview(file) {
      console.log('Preview file:', file);
    },
    handleUploadSuccess() {
      // Handle successful upload logic (e.g., close dialog, display success message)
      this.$emit('upload-success');
      this.dialogVisible = false;
      this.resetFormData();
    },
    handleUploadError(err) {
      console.error('Upload error:', err);
      // Handle upload error logic (e.g., display error message)
    },
    closeUploadDialog(){
      this.dialogVisible = false;
      this.$emit('upload-success');
    },
    submitCSV() {
      t = uploadRef.value
      // Implement logic to submit the form data (account ID and uploaded file)
      if (!this.formData.accountId || !this.formData.csvFile) {
        // Handle missing data error
        // return;
      }
      // You can use FormData or other methods to send data to the backend
      this.closeUploadDialog()
    },
  },
  created() {
  },
};
</script>

<style scoped>
.upload-csv-container {
  /* Add your custom styles for the dialog content */
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}
</style>