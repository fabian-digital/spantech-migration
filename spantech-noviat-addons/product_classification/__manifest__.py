# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Classification",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Product Management",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "data/product_classification_data.xml",
        "views/product_classification_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
}
