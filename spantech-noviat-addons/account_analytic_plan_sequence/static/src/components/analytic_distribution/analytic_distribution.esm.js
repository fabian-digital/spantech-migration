/** @odoo-module **/
/*

    Copyright 2009-2023 Noviat.
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

import {AnalyticDistribution} from "@analytic/components/analytic_distribution/analytic_distribution";
import {patch} from "@web/core/utils/patch";

patch(
    AnalyticDistribution.prototype,
    "account_analytic_plan_sequence/static/src/components/analytic_distribution/analytic_distribution.js",
    {
        get sortedList() {
            var res = this._super();
            res = res.sort((a, b) => {
                const aApp = a.sequence,
                    bApp = b.sequence;
                return aApp > bApp ? 1 : aApp < bApp ? -1 : 0;
            });
            return res;
        },

        get listFlat() {
            var res = this._super.apply(this, arguments);
            var sort_aa_by_plan_seq_function = function (plans) {
                for (var i = 0; i < res.length; i++) {
                    for (var j = 0; j < plans.length; j++) {
                        if (res[i].group_id === plans[j].id) {
                            res[i].sequence = plans[j].sequence;
                        }
                    }
                }
                res = res.sort((a, b) => {
                    const aApp = a.sequence,
                        bApp = b.sequence;
                    return aApp > bApp ? 1 : aApp < bApp ? -1 : 0;
                });
            };
            if (!this.allPlans.length) {
                this.fetchAllPlans(this.props).then(() => {
                    sort_aa_by_plan_seq_function(this.allPlans);
                    return res;
                });
            }
            sort_aa_by_plan_seq_function(this.allPlans);
            this.allPlans = [];
            return res;
        },

        deleteTag(id, fromGroup) {
            this.list[fromGroup].distribution = this.list[
                fromGroup
            ].distribution.filter((dist_tag) => dist_tag.id !== id);
            if (this.list[fromGroup].distribution.length === 1) {
                this.list[fromGroup].distribution[0].percentage = 100.0;
            }
            this._super.apply(this, arguments);
        },
    }
);
