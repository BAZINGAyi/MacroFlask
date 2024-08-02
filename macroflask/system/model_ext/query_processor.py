from typing import List, Dict, Union, Optional

from sqlalchemy.orm import load_only, joinedload, sessionmaker

from sqlalchemy.orm import Query, load_only, joinedload
from sqlalchemy import or_, and_, text, func


class QueryRequest:
    def __init__(self, body: Dict[str, Union[Dict, List]]):
        self.pagination = body.get('pagination', {})
        self.sorting = body.get('sorting', {})
        self.filters = body.get('filters', {})
        self.need_fields = body.get('need_fields', [])
        self.relations = body.get('relations', [])
        self.group_by = body.get('group_by', [])

        # Validation
        self._validate()

    def _validate(self):
        """ Validate the query request """
        if 'page' not in self.pagination or 'page_count' not in self.pagination:
            raise ValueError("Pagination must include 'page' and 'page_count'.")

        if self.sorting:
            if isinstance(self.sorting, dict):
                if 'sort_by' not in self.sorting or 'order' not in self.sorting:
                    raise ValueError("Sorting must include 'sort_by' and 'order'.")
                if not isinstance(self.sorting.get('sort_by', ''), str):
                    raise ValueError("Sorting 'sort_by' should be a string.")
                if not isinstance(self.sorting.get('order', 'asc'), str):
                    raise ValueError("Sorting 'order' should be a string.")
            elif isinstance(self.sorting, list):
                for sort in self.sorting:
                    if 'field' not in sort or 'order' not in sort:
                        raise ValueError("Each sorting criterion must include 'field' and 'order'.")
            else:
                raise ValueError("Sorting should be a dict or list of sorting criteria.")

        if self.filters:
            self._validate_filters(self.filters)

        if not isinstance(self.need_fields, list):
            raise ValueError("Need fields should be a list.")

        if not isinstance(self.relations, list):
            raise ValueError("Relations should be a list.")

        if self.group_by and self.need_fields:
            self._validate_group_by_fields()

    def _validate_filters(self, filters):
        """ Validate the filters recursively """
        if isinstance(filters, dict):
            if any(k not in ['and', 'or'] for k in filters.keys()):
                # Check if it is a simple filter (e.g., {"field": "username", "op": "like", "value": "John"})
                if 'field' in filters and 'op' in filters and 'value' in filters:
                    self._validate_filter(filters)
                else:
                    raise ValueError("Filters must contain only 'and', 'or', or a single filter with 'field', 'op', and 'value'.")
            else:
                for key, value in filters.items():
                    if not isinstance(value, list):
                        raise ValueError(f"Filters under '{key}' must be a list.")
                    for f in value:
                        self._validate_filters(f)

        elif isinstance(filters, list):
            for f in filters:
                self._validate_filters(f)

        else:
            raise ValueError("Filters must be a dict or list.")

    def _validate_filter(self, filter: Dict[str, Union[str, int]]):
        """ Validate a single filter """
        if not isinstance(filter.get('field', ''), str):
            raise ValueError("Filter 'field' must be a string.")
        if not isinstance(filter.get('op', ''), str):
            raise ValueError("Filter 'op' must be a string.")
        if 'value' not in filter:
            raise ValueError("Filter must include a 'value'.")

    def _validate_group_by_fields(self):
        """ Validate that all selected fields are either in group_by or are aggregate functions """
        valid_aggregate_functions = {'count', 'sum', 'avg', 'min', 'max'}
        group_by_fields = set(self.group_by)
        for field in self.need_fields:
            if field not in group_by_fields:
                if not any(func in field for func in valid_aggregate_functions):
                    raise ValueError(f"Field '{field}' must either be in 'group_by' or be an aggregate function.")

    def get_pagination(self) -> Dict[str, int]:
        return self.pagination

    def get_sorting(self) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
        return self.sorting

    def get_filters(self) -> Optional[Dict[str, Union[List[Dict[str, Union[str, int]]], Dict]]]:
        return self.filters

    def get_need_fields(self) -> Optional[List[str]]:
        return self.need_fields

    def get_relations(self) -> Optional[List[str]]:
        return self.relations

    def get_group_by(self):
        return self.group_by


