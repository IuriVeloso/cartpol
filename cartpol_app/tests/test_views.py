from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cartpol_app.models import County, State


class StateViewTest(APITestCase):
    def setUp(self):
        # Create test data
        self.state_data = {
            'name': 'Test State',
            'tse_id': '123'
        }
        self.state = State.objects.create(**self.state_data)
        self.url = reverse('state-list')

    def test_get_states(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.state_data['name'])

    def test_create_state(self):
        new_state_data = {
            'name': 'New State',
            'tse_id': '456'
        }
        response = self.client.post(self.url, new_state_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(State.objects.count(), 2)
        self.assertEqual(State.objects.get(name='New State').tse_id, '456')

    def test_search_state_by_name(self):
        response = self.client.get(f"{self.url}?name=Test State")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test State')


class CountyViewTest(APITestCase):
    def setUp(self):
        # Create test data
        self.state = State.objects.create(name='Test State', tse_id='123')
        self.county_data = {
            'name': 'Test County',
            'tse_id': '456',
            'state': self.state
        }
        self.county = County.objects.create(**self.county_data)
        self.url = reverse('county-list')

    def test_get_counties(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.county_data['name'])

    def test_create_county(self):
        new_county_data = {
            'name': 'New County',
            'tse_id': '789',
            'state': self.state.id
        }
        response = self.client.post(self.url, new_county_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(County.objects.count(), 2)
        self.assertEqual(County.objects.get(name='New County').tse_id, '789')

    def test_search_county_by_name(self):
        response = self.client.get(f"{self.url}?name=Test County")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test County')

    def test_search_county_by_state(self):
        response = self.client.get(f"{self.url}?state=Test State")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test County')
