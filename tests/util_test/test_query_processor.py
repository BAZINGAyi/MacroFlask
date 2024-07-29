normal_body = {
        "pagination": {
            "page": 1,
            "page_count": 10
        },
        "sorting": {
            "sort_by": "username",
            "order": "asc"
        },
        "filters": {
            "and": [
                # {"field": "email", "op": "like", "value": 18},
                {
                    "or": [
                        {"field": "username", "op": "like", "value": "admin"},
                        {"field": "username", "op": "like", "value": "Jane"}
                    ]
                },
                {"field": "id", "op": "in", "value": [1, 2, 3]}
            ]
        },
        "need_fields": ["id", "username", "email"],
    }

group_by_body = {
        "pagination": {"page": 1, "page_count": 10},
        "sorting": {"sort_by": "username", "order": "asc"},
        "filters": {"and": [{"field": "id", "op": ">", "value": 0}]},
        "need_fields": ["username", "count(id)", "sum(id)"],
        "group_by": ["username"]
}