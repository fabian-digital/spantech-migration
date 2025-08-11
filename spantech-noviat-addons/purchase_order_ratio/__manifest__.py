# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Purchase Order Ratio",
    "summary": "Add a ratio on delivered/invoiced quantities on the purchase orders",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Purchases",
    "depends": ["purchase_stock"],
    "data": [
        "views/purchase_order_views.xml",
    ],
    "installable": True,
}
