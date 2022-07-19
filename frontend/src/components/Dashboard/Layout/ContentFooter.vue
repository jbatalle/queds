<template>
  <footer class="footer">
    <div class="container-fluid">
      <nav class="pull-left">
        <ul>
        <li>
          <li>
            <a href="https://github.com/jbatalle/queds" class="nav-link" target="_blank" rel="noopener">Github</a>
          </li>
      </ul>
      </nav>
       <div class="copyright pull-right">
            <i class="fa fa-copyleft" style="font-weight: 200;"></i> {{ year }},
            <a href="https://github.com/jbatalle/queds" target="_blank" rel="noopener" >Queds</a>.
          </div>
    </div>
  </footer>
</template>
<script>
  export default {
    data() {
      return {
        year: new Date().getFullYear()
      };
    }
  }
</script>
<style>

</style>
