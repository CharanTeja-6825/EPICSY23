from django import template

register = template.Library()

FAILED_GRADES = {"GP", "WH", "DT", "F", "NA"}

@register.filter(name="is_failed")
def is_failed(grade):
    """Returns True if the grade is a failing grade"""
    return grade in FAILED_GRADES
