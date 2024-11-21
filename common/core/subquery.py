from django.db.models import Subquery, JSONField


class PostgresqlJsonField(JSONField):
    def from_db_value(self, value, expression, connection):
        return value


class SubqueryJson(Subquery):
    """
    A replacement for select_related, that allows to fetch row of linked data as a subquery
    """
    template = "(SELECT row_to_json(_subquery) FROM (%(subquery)s) _subquery)"
    output_field = PostgresqlJsonField()


class SubqueryJsonAgg(Subquery):
    """
    A replacement for prefetch_related, that allows to fetch array of linked data as a subquery
    """
    template = "(SELECT array_to_json(coalesce(array_agg(row_to_json(_subquery)), array[]::json[])) FROM (%(subquery)s) _subquery)"
    output_field = PostgresqlJsonField()
