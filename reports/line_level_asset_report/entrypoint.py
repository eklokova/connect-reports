# -*- coding: utf-8 -*-
#
# Copyright (c) 2024, Elena Klokova
# All rights reserved.

from reports import api_calls
from reports import utils

asset_headers = [
    'id', 'status', 'external_id', 'product-id', 'provider-id', 'provider-name', 'marketplace-id',
    'marketplace-name', 'contract-id', 'contract-name', 'reseller-id', 'reseller-external_id', 'reseller-name',
    'created-at', 'customer-id', 'customer-external_id', 'customer-name'
]

asset_params_headers = [
    'external_reference_id', 'seamless_move', 'discount_group', 'action_type', 'renewal_date', 'purchase_type', 'adobe_customer_id',
    'adobe_vip_number', 'adobe_user_email', 'commitment_status', 'commitment_start_date', 'commitment_end_date',
    'recommitment_status', 'recommitment_start_date', 'recommitment_end_date'
]

marketplace_headers = [
    'currency', 'cost', 'reseller_cost', 'msrp', 'seats', 'USD-cost', 'USD-msrp',
    'USD-reseller_cost'
]


def generate(
        client=None,
        input_data=None,
        progress_callback=None,
        renderer_type='xlsx',
        extra_context_callback=None
):
    """
    Extracts data from Connect using the ConnectClient instance
    and input data provided as arguments, applies
    required transformations (if any) and returns the data rendered
    by the given renderer on the arguments list.
    Some renderers may require extra context data to generate the report
    output, for example in the case of the Jinja2 renderer...

    :param client: An instance of the CloudBlue Connect
                    client.
    :type client: cnct.ConnectClient
    :param input_data: Input data used to calculate the
                        resulting dataset.
    :type input_data: dict
    :param progress_callback: A function that accepts t
                                argument of type int that must
                                be invoked to notify the progress
                                of the report generation.
    :type progress_callback: func
    :param renderer_type: Renderer required for generating report
                            output.
    :type renderer_type: string
    :param extra_context_callback: Extra content required by some
                            renderers.
    :type extra_context_callback: func
    """

    assets = api_calls.request_assets(client, input_data)
    total = assets.count()

    counter = 0
    if total == 0:
        yield 'EMPTY ASSETS'
    for asset in assets:
        marketplace_params = _get_marketplace_params(client, asset)
        if not marketplace_params:
            marketplace_params = dict.fromkeys(marketplace_headers)
        # assets need to be in a list to yield
        if "commitment_status" in input_data and input_data['commitment_status'] == '3yc':
            print(asset['id'])
            print(utils.get_param_value_by_name(asset['params'], 'commitment_status'))
            if utils.get_param_value_by_name(asset['params'], 'commitment_status') == '-' \
                    or utils.get_param_value_by_name(asset['params'], 'commitment_status') == '':
                counter += 1
                progress_callback(counter, total)
                continue

        line = _process_line(asset, marketplace_params)
        items = asset['items']
        if not items:
            yield line
        else:
            for item in items:
                item_details = [item['id'],item['mpn'],item['display_name'],item['item_type'],item['quantity']]
                yield line + item_details
        counter += 1
        progress_callback(counter, total)


def _process_line(asset: dict, marketplace_params: dict) -> list:
    """
    This functions uses several functions on this file to build a line with values to yield at xlsx file

    :param asset: one asset from requested assets
    :param marketplace_params: dict to build the line
    :return: list with line values
    """
    asset_values = utils.process_asset_headers(asset, asset_headers)
    asset_values.update(utils.process_asset_parameters_by_name(asset['params'], asset_params_headers))

    if not asset_values['renewal_date']:
        asset_values['renewal_date'] = str(utils.handle_renewal_date(asset_values['created-at']))

    asset_values.update(marketplace_params)
    return list(asset_values.values())


def _get_marketplace_params(client, asset):
    """
    This function returns a dict with key,value pairs for each marketplace_header or None if there is no listing
    for the marketplace and product in asset

    :type client: connect.ConnectClient
    :type asset: dict
    :param client: connect.ConnectClient
    :param asset: dict with asset from connect
    :return: dict if listing or None
    """
    listing = api_calls.request_listing(client, asset['marketplace']['id'], asset['product']['id'])
    if listing and 'pricelist' in listing:
        price_list_version = api_calls.request_price_list(client, listing['pricelist']['id'])
        price_list_points = api_calls.request_price_list_version_points(client, price_list_version['id']) \
            if price_list_version else []
        if price_list_version and price_list_points:
            try:
                # dict with currency and currency change
                currency = utils.get_currency_and_change(price_list_version)

                # dict with all financials from all items in price list
                price_list_financials = utils.get_financials_from_price_list(price_list_points)

                # dict with seats and financials from assets items
                financials_and_seats = utils.get_financials_and_seats(asset['items'], price_list_financials)

                # dict with financials in USD
                base_financials = utils.get_base_currency_financials(financials_and_seats, currency)
                currency.pop('change')
                currency.update(financials_and_seats)
                currency.update(base_financials)
                currency['cost'] = '{:0.2f}'.format(currency['cost'])
                currency['reseller_cost'] = '{:0.2f}'.format(currency['reseller_cost'])
                currency['msrp'] = '{:0.2f}'.format(currency['msrp'])
                return currency
            except:
                currency = {
                    'cost': "0.0",
                    'reseller_cost': "0.0",
                    'msrp': "0.0"
                }
                return currency
    # Listing has no price list or is not active
    return None
