# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Stock Backdating (MRP)",
    "summary": "Allow to backdate manufacturing orders",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Manufacturing",
    "depends": ["stock_backdating", "mrp"],
    "data": [
        "views/mrp_production_views.xml",
    ],
    "installable": True,
}
