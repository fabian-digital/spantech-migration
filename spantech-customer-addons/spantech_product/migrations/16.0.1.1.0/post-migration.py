# Copyright 2024 Noviat.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# pylint: disable=W7936
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _set_default_company_dependant_values(env)


def _set_default_company_dependant_values(env):
    property_fields = {
        "invoice_policy": env.ref("sale.field_product_template__invoice_policy"),
        "produce_delay": env.ref("mrp.field_product_template__produce_delay"),
        "days_to_prepare_mo": env.ref("mrp.field_product_template__days_to_prepare_mo"),
        "sale_delay": env.ref("stock.field_product_template__sale_delay"),
    }
    _logger.info("start _set_default_company_dependant_values")
    env.cr.execute(
        "SELECT id, %s FROM product_template" % (", ".join(property_fields.keys()))
    )
    datas = env.cr.dictfetchall()
    i = len(datas)
    _logger.info("_set_default_company_dependant_values Datas to process: %s" % i)
    for data in datas:
        for field, val in data.items():
            if val and field != "id":
                env["product.template"].browse(data["id"])[field] = val
        i -= 1
        if i % 1000 == 0:
            _logger.info(
                "_set_default_company_dependant_values Datas to process: %s" % i
            )
    _logger.info("_set_default_company_dependant_values properties created")
    properties = env["ir.property"].search(
        [
            ("fields_id", "in", [field.id for field in list(property_fields.values())]),
        ]
    )
    properties.write({"company_id": False})
    _logger.info("end _set_default_company_dependant_values (properties updated)")
