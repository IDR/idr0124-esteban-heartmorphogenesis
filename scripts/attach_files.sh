#!/bin/bash

projectId=$1

for i in `cat /uod/idr/metadata/idr0124-esteban-heartmorphogenesis/scripts/segmented_files.txt`
do
	filename=${i##*/}
	imagename=${filename%%_*}
	images=`python /uod/idr/metadata/idr-utils/scripts/annotate/find_images.py "${imagename}\.lif" Project:$projectId`
	for image in $images
	do
		python /uod/idr/metadata/idr-utils/scripts/annotate/attach_file.py -m "image/nii" $i $image
	done
done
