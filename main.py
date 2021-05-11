import requests as req
import datetime as dt
import schedule
import time
from pynotifier import Notification

API_HEAD = 'https://cdn-api.co-vin.in/api'


def get_states():
    endpoint = API_HEAD + '/v2/admin/location/states'
    res = req.get(endpoint, headers={'User-Agent': 'PostmanRuntime/7.26.8'})
    if not res.ok:
        print(res.content)
        raise Exception('get states failed')
    states_res = res.json()
    return {d['state_name']: d['state_id'] for d in states_res['states']}


def get_districts(state_id):
    endpoint = API_HEAD + '/v2/admin/location/districts/{}'.format(state_id)
    res = req.get(endpoint, headers={'User-Agent': 'PostmanRuntime/7.26.8'})
    if not res.ok:
        print(res.content)
        raise Exception('get districts failed')
    district_res = res.json()
    return {d['district_name']: d['district_id'] for d in district_res['districts']}


def search_by_pin(pin, date):
    endpoint = API_HEAD + '/v2/appointment/sessions/public/calendarByPin'
    res = req.get(endpoint,
                  params=dict(pincode=str(pin), date=date),
                  headers={'User-Agent': 'PostmanRuntime/7.26.8'})
    if not res.ok:
        print(res.content)
        raise Exception('get by pin failed')

    return res.json()['centers']


def show_session(sess):
    print('=' * 40)
    print('PIN', sess['pincode'])
    print('DATE', sess['date'])
    print(sess['name'])
    print(sess['address'])
    print(sess['fee_type'])
    print('Fee', sess['fee'] if sess['fee_type'].lower() == 'paid' else 0)
    print('Capacity', sess['available_capacity'])
    print(sess['vaccine'])
    print(sess['slots'])
    print('AGE', sess['min_age_limit'])
    print('=' * 40)
    print()


def show_center(center):
    print('=' * 40)
    print(center['name'])
    print(center['address'])
    print(center['fee_type'])
    print('From', center['from'])

    for sess in center['sessions']:
        print('SESSION')
        print('Capacity', sess['available_capacity'])
        if (sess['available_capacity'] != 0) and (sess['min_age_limit'] == 18):
            Notification(
                title='Slot AVAILABLE!!!',
                description=center['name'],
                duration=5,  # Duration in seconds
                urgency='high'
            ).send()
        print(sess['slots'])
        print('AGE', sess['min_age_limit'])

    print('=' * 40)
    print()


def get_appointments(states, dates, minage=45, district_substrings=None):
    state_info = get_states()
    for state in states:
        print(state)
        sid = state_info[state]
        districts = get_districts(sid)
        for dname, district_id in districts.items():
            find = False
            if district_substrings:
                for d in district_substrings:
                    if d.lower() in dname.lower():
                        find = True
                        break
            else:
                find = True

            if not find:
                continue

            print('\t', dname)
            for date in dates:
                endpoint = API_HEAD + '/v2/appointment/sessions/public/findByDistrict'
                res = req.get(endpoint,
                              params=dict(district_id=district_id,
                                          date=date),
                              headers={'User-Agent': 'PostmanRuntime/7.26.8'})
                if res.ok:
                    sessions = res.json()['sessions']
                    for sess in sessions:
                        if sess['min_age_limit'] == minage:
                            sess['date'] = date
                            show_session(sess)
                else:
                    raise Exception(res.content)


def make_date_range(sdate, edate):
    s_date = dt.datetime.strptime(sdate, '%d-%m-%Y')
    e_date = dt.datetime.strptime(edate, '%d-%m-%Y')
    dates = []
    while s_date <= e_date:
        dates.append(s_date)
        s_date = s_date + dt.timedelta(days=1)

    return [d.strftime('%d-%m-%Y') for d in dates]


def check():
    try:
        get_appointments(['Karnataka'],
                         make_date_range(
                             (dt.datetime.today() + dt.timedelta(days=1)).strftime(
                                 '%d-%m-%Y'),
                             (dt.datetime.today() + dt.timedelta(days=10)).strftime(
                                 '%d-%m-%Y')),
                         minage=18, district_substrings=['bbmp'])
        print('*' * 20)
    except:
        print('Some error, retrying... :-[')


def check_pincodes(pincodes, dates):
    for pincode in pincodes:
        print('PIN', pincode)
        for date in dates:
            print('DATE', date)
            centers = search_by_pin(pincode, date)
            for center in centers:
                show_center(center)


if __name__ == '__main__':
    # schedule.every(2).minutes.do(lambda: check_pincodes(['560076'], make_date_range(
    #     (dt.datetime.today() + dt.timedelta(days=1)).strftime(
    #         '%d-%m-%Y'),
    #     (dt.datetime.today() + dt.timedelta(days=14)).strftime(
    #         '%d-%m-%Y'))))
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)

    # check_pincodes(['560076'], make_date_range(
    #     (dt.datetime.today() + dt.timedelta(days=1)).strftime(
    #         '%d-%m-%Y'),
    #     (dt.datetime.today() + dt.timedelta(days=14)).strftime(
    #         '%d-%m-%Y')))

    schedule.every(30).seconds.do(check)
    while True:
        schedule.run_pending()
        time.sleep(1)
