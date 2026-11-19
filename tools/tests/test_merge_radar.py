"""Tests for tools/merge-radar.py, loaded by path (hyphenated filename)."""
import importlib.util
import os

_HERE = os.path.dirname(__file__)
_spec = importlib.util.spec_from_file_location(
    "merge_radar", os.path.join(_HERE, "..", "merge-radar.py"))
mr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mr)


def _sitio(victim, group, day='2026-11-19', country='US'):
    return {'id': 'aie-' + victim, 'origin': 'am-i-exposed', 'day': day, 'date': day,
            'seen': day + 'T10:00:00+00:00', 'victim': victim, 'group': group,
            'type': 'ransomware', 'status': 'reclamado', 'country': country,
            'sector': 'otros', 'victims': 1, 'batch': False, 'claim': '',
            'sources': [{'name': 'RansomLook', 'url': 'https://www.ransomlook.io/'}],
            'prospect': False, 'prospectNote': '', 'historical': False,
            'republished': False}


def _radar(victim, group, claim='', n=None, day='2026-11-19'):
    return {'id': 'r-' + victim, 'origin': 'Radar', 'day': day, 'date': day,
            'seen': day + 'T14:00:00+00:00', 'victim': victim, 'group': group,
            'type': 'ransomware', 'status': 'reclamado', 'country': 'PE',
            'sector': 'salud', 'victims': n or 1, 'batch': bool(n), 'claim': claim,
            'sources': [{'name': 'ransomware.live', 'url': 'https://www.ransomware.live/'}],
            'prospect': True, 'prospectNote': 'x', 'historical': False,
            'republished': False}


def test_keys_match_domain_and_name():
    assert mr.claves('www.sleepboxbymiracle.com') & mr.claves('sleepboxbymiracle.com (hoteleria)')
    assert mr.claves('Smith & Green, Attorneys at Law PLLC') == mr.claves('Smith & Green Attorneys at Law')


def test_same_case_keeps_radar_row_with_both_sources():
    out = mr.fusiona([_radar('Clinica Sur S.A.C.', 'Qilin')], [_sitio('clinica sur', 'qilin')])
    assert len(out) == 1
    assert out[0]['origin'] == 'Ambos'
    assert [s['name'] for s in out[0]['sources']] == ['ransomware.live', 'RansomLook']


def test_different_group_is_not_a_duplicate():
    out = mr.fusiona([_radar('Clinica Sur', 'Qilin')], [_sitio('Clinica Sur', 'akira')])
    assert len(out) == 2


def test_batch_fully_covered_is_dropped():
    lote = _radar('Grupo Krybit: 2 víctimas', 'Krybit', 'alpha.com (x), betaco.ae (y)', n=2)
    out = mr.fusiona([lote], [_sitio('www.alpha.com', 'krybit'), _sitio('betaco.ae', 'krybit')])
    assert len(out) == 2 and all(r['origin'] == 'am-i-exposed' for r in out)
    assert {r['group'] for r in out} == {'Krybit'}


def test_batch_partly_covered_is_reduced():
    lote = _radar('Grupo Soul: 3 víctimas', 'Soul', 'Alpha Corp, Gamma Ltd, Delta Inc', n=3)
    out = mr.fusiona([lote], [_sitio('Alpha Corp', 'soul')])
    lotes = [r for r in out if r['batch']]
    assert lotes[0]['victims'] == 2 and lotes[0]['victim'].startswith('Grupo Soul: 2')
    assert sum(r['victims'] for r in out) == 3
