from odoo import models
from odoo.exceptions import UserError


class MrpRoutingWorkcenter(models.Model):
    _inherit = "mrp.routing.workcenter"

    def _skip_operation_line(self, product):
        skip = super()._skip_operation_line(product=product)
        if not skip:
            try:
                self.check_access_rule("read")
                self.workcenter_id.check_access_rule("read")
            except UserError:
                skip = True
        return skip
