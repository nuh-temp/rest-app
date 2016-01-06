'use strict';

var express = require('express');
var phantomjs = require('phantomjs')
var webdriver = require('selenium-webdriver');
var bodyParser = require('body-parser');

var app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));

function getCurrentPrice(url) {
  var capabilities = webdriver.Capabilities.phantomjs();
  capabilities.set('phantomjs.binary.path', phantomjs.path);
  var driver = new webdriver.Builder().withCapabilities(capabilities).build();

  driver.get(url);
  return driver.wait(function() {
    var el1 = webdriver.By.id("priceblock_dealprice");
    var el2 = webdriver.By.id("priceblock_ourprice");

    return driver.isElementPresent(el1).then(function(presents) {
      if (presents) {
        return driver.findElement(el1).getText();
      }
      return driver.isElementPresent(el2).then(function(presents) {
        if (presents) {
          return driver.findElement(el2).getText();
        }
      });
    });
  }, 1000, 'Failed to find price after 1 second').then(function(strPrice) {
    return parseFloat(strPrice.replace(/^\$/, ''));
  });
}

app.route('/check')
  .get(function(req, res) {
    res.sendFile(__dirname + "/" + "check.html" );
  })
  .post(function(req, res) {
    var url = req.body.url;
    var price = parseFloat(req.body.price);
    getCurrentPrice(url).then(function(currentPrice) {
      res.json({
        url: url,
        price: price,
        currentPrice: currentPrice,
        valid: (price == currentPrice)
      });
    });
  });

app.get('/phantomjs', function(req, res) {
  var capabilities = webdriver.Capabilities.phantomjs();
  capabilities.set('phantomjs.binary.path', phantomjs.path);
  var driver = new webdriver.Builder().withCapabilities(capabilities).build();

  // driver.get('http://www.amazon.com/Nordic-Ware-Cast-Iron-Aluminum-Shortbread/dp/B000237FR6');
  driver.get('http://www.amazon.com/Donner-Mountain-Mens-Iron-BLACK/dp/B012BQH0K8');
  // http://www.amazon.com/Nordic-Ware-Cast-Iron-Aluminum-Shortbread/dp/B000237FR6 - 38.16
  // http://www.amazon.com/Donner-Mountain-Mens-Iron-BLACK/dp/B012BQH0K8 - 39.90
  driver.wait(function() {
    return driver.findElement(webdriver.By.id("priceblock_dealprice")).getText().then(function(text) {
      return res.status(200).send('Deal price: ' + text);
    }, function(error) {
      console.log('ELEMENT is not found:', error);
      return driver.findElement(webdriver.By.id("priceblock_ourprice")).getText().then(function(text) {
        return res.status(200).send('Our price: ' + text);
      }, function(error) {
        return res.status(404).send('Price is not found.');
      });
    });
  }, 1000);

  driver.quit();
});

app.get('/', function(req, res) {
  res.status(200).send('It works!');
});

var server = app.listen(process.env.PORT || 8080, function () {
  var host = server.address().address;
  var port = server.address().port;

  console.log('App listening at http://%s:%s', host, port);
});
