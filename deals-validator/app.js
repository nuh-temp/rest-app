'use strict';

var express = require('express');
var phantomjs = require('phantomjs');
var webdriver = require('selenium-webdriver');
var bodyParser = require('body-parser');
var urlParse = require('url').parse;
var fs = require('fs');

var app = express();

app.use(express.static('st'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));

var logPrefs = new webdriver.logging.Preferences();
logPrefs.setLevel(webdriver.logging.Type.DRIVER,
               webdriver.logging.Level.ALL);
logPrefs.setLevel(webdriver.logging.Type.BROWSER,
               webdriver.logging.Level.ALL);
logPrefs.setLevel(webdriver.logging.Type.CLIENT,
               webdriver.logging.Level.ALL);
console.log('webdriver logging', logPrefs);

var capabilities = webdriver.Capabilities.phantomjs();
capabilities.setLoggingPrefs(logPrefs);
capabilities.set('phantomjs.binary.path', phantomjs.path);
capabilities.set('phantomjs.cli.args', [
    '--load-images=false',
    // '--remote-debugger-port=9000',
]);
capabilities.set('phantomjs.page.settings.userAgent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36');
var driver = new webdriver.Builder().withCapabilities(capabilities).build();

// this runs in browser's scope
driver.executePhantomJS(function() {
  this.onResourceRequested = function(requestData, request) {
    var fs = require('fs');
    var logFile = '/tmp/console-logs.txt';
    fs.touch(logFile);
    var regexes = [
      /https?:\/\/.+?\.css/gi,
      /https?:\/\/.+?\.amazon-adsystem\.com/gi,
      /https?:\/\/fls-na\.amazon\.com/gi,
      /https?:\/\/.+?[\.-]images-amazon\.com/gi,
    ]
    var log = function(msg) {
      console.log(msg);
      // try {
      //   fs.write(logFile, msg + '\n', 'a');
      // } catch(e) {}
    };
    var abort = function() {
      log('The url of the request is matching. Aborting: ' + requestData['url']);
      request.abort()
    }

    if (requestData['Content-Type'] == 'text/css') {
      abort();
    }

    for (var i = 0; i < regexes.length; i++) {
      if (regexes[i].test(requestData['url'])) {
        abort();
        break;
      }
    }
  };
});

process.on('SIGINT', function() {
  console.log('Shuting down PhantomJS...');
  driver.quit();
  process.exit();
});

var HANDLERS = {
  'www.amazon.com': getAmazonPrice,
  'amzn.to': getAmazonPrice,
  'www1.macys.com': getMacysPrice,
};


function printLogs(driver) {
  var logs = new webdriver.WebDriver.Logs(driver);
  logs.getAvailableLogTypes().then(function(data) {
    console.log('getAvailableLogTypes:', data);
    if (data.indexOf(webdriver.logging.Type.BROWSER) == -1) {
      return []
    }
    return logs.get(webdriver.logging.Type.BROWSER);
  }).then(function (v) {
    console.log('BROWSER LOGS:', v.length);
    // v && v.length && console.log(v);
    v.forEach(function(entry) {
      console.log(entry.level.name + '::' + entry.timestamp + '::' + entry.message)
    })
  });
}

function printPageTitle(driver) {
  driver.getCurrentUrl().then(function(data) {
    console.log('getCurrentUrl:', data);
  });
}

function saveScreenshot(driver) {
  driver.takeScreenshot().then(function(data) {
    console.log('takeScreenshot:', data.length);
    fs.writeFileSync('/tmp/111.png', data, 'base64');
    console.log('Saved!');
  });
}

function getIntValueByPath(url, xPath) {
  driver.get(url);
  var el = webdriver.By.xpath(xPath);
  return driver.wait(
      driver.isElementPresent(el),
      1000,
      'Failed to find price after 1 second')
  .then(function(presents) {
    console.log('price element found');
    return (presents) ? driver.findElement(el).getText() : null;
  })
  .then(function(strValue) {
    return (strValue) ? parseFloat(strValue.replace(/[^\d.,]+/i, '')) : null;
  });
}

function getAmazonPrice(url) {
  return getIntValueByPath(
      url,
      "//span[@id='priceblock_ourprice' or @id='priceblock_dealprice']");
}

function getMacysPrice(url) {
  return getIntValueByPath(
      url,
      "//div[contains(@id, 'priceInfo')]" +
        "/div[contains(@class, 'standardProdPricingGroup')]" +
        "/span[contains(@class, 'priceSale')]");
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
