# Copyright 2009-2020 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Classification - Purchase",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Product Management",
    "depends": ["product_classification", "purchase"],
    "data": ["security/ir.model.access.csv", "views/menu.xml"],
    "installable": True,
    "auto_install": True,
}
