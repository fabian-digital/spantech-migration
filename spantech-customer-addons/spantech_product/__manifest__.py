# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech product",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": [
        "spantech_base",
        "spantech_analytic",
        "product",
        "mrp_account",
    ],
    "data": [
        "security/product_security.xml",
        "security/ir.model.access.csv",
        "wizards/code_product_update_views.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/product_sequence_views.xml",
    ],
    "installable": True,
}
