import pytest
from dynamodb_utils.dict_utils import DynamoDbDictUtils

test_dict = {
    'id': '123',
    'title': 'Test Video',
    'statistics': {
        'viewCount': 1000,
        'importantDates': {
            'datatype': 'date',
            'formatType': 'iso8601',
            'isoFormat': 'YYYY-MM-DDTHH:MM:SSZ',
            'publishedAt': '2023-01-01T00:00:23Z',
            'places': {
                'location': 'New York',
                'coordinates': {
                    'latitude': 40.7128,
                    'longitude': -74.0060
                },
                'address': {
                    'street': '123 Main',
                    'city': 'New York',
                    'state': 'NY',
                    'zip': '10001',
                    'country': 'USA'
                }
            }
        }
    }
}

def test_flatten_dict():
    expected_flat_dict = {
        'id': '123',
        'title': 'Test Video',
        'statistics.viewCount': 1000,
        'statistics.importantDates.datatype': 'datetime',
        'statistics.importantDates.formatType': 'iso8601',
        'statistics.importantDates.isoformat': 'YYYY-MM-DDTHH:MM:SSZ',
        'statistics.importantDates.publishedAt': '2023-01-01T00:00:23Z',
        'statistics.importantDates.places.location': 'New York',
        'statistics.importantDates.places.coordinates.latitude': 40.7128,
        'statistics.importantDates.places.coordinates.longitude': -74.0060,
        'statistics.importantDates.places.address.street': '123 Main',
        'statistics.importantDates.places.address.city': 'New York',
        'statistics.importantDates.places.address.state': 'NY',
        'statistics.importantDates.places.address.zip': '10001',
        'statistics.importantDates.places.address.country': 'USA'
    }
    flattened_dict = DynamoDbDictUtils.flatten_dict(test_dict)
    assert flattened_dict == expected_flat_dict
