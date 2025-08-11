/** @odoo-module **/
/*

    Copyright 2009-2023 Noviat.
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

import {AnalyticDistribution} from "@analytic/components/analytic_distribution/analytic_distribution";
import {patch} from "@web/core/utils/patch";

patch(
    AnalyticDistribution.prototype,
    "spantech_analytic/static/src/components/analytic_distribution/analytic_distribution.js",
    {
        analyticAccountDomain(groupId = null) {
            const domain = this._super(groupId);
            if (
                ["account.move", "account.move.line"].includes(
                    this.props.record.resModel
                )
            ) {
                if (
                    "move_type" in this.props.record.data &&
                    ["out_invoice", "out_refund", "out_receipt"].includes(
                        this.props.record.data.move_type
                    )
                ) {
                    if (
                        "commercial_partner_id" in this.props.record.data &&
                        this.props.record.data.commercial_partner_id
                    ) {
                        domain.push(
                            "|",
                            [
                                "partner_id",
                                "=",
                                this.props.record.data.commercial_partner_id[0],
                            ],
                            ["partner_id", "=", false]
                        );
                    } else if (
                        "partner_id" in this.props.record.data &&
                        this.props.record.data.partner_id
                    ) {
                        domain.push(
                            "|",
                            ["partner_id", "=", this.props.record.data.partner_id[0]],
                            ["partner_id", "=", false]
                        );
                    }
                }
            }
            return domain;
        },
    }
);
