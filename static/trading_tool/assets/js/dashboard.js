$(function () {
    // var positions_data = {{ positions_data | safe }};
    var realized_profits = [];
    var realized_loss = [];
    
    positions_data.netPositions.forEach(function(position) {
      var rounded_profit = Math.round(position.realized_profit * 100) / 100;
      if (rounded_profit >= 0) {
        realized_profits.push(rounded_profit);
        realized_loss.push(0);
      } else {
        realized_loss.push(-rounded_profit);
        realized_profits.push(0);
      }
    });
  
    // Extracting last 7 characters of each symbol string into another array
    var symbols_data = positions_data.netPositions.map(function(position) {
      return position.symbol.slice(-7);
    });
  
    // Sort the array in ascending order
    realized_profits.sort(function(a, b) {
      return a - b;
    });
    // Sort the array in ascending order
    realized_loss.sort(function(a, b) {
      return b - a;
    });
    
    console.log("realized_profitsrealized_profits",realized_profits);
    console.log("realized_profitsrealized_profits",realized_loss);
  
  
    // Find the highest value in the array
    var max_profit = Math.max(...realized_profits);
    var maxloss = Math.max(...realized_loss);
    var max_value = Math.max(max_profit, maxloss);
  
  
  
  
    // Round it up to the nearest hundred higher than that value
    var rounded_profit = Math.ceil(max_value / 100) * 100;
  
    console.log(rounded_profit);
  
  
  
    // =====================================
    // Profit
    // =====================================
  
    var chart = {
      series: [
        { name: "P\L this Position:", data: realized_profits },
        { name: "Loss this Day:", data:realized_loss},
      ],
  
      chart: {
        type: "bar",
        height: 345,
        offsetX: -15,
        toolbar: { show: true },
        foreColor: "#adb0bb",
        fontFamily: 'inherit',
        sparkline: { enabled: false },
      },
  
  
      colors: ["#5D87FF", "#FF033E"],
  
  
      plotOptions: {
        bar: {
          fill:"#E32636",
          horizontal: false,
          columnWidth: "35%",
          borderRadius: [6],
          borderRadiusApplication: 'end',
          borderRadiusWhenStacked: 'all'
        },
      },
      markers: { size: 0 },
  
      dataLabels: {
        enabled: false,
      },
  
  
      legend: {
        show: false,
      },
  
  
      grid: {
        borderColor: "rgba(0,0,0,0.1)",
        strokeDashArray: 3,
        xaxis: {
          lines: {
            show: false,
          },
        },
      },
  
      xaxis: {
        type: "category",
        categories: symbols_data,
        labels: {
          style: { cssClass: "grey--text lighten-2--text fill-color" },
        },
      },
  
  
      yaxis: {
        show: true,
        min: 0,
        max: rounded_profit,
        tickAmount: 4,
        labels: {
          style: {
            cssClass: "grey--text lighten-2--text fill-color",
          },
        },
      },
      stroke: {
        show: true,
        width: 3,
        lineCap: "butt",
        colors: ["transparent"],
      },
  
  
      tooltip: { theme: "light" },
  
      responsive: [
        {
          breakpoint: 600,
          options: {
            plotOptions: {
              bar: {
                borderRadius: 3,
              }
            },
          }
        }
      ]
  
  
    };
  
    var chart = new ApexCharts(document.querySelector("#chart"), chart);
    chart.render();
  
  
    // =====================================
    // Breakup
    // =====================================
    var breakup = {
      color: "#adb5bd",
      series: [38, 40, 25],
      labels: ["2022", "2021", "2020"],
      chart: {
        width: 180,
        type: "donut",
        fontFamily: "Plus Jakarta Sans', sans-serif",
        foreColor: "#adb0bb",
      },
      plotOptions: {
        pie: {
          startAngle: 0,
          endAngle: 360,
          donut: {
            size: '75%',
          },
        },
      },
      stroke: {
        show: false,
      },
  
      dataLabels: {
        enabled: false,
      },
  
      legend: {
        show: false,
      },
      colors: ["#5D87FF", "#ecf2ff", "#F9F9FD"],
  
      responsive: [
        {
          breakpoint: 991,
          options: {
            chart: {
              width: 150,
            },
          },
        },
      ],
      tooltip: {
        theme: "dark",
        fillSeriesColor: false,
      },
    };
  
    var chart = new ApexCharts(document.querySelector("#breakup"), breakup);
    chart.render();
  
  
  
    // =====================================
    // Earning
    // =====================================
    var earning = {
      chart: {
        id: "sparkline3",
        type: "area",
        height: 60,
        sparkline: {
          enabled: true,
        },
        group: "sparklines",
        fontFamily: "Plus Jakarta Sans', sans-serif",
        foreColor: "#adb0bb",
      },
      series: [
        {
          name: "Earnings",
          color: "#49BEFF",
          data: [25, 66, 20, 40, 12, 58, 20],
        },
      ],
      stroke: {
        curve: "smooth",
        width: 2,
      },
      fill: {
        colors: ["#f3feff"],
        type: "solid",
        opacity: 0.05,
      },
  
      markers: {
        size: 0,
      },
      tooltip: {
        theme: "dark",
        fixed: {
          enabled: true,
          position: "right",
        },
        x: {
          show: false,
        },
      },
    };
    new ApexCharts(document.querySelector("#earning"), earning).render();
  })