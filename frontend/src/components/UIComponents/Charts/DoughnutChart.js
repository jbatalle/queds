import { Pie } from 'vue-chartjs'
import pluginChartText from './plugins/plugin-chart-text';

const defaultOptions = {
  elements: {
    center: {
      text: '60%',
      color: '#66615c', // Default is #000000
      fontStyle: 'Arial', // Default is Arial
      sidePadding: 60 // Defualt is 20 (as a percentage)
    }
  },
  cutoutPercentage: 90,
  legend: {

    display: false
  },

  tooltips: {
    enabled: false
  },

  scales: {
    yAxes: [{

      ticks: {
        display: false
      },
      gridLines: {
        drawBorder: false,
        zeroLineColor: "transparent",
        color: 'rgba(255,255,255,0.05)'
      }

    }],

    xAxes: [{
      barPercentage: 1.6,
      gridLines: {
        drawBorder: false,
        color: 'rgba(255,255,255,0.1)',
        zeroLineColor: "transparent"
      },
      ticks: {
        display: false,
      }
    }]
  },
};

export default {
  name: 'doughnut-chart',
  extends: Pie,
  props: {
    labels: {
      type: [Object, Array],
      description: 'Chart labels. This is overridden when `data` is provided'
    },
    datasets: {
      type: [Object, Array],
      description: 'Chart datasets. This is overridden when `data` is provided'
    },
    data: {
      type: [Object, Array],
      description: 'Chart.js chart data (overrides all default data)'
    },
    color: {
      type: String,
      description: 'Chart color. This is overridden when `data` is provided'
    },
    extraOptions: {
      type: Object,
      description: 'Chart.js options'
    },
    title: {
      type: String,
      description: 'Chart title'
    },
  },
  methods: {
    assignChartData() {
      return {
        labels: this.labels || [],
        datasets: this.datasets ? this.datasets : [{
          pointRadius: 0,
          pointHoverRadius: 0,
          backgroundColor: [this.color || '#4acccd', this.secondaryColor || '#f4f3ef'],
          borderWidth: 0,
          data: this.data || []
        }]
      }
    },
    assignChartOptions(initialConfig) {
      let extraOptions = this.extraOptions || {};
      return {
        ...initialConfig,
        ...extraOptions
      };
    }
  },
  mounted() {
    this.addPlugin(pluginChartText);
    this.chartData = this.assignChartData({});
    this.options = this.assignChartOptions(defaultOptions);
    this.options.elements.center.text = this.data ? `${this.data[0]}%` : null;
    this.renderChart(this.chartData, this.options);
  }
}
