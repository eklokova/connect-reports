# Report Requests


This report creates an Excel file with details about all approved requests with subscription scope parameters


# Available parameters

Request can be parametrized by:

* Request creation date range
* Product
* Marketplace
* Environment
* Request Type

# Columns
* Request ID
* Connect Subscription ID
* End Customer or External Subscription ID
* Action, Adobe Order Number, Adobe Transfer ID Number, VIP Number, and Adobe Cloud Program or Customer ID,
* Pricing SKU Level (Volume Discount level), Product Description, Part Number, Product Period, Cumulative Seat
* Order delta, Reseller ID, Reseller Name, End Customer Name End Customer External ID
* Provider  ID, Provider Name, Marketplace, Product ID, Product Name, Subscription Status, Anniversary Date
* Request Effective Date, Request Creation Date, Request Type, Adobe User Email, Currency
* Cost, Reseller Cost, MSRP, Connection Type or Environment Type, Exported At

Command to create report: ccli report execute requests -d .