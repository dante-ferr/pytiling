# pytiling/utils/set_pixelated_scaling.py

from pyglet.gl import (
    GL_CLAMP_TO_EDGE,
    GL_NEAREST,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    glBindTexture,
    glTexParameteri,
)


def set_pixelated_scaling(image_or_texture):
    """
    Sets the texture scaling to nearest-neighbor for a given image
    or texture, preserving the pixelated look.

    Also clamps wrapping to the texture edge. Pyglet never sets a wrap mode,
    so textures keep the GL default GL_REPEAT: under a fractional camera
    transform, edge samples can land just outside [0, 1] and wrap to the
    opposite edge row/column, flashing 1px lines along tile borders.

    This function gets the underlying texture and applies the settings.
    """
    # Get the actual texture from the image data
    # This is the key change: we work with the texture object
    texture = image_or_texture.get_texture()

    # Bind the texture to apply changes, using the texture's attributes
    glBindTexture(texture.target, texture.id)

    # Set magnification and minification filters to GL_NEAREST
    glTexParameteri(texture.target, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(texture.target, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    glTexParameteri(texture.target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(texture.target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    # Unbind the texture
    glBindTexture(texture.target, 0)

    # Return the original image object, not the texture
    return image_or_texture
