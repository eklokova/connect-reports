from reports import api_calls
from datetime import datetime, timezone, date
import calendar

BASE_CURRENCY = 'USD'
FOREXAPI_URL = 'https://theforexapi.com/api/latest'


def get_param_value_by_name(params: list, value: str) -> str:
    try:
        if params[0]['name'] == value:
            return params[0]['value']
        if len(params) == 1:
            return '-'
        return get_param_value_by_name(list(params[1:]), value)
    except Exception:
        return '-'


def get_param_value(params: list, value: str) -> str:
    try:
        if params[0]['id'] == value:
            return params[0]['value']
        if len(params) == 1:
            return '-'
        return get_param_value(list(params[1:]), value)
    except Exception:
        return '-'


def get_basic_value(base, value):
    try:
        if base and value in base:
            return base[value]
        return '-'
    except Exception:
        return '-'


def get_value(base, prop, value):
    if prop in base:
        return get_basic_value(base[prop], value)
    return '-'


def convert_to_datetime(param_value):
    if param_value == "" or param_value == "-" or param_value is None:
        return "-"

    return datetime.strptime(
        param_value.replace("T", " ").replace("+00:00", ""),
        "%Y-%m-%d %H:%M:%S",
    )


def today() -> datetime:
    return datetime.datetime.today()


def today_str() -> str:
    return datetime.today().strftime('%Y-%m-%d %H:%M:%S')


def process_asset_headers(asset, asset_headers) -> dict:
    """
    This function takes an asset and asset_headers to reach values in asset for
    each key at asset_headers

    :type asset: dict
    :type asset_headers: list
    :param asset: one asset from requested assets
    :param asset_headers: headers to use as keys
    :return: dict with values from asset and keys from headers
    """
    params = dict.fromkeys(asset_headers)
    for header in asset_headers:
        if '-' in header:
            params[header] = get_value_from_split_header(asset, header)
        else:
            if header in asset:
                params[header] = asset[header]
            else:
                params[header] = '-'

    return params


def process_asset_parameters_by_name(asset_params: list, asset_parameters: list) -> dict:
    """
    This function takes asset_params and asset_parameters(headers) to reach values in asset_params for
    each key at asset_parameters

    :type asset_params: list
    :type asset_parameters: list
    :param asset_params: requested asset['params'] from connect
    :param asset_parameters: headers with keys to build the dict and reach the values
    :return: dict with values from asset_params and keys from asset_parameters
    """
    params_dict = dict.fromkeys(asset_parameters)
    for param in asset_params:
        param_id = param['name']
        if param_id == 'discount_group':
            discount_group = get_discount_level(param['value'])
            params_dict[param_id] = discount_group
        elif param_id == 'cb_price_level_hint_final_object' and 'structured_value' in param:
            params_dict['hvd_code'] = get_hvd_code(param)
        elif param_id in asset_parameters:
            params_dict[param_id] = param['value']

    return params_dict

def get_hvd_code(param):
    items = (
    param.get("structured_value", {})
        .get("discount", {})
        .get("items", [])
    )
    first_hvd = next(
        (item.get("rating_attribute") for item in items if item.get("rating_attribute", "").startswith("HVD")),
        ""
    )
    return first_hvd

def handle_renewal_date(asset_creation_date: str) -> date:
    return calculate_renewal_date(asset_creation_date, datetime.now(timezone.utc).date())

def calculate_renewal_date(asset_creation_date: str, current_date: date) -> date:
    date = datetime.fromisoformat(asset_creation_date).date()
    renewal_date = resolve_leap_year_renewal_date(date, current_date.year)
    if renewal_date >= current_date:
        return renewal_date
    return resolve_leap_year_renewal_date(renewal_date, current_date.year + 1)


def resolve_leap_year_renewal_date(original_date: date, target_year: int) -> date:
    if calendar.isleap(original_date.year) and original_date.month == 2 and original_date.day == 29:
        if calendar.isleap(target_year):
            return original_date.replace(year=target_year)
        else:
            return date(year=target_year, month=3, day=1)
    return original_date.replace(year=target_year)


def get_value_from_split_header(asset: dict, header: str) -> str:
    """
    This function gets the header with '-' format and split it to reach the value in asset
    example: product-id -> asset[product][id]

    :type asset: dict
    :type header: str
    :param asset: requested asset from connect
    :param header: str from headers
    :return: str with value from asset
    """
    try:
        h0 = header.split('-')[0]
        h1 = header.split('-')[1]
        if h0 == 'created':
            value = asset['events'][h0][h1]
        elif h0 == 'provider':
            value = asset['connection'][h0][h1]
        elif h0 in ['customer', 'reseller']:
            if h0 == 'reseller':
                h0 = 'tier1'
            value = asset['tiers'][h0][h1]
        else:
            value = asset[h0][h1]
        return value
    except Exception:
        return '-'


