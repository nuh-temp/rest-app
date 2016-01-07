'use strict';

var express = require('express');
var phantomjs = require('phantomjs');
var webdriver = require('selenium-webdriver');
var bodyParser = require('body-parser');
var urlParse = require('url').parse;

var app = express();

app.use(express.static('st'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));

var capabilities = webdriver.Capabilities.phantomjs();
capabilities.set('phantomjs.binary.path', phantomjs.path);
var driver = new webdriver.Builder().withCapabilities(capabilities).build();

var HANDLERS = {
  'www.amazon.com': getAmazonPrice,
  'amzn.to': getAmazonPrice,
  'www1.macys.com': getMacysPrice,
};


function getAmazonPrice(url) {
  driver.get(url);
  var el = webdriver.By.xpath("//span[@id='priceblock_ourprice' or @id='priceblock_dealprice']");
  return driver.wait(function() {
    return driver.isElementPresent(el).then(function(presents) {
      return (presents) ? driver.findElement(el).getText() : null;
    });
  }, 1000, 'Failed to find price after 1 second').then(function(strPrice) {
    return (strPrice) ? parseFloat(strPrice.replace(/[^\d.,]+/i, '')) : null;
  });
}

function getMacysPrice(url) {
  driver.get(url);
  var el = webdriver.By.xpath("//div[contains(@id, 'priceInfo')]/div[contains(@class, 'standardProdPricingGroup')]/span[contains(@class, 'priceSale')]");
  return driver.wait(function() {
    return driver.isElementPresent(el).then(function(presents) {
      return (presents) ? driver.findElement(el).getText() : null;
    });
  }, 1000, 'Failed to find price after 1 second').then(function(strPrice) {
    return (strPrice) ? parseFloat(strPrice.replace(/[^\d.,]+/i, '')) : null;
  });
}

app.route('/check')
  .get(function(req, res) {
    res.sendFile(__dirname + "/check.html" );
  })
  .post(function(req, res) {
    var url = req.body.url;
    var price = parseFloat(req.body.price);
    var urlObj = urlParse(url);

    var handler = HANDLERS[urlObj.host];
    if (!handler) {
      return res.json({
        status: 'err',
        msg: 'Unknown store "' + urlObj.host + '".',
      });
    }

    console.log('start checking: %s', url);
    handler(url).then(function(currentPrice) {
      console.log(' done checking: %s', url);
      res.json({
        url: url,
        price: price,
        currentPrice: currentPrice,
        valid: (price == currentPrice)
      });
    });
  });

app.get('/', function(req, res) {
  res.status(200).send('It works!');
});

var server = app.listen(process.env.PORT || 8080, function () {
  var host = server.address().address;
  var port = server.address().port;

  console.log('App listening at http://%s:%s', host, port);
});
