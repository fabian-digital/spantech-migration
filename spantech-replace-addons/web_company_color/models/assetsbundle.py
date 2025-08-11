# Copyright 2020 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.http import request

from odoo.addons.base.models.assetsbundle import AssetsBundle, ScssStylesheetAsset


class AssetsBundleCompanyColor(AssetsBundle):
    def get_company_color_asset_node(self):
        """Process the user active company scss and returns the node to inject"""
        try:
            active_company_list = request.httprequest.cookies.get("cids", "").split(",")
            if len(active_company_list) > 1:
                active_company_ids = [int(cid) for cid in active_company_list]
            else:
                active_company_ids = False
            active_company_id = int(active_company_list[0])
        except Exception:
            active_company_id = False
            active_company_ids = False
        company_id = (
            self.env["res.company"].browse(active_company_id) or self.env.company
        )
        company_ids = self.env["res.company"].browse(active_company_ids) or self.env.company
        asset = False
        if company_ids and len(company_ids) > 1:
            if (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "web_company_color.color_multi_active_companies", False
                )
            ):
                asset = ScssStylesheetAsset(
                    self, url=company_id.scss_get_url(multi_company=True)
                )
        if not asset:
            asset = ScssStylesheetAsset(self, url=company_id.scss_get_url())
        compiled = self.compile_css(asset.compile, asset.get_source())
        return "style", {}, compiled
