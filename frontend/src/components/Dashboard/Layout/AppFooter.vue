<template>
  <footer class="footer footer-black footer-white">
    <div class="container-fluid">
      <div class="row">
        <nav class="footer-nav">
          <ul>
            <li>
              <a href="https://github.com/jbatalle/queds" class="nav-link" target="_blank" rel="noopener">ABOUT</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </footer>
</template>
<script>
export default {
  name: 'main-footer',
  data() {
    return {
      year: new Date().getFullYear()
    };
  }
}
</script>
<style>
</style>
