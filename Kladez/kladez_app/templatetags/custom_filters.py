from django import template

register = template.Library()


@register.filter
def group_by(queryset, attribute):
    """
    Группирует queryset по указанному атрибуту
    Использование в шаблоне: queryset|group_by:"category"
    """
    from itertools import groupby
    from operator import attrgetter

    # Сортируем queryset по указанному атрибуту
    sorted_queryset = sorted(queryset, key=attrgetter(attribute))

    # Группируем
    result = []
    for key, group in groupby(sorted_queryset, key=attrgetter(attribute)):
        result.append({
            'grouper': key,
            'list': list(group)
        })

    return result