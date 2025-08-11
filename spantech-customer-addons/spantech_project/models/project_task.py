from odoo import fields, models


class ProjectTack(models.Model):
    _inherit = "project.task"

    installation_step = fields.Selection(
        selection=[
            ("site_preparation", "Site Preparation"),
            ("site_logistics", "Site Logistics"),
            ("foundation", "Foundation"),
            ("structure", "Structure"),
            ("shell", "Shell"),
            ("fit_out", "Fit Out"),
            ("mep", "MEP"),
            ("finishing", "Finishing"),
            ("contingency", "Contingency"),
        ],
        default="site_preparation",
    )
