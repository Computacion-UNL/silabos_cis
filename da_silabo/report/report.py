from odoo import models, api
from datetime import datetime

class ReportePlanAnalitico(models.AbstractModel):
    _name = "report.da_silabo.report_plan_analitico"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["das.plananalitico"].browse(docids)
        docargs = {
            "docs":docs,
            "fecha":datetime.now().strftime("%m-%d-%Y"),
        }
        return docargs

class ReporteSilaboco(models.AbstractModel):
    _name = "report.da_silabo.report_silabo"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["das.silabo"].browse(docids)
        docargs = {
            "docs":docs,
            "fecha":datetime.now().strftime("%m-%d-%Y"),
        }
        return docargs