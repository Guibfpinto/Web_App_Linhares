# fastapi_client.py
import requests
from typing import Optional, List, Dict

class FastAPIMonitorClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})

    def login(self, username: str, password: str) -> bool:
        try:
            resp = self.session.post(f'{self.base_url}/api/auth/login',
                                     json={'username': username, 'password': password})
            if resp.status_code == 200:
                self.token = resp.json().get('access_token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                return True
            return False
        except Exception:
            return False

    def get_live_fixture(self, team_id: Optional[int] = None) -> Optional[int]:
        params = {'team_id': team_id} if team_id else {}
        resp = self.session.get(f'{self.base_url}/api/fixtures/live', params=params)
        if resp.status_code == 200:
            return resp.json().get('fixture_id')
        return None

    def get_fixture_details(self, fixture_id: int) -> Dict:
        resp = self.session.get(f'{self.base_url}/api/fixtures/{fixture_id}')
        resp.raise_for_status()
        return resp.json()

    def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        resp = self.session.get(f'{self.base_url}/api/fixtures/{fixture_id}/events')
        resp.raise_for_status()
        return resp.json()

    def get_fixture_statistics(self, fixture_id: int) -> List[Dict]:
        resp = self.session.get(f'{self.base_url}/api/fixtures/{fixture_id}/statistics')
        resp.raise_for_status()
        return resp.json()

    def get_fixture_players(self, fixture_id: int) -> List[Dict]:
        resp = self.session.get(f'{self.base_url}/api/fixtures/{fixture_id}/players')
        resp.raise_for_status()
        return resp.json()

    def get_fixture_lineups(self, fixture_id: int) -> List[Dict]:
        resp = self.session.get(f'{self.base_url}/api/fixtures/{fixture_id}/lineups')
        resp.raise_for_status()
        return resp.json()

    def get_fixtures(self, team: Optional[int] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
        params = {}
        if team:
            params['team'] = team
        if from_date:
            params['from_date'] = from_date
        if to_date:
            params['to_date'] = to_date
        resp = self.session.get(f'{self.base_url}/api/fixtures', params=params)
        resp.raise_for_status()
        return resp.json()