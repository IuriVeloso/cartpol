from django.test import TestCase

from cartpol_app.models import County, State


class StateModelTest(TestCase):
    def setUp(self):
        self.state_data = {
            'name': 'Test State',
            'tse_id': '123'
        }
        self.state = State.objects.create(**self.state_data)

    def test_state_creation(self):
        self.assertEqual(self.state.name, self.state_data['name'])
        self.assertEqual(self.state.tse_id, self.state_data['tse_id'])
        self.assertEqual(str(self.state), self.state_data['name'])

    def test_state_ordering(self):
        State.objects.create(name='A State', tse_id='456')
        State.objects.create(name='B State', tse_id='789')
        states = State.objects.all()
        self.assertEqual(states[0].name, 'A State')
        self.assertEqual(states[1].name, 'B State')
        self.assertEqual(states[2].name, 'Test State')


class CountyModelTest(TestCase):
    def setUp(self):
        self.state = State.objects.create(name='Test State', tse_id='123')
        self.county_data = {
            'name': 'Test County',
            'tse_id': '456',
            'state': self.state
        }
        self.county = County.objects.create(**self.county_data)

    def test_county_creation(self):
        self.assertEqual(self.county.name, self.county_data['name'])
        self.assertEqual(self.county.tse_id, self.county_data['tse_id'])
        self.assertEqual(self.county.state, self.state)
        self.assertEqual(str(self.county), self.county_data['name'])

    def test_county_ordering(self):
        County.objects.create(name='A County', tse_id='789', state=self.state)
        County.objects.create(name='B County', tse_id='012', state=self.state)
        counties = County.objects.all()
        self.assertEqual(counties[0].name, 'A County')
        self.assertEqual(counties[1].name, 'B County')
        self.assertEqual(counties[2].name, 'Test County')
