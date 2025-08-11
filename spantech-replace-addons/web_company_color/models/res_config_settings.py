# Copyright 2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo import fields, models

COLOR_FIELDS = [
    "color_navbar_bg",
    "color_navbar_bg_hover",
    "color_navbar_text",
    "color_button_text",
    "color_button_bg",
    "color_button_bg_hover",
    "color_link_text",
    "color_link_text_hover",
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    color_multi_active_companies = fields.Boolean(
        string="Set of colors for multi companies",
        config_parameter="web_company_color.color_multi_active_companies",
    )
    color_navbar_bg = fields.Char(
        "Navbar Background Color", config_parameter="web_company_color.color_navbar_bg"
    )
    color_navbar_bg_hover = fields.Char(
        "Navbar Background Color Hover",
        config_parameter="web_company_color.color_navbar_bg_hover",
    )
    color_navbar_text = fields.Char(
        "Navbar Text Color", config_parameter="web_company_color.color_navbar_text"
    )
    color_button_text = fields.Char(
        "Button Text Color", config_parameter="web_company_color.color_button_text"
    )
    color_button_bg = fields.Char(
        "Button Background Color", config_parameter="web_company_color.color_button_bg"
    )
    color_button_bg_hover = fields.Char(
        "Button Background Color Hover",
        config_parameter="web_company_color.color_button_bg_hover",
    )
    color_link_text = fields.Char(
        "Link Text Color", config_parameter="web_company_color.color_link_text"
    )
    color_link_text_hover = fields.Char(
        "Link Text Color Hover",
        config_parameter="web_company_color.color_link_text_hover",
    )

    def set_values(self):
        super().set_values()
        IrAttachmentObj = self.env["ir.attachment"]
        if self.color_multi_active_companies:
            values = {}
            for color_field in COLOR_FIELDS:
                if getattr(self, color_field):
                    values[color_field] = getattr(self, color_field)
            datas = base64.b64encode(
                self.env.company._scss_generate_content(values).encode("utf-8")
            )
            custom_url = self.env.company.scss_get_url(multi_company=True)
            custom_attachment = IrAttachmentObj.sudo().search(
                [("url", "=", custom_url)]
            )
            values = {
                "datas": datas,
                "db_datas": datas,
                "url": custom_url,
                "name": custom_url,
                "company_id": False,
            }
            if custom_attachment:
                custom_attachment.sudo().write(values)
            else:
                values.update({"type": "binary", "mimetype": "text/scss"})
                IrAttachmentObj.sudo().create(values)
            self.env["ir.qweb"].sudo().clear_caches()
