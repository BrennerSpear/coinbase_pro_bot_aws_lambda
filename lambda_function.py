#!/usr/bin/env python

import boto3
import datetime
import decimal
import json
import math
import os
import sys
import time

import cbpro

from decimal import Decimal


def get_timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


"""
    Basic Coinbase Pro DCA buy/sell bot that executes a market order.
    * CB Pro does not incentivize maker vs taker trading unless you trade over $50k in
        a 30 day period (0.25% taker, 0.15% maker). Current fees are 0.50% if you make
        less than $10k worth of trades over the last 30 days. Drops to 0.35% if you're
        above $10k but below $50k in trades.
    * Market orders can be issued for as little as $5 in some markets of value versus limit orders which
        must be 0.001 BTC (e.g. $50 min if btc is at $50k). BTC-denominated market
        orders must be at least 0.0001 BTC.
"""

def lambda_handler(event, context):
    args = event
    print(f"{get_timestamp()}: STARTED: {args}")

    market_name = args['market_name']
    order_side = args['order_side'].lower()
    amount = Decimal(args['amount'])
    amount_currency = args['amount_currency']
    warn_after = 300

    if os.environ['ENV'] == 'PRODUCTION':
        key = os.environ['CBPRO_API_KEY']
        passphrase = os.environ['CBPRO_PASSPHRASE']
        secret = os.environ['CBPRO_SECRET_KEY']
    else:
        key = os.environ['CBPRO_API_KEY_SANDBOX']
        passphrase = os.environ['CBPRO_PASSPHRASE_SANDBOX']
        secret = os.environ['CBPRO_SECRET_KEY_SANDBOX']


    # Instantiate public and auth API clients
    if os.environ['ENV'] == 'PRODUCTION':
        auth_client = cbpro.AuthenticatedClient(key, secret, passphrase)
    else:
        # Use the sandbox API (requires a different set of API access credentials)
        auth_client = cbpro.AuthenticatedClient(
            key,
            secret,
            passphrase,
            api_url="https://api-public.sandbox.pro.coinbase.com")

    public_client = cbpro.PublicClient()

    # Retrieve dict list of all trading pairs
    products = public_client.get_products()
    base_increment = None
    quote_increment = None
    for product in products:
        if product.get("id") == market_name:
            base_currency = product.get("base_currency")
            quote_currency = product.get("quote_currency")
            base_increment = Decimal(product.get("base_increment")).normalize()
            quote_increment = Decimal(product.get("quote_increment")).normalize()
            if amount_currency == product.get("quote_currency"):
                amount_currency_is_quote_currency = True
            elif amount_currency == product.get("base_currency"):
                amount_currency_is_quote_currency = False
            else:
                raise Exception(f"amount_currency {amount_currency} not in market {market_name}")
            print(json.dumps(product, indent=2))

    if amount_currency_is_quote_currency:
        result = auth_client.place_market_order(
            product_id=market_name,
            side=order_side,
            funds=float(amount.quantize(quote_increment))
        )
    else:
        result = auth_client.place_market_order(
            product_id=market_name,
            side=order_side,
            size=float(amount.quantize(base_increment))
        )

    print(json.dumps(result, sort_keys=True, indent=4))

    if "message" in result:
        # Something went wrong if there's a 'message' field in response
        return {
            'statusCode': 500,
            'body': json.dumps(result, sort_keys=True, indent=4)
        }

    if result and "status" in result and result["status"] == "rejected":
        print(f"{get_timestamp()}: {market_name} Order rejected")

    order = result
    order_id = order["id"]
    print(f"order_id: {order_id}")

    '''
        Wait to see if the order was fulfilled.
    '''
    wait_time = 5
    total_wait_time = 0
    while "status" in order and \
            (order["status"] == "pending" or order["status"] == "open"):
        if total_wait_time > warn_after:
            return {
                'statusCode': 500,
                'body': json.dumps(order, sort_keys=True, indent=4)
            }

        print(f"{get_timestamp()}: Order {order_id} still {order['status']}. Sleeping for {wait_time} (total {total_wait_time})")
        time.sleep(wait_time)
        total_wait_time += wait_time
        order = auth_client.get_order(order_id)
        print(json.dumps(order, sort_keys=True, indent=4))

        if "message" in order and order["message"] == "NotFound":
            # Most likely the order was manually cancelled in the UI
            return {
                'statusCode': 500,
                'body': json.dumps(result, sort_keys=True, indent=4)
            }

    # Order status is no longer pending!
    print(json.dumps(order, indent=2))

    market_price = (Decimal(order["executed_value"])/Decimal(order["filled_size"])).quantize(quote_increment)

    subject = f"{market_name} {order_side} order of {amount} {amount_currency} {order['status']} @ {market_price} {quote_currency}"
    print(subject)
    return {
        'statusCode': 200,
        'body': json.dumps(order, sort_keys=True, indent=4)
    }

