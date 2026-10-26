""" Tests for NodeNameStore """
import json
import logging

from mtg.bot.meshtastic.node_names import NodeNameStore, normalize_node_id

LOG = logging.getLogger('test')


def test_normalize_node_id():
    assert normalize_node_id(2446632876) == '!91d4a7ac'
    assert normalize_node_id('!91D4A7AC') == '!91d4a7ac'
    assert normalize_node_id('91d4a7ac') == '!91d4a7ac'
    assert normalize_node_id('None') is None
    assert normalize_node_id(None) is None


def test_learn_persist_and_reload(tmp_path):
    path = str(tmp_path / 'names.json')
    store = NodeNameStore(path, LOG)
    assert store.get('!91d4a7ac') is None
    assert store.learn(2446632876, 'Renato', 'rena') is True
    assert store.learn('!91d4a7ac', 'Renato', 'rena') is False
    assert store.get(2446632876) == 'Renato'
    with open(path, encoding='utf-8') as fh:
        assert json.load(fh)['!91d4a7ac']['short'] == 'rena'
    assert NodeNameStore(path, LOG).get('!91d4a7ac') == 'Renato'


def test_seed_and_learned_override(tmp_path):
    path = str(tmp_path / 'names.json')
    store = NodeNameStore(path, LOG, seed='!91d4a7ac=Renato, !3fd72c6c=elen,bad')
    assert store.get('!3fd72c6c') == 'elen'
    store.learn('!3fd72c6c', 'Elen U')
    assert NodeNameStore(path, LOG, seed='!3fd72c6c=elen').get('!3fd72c6c') == 'Elen U'
    assert 'Renato' in store.as_seed()
