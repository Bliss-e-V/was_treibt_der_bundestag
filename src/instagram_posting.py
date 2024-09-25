#!/usr/bin/env python

"""instagram_posting.py: Contains code to automatically post on Instragram.
                         Without https://github.com/subzeroid/instagrapi this
                         wouldn't have possible able so easily.
                         Unfortunately, Instagram does not allow for
                         hyperlinks in posts, so we will not provide the
                         PDF url here. :-() """


def post_carousel(client, image_paths, caption):
    """
    Posts given images with given caption in an album/'Carousel' post to
    given client.
    Note that only JPG is supported!
    """
    if len(image_paths) == 1:
        client.photo_upload(image_paths[0], caption=caption)
        return
    # Check if there are more than 10 images! Need to split up the post then?!
    client.album_upload(image_paths, caption=caption)
