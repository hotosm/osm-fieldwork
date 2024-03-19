from io import BytesIO


def read_bytes_geojson(file_path):
    with open(file_path, "rb") as geojson_file:
        boundary = geojson_file.read()  # read as a `bytes` object.
        boundary_bytesio = BytesIO(boundary)  # add to a BytesIO wrapper

    return boundary_bytesio
