import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export default function () {
  const url = 'https://cartpol-api-17ba0f42060a.herokuapp.com/cartpol/political-votes/630524';
  // const url = 'http://127.0.0.1:8000/cartpol/political-votes/630524';

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  check(http.get(url, params), {
    'status is 200': (r) => r.status == 200,
  }) || errorRate.add(1);

  sleep(1);
}