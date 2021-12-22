from collections import defaultdict
import omero
import omero.cli


PROJECT = "idr0124-esteban-heartmorphogenesis/experimentA"


def get_images(conn):
    project = conn.getObject('Project', attributes={'name': PROJECT})
    for dataset in project.listChildren():
        for image in dataset.listChildren():
            yield image


def map_images(conn):
    image_map = defaultdict(list)
    for image in get_images(conn):
        image_map[image.getName()].append(image)
    return image_map


def main(conn):
    for name, images in map_images(conn).items():
        if len(images) < 2:
            continue
        for i, image in enumerate(images):
            old_name = image.getName()
            new_name = f"{old_name} - {i+1}"
            image.setName(f"{new_name}")
            image.save()
            print(f"{old_name} -> {new_name}")


if __name__ == "__main__":
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn)
