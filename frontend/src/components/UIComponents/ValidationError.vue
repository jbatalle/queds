<template>
  <span v-if="errors && errors.length">
    <small class="error" v-text="errors[0]"/>
  </span>
</template>

<script>
  export default {
    name: "validation-error",
    props: {
      errors: {
        type: Array,
        default: () => ([])
      }
    }
  }
</script>

<style lang="scss">
.error {
  width: 100%;
  margin-top: .25rem;
  font-size: 80%;
  color: #dc3545;
}
</style>
