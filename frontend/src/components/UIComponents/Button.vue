<template>
  <component :is="tag"
             :type="nativeType"
             @click="handleClick"
             class="btn"
             :class="classes">
    <span class="btn-label" v-if="$slots.label">
      <slot name="label"></slot>
    </span>
    <slot></slot>
    <span class="btn-label btn-label-right" v-if="$slots.labelRight">
      <slot name="labelRight"></slot>
    </span>
  </component>
</template>
<script>
  export default {
    name: 'p-button',
    props: {
      tag: {
        type: String,
        default: 'button',
        description: 'Html tag to use'
      },
      type: {
        type: String,
        default: 'default',
        description: 'Color type'
      },
      nativeType: {
        type: String,
        default: 'button',
        description: 'Native button type (e.g submit|button) '
      },
      round: Boolean,
      outline: Boolean,
      block: Boolean,
      social: Boolean,
      link: Boolean,
      icon: Boolean,
      wide: Boolean,
      size: String
    },
    computed: {
      classes() {
        let btnClasses = [
          {[`btn-outline-${this.type}`]: this.outline},
          {'btn-icon': this.icon},
          {'btn-round': this.round},
          {'btn-block': this.block},
          {'btn-social': this.social},
          {'btn-link': this.link},
          {'btn-wd': this.wide},
          `btn-${this.type}`
        ];
        if (this.size) {
          btnClasses.push(`btn-${this.size}`)
        }
        return btnClasses
      }
    },
    methods: {
      handleClick(evt) {
        this.$emit('click', evt)
      }
    }
  }
</script>
<style>
</style>
