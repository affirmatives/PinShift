from __future__ import annotations

import math


PI = math.pi
AXIS = 6378245.0
OFFSET = 0.00669342162296594323


def out_of_china(longitude: float, latitude: float) -> bool:
    return longitude < 72.004 or longitude > 137.8347 or latitude < 0.8293 or latitude > 55.8271


def wgs84_to_gcj02(longitude: float, latitude: float) -> tuple[float, float]:
    if out_of_china(longitude, latitude):
        return longitude, latitude
    d_lat = _transform_lat(longitude - 105.0, latitude - 35.0)
    d_lng = _transform_lng(longitude - 105.0, latitude - 35.0)
    rad_lat = latitude / 180.0 * PI
    magic = math.sin(rad_lat)
    magic = 1 - OFFSET * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((AXIS * (1 - OFFSET)) / (magic * sqrt_magic) * PI)
    d_lng = (d_lng * 180.0) / (AXIS / sqrt_magic * math.cos(rad_lat) * PI)
    return longitude + d_lng, latitude + d_lat


def gcj02_to_wgs84(longitude: float, latitude: float) -> tuple[float, float]:
    if out_of_china(longitude, latitude):
        return longitude, latitude
    gcj_lng, gcj_lat = wgs84_to_gcj02(longitude, latitude)
    return longitude * 2 - gcj_lng, latitude * 2 - gcj_lat


def _transform_lat(longitude: float, latitude: float) -> float:
    ret = -100.0 + 2.0 * longitude + 3.0 * latitude + 0.2 * latitude * latitude
    ret += 0.1 * longitude * latitude + 0.2 * math.sqrt(abs(longitude))
    ret += (20.0 * math.sin(6.0 * longitude * PI) + 20.0 * math.sin(2.0 * longitude * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(latitude * PI) + 40.0 * math.sin(latitude / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(latitude / 12.0 * PI) + 320 * math.sin(latitude * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(longitude: float, latitude: float) -> float:
    ret = 300.0 + longitude + 2.0 * latitude + 0.1 * longitude * longitude
    ret += 0.1 * longitude * latitude + 0.1 * math.sqrt(abs(longitude))
    ret += (20.0 * math.sin(6.0 * longitude * PI) + 20.0 * math.sin(2.0 * longitude * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(longitude * PI) + 40.0 * math.sin(longitude / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(longitude / 12.0 * PI) + 300.0 * math.sin(longitude / 30.0 * PI)) * 2.0 / 3.0
    return ret
