import omero.cli
import omero.gateway
import re
import pandas

project_id = 2101
anno_file = "/uod/idr/metadata/idr0124-esteban-heartmorphogenesis/experimentA/idr0124-experimentA-annotation.csv"

def get_images(project):
    for dataset in project.listChildren():
        for image in dataset.listChildren():
            yield dataset, image


def read_channel_names(file):
    channel_names = {}
    df = pandas.read_csv(file, dtype=str)
    for index, row in df.iterrows():
        key = "{},{}".format(row["Dataset Name"],
                                 row["Image Name"])
        channel_names[key] = row["Channels"]
    return channel_names


if __name__ == "__main__":
    with omero.cli.cli_login() as c:
        channel_names = read_channel_names(anno_file)

        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        project = conn.getObject("Project", attributes={'id': project_id})

        for dataset, image in get_images(project):
            key = f"{dataset.getName()},{image.getName()}"
            if key in channel_names:
                channels = image.getChannels(noRE=True)
                names = channel_names[key].split(",")
                if len(channels) != len(names):
                    print(f"Number of channels doesn't match number of channel names. Ignoring image {image.getName()}.")
                    continue
                for i in range(0, len(names)):
                    lc = channels[i].getLogicalChannel()
                    chname = re.sub(".+:", "", names[i])
                    lc.setName(chname)
                    lc.save()
                    print(f"Set channel name {chname} for channel {i} of image {key}")
            else:
                print(f"No entry found for {key}.")
