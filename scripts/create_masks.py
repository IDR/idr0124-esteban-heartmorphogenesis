#!/usr/bin/env python

import os
import numpy as np
import re
import omero
import omero.cli
from omero.gateway import BlitzGateway
from omero.gateway import ColorHolder
from omero.model import MaskI
from omero.rtypes import (
    rdouble,
    rint,
    rstring,
)

PROJECT = "idr0124-esteban-heartmorphogenesis/experimentA"
RGBA = (255, 255, 0, 128)
DELETE_ROIS = True
DRYRUN = True

PATTERN = re.compile(r"(?P<parent>.+)_SegImgs_(?P<desc>.+).nii")

def mask_from_binary_image(binim, rgba=None, z=None, c=None, t=None, text=None):
    """
    Create a mask shape from a binary image (background=0)

    :param numpy.array binim: Binary 2D array, must contain values [0, 1] only
    :param rgba int-4-tuple: Optional (red, green, blue, alpha) colour
    :param z: Optional Z-index for the mask
    :param c: Optional C-index for the mask
    :param t: Optional T-index for the mask
    :param text: Optional text for the mask
    :return: An OMERO mask
    """

    # Find bounding box to minimise size of mask
    xmask = binim.sum(0).nonzero()[0]
    ymask = binim.sum(1).nonzero()[0]
    if any(xmask) and any(ymask):
        x0 = min(xmask)
        w = max(xmask) - x0 + 1
        y0 = min(ymask)
        h = max(ymask) - y0 + 1
        submask = binim[y0:(y0 + h), x0:(x0 + w)]
        if (not np.array_equal(np.unique(submask), [0, 1]) and not
        np.array_equal(np.unique(submask), [1])):
            raise
    else:
        x0 = 0
        w = 0
        y0 = 0
        h = 0
        submask = []

    mask = MaskI()
    mask.setBytes(np.packbits(np.asarray(submask, dtype=int)))
    mask.setWidth(rdouble(w))
    mask.setHeight(rdouble(h))
    mask.setX(rdouble(x0))
    mask.setY(rdouble(y0))

    if w <= 0 or h <= 0:
        return None

    if rgba is not None:
        ch = ColorHolder.fromRGBA(*rgba)
        mask.setFillColor(rint(ch.getInt()))
    if z is not None:
        mask.setTheZ(rint(z))
    if c is not None:
        mask.setTheC(rint(c))
    if t is not None:
        mask.setTheT(rint(t))
    if text is not None:
        mask.setTextValue(rstring(text))

    return mask


def get_mask_images(conn):
    project = conn.getObject('Project', attributes={'name': PROJECT})
    for dataset in project.listChildren():
        for image in dataset.listChildren():
            match = PATTERN.match(image.name)
            if match:
                yield (match.groupdict()['parent'], match.groupdict()['desc'], image)


def get_image(conn, parent):
    project = conn.getObject('Project', attributes={'name': PROJECT})
    for dataset in project.listChildren():
        for image in dataset.listChildren():
            match = re.match(f"{parent}.*\.lif.*", image.name)
            if match:
                return image
    print(f"Could not find target image {parent}")
    return None


def save_roi(conn, im, roi):
    us = conn.getUpdateService()
    im = conn.getObject('Image', im.id)
    roi.setImage(im._obj)
    us.saveAndReturnObject(roi)


def delete_rois(conn, im):
    result = conn.getRoiService().findByImage(im.id, None)
    to_delete = []
    for roi in result.rois:
        to_delete.append(roi.getId().getValue())
    if to_delete:
        print(f"Deleting existing {len(to_delete)} rois on image {im.name}.")
        conn.deleteObjects("Roi", to_delete, deleteChildren=True, wait=True)


def create_roi(seg_img, desc):
    zct_list = []
    for z in range(0, seg_img.getSizeZ()):
        zct_list.append((z, 0, 0))
    planes = seg_img.getPrimaryPixels().getPlanes(zct_list)
    roi = omero.model.RoiI()
    has_masks = False
    for i, plane in enumerate(planes):
        mask = mask_from_binary_image(plane > 0, rgba=RGBA, z=i, c=None, t=None, text=desc)
        if mask:
            print(f"Found mask on plane {i}.")
            roi.addShape(mask)
            has_masks = True
    if has_masks:
        return roi
    return None


def main(conn):
    deleted = []
    for (parent, desc, mask_im) in get_mask_images(conn):
        im = get_image(conn, parent)
        if im:
            print("Processing {} - {}".format(mask_im.name, im.name))
            if DELETE_ROIS and not DRYRUN and im.id not in deleted:
                delete_rois(conn, im)
                deleted.append(im.id)
            roi = create_roi(mask_im, desc)
            if not DRYRUN and roi:
                print("Save Masks")
                save_roi(conn, im, roi)


if __name__ == "__main__":
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn)
