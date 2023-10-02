from server.apps.pictures.intrastructure.services.placeholder import PicturesFetch


def test_picture_service():
    service = PicturesFetch('http://json-server:3000', 5)
    result = service(limit=10)
    assert result[0].id == 1
    assert result[1].id == 2