def get_discount_level(discount_group: str) -> str:
    """
    Transform the discount_group to a proper level of discount

    :type discount_group: str
    :param discount_group:
    :return: str with level of discount
    """
    if len(discount_group) > 2 and discount_group[2] == 'A' and discount_group[0] == '1':
        discount = 'Level ' + discount_group[0:2]
    elif len(discount_group) > 2 and discount_group[2] == 'A':
        discount = 'Level ' + discount_group[1]
    elif len(discount_group) > 2 and discount_group[2] == '0':
        discount = 'TLP Level ' + discount_group[1]
    else:
        discount = 'Empty'

    return discount


def get_financials_from_price_list(price_list_points: list) -> dict:
    """
    This function retrieves the cost, reseller_cost and msrp from each point at the price list points

    :type price_list_points: list
    :param price_list_points: request with points of price list
    :return: dict with cost, reseller_cost and msrp
    """
    items_financials = {}
    for point in price_list_points:
        items_financials[point['item']['global_id']] = {} if point['item']['global_id'] not in items_financials \
            else point['item']['global_id']
        if float(point['attributes']['price']) != 0.0:
            items_financials[point['item']['global_id']]['cost'] = \
                float(point['attributes']['price'])

            items_financials[point['item']['global_id']]['reseller_cost'] = \
                float(point['attributes']['st0p']) if 'st0p' in point['attributes'] else 0.0

            items_financials[point['item']['global_id']]['msrp'] = \
                float(point['attributes']['st1p']) if 'st1p' in point['attributes'] else 0.0
    return items_financials


def get_currency_and_change(price_list_version: dict) -> dict:
    """
    Use the price list version to retrieve the currency and change from this currency to dollars in case
    of api fail the change will be 0 so the USD columns will be 0

    :type price_list_version: dict
    :param price_list_version: request with price list version
    :return: dict containing currency acronym and currency change
    """
    currency = {'currency': price_list_version['pricelist']['currency']}
    if currency['currency'] != BASE_CURRENCY:
        exchange_response = api_calls.request_get(FOREXAPI_URL)
        if exchange_response.status_code == 200:
            currency['change'] = exchange_response.json()['rates'][BASE_CURRENCY]
        else:
            currency['change'] = 0.0
    else:
        currency['change'] = 1.0

    return currency


def get_financials_and_seats(items: list, price_list_financials: dict) -> dict:
    """
    This function takes items and price list for those items to return a dict with values if they
    exits at items and all financials added from each item

    :type price_list_financials: dict
    :type items: list
    :param items: list with items from request
    :param price_list_financials: dict with cost, reseller_cost and msrp for each item[global_id]
    :return: dict
    """
    asset_financials = {}
    asset_type = None
    seats = cost = reseller_cost = msrp = 0.0
    for item in items:
        item_quantity = int(item['quantity'])
        if 'Enterprise' in item['display_name'] and not asset_type:
            asset_type = 'enterprise'
        elif 'Enterprise' in item['display_name'] and asset_type == 'team':
            asset_type = 'both'
        else:
            asset_type = 'team'
        if item_quantity > 0:
            seats = seats + item_quantity
            if price_list_financials and item['global_id'] in price_list_financials:
                cost = cost + item_quantity * price_list_financials[item['global_id']]['cost']
                reseller_cost = reseller_cost + item_quantity * price_list_financials[item['global_id']][
                    'reseller_cost']
                msrp = msrp + item_quantity * price_list_financials[item['global_id']]['msrp']

    asset_financials['purchase_type'] = asset_type
    asset_financials['cost'] = cost
    asset_financials['reseller_cost'] = reseller_cost
    asset_financials['msrp'] = msrp
    asset_financials['seats'] = seats
    return asset_financials


def get_base_currency_financials(financials_and_seats: dict, currency: dict) -> dict:
    """
    This function returns the value in dollars for the current cost, reseller_cost and msrp

    :type financials_and_seats: dict
    :type currency: dict
    :param financials_and_seats: contains the cost, reseller_cost and msrp
    :param currency: contains the change(float) to multiply against financials_and_seats values
    :return: dict with cost, reseller_cost and msrp in dollars
    """
    return {
        'USD-cost': '{:0.2f}'.format(financials_and_seats['cost'] * currency['change']),
        'USD-reseller_cost': '{:0.2f}'.format(financials_and_seats['reseller_cost'] * currency['change']),
        'USD-msrp': '{:0.2f}'.format(financials_and_seats['msrp'] * currency['change'])}


def get_financials_from_product_per_marketplace(client, marketplace_id, asset_id):
    listing = api_calls.request_listing(client, marketplace_id, asset_id)
    price_list_points = []
    try:
        if listing and listing['pricelist']:
            price_list_version = api_calls.request_price_list(client, listing['pricelist']['id'])
            price_list_points = api_calls.request_price_list_version_points(client, price_list_version['id'])
    except:
        return {}
    return get_financials_from_price_list(price_list_points)
