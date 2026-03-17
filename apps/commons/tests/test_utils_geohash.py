import pytest
import geohash
from commons.utils import generate_coordinates_geohash
from commons.settings import PRECISION_NUMBER_TO_GEOHASH
from dynamic_preferences.registries import global_preferences_registry

global_preferences = global_preferences_registry.manager()

@pytest.mark.parametrize("lat,lng", [
    (40.416775, -3.703790),   # Madrid
    (48.856613, 2.352222),    # París
    (34.052235, -118.243683), # Los Ángeles
])
def test_geohash_basic(lat, lng):
    """Verifica que se genere un geohash válido para coordenadas conocidas."""
    precision = global_preferences[PRECISION_NUMBER_TO_GEOHASH]
    result = generate_coordinates_geohash(lat, lng)
    expected = geohash.encode(round(lat, 6), round(lng, 6), precision=precision)
    assert result == expected
    assert isinstance(result, str)
    assert len(result) == precision


def test_geohash_stability_with_small_variations():
    """Verifica que pequeñas variaciones en lat/lng no cambien el geohash."""
    lat = 40.416775
    lng = -3.703790
    result1 = generate_coordinates_geohash(lat, lng)
    result2 = generate_coordinates_geohash(lat + 1e-8, lng + 1e-8)  # variación mínima
    assert result1 == result2


def test_geohash_different_locations():
    """Verifica que distintas ciudades generen geohash distintos."""
    madrid = generate_coordinates_geohash(40.416775, -3.703790)
    paris = generate_coordinates_geohash(48.856613, 2.352222)
    assert madrid != paris


def test_geohash_precision_setting(monkeypatch):
    """Verifica que el geohash respete la precisión configurada."""
    monkeypatch.setitem(global_preferences, PRECISION_NUMBER_TO_GEOHASH, 5)
    result = generate_coordinates_geohash(40.416775, -3.703790)
    assert len(result) == 5
