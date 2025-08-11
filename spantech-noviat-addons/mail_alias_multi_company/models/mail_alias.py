# Copyright 2022 Noviat (https://www.noviat.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import remove_accents


class MailAlias(models.Model):
    _inherit = "mail.alias"

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    def _compute_alias_domain(self):
        for rec in self:
            if rec.company_id:
                rec.alias_domain = rec.company_id.mail_alias_domain
            else:
                super(MailAlias, rec)._compute_alias_domain()
        return

    @api.model
    def create(self, vals):
        if vals.get("alias_defaults", {}) and vals["alias_defaults"].get(
            "company_id", False
        ):
            self = self.with_context(
                alias_company_id=vals["alias_defaults"].get("company_id")
            )
            vals["company_id"] = vals["alias_defaults"].get("company_id")
        return super().create(vals)

    def write(self, vals):
        if vals.get("alias_defaults", {}) and vals["alias_defaults"].get(
            "company_id", False
        ):
            self = self.with_context(
                alias_company_id=vals["alias_defaults"].get("company_id")
            )
            vals["company_id"] = vals["alias_defaults"].get("company_id")
        return super().write(vals)

    def _clean_and_check_unique(self, names):
        # Copy paste of the standard method in order
        # to change a domain which fits with our logic
        # Since the domain is in the middle of the method,
        # I don't see any other choice.
        def _sanitize_alias_name(name):
            """Cleans and sanitizes the alias name"""
            sanitized_name = remove_accents(name).lower().split("@")[0]
            sanitized_name = re.sub(r"[^\w+.]+", "-", sanitized_name)
            sanitized_name = re.sub(r"^\.+|\.+$|\.+(?=\.)", "", sanitized_name)
            sanitized_name = sanitized_name.encode("ascii", errors="replace").decode()
            return sanitized_name

        if self.env.context.get("alias_company_id"):
            alias_company = self.env["res.company"].browse(
                self.env.context.get("alias_company_id")
            )
        elif self and self.company_id:
            alias_company = self.company_id
        else:
            alias_company = False

        sanitized_names = [_sanitize_alias_name(name) for name in names]

        catchall_alias = (
            self.env["ir.config_parameter"].sudo().get_param("mail.catchall.alias")
        )
        bounce_alias = (
            self.env["ir.config_parameter"].sudo().get_param("mail.bounce.alias")
        )
        if alias_company and alias_company.mail_alias_domain:
            alias_domain = alias_company.mail_alias_domain
        else:
            alias_domain = (
                self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain")
            )

        # matches catchall or bounce alias
        for sanitized_name in sanitized_names:
            if sanitized_name in [catchall_alias, bounce_alias]:
                matching_alias_name = (
                    "%s@%s" % (sanitized_name, alias_domain)
                    if alias_domain
                    else sanitized_name
                )
                raise UserError(
                    _(
                        "The e-mail alias %(matching_alias_name)s is already used as "
                        "%(alias_duplicate)s alias. "
                        "Please choose another alias.",
                        matching_alias_name=matching_alias_name,
                        alias_duplicate=_("catchall")
                        if sanitized_name == catchall_alias
                        else _("bounce"),
                    )
                )

        # matches existing alias
        domain = [("alias_name", "in", sanitized_names)]
        if self:
            domain += [("id", "not in", self.ids)]
        matching_alias = (
            self.sudo()
            .search(domain)
            .filtered(lambda ma: ma.alias_domain == alias_domain)
        )
        if not matching_alias:
            return sanitized_names

        sanitized_alias_name = _sanitize_alias_name(matching_alias.alias_name)
        matching_alias_name = (
            "%s@%s" % (sanitized_alias_name, alias_domain)
            if alias_domain
            else sanitized_alias_name
        )
        if (
            matching_alias.alias_parent_model_id
            and matching_alias.alias_parent_thread_id
        ):
            # If parent model and parent thread ID both are set,
            # display document name also in the warning
            document_name = (
                self.env[matching_alias.alias_parent_model_id.model]
                .sudo()
                .browse(matching_alias.alias_parent_thread_id)
                .display_name
            )
            raise UserError(
                _(
                    "The e-mail alias %(matching_alias_name)s is already used "
                    "by the %(document_name)s %(model_name)s. Choose another alias "
                    "or change it on the other document.",
                    matching_alias_name=matching_alias_name,
                    document_name=document_name,
                    model_name=matching_alias.alias_parent_model_id.name,
                )
            )
        raise UserError(
            _(
                "The e-mail alias %(matching_alias_name)s is already linked "
                "with %(alias_model_name)s. Choose another alias "
                "or change it on the linked model.",
                matching_alias_name=matching_alias_name,
                alias_model_name=matching_alias.alias_model_id.name,
            )
        )

    _sql_constraints = [
        (
            "alias_unique",
            "UNIQUE(alias_name, company_id)",
            "Unfortunately this email alias is already used, please choose a unique one",
        )
    ]
