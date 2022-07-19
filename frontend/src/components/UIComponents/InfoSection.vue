<template>
    <div class="info-area" :class="`info-${direction}`">
        <div class="icon" :class="`icon-${type}`" v-if="$slots.icon || icon">
            <slot name="icon">
                <i :class="icon"></i>
            </slot>
        </div>
        <div class="description" v-if="$slots.default || title">
            <slot>
                <h5 class="info-title">{{title}}</h5>
                <p class="description">{{description}}</p>
            </slot>
        </div>
    </div>
</template>
<script>
  export default {
    props: {
      direction: {
        type: String,
        default: 'horizontal',
        description: 'Section direction (horizontal|vertical)'
      },
      type: {
        type: String,
        default: '',
        description: 'Section type (primary|danger etc)'
      },
      icon: {
        type: String,
        default: ''
      },
      title: {
        type: String,
        default: ''
      },
      description: {
        type: String,
        default: ''
      }
    }
  }
</script>
<style>
</style>
