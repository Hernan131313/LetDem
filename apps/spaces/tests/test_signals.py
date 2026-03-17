def test_geohash_generation(db, space_factory):
    space = space_factory(latitude=40.4168, longitude=-3.7038)
    assert space.geohash is not None
    assert space.geohash != ""