class QueryProcessor:
    def __init__(self, model, session, query: Query, request_body: QueryRequest):
        """
        :param session:
        :param query:
        :param request_body:
        """
        self.session = session
        self.model = model
        self.query = session.query(model)
        self.request_body = request_body

    def apply_pagination(self):
        """ Apply pagination to the query. """
        pagination = self.request_body.get_pagination()

        if 'page' in pagination and 'page_count' in pagination:
            page = pagination['page']
            page_count = pagination['page_count']
            self.query = self.query.limit(page_count).offset((page - 1) * page_count)

    def apply_sorting(self):
        """ Apply sorting to the query. """
        sorting = self.request_body.get_sorting().get('sort_by', None)
        if not sorting:
            return

        elif isinstance(sorting, str):
            order = self.request_body.get_sorting().get('order', 'asc')
            if order == 'asc':
                self.query = self.query.order_by(text(f"{sorting} asc"))
            else:
                self.query = self.query.order_by(text(f"{sorting} desc"))

        elif isinstance(sorting, list):
            for sort in sorting:
                field = sort.get('field')
                order = sort.get('order', 'asc')
                if field:
                    if order == 'asc':
                        self.query = self.query.order_by(text(f"{field} asc"))
                    else:
                        self.query = self.query.order_by(text(f"{field} desc"))

    def apply_filters(self):
        """ Apply filters to the query. """
        filters = self.request_body.get_filters()
        if 'and' in filters:
            self.query = self.query.filter(self._apply_filter_list(filters['and'], and_))
        if 'or' in filters:
            self.query = self.query.filter(self._apply_filter_list(filters['or'], or_))

    def _apply_filter_list(self, filter_list, operator):
        """ Apply a list of filters to the query using the specified operator. """
        conditions = []
        for f in filter_list:
            if 'and' in f:
                conditions.append(self._apply_filter_list(f['and'], and_))
            elif 'or' in f:
                conditions.append(self._apply_filter_list(f['or'], or_))
            else:
                field = f.get('field')
                op = f.get('op')
                value = f.get('value')

                if not field or not op or value is None:
                    continue

                column = getattr(self.model, field, None)
                if column is None:
                    continue

                if op == '==':
                    conditions.append(column == value)
                elif op == 'like':
                    conditions.append(column.like(f'%{value}%'))
                elif op == '>':
                    conditions.append(column > value)
                elif op == '<':
                    conditions.append(column < value)
                elif op == '>=':
                    conditions.append(column >= value)
                elif op == '<=':
                    conditions.append(column <= value)
                elif op == '!=':
                    conditions.append(column != value)
                elif op == 'in' and isinstance(value, list):
                    conditions.append(column.in_(value))

        return operator(*conditions) if conditions else True

    def apply_field_selection(self):
        """ Select specific fields to be returned, supporting group by with aggregate functions. """
        need_fields = self.request_body.get_need_fields()
        if need_fields:
            selected_columns = []
            for field in need_fields:
                if '(' in field and ')' in field:
                    # Handle aggregate functions
                    func_name, col_name = field.split('(')
                    col_name = col_name.rstrip(')')
                    column = getattr(self.model, col_name, None)
                    if column is None:
                        raise ValueError(f"Field '{col_name}' is not a valid column of the model.")
                    aggregate_func = getattr(func, func_name, None)
                    if aggregate_func is None:
                        raise ValueError(f"Aggregate function '{func_name}' is not valid.")
                    selected_columns.append(aggregate_func(column).label(field))
                else:
                    # Regular fields
                    column = getattr(self.model, field, None)
                    if column is None:
                        raise ValueError(f"Field '{field}' is not a valid column of the model.")
                    selected_columns.append(column)
            self.query = self.query.with_entities(*selected_columns)

    def apply_relations(self):
        """ Apply relation loading if needed. """
        relations = self.request_body.get_relations()
        for relation in relations:
            self.query = self.query.options(joinedload(relation))

    def apply_group_by(self):
        """ Apply group by to the query. """
        group_by = self.request_body.get_group_by()
        if group_by:
            group_by_columns = [getattr(self.model, field) for field in group_by]
            self.query = self.query.group_by(*group_by_columns)

    def process(self):
        """ Process the query according to the request. """
        self.apply_filters()
        self.apply_sorting()
        self.apply_group_by()
        self.apply_pagination()
        self.apply_field_selection()
        # self.apply_relations()
        datas = self.query.all()

        new_result = []
        if self.request_body.get_need_fields():
            for data in datas:
                new_data = {}
                for index, field in enumerate(self.request_body.get_need_fields()):
                    new_data[field] = data[index]
                new_result.append(new_data)
            datas = new_result

        return datas
