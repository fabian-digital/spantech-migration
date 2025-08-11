from odoo import models


class MailAliasMixin(models.AbstractModel):
    _name = "mail.alias.mixin"
    _inherit = "mail.alias.mixin"

    # dirty fix made by Odoo - See if it's the best solution
    # https://picasso.noviat.com/Noviat/Noviat_Generic/mail/-/merge_requests/14
    def _alias_filter_fields(self, values, filters=False):
        value_to_remove = "company_id"
        if value_to_remove in values:
            filters = [
                x
                for x in filters or self.env["mail.alias"]._fields.keys()
                if x != value_to_remove
            ]
        return super()._alias_filter_fields(values, filters)
