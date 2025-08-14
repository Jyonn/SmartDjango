from smartdjango.models import QuerySet


class Page:
    def __init__(self, queryset, count, next_value):
        self.queryset: QuerySet = queryset
        self.count = count
        self.next_value = next_value

    def dict(self, object_map, next_map=None):
        return dict(
            object_list=self.queryset.map(object_map),
            next_value=next_map(self.next_value) if next_map else self.next_value,
            count=self.count,
        )


class Paginator:
    def __init__(
            self,
            queryset: QuerySet,
            page_size: int,
    ):
        self.queryset = queryset
        self.page_size = page_size
        self.count = self.queryset.count()

        self.target_field = None

    def filter(self, **kwargs):
        assert len(kwargs) == 1, "only one filter is allowed"
        order = list(kwargs.keys())[0]
        assert '__' in order, "attribute must contain '__' to specify the comparison method"
        self.target_field, compare_op = order.split('__', 1)
        assert compare_op in ['lt', 'gt'], "comparison operation must be 'lt' or 'gt'"

        order = self.target_field
        if compare_op == 'lt':
            order = '-' + order

        self.queryset = self.queryset.filter(**kwargs).order_by(order)

    def get_page(
        self,
        page: int = None,
    ) -> Page:
        if page is None:
            assert self.target_field is not None, "filter should be firstly called when page is None"

            queryset = self.queryset[:self.page_size]
            next_value = self.queryset.count() > self.page_size and getattr(queryset.last(), self.target_field)

            return Page(queryset, self.count, next_value)

        queryset = self.queryset[self.page_size * page:self.page_size * (page + 1)]
        next_value = self.queryset.count() > self.page_size * (page + 1) and page + 1

        return Page(queryset, self.count, next_value)
