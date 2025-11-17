// Dashboard chart and sell modal functionality

// Chart initialization
function initializeChart(labels, values, colors) {
  var ctx = document.getElementById('allocChart');
  
  if (ctx) {
    var chart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderColor: '#fff',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                var label = context.label || '';
                var value = context.parsed || 0;
                return label + ': ' + value.toLocaleString();
              }
            }
          }
        }
      }
    });

    // Custom legend below chart
    var legendContainer = document.getElementById('chartLegend');
    var legendItems = labels.map(function(label, i) {
      return '<span style="display:inline-flex;align-items:center;margin-right:15px;">' +
        '<span style="width:16px;height:16px;background:' + colors[i] + ';border-radius:3px;display:inline-block;margin-right:6px;"></span>' +
        '<span>' + label + '</span>' +
        '</span>';
    }).join('');
    legendContainer.innerHTML = legendItems;
  }
}

// Sell Asset Modal
function sellAsset(assetId, assetName, maxQuantity, symbol, assetType) {
  document.getElementById('sell_asset_id').value = assetId;
  document.getElementById('sell_asset_name').textContent = assetName;
  document.getElementById('sell_max_quantity').textContent = maxQuantity.toFixed(2);
  document.getElementById('sell_quantity').max = maxQuantity;
  document.getElementById('sellForm').action = '/assets/' + assetId + '/sell';
  
  // Fetch current price
  var priceInput = document.getElementById('sell_price');
  var priceText = priceInput.nextElementSibling;
  priceInput.value = '';
  priceText.textContent = 'Fetching current price...';
  priceText.className = 'form-text text-muted';
  
  fetch('/api/price/' + encodeURIComponent(symbol) + '/' + encodeURIComponent(assetType))
    .then(function(res) { return res.json(); })
    .then(function(data) {
      if (data.price) {
        priceInput.value = data.price.toFixed(2);
        priceText.textContent = 'Current market price for ' + assetName;
        priceText.className = 'form-text text-success';
      } else {
        priceInput.value = '';
        priceInput.readOnly = false;
        priceText.textContent = 'Could not fetch price. Please enter manually.';
        priceText.className = 'form-text text-warning';
      }
    })
    .catch(function(err) {
      console.error('Price fetch error:', err);
      priceInput.value = '';
      priceInput.readOnly = false;
      priceText.textContent = 'Could not fetch price. Please enter manually.';
      priceText.className = 'form-text text-danger';
    });
  
  var modal = new bootstrap.Modal(document.getElementById('sellModal'));
  modal.show();
}
