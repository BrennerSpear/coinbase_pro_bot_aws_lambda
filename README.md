# coinbase_pro_bot
A basic Coinbase Pro buying bot that completes market trades in any of their available market pairings. 

Relies on [gdax-python](https://github.com/danpaquin/gdax-python). Thank you [danpaquin](https://github.com/danpaquin)

Forked from [gdax_bot](https://github.com/kdmukai/gdax_bot). Thank you [kdmukai](https://github.com/kdmukai)

Say hi on twitter: [@brennerspear](https://www.twitter.com/brennerspear)

### Setup

### Create Coinbase Pro API key
Try this out on Coinbase Pro's sandbox first. The sandbox is a test environment that is not connected to your actual fiat or crypto balances.

Log into your Coinbase/Coinbase Pro account in their test sandbox:
https://public.sandbox.pro.coinbase.com/

Find and follow existing guides for creating an API key. Only grant the "Trade" permission. Note the passphrase, the new API key, and API key's secret. Write these down.

While you're in the sandbox UI, fund your fiat account by transferring from the absurd fake balance that sits in the linked Coinbase account (remember, this is all just fake test data; no real money or crypto goes through the sandbox).

### Create a lambda function
[AWS Lambda](https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions)

1. click "Create Function"
2. enter a function name
3. Runtime: Python 3.8
4. click "Create Function"
5. click "Upload from" --> .zip file
6. upload the zip in this repo: `my-lambda-deployment-package.zip`

### Configure your lambda function

1. Click "Configuration"
2. Click "Environment variables"
3. Click "edit" on the right
4. add the following 7 key-value pairs you got from Coinbase Pro earlier:
```
ENV = SANDBOX

CBPRO_PASSPHRASE_SANDBOX = xxx
CBPRO_API_KEY_SANDBOX = xxx
CBPRO_SECRET_KEY_SANDBOX = xxx

CBPRO_PASSPHRASE = xxx
CBPRO_API_KEY = xxx
CBPRO_SECRET_KEY = xxx
```

click save

We're setting the environment as `SANDBOX` for now so we can do a test run first

### Try a sandbox test run

Click "Test"
Add an example event with the following JSON data (The sandbox only has BTC-USD)
```
{
  "market_name": "BTC-USD",
  "order_side": "BUY",
  "amount": "10",
  "amount_currency": "USD"
}
```

Click "Test"

It should give a successful run, and show the output in the dropdown

### Try a production test run

Go back to Configuration --> Environment variables --> edit

Change  `ENV` to `PRODUCTION`

Save and go back to test. Run another test. This time it will actually be buying btc from your real account!

### Scheduling your recurring buys

1. Search in the top search bar for "EventBridge" where you'll [create a rule](https://console.aws.amazon.com/events/home?region=us-east-1#/rules/create)
2. name your rule (I named one of mine "buy-eth-every-hour)
3. select "Schedule"
4. Fixed rate every x minutes/hours/days
5. Target: Lambda function
6. Function: your function's name
7. Configure input
8. select "Constant (JSON text)"
9. copy and paste the JSON data that fits what you want to buy. Example:
```
{
  "market_name": "SOL-USD",
  "order_side": "BUY",
  "amount": "10",
  "amount_currency": "USD"
}
```

Click "Add target"

Click "Create"

Congratulations! Your bot is running!

You can create multiple rules if you want to buy multiple different assets.

## Disclaimers
Use and modify it at your own risk. This is not investment advice. I am not an investment advisor. 

The requirments.txt file probably doesn't match exactly what's in the .zip.

`lambda_function.py` might have some imports it doesn't need.

You could get rid of the loops and sleeper since you don't actually need a response to execute the trade, but then you won't have any logs.

If you're going to edit the code and upload, [this tutorial](https://docs.aws.amazon.com/lambda/latest/dg/python-package-create.html#python-package-create-with-dependency) was helpful. Zipping the dependency files + `lambda_function.py` together can be a bit finicky. 


TODO:

The environment variables should probably be encrypted in transit. The code needed to decrypt them when they arrive needs to be added. 


