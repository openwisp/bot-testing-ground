"""Provide a small report lookup for the AI review integration fixture."""


def get_report(reports, organization_id, report_id):
    return reports.get(report_id)
