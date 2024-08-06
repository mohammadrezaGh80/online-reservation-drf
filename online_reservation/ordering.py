from rest_framework.filters import OrderingFilter


class DoctorOrderingFilter(OrderingFilter):
    direction_fields = {
        'max_successful_reserve': '-',
        'closest_free_reserve': ''
    }

    def filter_queryset(self, request, queryset, view):
        ordering_params = request.query_params.get(self.ordering_param)
        valid_fields = [field[0] for field in self.get_valid_fields(queryset, view, request)]

        if ordering_params:
            fields = [param.strip() for param in ordering_params.split(',')]
            ordering = []
            
            for field in fields:
                if field in valid_fields:
                    ordering.append(f'{self.direction_fields[field]}{field}')
            
            if ordering:
                return queryset.order_by(*ordering)

        return queryset