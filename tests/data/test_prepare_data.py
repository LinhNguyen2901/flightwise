"""Synthetic edge cases; none of these fixtures are production flight data."""
import pandas as pd
import pytest

from scripts.prepare_data import (COUNTS, aggregate, departure_hour, join_airports,
                                  prepare_airports, prepare_flights, rates)
from scripts.download_data import DownloadForm


def flights(**changes):
    row = dict(FlightDate='2025-01-01', DayOfWeek='3', Reporting_Airline='AA',
               Flight_Number_Reporting_Airline='1', OriginAirportID='100',
               OriginAirportSeqID='10001', Origin='AAA', DestAirportID='200',
               Dest='BBB', CRSDepTime='0830', ArrDelay='15', ArrDel15='1',
               Cancelled='0', Diverted='0')
    row.update(changes)
    return pd.DataFrame([row], dtype='string')


def airports(**changes):
    row = dict(AIRPORT_SEQ_ID='10001', AIRPORT_ID='100', AIRPORT='AAA',
               DISPLAY_AIRPORT_NAME='Synthetic airport', LATITUDE='30', LONGITUDE='-80',
               AIRPORT_START_DATE='2020-01-01', AIRPORT_THRU_DATE=None,
               AIRPORT_STATE_CODE='FL', AIRPORT_COUNTRY_CODE_ISO='US')
    row.update(changes)
    return pd.DataFrame([row], dtype='string')


@pytest.mark.parametrize('delay,flag,eligible,late', [
    ('14','0',1,0), ('15','1',1,1), (None,None,0,0),
    ('15',None,1,1), ('15','0',0,0), ('15','9',0,0),
])
def test_arrival_classification(delay, flag, eligible, late):
    result, _ = prepare_flights(flights(ArrDelay=delay, ArrDel15=flag), 2025, 1)
    assert result.arrival_eligible_count.iloc[0] == eligible
    assert result.late_count.iloc[0] == late


@pytest.mark.parametrize('field,value', [('Cancelled','1'), ('Diverted','1'),
                                        ('Cancelled',None), ('Diverted','9')])
def test_status_exclusion(field, value):
    result, _ = prepare_flights(flights(**{field: value}), 2025, 1)
    assert result.scheduled_count.sum() == 1
    assert result.arrival_eligible_count.sum() == 0


def test_times():
    actual = departure_hour(pd.Series(['0000','0059','0830','2359','2360','2400',None,'-1','830.5']))
    assert actual.iloc[:4].tolist() == [0,0,8,23]
    assert actual.iloc[4:].isna().all()


def test_duplicate_rows_are_reported_not_dropped():
    raw = pd.concat([flights(), flights(), flights(ArrDelay='16')], ignore_index=True)
    result, audit = prepare_flights(raw, 2025, 1)
    assert len(result) == 3
    assert audit['selected_field_duplicate_rows'] == 1
    assert audit['identity_collision_rows'] == 3


@pytest.mark.parametrize('changes', [{'FlightDate':'2025-02-01'}, {'DayOfWeek':'2'},
                                    {'OriginAirportID':None}])
def test_invalid_identity_or_period_fails(changes):
    with pytest.raises(ValueError):
        prepare_flights(flights(**changes), 2025, 1)


def test_history_join_uses_sequence_and_preserves_unmatched():
    reference = prepare_airports(pd.concat([airports(), airports(AIRPORT_SEQ_ID='10000',
        LATITUDE='40', AIRPORT_START_DATE='2010-01-01', AIRPORT_THRU_DATE='2019-12-31')]))
    rows, _ = prepare_flights(pd.concat([flights(), flights(OriginAirportSeqID='99999')]), 2025, 1)
    joined, audit = join_airports(rows, reference)
    assert len(joined) == 2
    assert joined.LATITUDE.iloc[0] == 30
    assert audit['unmatched_rows'] == 1


def test_duplicate_sequence_rejected():
    with pytest.raises(ValueError, match='Ambiguous'):
        prepare_airports(pd.concat([airports(), airports(LATITUDE='40')]))


@pytest.mark.parametrize('changes', [{'LATITUDE':'999'}, {'LATITUDE':None}, {'AIRPORT_THRU_DATE':'2024-12-31'}])
def test_invalid_coordinates_or_historical_date_not_mapped(changes):
    rows, _ = prepare_flights(flights(), 2025, 1)
    joined, audit = join_airports(rows, prepare_airports(airports(**changes)))
    assert audit['unmapped_rows'] == 1
    assert joined.scheduled_count.sum() == 1


def test_weighted_rates_nulls_and_unknown_cancellations():
    rows = pd.DataFrame([{**{k:0 for k in COUNTS}, 'group':'A', 'scheduled_count':1,
                         'cancellation_eligible_count':1, 'arrival_eligible_count':1, 'late_count':1},
                        {**{k:0 for k in COUNTS}, 'group':'A', 'scheduled_count':99,
                         'cancellation_eligible_count':99, 'arrival_eligible_count':99, 'late_count':0}])
    totals = aggregate(rows, ['group']).iloc[0]
    assert rates(totals)['late_arrival_rate'] == .01
    empty = {k:0 for k in COUNTS}
    assert rates(empty) == {'late_arrival_rate':None, 'cancellation_rate':None}
    assert rates({**empty,'scheduled_count':1})['cancellation_rate'] is None


def test_nested_bts_form():
    parser = DownloadForm()
    parser.feed('<form id="form1"><input type="hidden" name="__VIEWSTATE" value="x">'
                '<form name="search"></form><input type="checkbox" name="AIRPORT_SEQ_ID"></form>')
    assert parser.fields == {'__VIEWSTATE':'x', 'AIRPORT_SEQ_ID':'on'}
