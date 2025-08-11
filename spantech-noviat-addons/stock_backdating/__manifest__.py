# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Stock Backdating",
    "summary": "Allow to backdate pickings and inventory adjustments",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Inventory",
    "depends": ["stock", "stock_account"],
    "data": [
        "views/stock_picking_views.xml",
        "views/stock_quant_views.xml",
    ],
    "installable": True,
}
