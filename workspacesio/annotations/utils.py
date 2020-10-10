from .schemas import Feature


# interpolate all features [a, b)
def interpolate(a: Feature, b: Feature) -> List[Feature]:
    if a.interpolate is False:
        raise ValueError("Cannot interpolate feature without interpolate enabled")
    if b.frame <= a.frame:
        raise ValueError("b.frame must be larger than a.frame")
    feature_list = [a]
    frame_range = b.frame - a.frame
    for frame in range(1, frame_range):
        delta = frame / frame_range
        inverse_delta = 1 - delta
        bounds: List[float] = [
            round((abox * delta) + (bbox * inverse_delta))
            for (abox, bbox) in zip(a.bounds, b.bounds)
        ]
        feature_list.append(
            Feature(
                frame=a.frame + frame,
                bounds=bounds,
                keyframe=False,
            )
        )
    return feature_list
