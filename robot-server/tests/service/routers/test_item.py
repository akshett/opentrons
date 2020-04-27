from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY


def test_get_item(api_client):
    item_id = "1"
    response = api_client.get(f'items/{item_id}')
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "data": {
            "id": item_id,
            "type": 'Item',
            "attributes": {
                "name": "apple",
                "quantity": 10,
                "price": 1.2
            },
        },
        "links": {
            "self": f'/items/{item_id}',
        }
    }


def test_create_item(api_client):
    response = api_client.post(
        "/items",
        json={
            "data": {
                "type": "Item",
                "attributes": {
                    "name": "apple",
                    "quantity": 10,
                    "price": 1.20
                }
            }
        }
    )
    # NOTE(isk: 3/11/20): We don't have the id until the resource is created
    response_id = response.json().get("data", {}).get('id')
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "data": {
            "id": response_id,
            "type": 'Item',
            "attributes": {
                "name": "apple",
                "quantity": 10,
                "price": 1.20
            },
        },
        "links": {
            "self": f'/items/{response_id}',
        }
    }


def test_create_item_with_attribute_validation_error(api_client):
    response = api_client.post(
        "/items",
        json={
            "data": {
                "type": "item",
                "attributes": {}
            }
        }
    )
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        'errors': [{
            'status': str(HTTP_422_UNPROCESSABLE_ENTITY),
            'title': 'value_error.missing',
            'detail': 'field required',
            'source': {
                'pointer': '/body/item_request/data/attributes/name',
            }
        }, {
            'status': str(HTTP_422_UNPROCESSABLE_ENTITY),
            'title': 'value_error.missing',
            'detail': 'field required',
            'source': {
                'pointer': '/body/item_request/data/attributes/quantity',
            }
        }, {
            'status': str(HTTP_422_UNPROCESSABLE_ENTITY),
            'title': 'value_error.missing',
            'detail': 'field required',
            'source': {
                'pointer': '/body/item_request/data/attributes/price',
            }
        }]
    }
