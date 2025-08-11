/** @odoo-module **/
/*

    Copyright 2009-2023 Noviat.
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

import {AnalyticDistribution} from "@analytic/components/analytic_distribution/analytic_distribution";
import {patch} from "@web/core/utils/patch";

patch(
    AnalyticDistribution.prototype,
    "spantech_intercompany/static/src/components/analytic_distribution/analytic_distribution.js",
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
                    const base_domain = [
                        ["id", "not in", this.existingAnalyticAccountIDs],
                    ];
                    if (
                        "is_interco_partner" in this.props.record.data &&
                        this.props.record.data.is_interco_partner
                    ) {
                        base_domain.push(
                            "|",
                            ["company_id", "=", this.props.record.data.company_id[0]],
                            ["company_id", "=", false]
                        );
                        if (groupId) {
                            base_domain.push(["root_plan_id", "=", groupId]);
                        }
                        return base_domain;
                    }
                }
            }
            return domain;
        },
    }
);
