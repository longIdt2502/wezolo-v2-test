from rest_framework import response, status


def convert_response(message, status_code, **kwargs):
    """
        We want to convert body response to normalization.
    """

    results = {
        "message": message,
        "code": status_code,
    }
    for key, value in kwargs.items():
        results[key] = value
    return response.Response(status=status.HTTP_200_OK, data=results)
