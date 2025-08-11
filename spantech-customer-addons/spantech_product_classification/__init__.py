from . import models
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref(
        "product_classification.product_classification_root", raise_if_not_found=False
    ):
        env.ref("product_classification.product_classification_root").unlink()
