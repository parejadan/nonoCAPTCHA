import itertools
import os


def split_image(image_obj, pieces, save_to):
    """Splits an image into constituent pictures of x"""
    width, height = image_obj.size
    if pieces == 9:
        # Only case solved so far
        row_length = 3
        interval = width // row_length
        for x, y in itertools.product(range(row_length), repeat=2):
            cropped = image_obj.crop((interval*x, interval*y,
                                      interval*(x+1), interval*(y+1)))
            cropped.save(os.path.join(save_to, f'{y*row_length+x}.jpg'))