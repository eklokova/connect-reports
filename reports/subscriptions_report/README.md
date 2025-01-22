# Subscriptions report

This report creates an Excel file with details about subscriptions (assets) with scope parameters

# Available parameters

Subscriptions can be parametrized by:

* Product
* Creation date range
* Status
* Environment type
* Commitment status

# Columns

* Asset ID
* Asset Status
* External ID, Product ID, Marketplace, Marketplace Name
* Reseller ID, Reseller External ID, Reseller Name, Created At, Customer ID, Customer External ID, Customer Name
* Seamless Move, Discount Group, Action, Renewal Date, Purchase Type
* Adobe Customer ID, Adobe Vip Number
* Commitment status, Commitment start date, Commitment end date
* Recommitment status, Recommitment start date, Recommitment end date

Command to create report: ccli report execute assets -d .