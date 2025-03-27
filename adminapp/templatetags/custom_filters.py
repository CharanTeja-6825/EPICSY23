from django import template

register = template.Library()

FAILED_GRADES = {"GP", "WH", "DT", "F", "NA"}

@register.filter
def is_failed(grade):
    return grade in FAILED_GRADES
